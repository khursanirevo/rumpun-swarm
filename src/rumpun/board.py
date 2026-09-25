"""Board pickup: the GitHub Projects v2 board as rumpun's cross-machine kanban.

Directive seq 14: an instance files feature/bug issues into the campaign's
GitHub Project board when it identifies work, and any instance picks an
issue back up as season scope. The live gh calls stay inside pickup();
the parser and the argv builders are pure and offline-pin-able (s69 w2
pins, tests/test_s69_w2_pins.py).

The lifecycle (s74 w2): a sealed harvest reaches back to its issue --
sync_season comments the sealed record verbatim (seal checked first) and
closes the issue; the builders and the season-to-issue mapping are pure,
the live gh calls stay inside the bounded seam (_bounded_run), and
board --sync --dry-run renders the plan writing nothing
(tests/test_s74_w2_pins.py).

The feed (s76 w2): audit records arm candidates (`candidate: ` lines);
candidates_from_audit reads them verbatim and audit_issue_argv files
one as an issue; the pins hold the feed offline
(tests/test_s76_w2_pins.py).

The map emission (s78 w1): `rumpun board --map <sid> <issue-url>`
records which issue a season's lanes answer -- one rc-gated gh check
that the issue exists, then emit_lane_map merges {lane title: issue
url} for the season's lanes into .rumpun/board-map.json, and sync's
issue_for_season reads the map before the lane-title fallback.

The stall mirror (s125 w1): the heartbeat's lane-stalled events ride
the verdict cards -- stall_marks reads the bus (the report's s124
reader, imported not re-derived), and a season whose lanes carry a
stall gains a `stalled: <lane> since <iso>` line on its card after a
sync; a second sync changes nothing, and no stall leaves no mark.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rumpun import akar, epics, paths, report, yamlio

logger = logging.getLogger(__name__)

OWNER = "khursanirevo"
REPO = "khursanirevo/rumpun"
PROJECT_NUMBER = 1  # required: gh cannot prompt for it non-interactively
ITEM_LIST_ARGV = [
    "gh",
    "project",
    "item-list",
    str(PROJECT_NUMBER),
    "--owner",
    OWNER,
    "--format",
    "json",
]

# s74 w2: the lifecycle surface -- the lane-map file name and the per-gh-call
# bound for the sync seam (the pickup() bound is 60s; sync matches it).
BOARD_MAP_FILE = "board-map.json"
SYNC_TIMEOUT_S = 60


def parse_item_list(raw: str) -> list[dict[str, str]]:
    """Parse `gh project item-list --format json` stdout into plain rows.

    One row per non-draft item: state, title, url, read off the item's
    content object (the issue behind the project item). Draft items
    carry content: null, have no issue behind them, and drop out.
    """
    payload = json.loads(raw)
    items = payload.get("items") or []
    rows: list[dict[str, str]] = []
    for item in items:
        content = item.get("content")
        if not content:
            logger.debug(
                "item-list: item %s has no content (draft); dropped",
                item.get("id"),
            )
            continue
        rows.append(
            {
                "state": str(content.get("state", "")),
                "title": str(content.get("title", "")),
                "url": str(content.get("url", "")),
            }
        )
    return rows


def issue_create_argv(title: str, body: str) -> list[str]:
    """The exact `gh issue create` argv for filing one issue to the repo."""
    return [
        "gh", "issue", "create", "-R", REPO,
        "--title", title, "--body", body,
    ]


def item_add_argv(number: int, url: str) -> list[str]:
    """The exact `gh project item-add` argv once the issue exists."""
    return [
        "gh", "project", "item-add", str(number),
        "--owner", OWNER, "--url", url,
    ]


def candidates_from_audit(record_path: Path) -> list[str]:
    """The verbatim candidate texts of an audit record, in record order.

    The s66 convention: a candidate is a line starting exactly
    "candidate: "; its text is the stripped rest of the line -- the same
    strings the kanban backlog arms. Pure read: no seal gate, no dedupe;
    a missing file raises OSError (an honest read, not a silent []).
    """
    lines = record_path.read_text(encoding="utf-8").splitlines()
    return [
        line.removeprefix("candidate: ").strip()
        for line in lines
        if line.startswith("candidate: ")
    ]


AUDIT_ISSUE_TITLE_MAX = 60


def audit_issue_argv(candidate: str, citation: str) -> list[str]:
    """The exact `gh issue create` argv filing one audit candidate.

    Title: the candidate whitespace-collapsed, then truncated to the
    first 57 chars + "..." when over AUDIT_ISSUE_TITLE_MAX (60) --
    deterministic, same input same argv, <=60 always. Body: the
    candidate verbatim + the source citation, so the issue carries the
    full text the title compresses and names the record it came from.
    """
    collapsed = " ".join(candidate.split())
    title = (
        collapsed[: AUDIT_ISSUE_TITLE_MAX - 3] + "..."
        if len(collapsed) > AUDIT_ISSUE_TITLE_MAX
        else collapsed
    )
    return issue_create_argv(title, f"{candidate}\n\ncitation: {citation}")


ISSUE_TRAIL_LIMIT = 200


def issue_trail_argv() -> list[str]:
    """The exact `gh issue list` argv for the resolution-trail read.

    One call reads every issue's number, state, and body: an issue cites
    a candidate by quoting its line verbatim (the audit_issue_argv body
    shape), so the body is the field the trail matches on.
    """
    return [
        "gh", "issue", "list", "-R", REPO,
        "--state", "all", "--json", "number,state,body",
        "--limit", str(ISSUE_TRAIL_LIMIT),
    ]


def parse_issue_trail(raw: str) -> list[dict[str, Any]]:
    """Parse `gh issue list --json number,state,body` stdout into rows.

    One row per issue: number, state, body.  A non-dict row drops with
    a debug log (the parse_item_list discipline); corrupt JSON raises
    ValueError for the caller's degrade guard.
    """
    rows: list[dict[str, Any]] = []
    for row in json.loads(raw):
        if not isinstance(row, dict):
            logger.debug("issue-trail row is not a dict; dropped")
            continue
        rows.append(
            {
                "number": row.get("number"),
                "state": str(row.get("state", "")),
                "body": str(row.get("body", "")),
            }
        )
    return rows


def issue_trail(timeout: int = SYNC_TIMEOUT_S) -> list[dict[str, Any]]:
    """Live issue trail (network): one bounded gh call; BoardError on miss.

    The resolution-trail seam (issue #6).  The audit verb guards this
    call and degrades to the ledger-only trail on any failure, so an
    unreachable board never blocks the reflection.
    """
    proc = subprocess.run(
        issue_trail_argv(),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise BoardError(
            f"gh issue list exited {proc.returncode}: {proc.stderr.strip()}"
        )
    return parse_issue_trail(proc.stdout)


def pickup(timeout: int = 60) -> list[dict[str, str]]:
    """Live board pickup (network): run gh, parse stdout; raise on gh error.

    The one network seam. The kanban integration calls this inside its
    own degradation guard; the s69 w2 pins hold the parser and the argv
    builders offline.
    """
    proc = subprocess.run(
        ITEM_LIST_ARGV,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"gh project item-list exited {proc.returncode}: {proc.stderr.strip()}"
        )
    return parse_item_list(proc.stdout)


class BoardError(Exception):
    """A board lifecycle refusal or live-seam failure, naming the season."""


def render_sync(sid: str, url: str, record_path: Path, dry_run: bool) -> str:
    """What board --sync does: the comment target and the close target.

    The dry-run header promises nothing written; the live header is the
    receipt. The two action lines are byte-identical in both modes, so a
    dry-run render is exactly the live plan.
    """
    header = (
        f"board sync {sid} (dry-run): nothing written"
        if dry_run
        else f"board sync {sid}: commented and closed"
    )
    return "\n".join(
        [
            header,
            f"comment {url} with {record_path} (verbatim, sealed)",
            f"close {url}",
        ]
    )


def harvest_comment_argv(issue_url: str, record_path: Path) -> list[str]:
    """The exact `gh issue comment` argv: the record file as the verbatim body.

    --body-file points at the sealed harvest record itself, so the issue
    receives the record bytes verbatim (header, body, sha256 seal); no
    temp copy, no re-encoding. The URL carries the repo, so no -R flag.
    """
    return [
        "gh",
        "issue",
        "comment",
        issue_url,
        "--body-file",
        str(record_path),
    ]


def close_issue_argv(issue_url: str) -> list[str]:
    """The exact `gh issue close` argv once the record is commented."""
    return ["gh", "issue", "close", issue_url]


def issue_exists_argv(url: str) -> list[str]:
    """The exact `gh issue view` argv for the --map existence check.

    One rc-gated call: rc 0 proves the issue exists on the repo; the
    URL carries the repo, so no -R flag (the s74 argv discipline).
    """
    return ["gh", "issue", "view", url]


def lanes_for_season(root: Path, sid: str) -> list[str]:
    """The season's lane titles in writers order: nonempty, deduped.

    Issues carry the season's lane title (the seq 14 filing discipline),
    so the lane titles are the keys both mapping layers match on. A
    missing or malformed season yaml means no lanes ([]), the unmapped
    case; a read path never crashes on a malformed yaml.
    """
    try:
        cfg = yamlio.load(paths.seasons_dir(root) / f"{sid}.yaml")
    except (OSError, yamlio.YamlError):
        return []
    if not isinstance(cfg, dict):
        return []
    writers = cfg.get("writers")
    if not isinstance(writers, list):
        return []
    lanes: list[str] = []
    for writer in writers:
        lane = writer.get("lane") if isinstance(writer, dict) else None
        if isinstance(lane, str) and lane and lane not in lanes:
            lanes.append(lane)
    return lanes


def load_lane_map(root: Path) -> dict[str, str]:
    """The campaign's lane map: .rumpun/board-map.json, {lane title: issue url}.

    A missing file is an empty map: the fallback title match still
    applies. A present-but-corrupt file is a BoardError -- a broken map
    must never silently drop a harvest onto the fallback.
    """
    path = root / BOARD_MAP_FILE
    if not path.is_file():
        logger.debug("no lane map at %s; the fallback title match applies", path)
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        msg = f"{path} is not valid JSON: {exc}"
        raise BoardError(msg) from exc
    shape_ok = isinstance(data, dict) and all(
        isinstance(key, str) and isinstance(value, str) and value
        for key, value in data.items()
    )
    if not shape_ok:
        msg = f"{path} must be a JSON object mapping lane titles to issue urls"
        raise BoardError(msg)
    return data


def emit_lane_map(root: Path, sid: str, issue_url: str) -> dict[str, str]:
    """Merge {lane title: issue url} for a season's lanes into the lane map.

    The write side of load_lane_map (s78 w1): each of the season's
    lanes, in writers order, maps to the one issue url; entries for
    other lanes survive (merge, not clobber). The file lands whole
    (temp + os.replace), so a concurrent reader never sees a torn map.
    Refuses with BoardError on an empty url and on a lane-less season
    -- a map entry must name a real issue and a real lane.
    """
    if not issue_url:
        msg = "cannot map an empty issue url"
        raise BoardError(msg)
    lanes = lanes_for_season(root, sid)
    if not lanes:
        msg = f"season {sid} has no lanes to map"
        raise BoardError(msg)
    merged = dict(load_lane_map(root))
    for lane in lanes:
        merged[lane] = issue_url
    path = root / BOARD_MAP_FILE
    tmp = path.with_name(".board-map.json.tmp")
    tmp.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return merged


def issue_for_season(
    root: Path,
    sid: str,
    pickup_fn: Callable[[], list[dict[str, str]]] | None = None,
) -> str | None:
    """The board issue url a season's harvest should close; None when unmapped.

    Precedence: the committed lane map (.rumpun/board-map.json), each of
    the season's lanes in writers order; then the fallback: the first
    pickup() row (board order) whose issue title is one of the season's
    lane titles -- issues carry the season's lane title. pickup_fn
    replaces the live seam offline.
    """
    lanes = lanes_for_season(root, sid)
    if not lanes:
        return None
    lane_map = load_lane_map(root)
    for lane in lanes:
        if lane_map.get(lane):
            return lane_map[lane]
    fetch = pickup_fn if pickup_fn is not None else pickup
    for row in fetch():
        if row.get("title") in lanes and row.get("url"):
            return row["url"]
    return None


def _sealed_body(record_path: Path) -> str:
    """The akar record body, seal-checked: BoardError on tamper or no seal.

    The akar seal covers the body recoverable as lines[4:-1]; the sync
    closes the loop only on a sealed record, so a tampered or unsealed
    record refuses instead of reaching the issue.
    """
    lines = record_path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 6 or not lines[-1].startswith("sha256: "):
        msg = f"{record_path} is not a sealed akar record (missing sha256 footer)"
        raise BoardError(msg)
    body = "\n".join(lines[4:-1])
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if lines[-1] != f"sha256: {digest}":
        msg = f"{record_path} fails its sha256 seal; refusing to comment it"
        raise BoardError(msg)
    return body


def _bounded_run(argv: list[str], timeout: int = SYNC_TIMEOUT_S) -> None:
    """The bounded live seam: run gh, raise BoardError on nonzero or timeout."""
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"gh timed out after {timeout}s: {' '.join(argv)}"
        raise BoardError(msg) from exc
    if proc.returncode != 0:
        msg = f"gh exited {proc.returncode}: {proc.stderr.strip()}"
        raise BoardError(msg)


def sync_season(
    root: Path,
    sid: str,
    dry_run: bool,
    pickup_fn: Callable[[], list[dict[str, str]]] | None = None,
    run: Callable[[list[str]], object] | None = None,
) -> str:
    """Close the seq-14 loop: a sealed harvest comments and closes its issue.

    Refuses when the season has no harvest record (akar.AkarError -- the
    loop closes only for a harvested season), when the record's sha256
    seal is broken (BoardError), or when no board issue maps to the
    season (BoardError; a live pickup failure converts to BoardError
    too). --dry-run renders exactly what would run and writes nothing,
    calls nothing. Live: the comment lands BEFORE the close, each gh
    call bounded (SYNC_TIMEOUT_S); a comment failure leaves the issue
    open (honest), never closed without its record. Returns the render
    string either way; run replaces the live seam offline (the s71
    panel pattern).
    """
    record_path = akar.find_record(root, f"{sid}-harvest")
    _sealed_body(record_path)
    try:
        url = issue_for_season(root, sid, pickup_fn=pickup_fn)
    except RuntimeError as exc:
        msg = f"board pickup failed while mapping {sid}: {exc}"
        raise BoardError(msg) from exc
    if url is None:
        msg = (
            f"season {sid} is unmapped: no {BOARD_MAP_FILE} lane entry and no "
            "board issue carries a lane title of the season"
        )
        raise BoardError(msg)
    comment_argv = harvest_comment_argv(url, record_path)
    close_argv = close_issue_argv(url)
    if dry_run:
        return render_sync(sid, url, record_path, dry_run=True)
    execute = run if run is not None else _bounded_run
    execute(comment_argv)
    execute(close_argv)
    return render_sync(sid, url, record_path, dry_run=False)


# s119 w2: the verdict mirror -- a board card claims its season with a
# `season: <sid>` body line; the mirror seam keeps the s74 60s bound.
MIRROR_MARKER = "season: "


def _mirror_sid_key(sid: str) -> tuple[int, str]:
    """Deterministic truth order: non-numeric stems first, then numeric."""
    m = re.fullmatch(r"s(\d+)", sid)
    return (int(m.group(1)) if m else -1, sid)


def ledger_truth(root: Path) -> dict[str, tuple[str, str]]:
    """The local ledger's verdict truth: {sid: (verdict, basis)}.

    The epics rollup's two sources exactly: the verdict is the last
    runs/<sid>/verdicts.jsonl row naming the season (epics.season_verdict),
    the basis the harvest record's seal mark (epics._record_basis: the
    '<sid>-harvest@<sha8>' seal prefix, or the honest absence mark when no
    harvest record sealed). Only seasons with a verdict row naming them
    are truth -- nothing invented.
    """
    truth: dict[str, tuple[str, str]] = {}
    runs = paths.runs_dir(root)
    records = akar.declared_ids(root)
    if runs.is_dir():
        for path in sorted(runs.glob("s*/verdicts.jsonl")):
            sid = path.parent.name
            verdict = epics.season_verdict(root, sid)
            if verdict is None:
                continue
            truth[sid] = (verdict, epics._record_basis(sid, records))
    return {sid: truth[sid] for sid in sorted(truth, key=_mirror_sid_key)}


def stall_marks(root: Path) -> dict[str, dict[str, str]]:
    """s125 w1: the live stall truth for the cards: {sid: {lane: iso}}.

    The report's _stall_marks read (s124 w1), imported not re-derived:
    identical bus bytes, identical mapping -- one lane per file, sorted
    glob, unparseable files skipped, the last-progress anchor rendered
    ISO-UTC at seconds (the report's absence mark when the event carries
    none). A missing events dir is the quiet bus ({}). The heartbeat
    owns the bus's truth; the sync reads it.
    """
    return report._stall_marks(root)


def mirror_card_body(
    sid: str, verdict: str, basis: str, stalls: dict[str, str] | None = None
) -> str:
    """The verdict card's body bytes: the marker line, the verdict, the basis.

    Deterministic: the same truth re-renders the same bytes, so the body
    compare IS the drift test and a second mirror run plans nothing.
    s125 w1: exactly when the season's stall map is nonempty, a fourth
    line names each stalled lane and its last-progress stamp (lanes
    sorted); with none, the bytes stay the s119 three-line body.
    """
    lines = [f"season: {sid}", f"verdict: {verdict}", f"basis: {basis}"]
    if stalls:
        marked = ", ".join(
            f"{lane} since {stalls[lane]}" for lane in sorted(stalls)
        )
        lines.append(f"stalled: {marked}")
    return "\n".join(lines)


def _card_sid(body: str) -> str | None:
    """The season a card claims via its first `season: <sid>` line.

    None when no marker line stands, or when the marker names no season.
    """
    for line in body.splitlines():
        if line.startswith(MIRROR_MARKER):
            return line.removeprefix(MIRROR_MARKER).strip() or None
    return None


def mirror_plan(
    truth: dict[str, tuple[str, str]],
    cards: list[dict[str, Any]],
    stalls: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """The pure mirror: what must change so the board matches the truth.

    One row per action, in truth order: {"action": "create", "sid",
    "number": None, "body"} for a season with no card; {"action":
    "update", "sid", "number", "body"} for a card whose body drifted
    (the live issue number identifies it -- trail rows carry numbers,
    not urls). A card whose body already equals the expected body plans
    nothing (idempotence); bodies compare stripped, so the mirror
    matches content and GitHub's trailing-newline normalization never
    reads as drift. s125 w1: the stalls map rides in; a season whose
    stall map is nonempty gets the stall line, others keep their bytes.
    """
    claimed: dict[str, dict[str, Any]] = {}
    for row in cards:
        sid = _card_sid(str(row.get("body", "")))
        if sid and sid not in claimed:
            claimed[sid] = row
    plan: list[dict[str, Any]] = []
    for sid, (verdict, basis) in truth.items():
        expected = mirror_card_body(sid, verdict, basis, (stalls or {}).get(sid))
        card = claimed.get(sid)
        if card is None:
            plan.append(
                {"action": "create", "sid": sid, "number": None, "body": expected}
            )
        elif str(card.get("body", "")).strip() != expected.strip():
            plan.append(
                {
                    "action": "update",
                    "sid": sid,
                    "number": card.get("number"),
                    "body": expected,
                }
            )
    return plan


def render_mirror(plan: list[dict[str, Any]], dry_run: bool) -> str:
    """What board --mirror does: the plan as action lines under a header.

    The dry-run header promises nothing written; the live header is the
    receipt. The action lines are byte-identical in both modes, so a
    dry-run render is exactly the live plan. An empty plan renders the
    no-drift line (the honest nothing).
    """
    header = (
        "board mirror (dry-run): nothing written"
        if dry_run
        else "board mirror: applied"
    )
    lines = [header]
    for row in plan:
        if row["action"] == "create":
            lines.append(f"create {row['sid']}")
        elif row["number"] is not None:
            lines.append(f"update {row['sid']} (#{row['number']})")
        else:
            lines.append(f"update {row['sid']}")
    if not plan:
        lines.append("no drift: the board matches the ledger")
    return "\n".join(lines)


def issue_edit_body_argv(number: int, body: str) -> list[str]:
    """The exact `gh issue edit` argv: the expected body over the drifted one.

    The trail row's issue number identifies the card; -R names the repo
    (trail rows carry numbers, not urls).
    """
    return ["gh", "issue", "edit", str(number), "-R", REPO, "--body", body]


def _bounded_run_out(argv: list[str], timeout: int = SYNC_TIMEOUT_S) -> str:
    """The bounded live seam returning stdout: run gh; BoardError on a miss.

    The mirror's create step needs the new issue's url, which `gh issue
    create` prints to stdout; the s74 _bounded_run discards stdout, so
    the mirror runs through this variant. A clean call with no stdout
    returns "".
    """
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"gh timed out after {timeout}s: {' '.join(argv)}"
        raise BoardError(msg) from exc
    if proc.returncode != 0:
        msg = f"gh exited {proc.returncode}: {proc.stderr.strip()}"
        raise BoardError(msg)
    return proc.stdout


def mirror_sync(
    root: Path,
    dry_run: bool,
    trail_fn: Callable[[], list[dict[str, Any]]] | None = None,
    run: Callable[[list[str]], str] | None = None,
) -> str:
    """Mirror the local ledger's verdicts onto the board cards, on demand.

    One board read (issue_trail: every issue's number, state, body),
    then the plan against ledger_truth, then the plan applied in order.
    Nothing invented: only seasons with a local verdict row plan. Nothing
    censored: the sync creates and updates bodies; it never closes or
    deletes, and foreign cards are never touched (the s66 lesson).
    Idempotent: bodies strip-compare, so a second run plans nothing and
    runs nothing mutating. s125 w1: the sync reads the events bus
    (stall_marks) into the plan -- a season whose lanes carry stall
    events gains the stall line on its card; a swept event is honest
    drift, the mark drops with it. --dry-run renders the plan and mutates nothing
    (the trail read still runs: the plan needs the board side). Live: one
    seam (run or _bounded_run_out) carries every gh call; a create chains
    project item-add with the url read off the create stdout, so the new
    card lands on the project board; a failing action propagates -- the
    earlier actions stay applied (honest partial apply, no invented
    rollback). Returns the render either way. Refuses before any gh call:
    a corrupt verdict file, an unreadable ledger.
    """
    truth = ledger_truth(root)
    fetch = trail_fn if trail_fn is not None else issue_trail
    plan = mirror_plan(truth, fetch(), stall_marks(root))
    if dry_run:
        return render_mirror(plan, dry_run=True)
    execute = run if run is not None else _bounded_run_out
    for row in plan:
        if row["action"] == "create":
            out = execute(issue_create_argv(row["sid"], row["body"]))
            url = ""
            for line in out.splitlines():
                candidate = line.strip()
                if candidate.startswith("https://"):
                    url = candidate
            if url:
                execute(item_add_argv(PROJECT_NUMBER, url))
        else:
            if row["number"] is None:
                msg = f"trail row for {row['sid']} carries no issue number"
                raise BoardError(msg)
            execute(issue_edit_body_argv(int(row["number"]), row["body"]))
    return render_mirror(plan, dry_run=False)
