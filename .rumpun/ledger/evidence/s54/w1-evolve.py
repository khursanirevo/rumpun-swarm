"""rumpun evolve — deterministic next-season drafting v0 (build order step 5).

draft_next copies the latest season into the next lifecycle-fresh
musim/s<N>.yaml with a fresh primary_change skeleton; an evolver agent
fills it with akar citations; apply runs the P27 lint gate before the
draft may become a season. Stall resume (s36): a stopped_stall parent
drafts with every benih budget raised to its times 1.5 (rounded up) and
a header line citing the stall. Draft numbering reads a lifecycle high-water
mark (M8): the next id is one past the highest season number the lifecycle
ever allocated — musim/s*.yaml, musim/rejected/, and reject-/rollback-
akar records — so a rejected or rolled-back latest season is never
re-issued.
approve_draft / reject_draft record the operator's P33 decision on a draft
in akar; reject also moves the draft into musim/rejected/. rollback_season
contains an applied season the same way (a season that passed apply, not a
draft), stopping the season first when it is still active (H8), and never
runs git: code-level restore is an explicit git revert by the operator.
"""

from __future__ import annotations

import logging
import math
import re
from pathlib import Path

from rumpun import akar, engine, lint, paths, yamlio

logger = logging.getLogger(__name__)

_SEASON_RE = re.compile(r"^s(\d+)$")
_SEASON_FILE_RE = re.compile(r"^s(\d+)\.yaml$")
_LIFECYCLE_ID_RE = re.compile(r"^(?:reject|rollback)-s(\d+)$")

_PRIMARY_CHANGE_SKELETON = """\
  primary_change:
    type: add            # add | remove | rewire | retune (P12/P34 grammar)
    node: execute
    baseline: ""         # evolver fills: parent best + how measured (P13)
    expected_band: ""    # evolver fills: WIN if >= X, LOSS if <= Y
    rollback: ""         # evolver fills: git revert to parent season tag
    eval_window: ""      # evolver fills: which runs decide the verdict
"""

# stall resume (s36): a stopped_stall parent drafts a resume — every benih
# budget raises to its times 1.5 (rounded up) and the header cites the stall.
_STALL_RESUME_FACTOR = 1.5
_BUDGET_LINE_RE = re.compile(r"^(\s*)budget: \{minutes: (\d+)\}$")


class EvolveError(Exception):
    pass


def _season_numbers(directory: Path) -> list[int]:
    """s<N> numbers of the s<N>.yaml files directly inside one directory."""
    return [
        int(match.group(1))
        for entry in directory.iterdir()
        if entry.is_file() and (match := _SEASON_FILE_RE.match(entry.name))
    ]


def _latest_season(musim: Path) -> int | None:
    """The highest-numbered top-level musim/s<N>.yaml, or None."""
    return max(_season_numbers(musim), default=None)


def _high_water_mark(root: Path) -> int:
    """The highest season number the lifecycle has ever allocated (M8).

    Max over three ledger sources: top-level musim/s<N>.yaml, the rejected
    drafts and rolled-back seasons under musim/rejected/, and akar lifecycle
    record ids reject-s<N> / rollback-s<N> (declared-id scan — the H8
    resolution rule, so a filename/declared-id mismatch cannot hide an id).
    Scan by choice, no counter file: the akar ledger is append-only
    evidence, the mark derives fresh from it on every draft, and no mutable
    counter state can drift from what the ledger already says.
    """
    seasons = paths.seasons_dir(root)
    numbers = _season_numbers(seasons) if seasons.is_dir() else []
    rejected = seasons / "rejected"
    if rejected.is_dir():
        numbers += _season_numbers(rejected)
    for record_id in akar.declared_ids(root):
        if match := _LIFECYCLE_ID_RE.match(record_id):
            numbers.append(int(match.group(1)))
    return max(numbers, default=0)


def _stall_resume(root: Path, parent: dict, parent_id: str) -> dict[int, int] | None:
    """The benih-budget raise for a stopped_stall parent, or None to draft verbatim.

    Reads the parent's persisted engine state (engine.read_persisted_status on
    the parent sid). Only a terminal stopped_stall status drafts a resume: every
    benih budget maps to its parent's times 1.5 (rounded up to whole minutes,
    e.g. 40 -> 60). A parent with no persisted engine state (applied but never
    started) or any other status -- running, completed, stopped_operator,
    failed, stopped_budget -- returns None and drafts byte-identical to before.
    Malformed benih budgets on a stalled parent raise EvolveError instead of
    drafting a silent partial resume.
    """
    try:
        status = engine.read_persisted_status(root, parent_id).get("status")
    except engine.EngineError as exc:
        logger.info(
            "draft_next: no persisted engine state for %s (%s); drafting verbatim",
            parent_id,
            exc,
        )
        return None
    if status != "stopped_stall":
        return None
    return _stall_budgets(parent, parent_id)


def _stall_budgets(parent: dict, parent_id: str) -> dict[int, int]:
    """The resume map (parent minutes -> raised minutes); EvolveError when malformed.

    lint requires every benih to carry budget.minutes as a positive int, so a
    stalled parent missing one never passed apply -- refusing to draft is the
    honest response, not silently drafting an unraised budget.
    """
    writers = parent.get("writers") or parent.get("benih")
    if not isinstance(writers, list) or not writers:
        msg = f"stopped_stall parent {parent_id} has no writer table to re-size"
        raise EvolveError(msg)
    resume: dict[int, int] = {}
    for entry in writers:
        if not isinstance(entry, dict):
            msg = f"stopped_stall parent {parent_id}: writer entries must be mappings"
            raise EvolveError(msg)
        budget = entry.get("budget")
        minutes = budget.get("minutes") if isinstance(budget, dict) else None
        if not isinstance(minutes, int) or isinstance(minutes, bool) or minutes <= 0:
            msg = (
                f"stopped_stall parent {parent_id}: writer budget.minutes "
                "must be a positive int"
            )
            raise EvolveError(msg)
        resume[minutes] = math.ceil(minutes * _STALL_RESUME_FACTOR)
    return resume


def _render(
    parent_yaml: Path, parent_id: str, next_id: str, resume: dict[int, int] | None = None
) -> str:
    """Render next-season text: new id/parent, reset methodology head, rest verbatim.

    goal/metric/mode, the pipeline, the writer table, and stop are copied
    byte-identical from the parent (comments and the quoted "on" key
    included), except the top-level benih: key renders as writers: (the s54
    schema rename; benih stays the read alias); only the
    id/parent lines and the methodology head (approach carried, evidence
    reset, primary_change skeleton) are rewritten. With a resume map (s36
    stall resume) the header gains the stall citation line and benih budget
    lines are rewritten to their raised minutes; resume=None is the
    historical path.
    """
    out: list[str] = [
        f"# seasons/{next_id}.yaml — drafted by evolve v0 from {parent_id}; "
        "fill primary_change + evidence, then apply\n",
    ]
    if resume is not None:
        pairs = ", ".join(f"{old} -> {new}" for old, new in resume.items())
        out.append(f"# resumed from stopped_stall parent {parent_id}; budget {pairs} min\n")
    out += [
        f"id: {next_id}\n",
        f"parent: {parent_id}\n",
    ]
    approach = '  approach: ""\n'
    in_head = False
    for line in parent_yaml.read_text(encoding="utf-8").splitlines(keepends=True):
        if in_head:
            if line.startswith("  pipeline:"):
                out += [approach, "  evidence: []\n", _PRIMARY_CHANGE_SKELETON, line]
                in_head = False
            elif line.startswith("  approach:"):
                approach = line
            continue  # parent evidence/primary_change lines drop: season starts clean
        if line.startswith("#"):
            continue  # header comments describe the parent, not the draft
        if line.startswith(("id:", "parent:")):
            continue  # rewritten above
        if line.rstrip("\n") == "benih:":
            out.append("writers:\n")
            continue  # s54: drafts emit the writers key; benih stays the alias
        if resume is not None and (m := _BUDGET_LINE_RE.match(line.rstrip("\n"))):
            new = resume.get(int(m.group(2)))
            if new is None:
                msg = (
                    f"{parent_yaml}: budget line {m.group(2)!r} does not match "
                    "any parsed benih budget"
                )
                raise EvolveError(msg)
            out.append(f"{m.group(1)}budget: {{minutes: {new}}}\n")
            continue  # stall resume: the benih budget raises to its times 1.5
        if line.startswith("methodology:"):
            out.append(line)
            in_head = True
        else:
            out.append(line)
    if in_head:
        msg = f"{parent_yaml}: methodology has no '  pipeline:' line to carry over"
        raise EvolveError(msg)
    text = "".join(out)
    return text if text.endswith("\n") else text + "\n"


def draft_next(root: Path, parent_yaml: Path) -> Path:
    """Draft musim/s<N+1>.yaml from the latest season parent_yaml.

    N+1 is one past the lifecycle high-water mark (M8): the highest season
    number ever allocated across musim/s*.yaml, musim/rejected/, and
    reject-/rollback- akar lifecycle records. The parent must be the latest
    top-level season. Raises EvolveError when the parent is malformed or
    stale, or the target file already exists.

    Stall resume (s36): when the parent's persisted engine state shows
    terminal status stopped_stall, the draft raises every benih budget to
    its times 1.5 (rounded up to whole minutes) and the header gains the
    stall citation line ("resumed from stopped_stall parent <sid>; budget
    40 -> 60 min"). Any other parent -- no persisted state, or running,
    completed, stopped_operator, failed, stopped_budget -- drafts
    byte-identical to the pre-s36 behavior.
    """
    try:
        parent = yamlio.load(parent_yaml)
    except (yamlio.YamlError, OSError) as exc:
        msg = f"cannot load parent season {parent_yaml}: {exc}"
        raise EvolveError(msg) from exc

    parent_id = parent.get("id") if isinstance(parent, dict) else None
    match = _SEASON_RE.match(parent_id) if isinstance(parent_id, str) else None
    if not match:
        msg = f"parent season id must match s<N>, got {parent_id!r} in {parent_yaml}"
        raise EvolveError(msg)
    parent_n = int(match.group(1))

    seasons = paths.seasons_dir(root)  # root is the .rumpun dir (engine convention)
    if not seasons.is_dir():
        msg = f"no seasons directory under {root}: nothing to evolve from"
        raise EvolveError(msg)
    latest = _latest_season(seasons)
    if latest is None:
        msg = f"no seasons/s<N>.yaml files under {seasons}: nothing to evolve from"
        raise EvolveError(msg)
    if parent_n != latest:
        msg = f"parent {parent_id} is not the latest season (latest is s{latest})"
        raise EvolveError(msg)

    next_id = f"s{_high_water_mark(root) + 1}"
    target = seasons / f"{next_id}.yaml"
    if target.exists():
        msg = f"draft target already exists: {target}"
        raise EvolveError(msg)

    method = parent.get("methodology")
    if not isinstance(method, dict) or not method.get("pipeline"):
        msg = f"parent {parent_id} has no methodology.pipeline to carry over"
        raise EvolveError(msg)

    resume = _stall_resume(root, parent, parent_id)
    text = _render(parent_yaml, parent_id, next_id, resume)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)  # atomic: the seasons dir never holds a half-written season
    logger.info("drafted %s from %s", target, parent_yaml)
    return target


def _reject_record(root: Path, sid: str) -> Path | None:
    """The reject-<sid> akar record, or None; exact declared-id resolution.

    H8 (codex-review-2026-09-14): the scan resolves the exact declared id
    with akar.find_record -- the same declared-id scan citations resolve
    with -- so a substring id never matches (s19's H7 contract).
    """
    try:
        return akar.find_record(root, f"reject-{sid}")
    except akar.AkarError:
        return None


def apply(root: Path, drafted: Path) -> None:
    """Gate a drafted season through the lifecycle and lint checks.

    H8 (codex-review-2026-09-14): a season id carrying a reject-<sid> akar
    record is refused before lint -- a rejected season is non-executable.
    The record scan resolves the exact declared id (see _reject_record).
    The draft must parse with a valid s<N> id, then error-severity lint
    findings block the apply. root is part of the ratified verb signature;
    lint locates the project root from the season path itself.
    """
    doc = _load_draft(drafted)
    sid = doc["id"]
    rejected = _reject_record(root, sid)
    if rejected is not None:
        msg = (
            f"apply blocked, {drafted}: season {sid} was rejected "
            f"({rejected}); a rejected season is non-executable"
        )
        raise EvolveError(msg)
    try:
        findings = lint.lint(drafted)
    except (lint.LintError, yamlio.YamlError, OSError) as exc:
        msg = f"lint could not run on {drafted}: {exc}"
        raise EvolveError(msg) from exc
    errors = [f.message for f in findings if f.severity == "error"]
    if errors:
        msg = f"apply blocked, {drafted}: " + "; ".join(errors)
        raise EvolveError(msg)
    logger.info("apply passed lint: %s (%d findings, all non-error)", drafted, len(findings))


def _load_draft(drafted: Path) -> dict:
    """Load a draft, requiring a string id matching s<N>; EvolveError otherwise.

    A missing or unreadable file surfaces as EvolveError wrapping the OSError;
    yamlio's parse errors (invalid YAML, duplicate or non-string keys) wrap
    the same way. Returns the parsed document; its "id" is the validated sid.
    """
    try:
        doc = yamlio.load(drafted)
    except (yamlio.YamlError, OSError) as exc:
        msg = f"cannot load draft {drafted}: {exc}"
        raise EvolveError(msg) from exc
    drafted_id = doc.get("id") if isinstance(doc, dict) else None
    match = _SEASON_RE.match(drafted_id) if isinstance(drafted_id, str) else None
    if not match:
        msg = f"draft id must match s<N>, got {drafted_id!r} in {drafted}"
        raise EvolveError(msg)
    return doc


def _goal_line(doc: dict) -> str:
    """The draft's goal line, verbatim; a marker string when absent."""
    goal = doc.get("goal")
    return goal if isinstance(goal, str) else "(no goal line)"


def _evidence_line(doc: dict) -> str:
    """The akar citations methodology.evidence names, comma-joined; or "none"."""
    method = doc.get("methodology")
    evidence = method.get("evidence") if isinstance(method, dict) else None
    if isinstance(evidence, list):
        cited = [item for item in evidence if isinstance(item, str)]
        if cited:
            return ", ".join(cited)
    return "none"


def approve_draft(root: Path, drafted: Path) -> Path:
    """Record the operator's approval of a draft in akar; the draft never changes.

    Appends record approve-<sid>, title "season <sid> approved", with a body
    naming the autonomy stage (manual — every apply explicit, P33 MVP), the
    draft's goal line, and the citation methodology.evidence names (or
    "none"). akar.AkarError (e.g. approving twice) wraps into EvolveError so
    the CLI reports it instead of tracebacking. Returns the record path.
    """
    doc = _load_draft(drafted)
    sid = doc["id"]
    body = (
        "operator approved the draft at autonomy stage manual.\n"
        f"goal: {_goal_line(doc)}\n"
        f"evidence: {_evidence_line(doc)}"
    )
    try:
        record = akar.append_record(root, f"approve-{sid}", f"season {sid} approved", body)
    except akar.AkarError as exc:
        msg = f"cannot append approve record for {sid}: {exc}"
        raise EvolveError(msg) from exc
    logger.info("approved %s -> %s", drafted, record)
    return record


def reject_draft(root: Path, drafted: Path) -> Path:
    """Reject a draft: move it to musim/rejected/ and record the P33 policy.

    The draft moves first (Path.replace, atomic; target collision is an
    EvolveError, the rejected/ dir is created), then akar record reject-<sid>
    appends with a body recording the on_reject containment leg: action
    rollback_to_last_good, pause true, escalate_after consecutive_rejects 2 —
    and that at autonomy stage manual the operator is who pauses the chain.
    Returns the record path.
    """
    doc = _load_draft(drafted)
    sid = doc["id"]
    rejected_dir = paths.seasons_dir(root) / "rejected"
    target = rejected_dir / drafted.name
    if target.exists():
        msg = f"reject target already exists: {target}"
        raise EvolveError(msg)
    rejected_dir.mkdir(parents=True, exist_ok=True)
    drafted.replace(target)
    body = (
        "P33 on_reject policy: action rollback_to_last_good; pause true; "
        "escalate_after consecutive_rejects 2.\n"
        "autonomy stage manual: the operator pauses the chain."
    )
    try:
        record = akar.append_record(root, f"reject-{sid}", f"season {sid} rejected", body)
    except akar.AkarError as exc:
        msg = f"cannot append reject record for {sid}: {exc}"
        raise EvolveError(msg) from exc
    logger.info("rejected %s -> %s (draft moved to %s)", drafted, record, target)
    return record


def rollback_season(root: Path, sid: str) -> Path:
    """Roll back an applied season: stop it if active, contain, record P33.

    H8 (codex-review-2026-09-14): rollback previously recorded containment
    while the season could keep running. When rimba/<sid>/_season/state.json
    shows status running, engine.stop_season runs first, in this caller's
    thread (ordered, never concurrent), finalizing stopped_operator and
    killing the agents before anything is moved or recorded.

    Reject contains a draft (pre-apply); rollback contains a season that
    passed apply and may have run. After the stop, the season file moves to
    musim/rejected/ (Path.replace, atomic; target collision is an
    EvolveError, the rejected/ dir is created), then akar record
    rollback-<sid> appends with a body recording the on_reject containment
    leg: action rollback_to_last_good, pause true, escalate_after
    consecutive_rejects 2 — and that code-level restore is an explicit git
    revert by the operator: git history is the evolution ledger, and this
    verb never runs git. akar.AkarError (e.g. rolling back twice) wraps
    into EvolveError so the CLI reports it instead of tracebacking.
    Returns the record path.
    """
    if not _SEASON_RE.match(sid):
        msg = f"season id must match s<N>, got {sid!r}"
        raise EvolveError(msg)
    season = paths.seasons_dir(root) / f"{sid}.yaml"
    if not season.is_file():
        msg = (
            f"no applied season at {season}: rollback contains a season that "
            "passed apply; for a draft that was never applied, use "
            "'rumpun evolve reject'"
        )
        raise EvolveError(msg)
    state = engine._load_state(root, sid)
    if state is not None and state.get("status") == "running":
        try:
            engine.stop_season(root, sid)
        except engine.EngineError as exc:
            msg = f"cannot roll back {sid}: stop failed: {exc}"
            raise EvolveError(msg) from exc
    rejected_dir = paths.seasons_dir(root) / "rejected"
    target = rejected_dir / season.name
    if target.exists():
        msg = f"rollback target already exists: {target}"
        raise EvolveError(msg)
    rejected_dir.mkdir(parents=True, exist_ok=True)
    season.replace(target)
    body = (
        "P33 on_reject policy: action rollback_to_last_good; pause true; "
        "escalate_after consecutive_rejects 2.\n"
        "code-level restore is an explicit git revert by the operator: "
        "git history is the evolution ledger; this verb never runs git."
    )
    try:
        record = akar.append_record(
            root, f"rollback-{sid}", f"season {sid} rolled back", body
        )
    except akar.AkarError as exc:
        msg = f"cannot append rollback record for {sid}: {exc}"
        raise EvolveError(msg) from exc
    logger.info("rolled back %s -> %s (season moved to %s)", season, record, target)
    return record
