"""rumpun harvest — season close into the akar ledger (build order step 4).

`harvest_season` reads the engine's season snapshot and appends one record per
season close: status, duration, per-agent state table, verdict, implies line.
Manual verdict entry first (build order step 4); the body is derived from
harness-observed state only ([H] per P36), never from agent-authored text.

M3 (codex-review-2026-09-14): the close ALSO appends the season-level row to
rimba/<sid>/verdicts.jsonl — the file report and audit already read — so one
harvest call writes both books. band/observed/implies are caller-supplied
verdict content ([A]); the row write itself is harness-side.

M4 full (s41 w1): only terminal seasons harvest. A season whose persisted
status is not completed / failed / stopped_* is refused with AkarError
naming the season and status, before any id is consumed or row written.
The s21 row-exists refusal stays as the second guard behind it.

s62 w1 (usefulness-decade-5 residual 7): a stopped_* close is a salvage --
the operator harvested a season that never completed. The mark is the
persisted terminal status itself (harness-observed [H], never verdict
content): the verdict row gains "salvaged": true and the record title
carries "(salvaged)". completed and failed closes stay unmarked.

s135 w2 (issue #47): the close emits the LOSS the season meets. A WIN
downgrades to LOSS when the close inputs carry a deterministic met-LOSS
signal: the observed text admits a declared lane never ran, the observed
text admits a met LOSS condition outright, or a prior judge row in the
season's verdicts.jsonl reads LOSS. An explicit `justification:` line in
the observed text retains the WIN; the grading is recorded either way.
Non-WIN verdicts pass through untouched.

Write order (s41 w1, the s32 repair): the akar record is appended BEFORE
the verdicts.jsonl season row. A fault after the append but before the row
write leaves the record on the ledger as the recovery source (the row can
be re-added from it); a fault before the append strands nothing, because
the record append is the close's first side effect.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from rumpun import akar, engine, paths, yamlio

logger = logging.getLogger(__name__)

VERDICTS = ("WIN", "LOSS", "NEUTRAL", "INVALID")


def _dash(value: Any) -> str:
    """Markdown cell: None renders as '-', anything else as str()."""
    return "-" if value is None else str(value)


def _render_body(state: dict[str, Any], verdict: str, implies: str) -> str:
    """Record body: season status, duration, agent table, incomplete marks, verdict, implies."""
    started = float(state["started_at"])
    ended = state.get("ended_at") or time.time()
    agents = state.get("agents") or {}
    lines = [
        f"season {state['id']}: {state['status']}",
        f"duration: {ended - started:.0f}s",
        "",
        "| agent | route | state | exit_code | seconds |",
        "|---|---|---|---|---|",
    ]
    for name in sorted(agents):
        a = agents[name]
        lines.append(
            f"| {_dash(a.get('name', name))} | {_dash(a.get('route'))}"
            f" | {_dash(a.get('state'))} | {_dash(a.get('exit_code'))}"
            f" | {_dash(a.get('seconds'))} |"
        )
    seconds = [
        float(a["seconds"])
        for a in agents.values()
        if isinstance(a.get("seconds"), (int, float))
    ]
    lines += [
        "",
        f"spend: writers={len(agents)}"
        f" writer_seconds={sum(seconds):.1f}"
        f" duration_s={ended - started:.0f}",
    ]
    # s114 w2 (the harvest gate): the body says what the notes gate saw --
    # one line per unit whose snap carries the additive incomplete key,
    # unit then the key value verbatim. Clean seasons gain nothing.
    for name in sorted(agents):
        gap = agents[name].get("incomplete")
        if gap:
            lines.append(f"incomplete {name}: {gap}")
    judge = state.get("judge") or {}
    adopt = judge.get("adopt") or ([judge["winner"]] if judge.get("winner") else [])
    if adopt:
        lines.append(
            f"adopted: {', '.join(str(a) for a in adopt)}"
            f" ({str(judge.get('reason', ''))[:200]})"
        )
        eliminated = [n for n in sorted(agents) if n not in {str(a) for a in adopt}]
        if eliminated:
            lines.append(f"not adopted: {', '.join(eliminated)}")
    elif judge:
        lines.append(
            "adopted: none ("
            + str(judge.get("reason") or judge.get("error") or "no verdict")[:200]
            + ")"
        )
    lines += ["", f"verdict: {verdict}", f"implies: {implies}"]
    return "\n".join(lines)


def _season_metric(root: Path, sid: str) -> str:
    """Campaign metric from musim/<sid>.yaml; '' when the file or key is absent."""
    try:
        cfg = yamlio.load(paths.seasons_dir(root) / f"{sid}.yaml")
    except (OSError, yamlio.YamlError):
        return ""
    value = cfg.get("metric") if isinstance(cfg, dict) else None
    return "" if value is None else str(value)


def _has_season_row(root: Path, sid: str) -> bool:
    """True when rimba/<sid>/verdicts.jsonl already carries a season-level row.

    Corrupt lines are skipped, the same reader contract as report._verdict_of.
    """
    path = paths.runs_dir(root) / sid / "verdicts.jsonl"
    if not path.is_file():
        return False
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                if json.loads(line).get("season") == sid:
                    return True
            except ValueError:
                continue
    return False


def _is_terminal(status: str) -> bool:
    """M4: a season is harvestable only once its judgment is final.

    completed, failed, and any stopped_* rule stop are terminal. running
    and any unrecognized status are not: an unrecognized status must fail
    closed, the same stance as engine.status_exit_code, so no unknown
    status consumes the permanent id.
    """
    return status == "completed" or status == "failed" or status.startswith("stopped_")


_LOSS_DOWN_PHRASES = ("never ran", "never started", "did not run", "not run")
_MET_LOSS_RE = re.compile(r"\bloss (?:condition )?met\b", re.IGNORECASE)
_JUSTIFIED_RE = re.compile(r"\bjustification:", re.IGNORECASE)


def _writer_names(root: Path, sid: str) -> list[str]:
    """Declared writer names from the season yaml; [] when unreadable."""
    try:
        cfg = yamlio.load(paths.seasons_dir(root) / f"{sid}.yaml")
    except (OSError, yamlio.YamlError):
        return []
    writers = cfg.get("writers") or cfg.get("benih") or [] if isinstance(cfg, dict) else []
    names = []
    for w in writers:
        if isinstance(w, dict) and w.get("name"):
            names.append(str(w["name"]))
    return names


def _judge_loss_ids(root: Path, sid: str) -> list[str]:
    """Experiment ids of prior judge rows already reading LOSS (issue #47).

    Same reader contract as _has_season_row: corrupt lines are skipped.
    """
    path = paths.runs_dir(root) / sid / "verdicts.jsonl"
    if not path.is_file():
        return []
    ids = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and str(row.get("verdict", "")).upper() == "LOSS":
                ids.append(str(row.get("experiment_id") or row.get("season") or "row"))
    return ids


def _loss_grade(root: Path, sid: str, verdict: str, observed: str) -> tuple[str, str | None]:
    """Emit the LOSS the season meets (s135 w2, issue #47).

    WIN-only grading is the #47 defect: audit F3 read WIN 10 / LOSS 0
    across khursani s77-s86 while s85's own observed field admitted its
    verify lane never ran. The grade is deterministic, never prose
    grading. Signals in the close inputs:
    - the observed text admits a declared lane never ran
      (`<writer> ... never ran|never started|did not run|not run`);
    - the observed text admits a met LOSS condition outright;
    - a prior judge row in verdicts.jsonl already reads LOSS.
    A `justification:` line in observed retains the WIN explicitly; the
    grading is recorded either way, silence is the #47 shape. Non-WIN
    verdicts pass through untouched (no inversion).
    """
    if verdict != "WIN":
        return verdict, None
    observed = observed or ""
    signals: list[str] = []
    for name in _writer_names(root, sid):
        pattern = (
            r"\b" + re.escape(name) + r"\b[^.;]*\b(?:"
            + "|".join(re.escape(p) for p in _LOSS_DOWN_PHRASES)
            + r")\b"
        )
        if re.search(pattern, observed, re.IGNORECASE):
            signals.append(f"observed admits declared lane {name} never ran")
    if _MET_LOSS_RE.search(observed):
        signals.append("observed admits a met LOSS condition")
    for rid in _judge_loss_ids(root, sid):
        signals.append(f"judge row {rid} reads LOSS")
    if not signals:
        return verdict, None
    if _JUSTIFIED_RE.search(observed):
        note = "loss-grade: WIN retained with justification: " + "; ".join(signals)
        logger.warning("season %s %s", sid, note)
        return "WIN", note
    note = "loss-grade: WIN downgraded to LOSS: " + "; ".join(signals)
    logger.warning("season %s %s", sid, note)
    return "LOSS", note


def harvest_season(
    root: Path,
    sid: str,
    verdict: str,
    implies: str,
    band: str = "",
    observed: str = "",
) -> Path:
    """Close season `sid`: append its akar record AND the season verdict row.

    M4 full: the season's persisted status must be terminal (completed,
    failed, or stopped_*); anything else -- running included -- is refused
    with AkarError naming the season and status, before any id is consumed
    or row written. The s21 refusal (second harvest of a season whose
    verdicts.jsonl already carries the season-level row) stays as the
    second guard. M3: one close writes both books, the akar record and the
    verdicts row; the record is appended FIRST, so a fault between the two
    writes leaves the record as the recovery source and the row re-addable,
    while a fault before it strands nothing. Returns the akar record path.

    s62 w1: a stopped_* close is a salvage -- the mark derives from the
    persisted terminal status already read here (engine.read_persisted_status),
    so the verdict row gains "salvaged": true and the record title carries
    "(salvaged)". completed and failed closes stay unmarked.

    s135 w2 (issue #47): the emitted verdict is graded, not trusted. A WIN
    whose close inputs carry a met-LOSS signal reads LOSS in the row (or
    reads WIN only with an explicit `justification:` line in observed);
    _loss_grade returns the effective verdict and the note the record
    carries.
    """
    if verdict not in VERDICTS:
        msg = f"verdict must be one of {'|'.join(VERDICTS)}, got '{verdict}'"
        raise ValueError(msg)
    state = engine.read_persisted_status(root, sid)
    status = state["status"]
    if not _is_terminal(status):
        msg = (
            f"season {sid} is not terminal (status: {status}); refusing"
            " harvest: only completed, failed, or stopped_* seasons close"
        )
        raise akar.AkarError(msg)
    # s62 w1 (usefulness-decade-5 residual 7): a stopped_* close is a
    # salvage -- the operator harvested a season that never completed. The
    # mark is the persisted terminal status itself (harness-observed [H]),
    # so a salvaged WIN reads as salvaged wherever the row travels.
    salvaged = status.startswith("stopped_")
    if _has_season_row(root, sid):
        msg = (
            f"season {sid} is terminal (status: {state['status']}) and"
            " its verdicts.jsonl already carries a season-level"
            " row; refusing second harvest"
        )
        raise akar.AkarError(msg)
    # s135 w2 (issue #47): grade before any write, so the record, the row,
    # the event, and the lesson all carry the emitted verdict.
    verdict, loss_note = _loss_grade(root, sid, verdict, observed)
    record_id = f"{sid}-harvest"
    body = _render_body(state, verdict, implies)
    if loss_note:
        body += "\n" + loss_note
    # Write order (the s32 repair): the record lands before the row, so a
    # fault after the append leaves the record as the recovery source (the
    # row can be re-added from it) and a fault before the append strands
    # nothing -- the append is the close's first side effect.
    title = f"season {sid} harvest" + (" (salvaged)" if salvaged else "")
    path = akar.append_record(root, record_id, title, body)
    row = {
        "season": sid,
        "verdict": verdict,
        "metric": _season_metric(root, sid),
        "band": band,
        "observed": observed,
        "implies": implies,
    }
    if salvaged:
        row["salvaged"] = True
    verdicts = paths.runs_new(root) / sid / "verdicts.jsonl"
    verdicts.parent.mkdir(parents=True, exist_ok=True)
    with verdicts.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
        fh.flush()
    logger.info("season %s verdict row appended -> %s", sid, verdicts)
    logger.info("season %s harvested (%s) -> %s", sid, verdict, path)
    # Issue #30: harvest is the second producer on the event bus.
    from rumpun import loop as loop_mod

    loop_mod.emit_event(root, loop_mod.HARVESTED, sid, f"harvest:{verdict}")
    # Issue #27: refresh the one-screen re-entry view at every close.
    from rumpun import resume as resume_mod

    resume_mod.write_resume(root)
    # Issue #43: the lesson compounds into future generations -- one line
    # per close; season start injects the last 10 into every agent prompt.
    lessons = paths.state_dir(root) / "lessons.md"
    with lessons.open("a", encoding="utf-8") as fh:
        fh.write(f"- {sid} {verdict}: {implies}\n")
    return path
