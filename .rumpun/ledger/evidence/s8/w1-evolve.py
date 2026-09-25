"""rumpun evolve — deterministic next-season drafting v0 (build order step 5).

draft_next copies the latest season into musim/s<N+1>.yaml with a fresh
primary_change skeleton; an evolver agent fills it with akar citations;
apply runs the P27 lint gate before the draft may become a season.
approve_draft / reject_draft record the operator's P33 decision on a draft
in akar; reject also moves the draft into musim/rejected/.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from rumpun import akar, lint, yamlio

logger = logging.getLogger(__name__)

_SEASON_RE = re.compile(r"^s(\d+)$")
_SEASON_FILE_RE = re.compile(r"^s(\d+)\.yaml$")

_PRIMARY_CHANGE_SKELETON = """\
  primary_change:
    type: add            # add | remove | rewire | retune (P12/P34 grammar)
    node: execute
    baseline: ""         # evolver fills: parent best + how measured (P13)
    expected_band: ""    # evolver fills: WIN if >= X, LOSS if <= Y
    rollback: ""         # evolver fills: git revert to parent season tag
    eval_window: ""      # evolver fills: which runs decide the verdict
"""


class EvolveError(Exception):
    pass


def _latest_season(musim: Path) -> int | None:
    numbers = [
        int(match.group(1))
        for entry in musim.iterdir()
        if entry.is_file() and (match := _SEASON_FILE_RE.match(entry.name))
    ]
    return max(numbers, default=None)


def _render(parent_yaml: Path, parent_id: str, next_id: str) -> str:
    """Render next-season text: new id/parent, reset methodology head, rest verbatim.

    goal/metric/mode, the pipeline, benih, and stop are copied byte-identical
    from the parent (comments and the quoted "on" key included); only the
    id/parent lines and the methodology head (approach carried, evidence
    reset, primary_change skeleton) are rewritten.
    """
    out: list[str] = [
        f"# musim/{next_id}.yaml — drafted by evolve v0 from {parent_id}; "
        "fill primary_change + evidence, then apply\n",
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

    N+1 is the max existing musim/s*.yaml number plus one; the parent must be
    that latest season. Raises EvolveError when the parent is malformed or
    stale, or the target file already exists.
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

    musim = root / "musim"  # root is the .rumpun dir (engine convention)
    if not musim.is_dir():
        msg = f"no musim directory under {root}: nothing to evolve from"
        raise EvolveError(msg)
    latest = _latest_season(musim)
    if latest is None:
        msg = f"no musim/s<N>.yaml seasons under {musim}: nothing to evolve from"
        raise EvolveError(msg)
    if parent_n != latest:
        msg = f"parent {parent_id} is not the latest season (latest is s{latest})"
        raise EvolveError(msg)

    next_id = f"s{latest + 1}"
    target = musim / f"{next_id}.yaml"
    if target.exists():
        msg = f"draft target already exists: {target}"
        raise EvolveError(msg)

    method = parent.get("methodology")
    if not isinstance(method, dict) or not method.get("pipeline"):
        msg = f"parent {parent_id} has no methodology.pipeline to carry over"
        raise EvolveError(msg)

    text = _render(parent_yaml, parent_id, next_id)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(target)  # atomic: musim/ never holds a half-written season
    logger.info("drafted %s from %s", target, parent_yaml)
    return target


def apply(root: Path, drafted: Path) -> None:
    """Gate a drafted season through lint; error-severity findings block the apply.

    Empty primary_change fields are lint errors, so an unfilled skeleton
    cannot be applied. root is part of the ratified verb signature; lint
    locates the project root from the season path itself.
    """
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
    rejected_dir = root / "musim" / "rejected"
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
