"""rumpun epics — the epic declaration and the rollup verb (s58; directive seq 5).

Seasons group into epics as DATA (operator directive seq 5, 2026-09-16): one
campaign-level declaration, .rumpun/epics.yaml, maps an epic id to {title,
goal, basis, seasons: [...]}, and `rumpun epics` renders one line per epic —
id, the member seasons' span, the verdict rollup (X WIN / Y LOSS / Z other),
and the title. A member with no run state is marked on the line, never
counted or guessed. Under each row the s110 render names each member's
basis on its own indented line: a WIN or LOSS member names its harvest
record id@sha8 (the sha256 seal prefix of the <sid>-harvest ledger record;
the honest absence mark when nothing sealed), an other member names the
basis string its epic declared (the honest mark when nothing is declared).
The s111 render also names the second opinion: a member whose panel family
holds a sealed panel-<sid>[-<gen>]-verdict record names it beside its basis
— <record-id>@<sha8>, the s108 rerun convention with the highest verdict
generation winning (no verdict record, no mark).
The s112 render names the dissent: when that latest panel verdict and the
member's harvest verdict both exist and differ, the mark reads
<record-id>@<sha8> dissent:<panel-verdict> — the panel verdict is the
record status line's first token (the verdict word; a qualifying clause
like the s76 fallback allowance stays in the record, never a dissent).
A member without both sides renders exactly as before (no invented
dissents).
The s117 render adds the dissent adjustment beside the counts: a member
whose judge verdict is WIN and whose latest dissent is INCONCLUSIVE or
NEUTRAL moves from WIN to other in the adjusted counts, rendered as
`(adjusted: W WIN / L LOSS / O other)` between the counts and the title.
The raw counts stay verbatim and the member lines keep the s112 shape.
An epic with no qualifying member renders exactly as before. A LOSS
dissent contradicts but never adjusts (the real s77), and a member whose
judge verdict is not WIN never adjusts (the real s69).

The rollup reads the harvest verdict rows (runs/<sid>/verdicts.jsonl,
the last row naming the season wins) and the runs state (the engine's
persisted-status contract: a missing state.json is the EngineError case
'season list' already handles). The ledger is never written by this feature:
declaration plus read-only views, append-only preserved.

--init scaffolds epics.yaml from the season yamls: one 'campaign' epic holding
every season id in numeric order, title and goal from the campaign rumpun.yaml
(falls back to the epic id and an empty goal). It refuses to overwrite an
existing declaration.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from rumpun import akar, engine, paths, yamlio

logger = logging.getLogger(__name__)

EPICS_FILENAME = "epics.yaml"
CAMPAIGN_EPIC_ID = "campaign"

# The dissent words that adjust the rollup's WIN count (the s117 render:
# only an INCONCLUSIVE or NEUTRAL second opinion withholds the WIN; a
# LOSS dissent contradicts but never adjusts, and the dissent mark still
# renders on the member line).
ADJUSTING_DISSENTS = ("INCONCLUSIVE", "NEUTRAL")


class EpicsError(Exception):
    pass


def epics_path(root: Path) -> Path:
    """The declaration file inside the .rumpun root (root IS .rumpun)."""
    return root / EPICS_FILENAME


def _season_num(sid: str) -> tuple[int, str]:
    m = re.fullmatch(r"s(\d+)", sid)
    return (int(m.group(1)) if m else 0, sid)


def season_ids(root: Path) -> list[str]:
    """Season yaml ids, in numeric order (s<N> first by number, then stems)."""
    out: list[tuple[int, str]] = []
    for path in sorted(paths.seasons_dir(root).glob("s*.yaml")):
        sid = str(yamlio.load(path).get("id") or path.stem)
        out.append(_season_num(sid))
    return [sid for _, sid in sorted(out)]


def scaffold(root: Path) -> dict[str, Any]:
    """The --init document: one campaign epic over every season yaml id."""
    title, goal = CAMPAIGN_EPIC_ID, ""
    try:
        campaign = yamlio.load(root / "rumpun.yaml").get("campaign") or {}
        if isinstance(campaign, dict):
            title = str(campaign.get("title") or CAMPAIGN_EPIC_ID)
            goal = str(campaign.get("goal") or "")
    except yamlio.YamlError:
        logger.warning("rumpun.yaml unreadable; scaffolding with an empty goal")
    return {
        CAMPAIGN_EPIC_ID: {"title": title, "goal": goal, "seasons": season_ids(root)}
    }


def init(root: Path) -> Path:
    """Write the scaffold to .rumpun/epics.yaml (atomic; never overwrites)."""
    target = epics_path(root)
    if target.exists():
        msg = f"{target} already exists; --init never overwrites a declaration"
        raise EpicsError(msg)
    doc = scaffold(root)
    tmp = target.with_name(EPICS_FILENAME + ".tmp")
    tmp.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(target)
    members = doc[CAMPAIGN_EPIC_ID]["seasons"]
    logger.info(
        "scaffolded %s: 1 epic (%s), %d season(s)",
        target, CAMPAIGN_EPIC_ID, len(members),
    )
    return target


def has_run_state(root: Path, sid: str) -> bool:
    """Runs-state presence per the engine's persisted-status contract."""
    try:
        engine.read_persisted_status(root, sid)
    except engine.EngineError:
        return False
    return True


def _seal8(path: Path) -> str | None:
    """The record's sha256 seal prefix (8 chars), or None when absent."""
    lines = path.read_text(encoding="utf-8").rstrip("\n").splitlines()
    seal = lines[-1] if lines else ""
    if seal.startswith("sha256: "):
        return seal[len("sha256: "):].strip()[:8]
    return None


def _record_basis(sid: str, records: dict[str, Path]) -> str:
    """The verdict-backed member's basis: '<sid>-harvest@<sha8>' — the
    record's sha256 seal prefix (the same seal evidence refs cite) — or
    the honest absence mark when the harvest record never sealed. A record
    read error propagates: an unreadable record is a real error.
    """
    path = records.get(f"{sid}-harvest")
    if path is None:
        return f"no sealed {sid}-harvest record"
    sha8 = _seal8(path)
    if sha8 is None:
        return f"no sealed {sid}-harvest record"
    return f"{sid}-harvest@{sha8}"


def _latest_verdict_id(sid: str, records: dict[str, Path]) -> str | None:
    """The family scan of panel.latest_panel_record narrowed to verdict
    records: the s108 rerun generations high to low, the first generation
    holding a panel-<sid>[-<gen>]-verdict record wins. A newer generation
    holding only a pending request or an error never hides the sealed
    verdict behind it.
    """
    base = f"panel-{sid}"
    hits = [rid for rid in records if rid == base or rid.startswith(f"{base}-")]

    def _gen(rid: str) -> int:
        token = rid[len(base):].strip("-").split("-", 1)[0]
        return int(token) if token.isdigit() else 1

    for gen in sorted({_gen(rid) for rid in hits}, reverse=True):
        stem = base if gen == 1 else f"{base}-{gen}"
        if f"{stem}-verdict" in records:
            return f"{stem}-verdict"
    return None


def _panel_mark(sid: str, records: dict[str, Path]) -> str:
    """The member's latest sealed panel verdict mark: '<record-id>@<sha8>'
    (the s110 basis format, the record's sha256 seal prefix); the bare
    record id when the record lacks its seal trailer (the record exists,
    only the seal is missing); '' when the family holds no verdict record
    at all (the honest absence: no mark, no invented verdict)."""
    rid = _latest_verdict_id(sid, records)
    if rid is None:
        return ""
    sha8 = _seal8(records[rid])
    return f"{rid}@{sha8}" if sha8 else rid


def _panel_status(path: Path) -> str | None:
    """The record's verdict word: the first token of its 'status: ' line,
    or None when the record declares no status (never raises: the render
    must survive a malformed record)."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("status: "):
            return line[len("status: "):].strip().split(" ", 1)[0] or None
    return None


def _dissent_word(
    sid: str, verdict: str | None, records: dict[str, Path]
) -> str | None:
    """The dissenting panel verdict word: the member's latest panel verdict
    status when it and the harvest verdict both exist and differ (the
    status line's first token, the verdict word; a qualifying clause like
    s76's fallback allowance stays in the record, never a dissent). Either
    side missing: None (no invented dissents)."""
    if not verdict:
        return None
    rid = _latest_verdict_id(sid, records)
    if rid is None:
        return None
    status = _panel_status(records[rid])
    if not status or status == verdict:
        return None
    return status


def _dissent_mark(sid: str, verdict: str | None, records: dict[str, Path]) -> str:
    """The dissent mark: ' dissent:<panel-verdict>' when the member's
    latest panel verdict record and its harvest verdict both exist and
    differ. Either side missing: '' (no invented dissents)."""
    word = _dissent_word(sid, verdict, records)
    return f" dissent:{word}" if word else ""


def season_verdict(root: Path, sid: str) -> str | None:
    """The harvest verdict: the LAST verdicts.jsonl row naming sid; None when
    the season has no verdict row (never harvested, or the row names another
    season). A read error propagates: a corrupt verdict file is a real error.
    """
    path = paths.runs_dir(root) / sid / "verdicts.jsonl"
    if not path.is_file():
        return None
    verdict: str | None = None
    with path.open(encoding="utf-8") as fh:
        for row_line in fh:
            if not row_line.strip():
                continue
            row = json.loads(row_line)
            if str(row.get("season")) == sid:
                verdict = str(row.get("verdict") or "")
    return verdict or None


def render(root: Path) -> list[str]:
    """One line per epic, in declaration order.

    `{id}  {span}  {W} WIN / {L} LOSS / {O} other  {title}` with a trailing
    `(no state: <ids>)` when a member has no runs state. The span is the
    numeric first-last of the member ids. Counts: WIN/LOSS verdicts exactly;
    `other` absorbs NEUTRAL/INVALID verdicts AND members with run state but
    no verdict row (an honest unknown, named here rather than guessed). A
    no-run-state member is excluded from the counts and marked on the line.

    Under each row, one indented basis line per member (s110): a WIN or
    LOSS member names `<sid>-harvest@<sha8>` from the record's sha256
    seal; an other member names the basis string its epic declared, or
    `(no declared basis)`; a no-state member's line reads `<sid>  no
    state`. Beside the basis (s111), a member whose panel family holds a
    sealed panel-<sid>[-<gen>]-verdict record names it as
    `<record-id>@<sha8>` (the s108 rerun convention, the highest verdict
    generation winning); a member with no verdict record stays honest —
    no mark, no invented verdict; a record missing its seal names its
    bare id. Beside the mark (s112), a member whose latest panel verdict
    and its harvest verdict both exist and differ names both: the mark
    reads `<record-id>@<sha8> dissent:<panel-verdict>` (the panel
    verdict is the status line's first token — the verdict word; a
    qualifying clause stays in the record). A member without both sides
    renders exactly as before. The member lines name bases only — the
    counts above never change.
    Beside the counts (s117), an epic holding a member whose judge verdict
    is WIN and whose latest dissent is INCONCLUSIVE or NEUTRAL renders the
    adjusted view: `(adjusted: W WIN / L LOSS / O other)` between the
    counts and the title, the raw triple re-counted with each qualifying
    member moved from WIN to other. The raw counts stay verbatim and the
    member lines keep the s112 shape; an epic with no qualifying member
    renders byte-identical to the s58 shape.
    """
    doc = yamlio.load(epics_path(root))
    if not isinstance(doc, dict):
        msg = f"{epics_path(root)}: the epics document must be a mapping"
        raise EpicsError(msg)
    lines: list[str] = []
    records = akar.declared_ids(root)
    for epic_id, body in doc.items():
        if not isinstance(body, dict):
            msg = f"epic '{epic_id}': declaration must be a mapping"
            raise EpicsError(msg)
        members = sorted((str(m) for m in body.get("seasons") or []), key=_season_num)
        span = members[0] if len(members) == 1 else f"{members[0]}-{members[-1]}"
        wins = losses = others = 0
        adjusted = 0
        no_state: list[str] = []
        basis = str(body.get("basis") or "")
        member_rows: list[str] = []
        for sid in members:
            verdict = season_verdict(root, sid)
            if verdict is None and not has_run_state(root, sid):
                no_state.append(sid)
                member_rows.append(f"  {sid}  no state")
                continue
            panel = _panel_mark(sid, records)
            word = _dissent_word(sid, verdict, records)
            dissent = f" dissent:{word}" if word else ""
            mark = f"  {panel}{dissent}" if panel else ""
            if verdict == "WIN":
                wins += 1
                if word in ADJUSTING_DISSENTS:
                    adjusted += 1
                member_rows.append(f"  {sid}  WIN  {_record_basis(sid, records)}{mark}")
            elif verdict == "LOSS":
                losses += 1
                member_rows.append(f"  {sid}  LOSS  {_record_basis(sid, records)}{mark}")
            else:
                others += 1
                member_rows.append(f"  {sid}  other  {basis or '(no declared basis)'}{mark}")
        title = str(body.get("title") or epic_id)
        row = f"{epic_id}  {span}  {wins} WIN / {losses} LOSS / {others} other"
        if adjusted:
            row += (
                f"  (adjusted: {wins - adjusted} WIN / {losses} LOSS / "
                f"{others + adjusted} other)"
            )
        row += f"  {title}"
        if no_state:
            row += f"  (no state: {', '.join(no_state)})"
        lines.append(row)
        lines.extend(member_rows)
    return lines
