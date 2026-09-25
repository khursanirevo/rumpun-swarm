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

from rumpun import akar, collab, engine, lint, paths, yamlio

logger = logging.getLogger(__name__)

_SEASON_RE = re.compile(r"^s(\d+)$")
_SEASON_FILE_RE = re.compile(r"^s(\d+)\.yaml$")
_LIFECYCLE_ID_RE = re.compile(r"^(?:reject|rollback)-s(\d+)$")

_PRIMARY_CHANGE_SKELETON = """\
  primary_change:
    type: add            # add | fix | remove | rewire | retune (P12/P34 grammar)
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

# The standing usefulness assessment (s88): every close seals one
# usefulness-<sid> record. The s107 -> s114 gap crossed seven closes before
# the eighth sealed and only the close worker noticed — the duty rode on
# operator memory. When the lineage behind the parent season carries no seal
# for this many consecutive closes — six, exactly the s108..s113 drought that
# preceded the s114 seal — the plan announces the assessment due and names
# the last sealed id.
_ASSESSMENT_CADENCE_CLOSES = 6
_USEFULNESS_SEAL_RE = re.compile(r"^usefulness-s(\d+)$")
# s122 (issue #38): the decade reviews (the audit F7 series) seal
# usefulness-decade-<N> records and are standing usefulness judgments like
# the per-close seals. The s-series-only scan never stopped the drought walk
# on a decade review and the announcement could never name one. A decade
# record posted on/after the stopper seal's ledger date (record filenames
# carry <date>_<id>) is the fresher judgment and silences the hint; the
# announcement names the drought's stopping record, whichever series it
# belongs to.
_USEFULNESS_DECADE_RE = re.compile(r"^usefulness-decade-(\d+)$")
_RECORD_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_")
# s132 w1: the campaign names its own candidate exhaustion. The audit-*
# records carry the actionable candidate lines; when the newest audit's
# candidates all repeat candidates an earlier audit already named, the
# pipeline has stopped finding anything new -- the stopping-rule moment
# the directive frame defines. The plan surfaces it the s116 way:
# plan-time, named, never blocking; the operator decides.
_AUDIT_ID_RE = re.compile(r"^audit-(\d+)$")
_CANDIDATE_PREFIX = "candidate: "


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
        if line.rstrip("\n") == "      agents: benih":
            out.append("      agents: writers\n")
            continue  # s54: the pipeline label follows the roster rename
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


def _ledger_date(path: Path) -> str | None:
    """The YYYY-MM-DD ledger date prefix of a record file name, or None.

    append_record names every file <date>_<record_id>.md. ISO dates sort
    lexically, so the string compares as a correct order.
    """
    if match := _RECORD_DATE_RE.match(path.name):
        return match.group(1)
    return None


def _decade_frontier(root: Path, ids: dict[str, Path]) -> int | None:
    """The covered frontier of the decade reviews, or None with no records.

    (issue #51, s134 w1) Same scope arithmetic as the audit F7 gate's
    _decade_coverage: a `seasons: <int>` line within 1..season-yaml-count
    is the record's covered frontier; no parseable or in-range scope
    keeps the per-record credit (10 * N, the audit gate's
    USEFULNESS_DECADE_SIZE). None when the ledger holds no decade record.
    """
    frontier: int | None = None
    count = 0
    seasons = paths.seasons_dir(root)
    if seasons.is_dir():
        count = sum(
            1 for p in seasons.iterdir() if p.is_file() and _SEASON_RE.match(p.stem)
        )
    for record_id, path in ids.items():
        if not (m := _USEFULNESS_DECADE_RE.match(record_id)):
            continue
        credit = 10 * int(m.group(1))
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.info("cannot read usefulness record %s: %s", path, exc)
        else:
            for line in text.splitlines():
                if line.startswith("seasons:"):
                    raw = line[len("seasons:"):].lstrip()
                    if m := re.match(r"\d+", raw):
                        value = int(m.group(0))
                        if 1 <= value <= count:
                            credit = value
                    break
        frontier = credit if frontier is None else max(frontier, credit)
    return frontier


def _assessment_due(root: Path, parent_id: str) -> str | None:
    """The assessment-due plan hint, or None when the lineage is current.

    Walks the parent lineage behind the parent season (the seasons/<sid>.yaml
    parent chain) counting consecutive closes whose usefulness-<sid> akar
    record is absent. The first seal stops the walk; a missing or unreadable
    lineage file stops it too, keeping the count honest to what the tree
    shows. A drought reaching _ASSESSMENT_CADENCE_CLOSES announces the
    standing assessment due and names the record that stopped the drought
    (or "none" when the ledger holds no usefulness record at all); a current
    lineage returns None.

    s122 (issue #38): the decade reviews seal usefulness-decade-<N> records
    and are standing usefulness judgments too. When the walk stops at a seal
    whose ledger date matches or precedes the newest decade record, the
    decade review is the fresher judgment and the drought it covers stays
    silent. Without a stopper the announcement names the newest judgment of
    either series by ledger date.

    s134 (issue #51): with no stopper the decade reviews still scope the
    drought: the closes above the decade frontier (see _decade_frontier)
    are the honest count; below the cadence the hint stays silent, at or
    above it the announcement carries the uncovered count. A lineage with
    no decade record keeps the walk count.
    """
    ids = akar.declared_ids(root)
    seasons = paths.seasons_dir(root)
    drought = 0
    drought_numbers: list[int] = []
    sid: str | None = parent_id
    stopper: str | None = None
    seen: set[str] = set()
    while sid is not None and sid not in seen:
        seen.add(sid)
        if f"usefulness-{sid}" in ids:
            stopper = sid
            break  # the first seal inside the lineage stops the drought count
        drought += 1
        if m := _SEASON_RE.match(sid):
            drought_numbers.append(int(m.group(1)))
        lineage = seasons / f"{sid}.yaml"
        try:
            doc = yamlio.load(lineage)
        except (yamlio.YamlError, OSError):
            logger.info("assessment scan stops: cannot read %s", lineage)
            break
        ancestor = doc.get("parent") if isinstance(doc, dict) else None
        valid = isinstance(ancestor, str) and bool(_SEASON_RE.match(ancestor))
        sid = ancestor if valid else None
    if drought < _ASSESSMENT_CADENCE_CLOSES:
        return None
    stopper_date = (
        _ledger_date(ids[f"usefulness-{stopper}"]) if stopper is not None else None
    )
    decade_newer = False
    if stopper is not None and stopper_date is not None:
        for rid, path in ids.items():
            if not _USEFULNESS_DECADE_RE.match(rid):
                continue
            decade_date = _ledger_date(path)
            if decade_date is not None and decade_date >= stopper_date:
                decade_newer = True
                break
    if decade_newer:
        # s122: a decade review on/after the stopper's seal is the fresher
        # standing judgment; the drought it covers stays silent.
        return None
    if stopper is not None:
        last = f"usefulness-{stopper}"
    else:
        frontier = _decade_frontier(root, ids)
        if frontier is not None:
            uncovered = sum(1 for n in drought_numbers if n > frontier)
            if uncovered < _ASSESSMENT_CADENCE_CLOSES:
                return None
            drought = uncovered
        judged = [
            (_ledger_date(path) or "", rid)
            for rid, path in ids.items()
            if _USEFULNESS_SEAL_RE.match(rid) or _USEFULNESS_DECADE_RE.match(rid)
        ]
        best = max(judged, default=None)
        last = best[1] if best is not None else "none"
    return (
        f"assessment due: {drought} closes since the last usefulness record "
        f"(cadence {_ASSESSMENT_CADENCE_CLOSES} closes); last sealed {last}"
    )


def _candidate_lines(path: Path) -> list[str]:
    """The candidate bodies of one audit record, one per `candidate: ` line.

    Unreadable records contribute nothing (logged, never raised): the scan
    reads the ledger as it stands, the same honesty the drought walk uses.
    The trailing "candidate cap 3 reached in pipeline order" line does not
    start with the `candidate: ` prefix, so the cap line never counts as a
    candidate.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        logger.info("candidate scan skips unreadable %s", path)
        return []
    return [
        line[len(_CANDIDATE_PREFIX) :].strip()
        for line in text.splitlines()
        if line.startswith(_CANDIDATE_PREFIX)
    ]


def _candidate_exhaustion(root: Path) -> str | None:
    """The candidate-exhaustion plan hint, or None while the pool is fresh.

    The repetition test over the audit-* akar records: the newest audit
    (highest (ledger date, id number)) announces only when every candidate
    line it names matches a candidate any earlier audit named. One fresh
    candidate keeps the announcement silent. A newest audit naming zero
    candidates stays silent too: nothing repeated, and a 0-of-0
    announcement would fake a signal the audits did not give. One audit
    record alone has no earlier pool and stays silent.

    Plan-time, named, never blocking (the s116 house style): the caller
    logs the returned hint at warning level; the draft lands either way.
    """
    audits: list[tuple[str, int, Path]] = []
    for rid, path in akar.declared_ids(root).items():
        if match := _AUDIT_ID_RE.match(rid):
            audits.append((_ledger_date(path) or "", int(match.group(1)), path))
    if len(audits) < 2:
        return None
    audits.sort(key=lambda item: (item[0], item[1]))
    *earlier, latest = audits
    pool = {body for _, _, path in earlier for body in _candidate_lines(path)}
    candidates = _candidate_lines(latest[2])
    if not candidates:
        return None
    repeated = [body for body in candidates if body in pool]
    if len(repeated) < len(candidates):
        return None
    return (
        f"the candidate pool is repeating: the operator decides "
        f"(audit-{latest[1]}, {len(repeated)} of {len(candidates)} candidates "
        f"repeat earlier audits)"
    )


def _directives_lane(root: Path) -> dict[str, str]:
    """The P8 directives lane (file+lock), resolved like the CLI resolves it."""
    ledger = paths.ledger_dir(root)
    return {
        "file": str(ledger / "directives.jsonl"),
        "lock": str(ledger / "directives.lock"),
    }


def _evidence_in_tree(root: Path, entry: str) -> bool:
    """One evidence entry: in the tree when the named artifact exists.

    A path entry resolves against the project dir (root.parent, the dir
    holding the state dir); a ledger: citation resolves the record id
    against the ledger scan, and a named @digest must match the record's
    sha256 body trailer (exact or unambiguous prefix), the citation shape
    the ledger already uses (ledger:s80-harvest@ed4d22e4...).
    """
    if entry.startswith("ledger:"):
        rid, _, named = entry[len("ledger:"):].partition("@")
        record = akar.declared_ids(root).get(rid)
        if record is None:
            return False
        if not named:
            return True
        text = record.read_text(encoding="utf-8")
        trailer = [ln for ln in text.splitlines() if ln.startswith("sha256: ")]
        if len(trailer) != 1:
            return False
        return trailer[0][len("sha256: "):].strip().startswith(named)
    return (root.parent / entry).is_file()


def directive_statuses(root: Path) -> list[dict]:
    """Directives rows with the reader-derived shipped mark (issue #48).

    The written status stays; the additive effective_status key carries
    the mark: a pending row whose evidence names only artifacts that
    exist reads shipped; every other row reads as written. Evidence
    entries: a path relative to the project dir (root.parent) or a
    ledger:<id>[@<digest>] citation. The queue file is never rewritten:
    the mark is the reader's, the append-only lane keeps its history.
    Surface: draft_next names the rows that now read shipped at plan
    time, and the loop's close-prep drafts through draft_next, so the
    same mark rides the loop.
    """
    lane_file = Path(_directives_lane(root)["file"])
    if not lane_file.is_file():
        return []
    out: list[dict] = []
    for row in collab.read_events(_directives_lane(root)):
        status = row.get("status")
        effective = status
        evidence = row.get("evidence")
        if status == "pending" and evidence:
            entries = [evidence] if isinstance(evidence, str) else list(evidence)
            if all(
                isinstance(entry, str) and _evidence_in_tree(root, entry)
                for entry in entries
            ):
                effective = "shipped"
        out.append({**row, "effective_status": effective})
    return out


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

    Loop draft preference (s123): when the loop's close-prep staging
    already holds a draft of this next id -- runs/<parent>/seasons/<next>.yaml,
    the s120 hand-off -- the plan logs a warning naming that path: the
    worker fills that draft instead of a fresh one. The warning never
    blocks the draft.

    Candidate exhaustion (s132): when the newest audit-* record's
    candidates all repeat candidates earlier audits already named (the
    repetition test), the plan logs "the candidate pool is repeating:
    the operator decides" with the repeated count; any fresh candidate
    stays silent. The warning never blocks the draft.
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
    loop_draft = paths.runs_dir(root) / parent_id / "seasons" / f"{next_id}.yaml"
    if loop_draft.is_file():
        logger.warning(
            "loop draft exists: %s already drafts %s from %s; the worker "
            "fills that draft instead of a fresh one",
            loop_draft,
            next_id,
            parent_id,
        )  # s123: the plan prefers the loop's s120 close-prep hand-off
    if (hint := _assessment_due(root, parent_id)) is not None:
        logger.warning(hint)  # s116: the standing assessment rides the plan, not memory
    if (exhausted := _candidate_exhaustion(root)) is not None:
        logger.warning(
            exhausted
        )  # s132: the repeating pool rides the plan, never blocks
    try:
        shipped = [
            row
            for row in directive_statuses(root)
            if row.get("effective_status") == "shipped"
        ]
    except (collab.LaneError, OSError) as exc:
        # named, never blocking: an unreadable directives lane must not
        # stop the draft; the log carries the full lane error
        logger.warning("directives lane unreadable, shipped mark skipped: %s", exc)
    else:
        for row in shipped:
            logger.warning(
                "directive seq %s reads shipped (evidence: %s); the queue mark "
                "is the reader's, not the file's",
                row.get("seq", "?"),
                row.get("evidence"),
            )
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
    yamlio.require_supported_schema(root)  # s68 w2: the campaign age precedes the draft

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
    yamlio.require_supported_schema(root)  # s68 w2: the campaign age precedes the draft

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
    yamlio.require_supported_schema(root)  # s68 w2: the campaign age precedes the draft

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
