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
- a route with >= 2 clean-empty agent spawns -> "add spawn tool-check or
  prefer alternative route" (after the phase triggers, cap applies)
- >= 2 LOSS seasons that each shipped >= 1 integrated module ->
  "recalibrate LOSS bands" (after the route triggers, cap applies)
- stopped_stall in >= 2 audited seasons -> "re-size stall/budget rules"
  (last among the candidates)
The budget cap never proposes a mutation: campaign_cost_cap unset is a
finding only — the operator sets the number, the tool just flags it.

yamlio.YamlError from a season file or rumpun.yaml propagates unwrapped
(the CLI already reports it); akar.AkarError wraps into AuditError.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

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
ROUTED_EMPTY_TRIGGER = 2
BAND_MASKED_SEASONS = 2
MAX_CANDIDATES = 3

BOOKKEEPING_FILES = frozenset(
    {
        "agent.log",
        "exit",
        "prompt.md",
        "prompt-meta.yaml",
        "state.json",
        "terminated",
        "terminated.tmp",
        "__pycache__",
    }
)
"""Engine-owned entries of an agent workspace; never a deliverable.

A file counts as bookkeeping when any component of its workspace-relative
path is in this set, so __pycache__/*.pyc stays bookkeeping too.
"""

OUTCOME_KEYS = ("clean-deliverable", "clean-empty", "failed", "not-exited")
"""Spawn outcome categories, record order for the F4 per-route line."""

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


def _season_state(root: Path, sid: str) -> dict[str, Any] | None:
    """The season's parsed _season/state.json; None when absent or not a dict.

    One read feeds both the F2 status rule and the F4 agent snapshots; a
    corrupt state refuses the audit rather than guessing.
    """
    path = root / "rimba" / sid / "_season" / "state.json"
    if not path.is_file():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("cannot read season state %s", path)
        raise AuditError(f"cannot read {path}: {exc}") from exc
    return state if isinstance(state, dict) else None


def _read_jsonl(path: Path) -> list[dict]:
    """Parsed JSONL rows of one ledger file; [] when the file is absent.

    A row without the keys a caller looks for is not a statement and does
    not count toward that rule (a defined rule, not a silent drop). A
    corrupt line refuses the audit rather than guessing.
    """
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
                raise AuditError(f"{path}: line {lineno} is not valid JSON: {exc}") from exc
    except OSError as exc:
        logger.exception("cannot read %s", path)
        raise AuditError(f"cannot read {path}: {exc}") from exc
    return rows


def _verdict_rows(root: Path, sid: str) -> list[dict]:
    """verdicts.jsonl rows of one season; [] when the file is absent."""
    return _read_jsonl(root / "rimba" / sid / "verdicts.jsonl")


def _result_rows(root: Path, sid: str) -> list[dict]:
    """results.jsonl rows of one season; [] when the file is absent."""
    return _read_jsonl(root / "rimba" / sid / "results.jsonl")


def _season_verdict(rows: list[dict], sid: str) -> str | None:
    """Verdict of the last season-level verdicts row for sid; None if absent.

    Season-level follows the report verb's rule [H]: a row whose `season`
    value is this sid; the last such row wins.
    """
    verdict = ""
    for row in rows:
        if row.get("season") == sid:
            verdict = str(row.get("verdict", ""))
    return verdict or None


def _has_deliverable(ws: Path) -> bool:
    """Any file under the agent workspace the engine does not own (recursive).

    A file is bookkeeping when any component of its workspace-relative path
    is in BOOKKEEPING_FILES; everything else is a deliverable.
    """
    if not ws.is_dir():
        return False
    for path in ws.rglob("*"):
        if not path.is_file():
            continue
        parts = path.relative_to(ws).parts
        if not any(part in BOOKKEEPING_FILES for part in parts):
            return True
    return False


def _spawn_outcome(snap: dict, deliverable: bool) -> str:
    """Classify one finalized agent snap into an OUTCOME_KEYS category.

    exit_code 0 splits on deliverable presence (clean-empty is the tool-less
    signature); a non-zero exit or an unparseable exit file (engine state
    "failed") is failed; anything that never reached exited/failed —
    terminated, crashed, stalled, running — is not-exited. An exited snap
    always carries a parsed exit_code (engine contract), so code None with
    state exited cannot occur; it classifies not-exited rather than guessing.
    """
    code = snap.get("exit_code")
    if code == 0:
        return "clean-deliverable" if deliverable else "clean-empty"
    if code is not None or snap.get("state") == "failed":
        return "failed"
    return "not-exited"


def _budget_cap(root: Path) -> Any:
    """The campaign cost cap from rumpun.yaml; None when unset or absent.

    The key lives at budget.campaign_cost_cap — the top-level `budget:` block
    scaffold.py writes into the campaign config. A set value is never
    interpreted here, only its presence is flagged.
    """
    path = root / "rumpun.yaml"
    if not path.is_file():
        return None
    doc = yamlio.load(path)
    budget = doc.get("budget") if isinstance(doc, dict) else None
    if not isinstance(budget, dict):
        return None
    return budget.get("campaign_cost_cap")


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
    states = {sid: _season_state(root, sid) for sid in engine_ids}
    with_state = [sid for sid, s in states.items() if s is not None]
    stalled = [sid for sid, s in states.items() if (s or {}).get("status") == "stopped_stall"]
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
    verdict_rows: dict[str, list[dict]] = {}
    for sid in engine_ids:
        rows = _verdict_rows(root, sid)
        verdict_rows[sid] = rows
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

    # F4 route outcomes: classify every finalized agent snap (engine writes
    # agents{name: snap} into _season/state.json at finalize) per route.
    # A season still running has no agents block yet and contributes nothing.
    route_counts: dict[str, Counter[str]] = {}
    route_sids: dict[str, list[str]] = {}
    routed = False
    for sid in engine_ids:
        agents = (states[sid] or {}).get("agents")
        if not isinstance(agents, dict) or not agents:
            continue
        routed = True
        for name in sorted(agents):
            snap = agents[name]
            if not isinstance(snap, dict):
                logger.warning("skipping non-dict agent snap %s in season %s", name, sid)
                continue
            route = str(snap.get("route", "?"))
            deliverable = _has_deliverable(root / "rimba" / sid / name)
            route_counts.setdefault(route, Counter())[_spawn_outcome(snap, deliverable)] += 1
            sids = route_sids.setdefault(route, [])
            if sid not in sids:
                sids.append(sid)
    if not routed:
        lines.append(
            f"F4 route outcomes: no finalized agent snapshots in audited engine "
            f"seasons ({ids_str})"
        )
    for route in sorted(route_counts):
        counts = route_counts[route]
        lines.append(
            f"F4 route outcomes: route {route}: "
            + ", ".join(f"{counts[key]} {key}" for key in OUTCOME_KEYS)
            + f" over {sum(counts.values())} spawns ({','.join(route_sids[route])})"
        )

    # F5 band calibration: a LOSS season that still shipped integrated
    # modules is a band that masked delivered value (s4/s5/s6 precedent).
    harvested = [
        sid for sid in engine_ids if (root / "rimba" / sid / "results.jsonl").is_file()
    ]
    masked: list[tuple[str, int]] = []
    for sid in harvested:
        integrated = sum(1 for row in _result_rows(root, sid) if row.get("integrated") is True)
        if _season_verdict(verdict_rows.get(sid, []), sid) == "LOSS" and integrated >= 1:
            masked.append((sid, integrated))
            lines.append(
                f"F5 band calibration: LOSS season {sid} shipped {integrated} "
                f"integrated module(s) — band masked value"
            )
    if not masked:
        scope = (
            ",".join(harvested)
            if harvested
            else f"no engine season holds results.jsonl ({ids_str})"
        )
        lines.append(f"F5 band calibration: no LOSS season shipped integrated modules ({scope})")

    # F6 budget compliance: a flag, never a candidate. The operator sets the
    # number; the audit only reports that it is still unset (P9).
    if _budget_cap(root) is None:
        lines.append(
            "F6 budget compliance: campaign_cost_cap unset since campaign start (P9) "
            "— operator sets the number; the tool only flags"
        )

    # Candidates: deterministic triggers only, phases in pipeline order
    # first, then route, then calibration, stall trigger last, hard cap.
    # Never invented, never over cap.
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
    for route in sorted(route_counts):
        empty = route_counts[route]["clean-empty"]
        if empty >= ROUTED_EMPTY_TRIGGER:
            proposals.append(
                (
                    f"route {route} ({empty} clean-empty)",
                    f"candidate: route {route}: {empty} clean-empty spawns — add spawn "
                    f"tool-check or prefer alternative route ({','.join(route_sids[route])}); "
                    f"band: WIN when clean-empty rate drops to 0 or a tool-check lands",
                )
            )
    if len(masked) >= BAND_MASKED_SEASONS:
        proposals.append(
            (
                "LOSS band calibration",
                f"candidate: recalibrate LOSS bands — count integrated deliverables in "
                f"the band ({','.join(sid for sid, _k in masked)}); "
                f"band: WIN when no later LOSS season ships an integrated module "
                f"its band ignores",
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
            f"also triggered but unproposed here: {','.join(dropped)}"
        )
    return lines, candidates


def run_audit(root: Path, last_n: int = 10) -> Path:
    """Reflect over the last `last_n` seasons; append the audit akar record.

    Reads musim/s*.yaml (sorted by number, last N), the ledger artifacts
    under rimba/<sid>/, the latest season's declared pipeline, per-season
    state.json statuses and finalized agent snapshots, verdicts.jsonl and
    results.jsonl rows, and the rumpun.yaml budget block. Every claim the
    record makes cites its season ids; the only mutation is the appended
    record (id audit-<k>, k = 1 + existing audit-* records by akar/
    filename scan). akar.AkarError wraps into AuditError. Returns the
    record path.
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
