"""rumpun audit — reflection over the season ledger (DESIGN section 15).

Phase-2 self-evolution needs reflection: run_audit reads the last N musim
seasons, records which ledger artifacts each engine season (a season with a
.rumpun/runs/<sid>/ dir) actually wrote, and appends one ledger record of
deterministic findings plus at most three candidate mutations — every
findings and candidate line cites the season ids it rests on. The verb
mutates nothing except appending that record: candidates reach the pipeline
only through the existing evolve gate (lint plus operator at the manual
stage).

Deterministic trigger rules — nothing outside these may propose a mutation:
- a committed replay matrix row with verdict FAIL or a REGRESSION note ->
  "corpus regression: <script> <first-failing-line>" (FIRST among the
  candidates — a main-line regression outranks every improvement trigger)
- a replay matrix row with verdict DRIFT -> "drift mismatch: <script>" —
  one candidate per drifted script citing the script and its matrix note
  (right after the regression candidate, before the cap)
- a declared phase whose `writes` artifact exists in 0 of >= 2 engine
  seasons -> "exercise or trim phase P" (pipeline order, cap applies)
- a route with >= 2 clean-empty agent spawns -> "add spawn tool-check or
  prefer alternative route" (after the phase triggers, cap applies)
- >= 2 LOSS seasons that each shipped >= 1 integrated module AND whose yamls
  the lint band-mask guard warns (metric modules_integrated, expected_band
  without integration-evidence tokens) -> "recalibrate LOSS bands" (after the
  route triggers, cap applies)
- a season verdict WIN whose results.jsonl carries a unit row with verdict
  FAIL -> "verdict mismatch" (after the calibration trigger, cap applies)
- stopped_stall in >= 2 audited seasons -> "re-size stall/budget rules"
  (last among the candidates)
The budget cap never proposes a mutation: campaign_cost_cap unset is a
finding only — the operator sets the number, the tool just flags it.
The usefulness decade finding (s33 w1) is the same shape: a flag that never
proposes a mutation. When floor(musim season count / 10) exceeds the number
of usefulness-decade-* akar records, run_audit reports "usefulness audit
due for decade N (different-model review)". The due decade N is the first
without a record (debt paid in order), so the usefulness-decade-N record
the tool appends reaches the gate's fixed point; the verdict record's
residuals arm candidates through the existing machinery, never this line.

Basis supersedes (s105 w2): a sealed assessment's basis line is corrected by
appending, never editing. A superseding re-seal refuses an unchanged basis
and otherwise appends usefulness-<sid>-basis -- a full assessment record
whose basis line is the correction and whose supersedes line cites the
original id and body sha256; the original stands (the akar discipline).
read_usefulness_assessment returns the superseding basis when the record
has one, naming it in basis_superseded_by.

Adjusted truth at the seal (s118 w1): the assessment reads the epic
rollup's adjusted counts from the campaign at seal time (the s117 rule,
the same counting the board renders) and carries them in the body beside
the raw ones -- one epics section, one row per declared epic, the raw
WIN/LOSS/other triple verbatim and the adjusted triple named beside it
when any member's dissent qualifies. Nothing is rewritten: a campaign
without epics.yaml seals byte-identical to the s88 shape, and
read_usefulness_assessment reads old records back with an empty epics
list.

yamlio.YamlError from a season file or rumpun.yaml propagates unwrapped
(the CLI already reports it); akar.AkarError wraps into AuditError.

--corpus (s30 w1): refresh_corpus_matrix runs the corpus runner first as
an isolated subprocess (repo venv python, own process group, captured
output, hard timeout) and run_audit ingests the matrix that run just
wrote. A missing runner, a nonzero exit, a timeout, or an exit 0
without the promised matrix raises AuditError naming the runner: a
stale or partial matrix is never ingested. The runner's captured
streams are never echoed into the record; only the fresh matrix's
verdict counts land there. The s43 coverage finding rides fresh
ingestion: one line, "corpus coverage: N repro scripts PASS of M
discovered (K SKIP)", whose numbers cover every discovered script and
which stays present at 0 PASS; the "all green on main" suffix is
emitted only when no discovered script skipped.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import re
import signal
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from rumpun import akar, epics, lint, paths, yamlio

logger = logging.getLogger(__name__)

HISTOGRAM_KEYS = ("WIN", "LOSS", "INVALID")
STALL_RECURRENCE = 2
ROUTED_EMPTY_TRIGGER = 2
BAND_MASKED_SEASONS = 2
MAX_CANDIDATES = 3
USEFULNESS_DECADE_SIZE = 10
_USEFULNESS_DECADE_RE = re.compile(r"^usefulness-decade-(\d+)$")

CORPUS_MATRIX_NAME = "replay-matrix.md"
CORPUS_RUNNER = Path("tools") / "replay_corpus.py"
_EVIDENCE_DIR_RE = re.compile(r"^s(\d+)$")
_MATRIX_HEADER = "| script | verdict | first failing line | note |"

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
_HARVEST_ID_RE = re.compile(r"^s\d+-harvest$")


class AuditError(Exception):
    """Invalid audit input or unreadable ledger state."""


def _seasons(root: Path, last_n: int) -> list[tuple[str, Path]]:
    """(sid, yaml path) for the last N musim seasons, sorted by number.

    sid follows the season-list convention: the yaml id field, stem fallback.
    """
    seasons = paths.seasons_dir(root)
    if not seasons.is_dir():
        raise AuditError(f"no seasons directory under {root}: nothing to audit")
    numbered = sorted(
        (int(m.group(1)), p)
        for p in seasons.iterdir()
        if p.is_file() and (m := _SEASON_FILE_RE.match(p.name))
    )
    if not numbered:
        raise AuditError(f"no seasons/s<N>.yaml files under {seasons}: nothing to audit")
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


def _season_running(state: dict[str, Any] | None) -> bool:
    """True when a season's recorded state says still running.

    Completed-only F1 denominator (M2): a running season has not reached
    the phase yet, so its missing artifact is not liveness evidence. A
    season with no state.json is not provably running and counts (the s13
    base-fixture contract: an empty .rumpun/runs/<sid> dir stays in the window).
    """
    return bool(state) and state.get("status") == "running"


def _season_state(root: Path, sid: str) -> dict[str, Any] | None:
    """The season's parsed _season/state.json; None when absent or not a dict.

    One read feeds both the F2 status rule and the F4 agent snapshots; a
    corrupt state refuses the audit rather than guessing.
    """
    path = paths.runs_dir(root) / sid / "_season" / "state.json"
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
    return _read_jsonl(paths.runs_dir(root) / sid / "verdicts.jsonl")


def _result_rows(root: Path, sid: str) -> list[dict]:
    """results.jsonl rows of one season; [] when the file is absent."""
    return _read_jsonl(paths.runs_dir(root) / sid / "results.jsonl")


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


def _decade_coverage(
    declared: Mapping[str, Path], count: int
) -> tuple[int, int]:
    """(covered frontier, next decade) over the usefulness-decade records.

    (issue #45, s134 w1) Each decade record carries its audit-time scope
    on a `seasons: <int>` line (the runner stamps "seasons: N season
    yamls at audit time"). A value within 1..count is the covered
    frontier. A record with no parseable or in-range scope keeps the
    pre-s134 per-record credit (USEFULNESS_DECADE_SIZE * N), so ledger
    shapes predating the scope line keep their standing arithmetic.
    """
    frontier = 0
    top = 0
    for record_id, path in declared.items():
        if not (m := _USEFULNESS_DECADE_RE.match(record_id)):
            continue
        n = int(m.group(1))
        top = max(top, n)
        credit = USEFULNESS_DECADE_SIZE * n
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning(
                "cannot read usefulness record %s: %s", path, exc
            )
        else:
            for line in text.splitlines():
                if line.startswith("seasons:"):
                    raw = line[len("seasons:"):].lstrip()
                    if (m := re.match(r"\d+", raw)):
                        value = int(m.group(0))
                        if 1 <= value <= count:
                            credit = value
                    break
        frontier = max(frontier, credit)
    return frontier, top + 1


def _usefulness_decade_due(root: Path) -> str | None:
    """The usefulness-decade finding line, or None when not due.

    (s33 w1) Every 10 musim seasons a different-model usefulness review
    is due. The gate is coverage (issue #45, s134 w1): a review is due
    only when USEFULNESS_DECADE_SIZE seasons sit above the covered
    frontier the decade records name (see _decade_coverage). The
    reported decade is max(N)+1 over the ledger's records, so the
    usefulness-decade-N record the tool appends reaches the fixed point;
    the finding is never a candidate itself -- the verdict record's
    residuals arm candidates through the existing machinery. akar.AkarError
    wraps into AuditError.
    """
    seasons = paths.seasons_dir(root)
    count = 0
    if seasons.is_dir():
        count = sum(
            1
            for p in seasons.iterdir()
            if p.is_file() and _SEASON_FILE_RE.match(p.name)
        )
    try:
        declared = akar.declared_ids(root)
    except akar.AkarError as exc:
        msg = f"cannot scan akar records: {exc}"
        raise AuditError(msg) from exc
    frontier, decade = _decade_coverage(declared, count)
    if count - frontier < USEFULNESS_DECADE_SIZE:
        return None
    return (
        f"F7 usefulness decade: usefulness audit due for decade {decade} "
        f"(different-model review) — {count} season yamls, "
        f"{sum(1 for rid in declared if _USEFULNESS_DECADE_RE.match(rid))} "
        "usefulness-decade records on the ledger"
    )


def _usefulness_residuals(root: Path) -> list[tuple[str, str]]:
    """(record id, residual text) pairs from usefulness-decade records.

    (s33 w2 pins) Each body line starting "residual: " arms one candidate
    citing the residual and its record; the scan is filename-sorted, so
    the order is chronological and deterministic.
    """
    ledger = paths.ledger_dir(root)
    if not ledger.is_dir():
        return []
    out: list[tuple[str, str]] = []
    for path in sorted(ledger.glob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("cannot read usefulness record %s: %s", path, exc)
            continue
        rid = next(
            (ln[4:].strip() for ln in lines[:6] if ln.startswith("id: ")),
            "",
        )
        if not _USEFULNESS_DECADE_RE.match(rid):
            continue
        in_residuals = False
        for ln in lines:
            stripped = ln.strip()
            if stripped == "residuals:":
                in_residuals = True
                continue
            if ln.startswith("residual: "):
                out.append((rid, ln[len("residual: "):].strip()))
            elif in_residuals and ln.startswith("- "):
                # The runner writes residuals as markdown bullets under a
                # 'residuals:' header (usefulness-decade-3's real shape).
                out.append((rid, ln[2:].strip()))
    return out


def _harvest_resolution_lines(root: Path) -> list[tuple[str, str]]:
    """(record id, line value) of every harvest implies/observed line.

    (issue #6) The ledger's half of the resolution trail: a harvest
    record's implies/observed line can name what became of an audit
    candidate by citing the number of the issue filed from it (#N).
    The scan is filename-sorted like _usefulness_residuals, so the
    first naming record is deterministic.
    """
    ledger = paths.ledger_dir(root)
    if not ledger.is_dir():
        return []
    out: list[tuple[str, str]] = []
    for path in sorted(ledger.glob("*.md")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("cannot read harvest record %s: %s", path, exc)
            continue
        rid = next(
            (ln[4:].strip() for ln in lines[:6] if ln.startswith("id: ")),
            "",
        )
        if not _HARVEST_ID_RE.match(rid):
            continue
        for ln in lines:
            for key in ("implies: ", "observed: "):
                if ln.startswith(key):
                    out.append((rid, ln[len(key):].strip()))
    return out


def _names_issue(line: str, number: int) -> bool:
    """True when a trail line names issue `number` (#N or issues/N form)."""
    return re.search(rf"(?<!\d)(#{number}|issues/{number})(?!\d)", line) is not None


def _resolved_candidate(
    issue_trail: list[dict[str, Any]],
    harvest_lines: list[tuple[str, str]],
    emitted: str,
) -> str | None:
    """The `resolved: ` marker for a candidate whose trail resolves it.

    (issue #6) A usefulness candidate is resolved when either leg of its
    resolution trail holds: a board issue citing the candidate line
    verbatim (the body quotes it minus the `candidate: ` prefix) whose
    state is CLOSED, or a harvest record's implies/observed line naming
    the number of an issue that cites it.  The marker carries the
    evidence that resolved the candidate; None leaves it live.
    """
    for row in issue_trail:
        if emitted not in str(row.get("body", "")):
            continue
        number = row.get("number")
        if row.get("state") == "CLOSED":
            return f"resolved: {emitted} — issue #{number} closed"
        named = next(
            (
                rid
                for rid, line in harvest_lines
                if _names_issue(line, int(number))
            ),
            None,
        )
        if named is not None:
            return f"resolved: {emitted} — issue #{number} named in {named}"
    return None


def refresh_corpus_matrix(root: Path, runner_path: str | Path, timeout_s: int = 120) -> Path:
    """Run the corpus runner as an isolated subprocess; return its fresh matrix.

    runner_path (the constant CORPUS_RUNNER by default) resolves against
    the repo root — the parent of the .rumpun root — unless absolute. The
    runner runs under <repo>/.venv/bin/python when that exists, else the
    current interpreter, with its own process group, captured (and
    discarded) streams, and a hard timeout. A missing runner, a nonzero
    exit, a timeout, or an exit 0 without the promised matrix raises
    AuditError naming the runner: the caller must never fall back to the
    committed (stale) matrix, and the runner's captured streams are never
    echoed into a record.
    """
    repo = root.parent
    runner = Path(runner_path)
    if not runner.is_absolute():
        runner = repo / runner
    if not runner.is_file():
        raise AuditError(
            f"corpus runner not found: {runner} "
            f"(resolved {runner_path!r} against the repo root {repo})"
        )
    venv_python = repo / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.is_file() else sys.executable
    try:
        proc = subprocess.Popen(
            [python, str(runner)],
            cwd=str(repo),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            _, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGKILL)
            with contextlib.suppress(Exception):
                proc.communicate(timeout=10)
            msg = f"corpus runner timed out after {timeout_s}s: {runner}"
            raise AuditError(msg) from None
        if proc.returncode != 0:
            tail = (
                f"; stderr head: {stderr.strip()[:200]}"
                if stderr and stderr.strip()
                else ""
            )
            msg = f"corpus runner failed with exit {proc.returncode}: {runner}{tail}"
            raise AuditError(msg)
        matrix = repo / "replay-matrix.md"
        if not matrix.is_file():
            msg = f"corpus runner exited 0 but wrote no matrix at {matrix}"
            raise AuditError(msg)
        return matrix
    except OSError as exc:
        msg = f"corpus runner could not start: {runner}: {exc}"
        raise AuditError(msg) from exc


def _corpus_matrix(root: Path) -> Path | None:
    """Newest committed corpus matrix: evidence/s<N>/replay-matrix.md, max N.

    Only the committed ledger copies under .rumpun/ledger/evidence/ (legacy
    .rumpun/akar/evidence/) are read;
    the runner's repo-root replay-matrix.md is regenerated per run and
    uncommitted, so it never feeds reflection. Highest season number wins;
    None when no evidence season holds a matrix.
    """
    evidence = paths.ledger_dir(root) / "evidence"
    if not evidence.is_dir():
        return None
    best: tuple[int, Path] | None = None
    for entry in evidence.iterdir():
        if not entry.is_dir() or not (m := _EVIDENCE_DIR_RE.fullmatch(entry.name)):
            continue
        matrix = entry / CORPUS_MATRIX_NAME
        if matrix.is_file() and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), matrix)
    return best[1] if best else None


def _parse_matrix(
    path: Path,
) -> list[tuple[str, str, str, str]] | None:
    """(script, verdict, first failing line, note) rows of one matrix file.

    None when the file exists but carries no parsable table (no header row,
    or a header with zero parsable rows): the caller treats that exactly
    like an absent matrix. Malformed rows are skipped with a warning,
    never silently. Cell content is unescaped (\\| -> |) verbatim.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("cannot read corpus matrix %s: %s", path, exc)
        return None
    lines = text.splitlines()
    try:
        head = lines.index(_MATRIX_HEADER)
    except ValueError:
        logger.warning("no corpus table header in %s", path)
        return None
    rows: list[tuple[str, str, str, str]] = []
    for line in lines[head + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 5 or cells[0] or cells[-1]:
            logger.debug("skipping malformed corpus matrix row in %s: %s", path, line)
            continue
        script, verdict, first_fail, note = (
            cell.replace("\\|", "|") for cell in cells[1:5]
        )
        if not script or not verdict:
            logger.debug("skipping empty corpus matrix row in %s: %s", path, line)
            continue
        if verdict not in {"PASS", "FAIL", "DRIFT", "REGRESSION", "SKIP"}:
            logger.debug("skipping unknown corpus matrix verdict in %s: %s", path, line)
            continue
        rows.append((script, verdict, first_fail, note))
    if not rows:
        logger.warning("no parsable rows in corpus matrix %s", path)
        return None
    return rows


def _next_index(root: Path) -> int:
    """1 + count of existing audit-* record files in the ledger, by filename scan."""
    ledger = paths.ledger_dir(root)
    if not ledger.is_dir():
        return 1
    return 1 + sum(
        1 for entry in ledger.iterdir() if entry.is_file() and _AUDIT_FILE_RE.match(entry.name)
    )


def _findings_and_candidates(
    root: Path,
    seasons: list[tuple[str, Path]],
    corpus_matrix: Path | None = None,
    issue_trail: list[dict[str, Any]] | None = None,
) -> tuple[list[str], list[str]]:
    """Deterministic, season-cited body lines: findings, then candidates.

    corpus_matrix (s30 w1): a fresh path from refresh_corpus_matrix replaces
    the newest committed evidence matrix for this audit; the record then
    carries the fresh run's verdict counts. None keeps s26 byte-identical.

    Split out of run_audit so every rule is testable without touching akar.
    """
    latest_sid, latest_yaml = seasons[-1]
    engine_ids = [
        sid for sid, _path in seasons if (paths.runs_dir(root) / sid).is_dir()
    ]
    n = len(engine_ids)
    ids_str = ",".join(engine_ids)

    phases = _declared_phases(latest_yaml)
    states = {sid: _season_state(root, sid) for sid in engine_ids}
    season_phases = {
        sid: dict(_declared_phases(path))
        for sid, path in seasons
        if (paths.runs_dir(root) / sid).is_dir()
    }

    lines: list[str] = [
        f"scope: last {len(seasons)} seasons "
        f"({','.join(sid for sid, _p in seasons)}); engine seasons with runs/ "
        f"({n}): {ids_str}",
        "declared phases from latest season "
        + latest_sid
        + ": "
        + (", ".join(f"{phase}->{writes}" for phase, writes in phases) or "none"),
    ]

    # F1 phase liveness (M2, codex-review-2026-09-14): each audited season's
    # OWN yaml decides. A season counts toward a phase's denominator only
    # when its own pipeline declared that phase (a pre-phase season is no
    # evidence either way) and it is not still running (it has not reached
    # the phase yet). The numerator checks that season's own declared writes
    # filename for existence at .rumpun/runs/<sid>/ via paths.runs_dir — no
    # fixed artifact list, so a declared custom.jsonl present everywhere
    # counts as liveness, not death.
    liveness: list[tuple[str, str, int, int]] = []
    for phase, writes in phases:
        holding = [
            sid
            for sid in engine_ids
            if phase in season_phases[sid] and not _season_running(states[sid])
        ]
        k = sum(
            1
            for sid in holding
            if (paths.runs_dir(root) / sid / season_phases[sid][phase]).is_file()
        )
        liveness.append((phase, writes, k, len(holding)))
        lines.append(
            f"F1 phase liveness: phase {phase} (writes {writes}) wrote its "
            f"artifact in {k} of {len(holding)} engine seasons ({ids_str})"
        )

    # F2 stall recurrence: harness-observed stopped_stall terminal states.
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
    salvaged: Counter[str] = Counter()
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
                if row.get("salvaged") is True:
                    salvaged[verdict] += 1
    other = sum(hist.values()) - sum(hist[key] for key in HISTOGRAM_KEYS)
    # s62 w1 (usefulness-decade-5 residual 7): the WIN cell splits into
    # "X WIN (Y salvaged)" when the window holds at least one WIN row
    # marked "salvaged": true; with none marked the line is byte-identical
    # to the pre-s62 form. The split reads the rows as they are -- no
    # existing record is rewritten, and only WIN splits per the s62 spec.
    if salvaged["WIN"]:
        # the split form is count-first (the s62 w2 agreed shape); the
        # unmarked form stays byte-identical to the pre-s62 goldens
        cells = [
            f"{hist[key]} {key}" + (
                f" ({salvaged['WIN']} salvaged)" if key == "WIN" else ""
            )
            for key in HISTOGRAM_KEYS
        ]
    else:
        cells = [f"{key} {hist[key]}" for key in HISTOGRAM_KEYS]
    lines.append(
        "F3 verdict histogram over verdicts.jsonl of "
        f"{','.join(sources) if sources else 'none'}"
        + (f" (none in: {','.join(bare)})" if bare else "")
        + ": "
        + ", ".join(cells)
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
            deliverable = _has_deliverable(paths.runs_dir(root) / sid / name)
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
        sid for sid in engine_ids if (paths.runs_dir(root) / sid / "results.jsonl").is_file()
    ]
    masked: list[tuple[str, int]] = []
    result_rows: dict[str, list[dict]] = {}
    for sid in harvested:
        result_rows[sid] = _result_rows(root, sid)
        integrated = sum(1 for row in result_rows[sid] if row.get("integrated") is True)
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

    # Band-mask guard (s32 w1): the recalibrate candidate arms only on masked
    # LOSS seasons whose yamls the lint band-mask guard warns — metric
    # modules_integrated with an expected_band carrying none of the
    # integration-evidence tokens. Compliant bands stop arming it; F5 keeps
    # reporting every masked season and the candidate cites only the warned.
    warned: set[str] = set()
    for sid, path in seasons:
        doc = yamlio.load(path)
        if isinstance(doc, dict) and lint.band_mask_warning(doc):
            warned.add(sid)
    armed = [(sid, k) for sid, k in masked if sid in warned]

    # F6 budget compliance: a flag, never a candidate. The operator sets the
    # number; the audit only reports that it is still unset (P9).
    if _budget_cap(root) is None:
        lines.append(
            "F6 budget compliance: campaign_cost_cap unset since campaign start (P9) "
            "— operator sets the number; the tool only flags"
        )

    # F7 usefulness decade (s33 w1): a finding only, never a candidate. The
    # verdict record's residuals arm candidates through the existing
    # machinery; this line proposes nothing.
    due_line = _usefulness_decade_due(root)
    if due_line is not None:
        lines.append(due_line)

    # Corpus matrix (s26 w1): the replay corpus matrix is the one ledger
    # artifact that can show a main-line regression (audit-13/14 never read
    # it — the recorded blind spot). A FAIL or REGRESSION row arms ONE
    # candidate placed FIRST (a regression outranks improvements); an
    # all-green matrix (>= 1 PASS, zero FAIL, zero REGRESSION notes) is a
    # plain finding; a missing or unparseable matrix changes nothing.
    corpus_candidate: tuple[str, str] | None = None
    corpus_drifts: list[tuple[str, str]] = []  # (label, record line), matrix order
    matrix_path = (
        corpus_matrix if corpus_matrix is not None else _corpus_matrix(root)
    )
    if matrix_path is not None:
        matrix_rows = _parse_matrix(matrix_path)
        if matrix_rows is not None:
            corpus_fails = [
                row for row in matrix_rows if row[1] == "FAIL" or "REGRESSION" in row[3]
            ]
            corpus_passes = sum(1 for row in matrix_rows if row[1] == "PASS")
            corpus_skips = sum(1 for row in matrix_rows if row[1] == "SKIP")
            # DRIFT arming (s43 w1, from usefulness-decade-4 residual 8): a
            # DRIFT row is a script whose assumptions moved — the reviewer's
            # own probe going stale — and it escaped the mismatch arming. One
            # candidate per drifted script, first note wins, matrix order;
            # the regression candidate keeps its FIRST priority.
            drift_seen: set[str] = set()
            for script, verdict, _first_fail, note in matrix_rows:
                if verdict == "DRIFT" and script not in drift_seen:
                    drift_seen.add(script)
                    corpus_drifts.append(
                        (
                            f"corpus drift {script}",
                            f"candidate: drift mismatch: {script} — assumptions moved "
                            f"({note or 'no note'}); band: WIN when {script} is "
                            "updated or re-sealed to current main behavior",
                        )
                    )
            if corpus_fails:
                script, _verdict, first_fail, _note = corpus_fails[0]
                where = script if first_fail in ("", "--") else f"{script} {first_fail}"
                corpus_candidate = (
                    f"corpus regression {script}",
                    f"candidate: corpus regression: {where}; "
                    f"band: WIN when the named script passes on main",
                )
            if corpus_matrix is not None:
                counts = Counter(row[1] for row in matrix_rows)
                # s43 w2 contract (s52 w1, audit-38): the green claim is honest
                # only when every discovered script passed; any SKIP retires
                # it — the coverage finding below carries the full denominator.
                green = (
                    ""
                    if corpus_fails or corpus_drifts or corpus_skips
                    else " — all green on main, no candidates"
                )
                lines.append(
                    f"corpus: fresh matrix, {counts['PASS']} PASS, {counts['FAIL']} FAIL, "
                    f"{counts['DRIFT']} DRIFT, {counts['SKIP']} SKIP{green}"
                )
                # s43 w2 coverage finding: one line covering every discovered
                # script, present even at 0 PASS (the honest floor). Finding
                # only — the gap arms zero candidates; the "candidates: none"
                # line stays when nothing else triggers.
                lines.append(
                    f"corpus coverage: {corpus_passes} repro scripts PASS of "
                    f"{len(matrix_rows)} discovered ({corpus_skips} SKIP)"
                )
            elif corpus_passes:
                lines.append(
                    f"corpus: {corpus_passes} repro scripts green on main (no candidates)"
                )

    # Candidates: deterministic triggers only, corpus regression first, then
    # drift mismatches (one per drifted script, matrix order), then phases in
    # pipeline order, then route, then calibration, stall trigger last, hard
    # cap. Never invented, never over cap.
    proposals: list[tuple[str, str]] = []  # (short label, record line)
    if corpus_candidate is not None:
        proposals.append(corpus_candidate)
    proposals.extend(corpus_drifts)
    if n >= 2:
        for phase, writes, k, n_completed in liveness:
            if k == 0 and n_completed >= 1:
                proposals.append(
                    (
                        f"{phase} ({writes})",
                        f"candidate: exercise or trim phase {phase} — {writes} "
                        f"written in 0 of {n_completed} engine seasons ({ids_str}); "
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
    if len(armed) >= BAND_MASKED_SEASONS:
        proposals.append(
            (
                "LOSS band calibration",
                f"candidate: recalibrate LOSS bands — count integrated deliverables in "
                f"the band ({','.join(sid for sid, _k in armed)}); "
                f"band: WIN when no later LOSS season ships an integrated module "
                f"its band ignores",
            )
        )
    # Verdict-artifact cross-check (s35 w1): a season verdict WIN contradicted
    # by a verdict FAIL in the season's own results.jsonl arms ONE candidate
    # naming the season and its first failing unit in file order. Consistent
    # seasons arm nothing; seasons without results rows are out of scope; the
    # F3 histogram over verdicts.jsonl is unchanged.
    for sid in harvested:
        if _season_verdict(verdict_rows.get(sid, []), sid) != "WIN":
            continue
        failed_units = [
            str(row.get("unit") or "?")
            for row in result_rows.get(sid, [])
            if row.get("verdict") == "FAIL"
        ]
        if not failed_units:
            continue
        units = ", ".join(failed_units)
        proposals.append(
            (
                "verdict mismatch",
                f"candidate: verdict mismatch: {sid} harvested WIN while its results "
                f"carry FAIL ({units}); band: WIN when the verdict matches the artifacts",
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
    # Resolution trail (issue #6): before a usefulness residual becomes a
    # candidate, its trail decides -- a board issue citing it that is
    # CLOSED, or a harvest implies/observed line naming the citing issue's
    # number, resolves it into a `resolved: ` marker: never a candidate,
    # never a cap slot.
    trail = issue_trail if issue_trail is not None else []
    harvest_lines = _harvest_resolution_lines(root)
    resolved_lines: list[str] = []
    for record_id, residual_text in _usefulness_residuals(root):
        emitted = f"usefulness residual: {residual_text} ({record_id})"
        marker = _resolved_candidate(trail, harvest_lines, emitted)
        if marker is not None:
            resolved_lines.append(marker)
            continue
        proposals.append((f"residual ({record_id})", f"candidate: {emitted}"))
    dropped = [label for label, _line in proposals[MAX_CANDIDATES:]]
    candidates = [line for _label, line in proposals[:MAX_CANDIDATES]]
    if not candidates:
        lines.append("candidates: none — no trigger met; nothing proposed without evidence")
    lines.extend(candidates)
    lines.extend(resolved_lines)
    if dropped:
        lines.append(
            f"candidate cap {MAX_CANDIDATES} reached in pipeline order; "
            f"also triggered but unproposed here: {','.join(dropped)}"
        )
    return lines, candidates


def run_audit(
    root: Path,
    last_n: int = 10,
    corpus_matrix: Path | None = None,
    issue_trail: list[dict[str, Any]] | None = None,
) -> Path:
    """Reflect over the last `last_n` seasons; append the audit akar record.

    Reads musim/s*.yaml (sorted by number, last N), each audited season's
    own declared pipeline, each window season's yaml through the lint
    band-mask guard, the per-season state.json statuses and finalized
    agent snapshots, verdicts.jsonl and results.jsonl rows, the rumpun.yaml
    budget block, and the newest committed replay matrix
    (.rumpun/akar/evidence/s<N>/replay-matrix.md) — or, when corpus_matrix
    is given (s30 w1), the fresh matrix refresh_corpus_matrix just wrote.
    Every claim the
    record makes cites its season ids; the only mutation is the appended
    record (id audit-<k>, k = 1 + existing audit-* records by akar/
    filename scan). akar.AkarError wraps into AuditError. Returns the
    record path.  issue_trail (issue #6): trail rows {number, state,
    body}; with them, a usefulness candidate whose resolution trail
    holds (a CLOSED board issue citing the candidate line verbatim, or
    a harvest implies/observed line naming the citing issue's number)
    is emitted as a `resolved: ` marker carrying that evidence, never a
    candidate or a cap slot.  None keeps the ledger-only behavior
    byte-stable with the pre-s84 audit.
    """
    if last_n < 1:
        raise AuditError(f"last_n must be >= 1, got {last_n}")
    seasons = _seasons(root, last_n)
    engine_ids = [sid for sid, _p in seasons if (paths.runs_dir(root) / sid).is_dir()]
    if not engine_ids:
        raise AuditError(
            f"no audited season has a season directory under {root}; "
            "nothing to reflect on"
        )
    body, _candidates = _findings_and_candidates(
        root, seasons, corpus_matrix, issue_trail
    )
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


def season_review_lines(root: Path, last_n: int = 10) -> list[str]:
    """One review row per window season, printed by the audit verb.

    Each row names the season, its judge verdict (WIN and LOSS verbatim,
    any other word renders as other), the latest panel verdict record,
    and the dissent mark when the two sides differ.
    """
    seasons = _seasons(root, last_n)
    records = akar.declared_ids(root)
    rows: list[str] = []
    for sid, _path in seasons:
        verdict = epics.season_verdict(root, sid)
        row = f"  {sid}"
        if verdict:
            klass = verdict if verdict in ("WIN", "LOSS") else "other"
            row += f"  judge {klass}"
        rid = epics._latest_verdict_id(sid, records)
        if rid is not None:
            sha8 = epics._seal8(records[rid])
            mark = f"{rid}@{sha8}" if sha8 else rid
            word = epics._panel_status(records[rid])
            row += f"  {mark}" + (f" ({word})" if word else "")
        row += epics._dissent_mark(sid, verdict, records)
        rows.append(row)
    return rows


def _usefulness_front_line(front: Mapping[str, str]) -> str:
    """One canonical front bullet; refuses shapes that would not parse back.

    The canonical line (the s87 shape):

        - <name> - owner: <owner>. <basis> Next: <next>.

    The composer terminates next with one trailing period; the reader
    strips exactly that period back off. name, owner, and next are
    required and nonempty; basis is optional. Refusals (AuditError,
    never a silent skip): a required field empty; a name carrying the
    owner separator; an owner carrying ". " (the reader would split the
    owner there and swallow the basis); any field carrying " Next: "
    (the tail would be lost on read).
    """
    name = str(front.get("name", "")).strip()
    owner = str(front.get("owner", "")).strip()
    basis = str(front.get("basis", "")).strip()
    nxt = str(front.get("next", "")).strip()
    missing = [k for k in ("name", "owner", "next") if not str(front.get(k, "")).strip()]
    if missing:
        raise AuditError(f"assessment front is missing {', '.join(missing)}: {front!r}")
    if " - owner: " in name:
        raise AuditError(f"assessment front name carries the owner separator: {name!r}")
    if ". " in owner:
        msg = f"assessment front owner carries '. ' (the basis would not read back): {owner!r}"
        raise AuditError(msg)
    for field in (owner, basis, nxt):
        if " Next: " in field:
            msg = f"assessment front field carries the next separator: {field!r}"
            raise AuditError(msg)
    line = f"- {name} - owner: {owner}."
    if basis:
        line += f" {basis}"
    return f"{line} Next: {nxt}."


def _usefulness_basis_value(raw_basis: Any) -> str | None:
    """Pre-flight the optional top-level basis; refuses shape-tearing values.

    The basis splices into the record as one `basis: <text>` body line
    (the s87 shape), so a non-string (silently stringified before s114)
    and a string carrying a newline (the body would tear; the reader
    would never parse the line back) refuse through AuditError, the same
    both-doors discipline _usefulness_front_line gives the fronts. An
    empty or whitespace-only basis returns None, and None keeps the
    module default (_USEFULNESS_BASIS) at the seal.
    """
    if raw_basis is None:
        return None
    if not isinstance(raw_basis, str):
        msg = f"assessment basis must be a string, got {type(raw_basis).__name__}"
        raise AuditError(msg)
    if "\n" in raw_basis or "\r" in raw_basis:
        msg = "assessment basis must be one line (a newline tears the record shape)"
        raise AuditError(msg)
    return raw_basis.strip() or None


def _parse_usefulness_front(line: str) -> dict[str, str]:
    """One front bullet -> {name, owner, basis, next}.

    Lenient where the s87 precedent is: a front whose account ends
    without a Next: segment reads back with next "" (the composer never
    emits that shape -- next is required -- but usefulness-s87 seals two
    such fronts, and the precedent parses). A bullet with no owner
    segment or an empty owner is a torn record and refuses (AuditError).
    """
    if " - owner: " not in line:
        raise AuditError(f"front bullet carries no owner segment: {line!r}")
    name, rest = line[2:].split(" - owner: ", 1)
    if " Next: " in rest:
        mid, nxt = rest.rsplit(" Next: ", 1)
        nxt = nxt.strip().removesuffix(".")
    else:
        mid, nxt = rest, ""
    if ". " in mid:
        owner, basis = mid.split(". ", 1)
    else:
        owner, basis = mid, ""
    owner, basis = owner.strip(), basis.strip()
    if not name.strip() or not owner:
        raise AuditError(f"front bullet carries an empty name or owner: {line!r}")
    return {"name": name.strip(), "owner": owner, "basis": basis, "next": nxt}


def _record_body_digest(record: Path) -> str:
    """The sha256 trailer hex of an akar record file (s105 w2).

    A file whose last line is not the sha256 trailer is a torn record
    and refuses (AuditError): a supersede never cites a digest it did
    not read.
    """
    try:
        lines = record.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        logger.exception("cannot read akar record %s", record)
        raise AuditError(f"cannot read {record}: {exc}") from exc
    if not lines or not lines[-1].startswith("sha256: "):
        raise AuditError(f"{record}: no sha256 trailer (torn record)")
    return lines[-1].removeprefix("sha256: ").strip()


def _superseding_basis_record(ledger: Path, record_id: str) -> Path | None:
    """The newest usefulness-<sid>-basis sibling of record_id, or None (s105 w2).

    The s104 disclosed miss's convention: a corrected basis lands as a
    sibling record, filename-sorted so the newest wins; only an original
    usefulness-<sid> consults its siblings (a -basis record's own glob
    never matches itself). A name match is not a parse -- the caller
    reads the sibling through the full record contract, digest included.
    """
    sid = record_id.removeprefix("usefulness-")
    if not sid:
        return None
    matches = sorted(ledger.glob(f"*_usefulness-{sid}-basis.md"))
    return matches[-1] if matches else None


def _usefulness_epics_rows(root: Path) -> list[str]:
    """Per-epic raw and adjusted count rows for the assessment body (s118 w1).

    The decade-6 review's residual: the assessment preserved WIN totals
    while the rollup adjusted them. The seal reads the adjusted truth
    from the campaign itself, so no composer hand-copies the counts (the
    count-from-memory error class). For each epic declared in epics.yaml
    the body renders one row naming the raw WIN/LOSS/other triple
    verbatim, with the adjusted triple beside it when any member's
    dissent qualifies (epics.ADJUSTING_DISSENTS: a WIN member whose
    latest dissent is INCONCLUSIVE or NEUTRAL moves WIN -> other). The
    counting reuses the epics helpers the rollup itself uses, so the two
    surfaces cannot disagree; members without run state are excluded
    from the counts. An epic with no qualifying member renders no
    adjusted clause; no epics.yaml (or an empty declaration) renders no
    section, so a campaign without epics seals byte-identical to the s88
    shape. A malformed declaration refuses through AuditError: the
    assessment never seals on counts it cannot read.
    """
    epics_file = epics.epics_path(root)
    if not epics_file.is_file():
        return []
    doc = yamlio.load(epics_file)
    if not isinstance(doc, dict):
        msg = f"{epics_file}: the epics document must be a mapping"
        raise AuditError(msg)
    records = akar.declared_ids(root)
    rows: list[str] = []
    for epic_id, body in doc.items():
        if not isinstance(body, dict):
            msg = f"epic '{epic_id}': declaration must be a mapping"
            raise AuditError(msg)
        members = sorted(
            (str(m) for m in body.get("seasons") or []), key=epics._season_num
        )
        wins = losses = others = adjusted = 0
        for sid in members:
            verdict = epics.season_verdict(root, sid)
            if verdict is None and not epics.has_run_state(root, sid):
                continue
            word = epics._dissent_word(sid, verdict, records)
            if verdict == "WIN":
                wins += 1
                if word in epics.ADJUSTING_DISSENTS:
                    adjusted += 1
            elif verdict == "LOSS":
                losses += 1
            else:
                others += 1
        row = f"- {epic_id}: {wins} WIN / {losses} LOSS / {others} other"
        if adjusted:
            row += (
                f"  (adjusted: {wins - adjusted} WIN / {losses} LOSS / "
                f"{others + adjusted} other)"
            )
        rows.append(row)
    return ["epics:", *rows] if rows else []


def _seal_basis_supersede(
    root: Path,
    sid: str,
    verdict: str,
    fronts: Sequence[Mapping[str, str]],
    *,
    satisfied: Sequence[str],
    basis: str | None,
) -> Path:
    """Append the basis-supersede record for usefulness-<sid> (s105 w2).

    The s104 disclosed miss: the s104 w1 assessment sealed with the
    module's default basis (the yaml omitted the top-level basis key)
    and sealed records never delete, so the correction is an append --
    usefulness-<sid>-basis, a full assessment record whose basis line is
    the correction and whose supersedes line cites the original id and
    body sha256; the original stands (the akar discipline). Refusals
    (AuditError, never noise): no original; a torn original; an
    unchanged basis -- the effective basis (a prior supersede's basis
    when one stands) already says it. A second, still-different
    correction collides with the declared usefulness-<sid>-basis id;
    akar refuses the duplicate honestly. The body carries the s118 epics
    count rows the same as the original seal.
    """
    original_id = f"usefulness-{sid}"
    try:
        original = akar.find_record(root, original_id)
    except akar.AkarError as exc:
        logger.exception("cannot supersede %s: the original is missing", original_id)
        raise AuditError(f"cannot supersede {original_id}: {exc}") from exc
    effective = read_usefulness_assessment(original)["basis"]
    requested = basis if basis is not None else _USEFULNESS_BASIS
    if requested == effective:
        msg = f"{original_id}: basis unchanged ({requested!r}); no supersede record appended"
        raise AuditError(msg)
    lines = [
        f"verdict: {verdict}",
        f"basis: {requested}",
        f"supersedes: {original_id} (sha256 {_record_body_digest(original)})",
        *_usefulness_epics_rows(root),
        "fronts:",
        *(_usefulness_front_line(front) for front in fronts),
    ]
    lines.append(_SATISFIED_HEADER)
    lines.extend(f"- {item}" for item in satisfied)
    title = f"{verdict} (the basis supersede of {original_id})"
    return akar.append_record(root, f"usefulness-{sid}-basis", title, "\n".join(lines))


def seal_usefulness_assessment(
    root: Path,
    sid: str,
    verdict: str,
    fronts: Sequence[Mapping[str, str]],
    *,
    satisfied: Sequence[str] = (),
    basis: str | None = None,
    supersede: bool = False,
) -> Path:
    """Seal the per-season usefulness assessment as usefulness-<sid> (s88 w2).

    The sealed s87 record (usefulness-s87) is the contract: the body is
    the verdict line, the basis line, the fronts each named with its
    owner and next-action, and the satisfied list (recorded, not
    fronts); akar wraps it with the standard header and the body sha256.
    The verdict vocabulary is CONTINUE | PAUSE | EXHAUSTED -- an unknown
    verdict raises ValueError naming the vocabulary, the same honesty as
    harvest_season's verdict check. Front shapes refuse through
    _usefulness_front_line (AuditError). fronts may be empty (an
    EXHAUSTED close): the section header still lands, so the body shape
    is byte-stable at every arity.

    The seal reads the adjusted truth from the campaign (s118 w1): one
    epics section sits between the basis and the fronts, one row per
    declared epic, the raw triple verbatim with the adjusted triple
    named beside it when a member's dissent qualifies; a campaign
    without epics.yaml seals byte-identical to the s88 shape.

    The fronts are the caller's judgment composed FROM the board trail
    and the ledger: each front's basis carries its own citations
    (ledger:<id>@<sha>); the composer cites nothing it did not read.

    With supersede=True the call is the re-seal half of the convention
    (s105 w2, the s104 disclosed miss): the original stands, the corrected
    basis lands as usefulness-<sid>-basis -- a full assessment record
    whose supersedes line cites the original id and body sha256. Refusals
    (AuditError): no original; a torn original; an unchanged basis. A
    second, still-different correction collides with the declared
    usefulness-<sid>-basis id; akar refuses the duplicate honestly.
    Returns the sealed record path.
    """
    if verdict not in USEFULNESS_VERDICTS:
        msg = f"usefulness verdict must be one of {'|'.join(USEFULNESS_VERDICTS)}, got {verdict!r}"
        raise ValueError(msg)
    basis = _usefulness_basis_value(basis)
    if supersede:
        return _seal_basis_supersede(
            root, sid, verdict, fronts, satisfied=satisfied, basis=basis
        )
    lines = [
        f"verdict: {verdict}",
        f"basis: {basis if basis is not None else _USEFULNESS_BASIS}",
        *_usefulness_epics_rows(root),
        "fronts:",
        *(_usefulness_front_line(front) for front in fronts),
    ]
    lines.append(_SATISFIED_HEADER)
    lines.extend(f"- {item}" for item in satisfied)
    title = f"{verdict} ({_USEFULNESS_TITLE})"
    return akar.append_record(root, f"usefulness-{sid}", title, "\n".join(lines))


def usefulness_inputs(data: Any) -> tuple[str, list[dict[str, str]], list[str], str | None]:
    """Pre-flight the --assessment-file mapping (s88 w2).

    Accepts the yaml mapping the harvest verb reads:

        verdict: CONTINUE            # required; CONTINUE | PAUSE | EXHAUSTED
        basis: <optional override of the default basis line>
        fronts:                      # required list, may be empty
        - name: ...
          owner: ...
          basis: <optional>
          next: ...
        satisfied:                   # optional list of lines

    Every violation raises AuditError naming the field. The CLI runs this
    BEFORE the close writes anything, so a bad assessment file refuses
    the whole close instead of leaving a harvest without its assessment.
    Returns (verdict, fronts, satisfied, basis-or-None); the fronts come
    back already validated through _usefulness_front_line.
    """
    if not isinstance(data, dict):
        raise AuditError(f"assessment file must be a mapping, got {type(data).__name__}")
    verdict = data.get("verdict")
    if not isinstance(verdict, str) or verdict not in USEFULNESS_VERDICTS:
        vocab = "|".join(USEFULNESS_VERDICTS)
        raise AuditError(f"assessment verdict must be one of {vocab}, got {verdict!r}")
    raw_fronts = data.get("fronts")
    if not isinstance(raw_fronts, list):
        raise AuditError("assessment fronts must be a list")
    fronts: list[dict[str, str]] = []
    for front in raw_fronts:
        if not isinstance(front, dict):
            raise AuditError(f"assessment front must be a mapping, got {front!r}")
        _usefulness_front_line(front)
        fronts.append({
            "name": str(front.get("name", "")).strip(),
            "owner": str(front.get("owner", "")).strip(),
            "basis": str(front.get("basis", "")).strip(),
            "next": str(front.get("next", "")).strip(),
        })
    raw_satisfied = data.get("satisfied", [])
    if not isinstance(raw_satisfied, list):
        raise AuditError("assessment satisfied must be a list")
    satisfied = [str(item) for item in raw_satisfied]
    basis = _usefulness_basis_value(data.get("basis"))
    return verdict, fronts, satisfied, basis


def read_usefulness_assessment(record: Path) -> dict[str, Any]:
    """Parse a sealed usefulness-<sid> record back into its fields (s88 w2).

    The akar layout docstring is the recovery contract: the body is
    lines[4:-1] between the title header and the sha256 trailer, and the
    trailer must digest exactly those body bytes -- a mismatch is an
    AuditError, so a torn or edited record never reads as an assessment.
    The verdict must sit in USEFULNESS_VERDICTS. Returns {id, title,
    verdict, basis, weight, fronts, satisfied}; each front is {name,
    owner, basis, next} through _parse_usefulness_front. The epics
    section (s118 w1) reads back as verbatim row strings under epics; a
    record without the section reads back with an empty list.

    When the record has a superseding-basis sibling (s105 w2, the s104
    disclosed miss), the returned basis is the superseding one and
    basis_superseded_by names the superseding record; the sibling reads
    through this same contract, so a torn supersede never reads as an
    assessment.
    """
    try:
        lines = record.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        logger.exception("cannot read usefulness record %s", record)
        raise AuditError(f"cannot read {record}: {exc}") from exc
    if len(lines) < 6 or not lines[0].startswith("# akar record: usefulness-"):
        raise AuditError(f"{record} is not a usefulness record")
    record_id = lines[1].removeprefix("id: ").strip()
    title = lines[3].removeprefix("title: ").strip()
    body, trailer = lines[4:-1], lines[-1]
    digest = trailer.removeprefix("sha256: ").strip()
    if hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest() != digest:
        raise AuditError(f"{record}: body digest mismatch (torn or edited record)")
    fields: dict[str, str] = {}
    fronts: list[dict[str, str]] = []
    satisfied: list[str] = []
    epics_rows: list[str] = []
    section = ""
    for line in body:
        if line.startswith("fronts:"):
            section = "fronts"
            continue
        if line.startswith("epics:"):
            section = "epics"
            continue
        if line.startswith(_SATISFIED_HEADER):
            section = "satisfied"
            continue
        if line.startswith("- "):
            if section == "fronts":
                fronts.append(_parse_usefulness_front(line))
            elif section == "satisfied":
                satisfied.append(line[2:])
            elif section == "epics":
                epics_rows.append(line[2:])
            continue
        if line.startswith("verdict: "):
            fields["verdict"] = line.removeprefix("verdict: ").strip()
            section = ""
        elif ": " in line:
            key, value = line.split(": ", 1)
            if key in ("basis", "weight", "seasons", "scope"):
                fields[key] = value.strip()
            section = ""
    verdict = fields.get("verdict", "")
    if verdict not in USEFULNESS_VERDICTS:
        vocab = "|".join(USEFULNESS_VERDICTS)
        raise AuditError(f"{record}: verdict {verdict!r} is not one of {vocab}")
    result = {
        "id": record_id,
        "title": title,
        "verdict": verdict,
        "basis": fields.get("basis", ""),
        "weight": fields.get("weight", ""),
        "fronts": fronts,
        "satisfied": satisfied,
        "epics": epics_rows,
    }
    superseding = _superseding_basis_record(record.parent, record_id)
    if superseding is not None:
        superseding_data = read_usefulness_assessment(superseding)
        result["basis"] = superseding_data["basis"]
        result["basis_superseded_by"] = superseding_data["id"]
    return result


USEFULNESS_VERDICTS = ("CONTINUE", "PAUSE", "EXHAUSTED")
_USEFULNESS_TITLE = "the per-season usefulness assessment over the whole ledger"
_USEFULNESS_BASIS = (
    "directive seq 9 - usefulness exhaustion is the stopping criterion;"
    " every front below names its owner and next-action"
)
_SATISFIED_HEADER = "satisfied (recorded, not fronts):"
