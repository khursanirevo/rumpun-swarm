"""rumpun audit — reflection over the season ledger (DESIGN section 15).

Phase-2 self-evolution needs reflection: run_audit reads the last N musim
seasons, records which ledger artifacts each engine season (a season with a
rimba/<sid>/ dir) actually wrote, and appends one akar record of
deterministic findings plus at most three candidate mutations — every
findings and candidate line cites the season ids it rests on. The verb
mutates nothing except appending that record: candidates reach the pipeline
only through the existing evolve gate (lint plus operator at the manual
stage).

Deterministic trigger rules — nothing outside these may propose a mutation:
- a declared phase whose `writes` artifact exists in 0 of >= 2 engine
  seasons -> "exercise or trim phase P" (pipeline order, cap applies)
- stopped_stall in >= 2 audited seasons -> "re-size stall/budget rules"

yamlio.YamlError from a season file propagates unwrapped (the CLI already
reports it); akar.AkarError wraps into AuditError.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path

from rumpun import akar, yamlio

logger = logging.getLogger(__name__)

LEDGER_ARTIFACTS = (
    "errors.jsonl",
    "gaps.yaml",
    "hypotheses.yaml",
    "experiments.yaml",
    "falsification.yaml",
    "results.jsonl",
    "verdicts.jsonl",
    "report.html",
)
"""Ledger artifacts checked per engine season at rimba/<sid>/."""

HISTOGRAM_KEYS = ("WIN", "LOSS", "INVALID")
STALL_RECURRENCE = 2
MAX_CANDIDATES = 3

_SEASON_FILE_RE = re.compile(r"^s(\d+)\.yaml$")
_AUDIT_FILE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_audit-\d+\.md$")


class AuditError(Exception):
    """Invalid audit input or unreadable ledger state."""


def _seasons(root: Path, last_n: int) -> list[tuple[str, Path]]:
    """(sid, yaml path) for the last N musim seasons, sorted by number.

    sid follows the season-list convention: the yaml id field, stem fallback.
    """
    musim = root / "musim"
    if not musim.is_dir():
        raise AuditError(f"no musim directory under {root}: nothing to audit")
    numbered = sorted(
        (int(m.group(1)), p)
        for p in musim.iterdir()
        if p.is_file() and (m := _SEASON_FILE_RE.match(p.name))
    )
    if not numbered:
        raise AuditError(f"no musim/s<N>.yaml seasons under {musim}: nothing to audit")
    window: list[tuple[str, Path]] = []
    for _num, path in numbered[-last_n:]:
        doc = yamlio.load(path)
        sid = doc.get("id") if isinstance(doc, dict) else None
        window.append((str(sid) if sid else path.stem, path))
    return window


def _declared_phases(latest: Path) -> list[tuple[str, str]]:
    """(phase, writes) pairs of the latest season yaml's methodology.pipeline.

    A pipeline entry without a string phase and a string writes carries no
    liveness evidence to check; it is skipped with a warning, never silently.
    """
    doc = yamlio.load(latest)
    method = doc.get("methodology") if isinstance(doc, dict) else None
    pipeline = (method or {}).get("pipeline") or []
    phases: list[tuple[str, str]] = []
    for entry in pipeline:
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("phase"), str)
            and isinstance(entry.get("writes"), str)
        ):
            phases.append((entry["phase"], entry["writes"]))
        else:
            logger.warning("skipping pipeline entry without phase/writes in %s", latest)
    return phases


def _season_artifacts(root: Path, sid: str) -> frozenset[str]:
    """Which ledger artifacts exist at rimba/<sid>/ (empty when no dir)."""
    sdir = root / "rimba" / sid
    if not sdir.is_dir():
        return frozenset()
    return frozenset(name for name in LEDGER_ARTIFACTS if (sdir / name).is_file())


def _season_status(root: Path, sid: str) -> str | None:
    """The season's state.json status, or None when no state file exists."""
    path = root / "rimba" / sid / "_season" / "state.json"
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("cannot read season state %s", path)
        raise AuditError(f"cannot read {path}: {exc}") from exc
    return str(state.get("status")) if isinstance(state, dict) else None


def _verdict_rows(root: Path, sid: str) -> list[dict]:
    """Parsed verdicts.jsonl rows of one season; [] when the file is absent.

    A row without a `verdict` value is not a verdict statement and does not
    count toward the histogram (a defined rule, not a silent drop). A
    corrupt line refuses the audit rather than guessing.
    """
    path = root / "rimba" / sid / "verdicts.jsonl"
    if not path.is_file():
        return []
    rows: list[dict] = []
    try:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AuditError(
                    f"{path}: line {lineno} is not valid JSON: {exc}"
                ) from exc
    except OSError as exc:
        logger.exception("cannot read %s", path)
        raise AuditError(f"cannot read {path}: {exc}") from exc
    return rows


def _next_index(root: Path) -> int:
    """1 + count of existing audit-* record files in akar/, by filename scan."""
    akar_dir = root / "akar"
    if not akar_dir.is_dir():
        return 1
    return 1 + sum(
        1 for entry in akar_dir.iterdir() if entry.is_file() and _AUDIT_FILE_RE.match(entry.name)
    )


def _findings_and_candidates(
    root: Path,
    seasons: list[tuple[str, Path]],
) -> tuple[list[str], list[str]]:
    """Deterministic, season-cited body lines: findings, then candidates.

    Split out of run_audit so every rule is testable without touching akar.
    """
    latest_sid, latest_yaml = seasons[-1]
    engine_ids = [
        sid for sid, _path in seasons if (root / "rimba" / sid).is_dir()
    ]
    n = len(engine_ids)
    ids_str = ",".join(engine_ids)

    phases = _declared_phases(latest_yaml)
    artifacts = {sid: _season_artifacts(root, sid) for sid in engine_ids}

    lines: list[str] = [
        f"scope: last {len(seasons)} musim seasons "
        f"({','.join(sid for sid, _p in seasons)}); engine seasons with rimba/ "
        f"({n}): {ids_str}",
        "declared phases from latest season "
        + latest_sid
        + ": "
        + (", ".join(f"{phase}->{writes}" for phase, writes in phases) or "none"),
    ]

    # F1 phase liveness: K of N engine seasons hold each declared phase's
    # writes artifact. Liveness 0 across the window is unexercised-phase
    # evidence; partial liveness is evidence the phase does run sometimes.
    liveness: list[tuple[str, str, int]] = []
    for phase, writes in phases:
        k = sum(1 for sid in engine_ids if writes in artifacts[sid])
        liveness.append((phase, writes, k))
        lines.append(
            f"F1 phase liveness: phase {phase} (writes {writes}) wrote its "
            f"artifact in {k} of {n} engine seasons ({ids_str})"
        )

    # F2 stall recurrence: harness-observed stopped_stall terminal states.
    statuses = {sid: _season_status(root, sid) for sid in engine_ids}
    with_state = [sid for sid, s in statuses.items() if s is not None]
    stalled = [sid for sid, s in statuses.items() if s == "stopped_stall"]
    if with_state:
        lines.append(
            f"F2 stall recurrence: stopped_stall in {len(stalled)} of "
            f"{len(with_state)} seasons with state.json "
            f"({','.join(stalled) if stalled else 'none'}); "
            f"recurrence {'yes' if len(stalled) >= STALL_RECURRENCE else 'no'} "
            f"(threshold {STALL_RECURRENCE})"
        )
    else:
        lines.append(f"F2 stall recurrence: no engine season has a state.json ({ids_str})")

    # F3 verdict histogram over every window season's verdicts.jsonl.
    hist: Counter[str] = Counter()
    sources: list[str] = []
    bare: list[str] = []
    for sid in engine_ids:
        rows = _verdict_rows(root, sid)
        if rows:
            sources.append(sid)
        else:
            bare.append(sid)
        for row in rows:
            verdict = row.get("verdict")
            if isinstance(verdict, str):
                hist[verdict] += 1
    other = sum(hist.values()) - sum(hist[key] for key in HISTOGRAM_KEYS)
    lines.append(
        "F3 verdict histogram over verdicts.jsonl of "
        f"{','.join(sources) if sources else 'none'}"
        + (f" (none in: {','.join(bare)})" if bare else "")
        + ": "
        + ", ".join(f"{key} {hist[key]}" for key in HISTOGRAM_KEYS)
        + (f", other {other}" if other else "")
    )

    # Candidates: deterministic triggers only, phases in pipeline order
    # first, stall trigger last, hard cap. Never invented, never over cap.
    proposals: list[tuple[str, str]] = []  # (short label, record line)
    if n >= 2:
        for phase, writes, k in liveness:
            if k == 0:
                proposals.append(
                    (
                        f"{phase} ({writes})",
                        f"candidate: exercise or trim phase {phase} — {writes} "
                        f"written in 0 of {n} engine seasons ({ids_str}); "
                        f"band: WIN when a later season's ledger holds {writes} "
                        f"or the pipeline drops {phase}",
                    )
                )
    if len(stalled) >= STALL_RECURRENCE:
        proposals.append(
            (
                "stall/budget rules",
                f"candidate: re-size stall/budget rules — stopped_stall in "
                f"{len(stalled)} seasons ({','.join(stalled)}); "
                f"band: WIN when a later season reaches a terminal state "
                f"without stopped_stall",
            )
        )
    dropped = [label for label, _line in proposals[MAX_CANDIDATES:]]
    candidates = [line for _label, line in proposals[:MAX_CANDIDATES]]
    if not candidates:
        lines.append("candidates: none — no trigger met; nothing proposed without evidence")
    lines.extend(candidates)
    if dropped:
        lines.append(
            f"candidate cap {MAX_CANDIDATES} reached in pipeline order; "
            f"also unexercised but unproposed here: {','.join(dropped)}"
        )
    return lines, candidates


def run_audit(root: Path, last_n: int = 10) -> Path:
    """Reflect over the last `last_n` seasons; append the audit akar record.

    Reads musim/s*.yaml (sorted by number, last N), the ledger artifacts
    under rimba/<sid>/, the latest season's declared pipeline, per-season
    state.json statuses, and verdicts.jsonl rows. Every claim the record
    makes cites its season ids; the only mutation is the appended record
    (id audit-<k>, k = 1 + existing audit-* records by akar/ filename
    scan). akar.AkarError wraps into AuditError. Returns the record path.
    """
    if last_n < 1:
        raise AuditError(f"last_n must be >= 1, got {last_n}")
    seasons = _seasons(root, last_n)
    engine_ids = [sid for sid, _p in seasons if (root / "rimba" / sid).is_dir()]
    if not engine_ids:
        raise AuditError(
            f"no audited season has a rimba/ directory under {root}; "
            "nothing to reflect on"
        )
    body, _candidates = _findings_and_candidates(root, seasons)
    record_id = f"audit-{_next_index(root)}"
    try:
        path = akar.append_record(root, record_id, "reflection audit", "\n".join(body))
    except akar.AkarError as exc:
        raise AuditError(f"cannot append audit record {record_id}: {exc}") from exc
    return path


def candidate_lines(record: Path) -> list[str]:
    """The record's candidate lines, for the verb's own output.

    Body recovery follows the akar layout docstring: body lines are
    lines[4:-1] between the header and the sha256 trailer.
    """
    try:
        lines = record.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        logger.exception("cannot read audit record %s", record)
        raise AuditError(f"cannot read {record}: {exc}") from exc
    return [line for line in lines[4:-1] if line.startswith("candidate:")]
