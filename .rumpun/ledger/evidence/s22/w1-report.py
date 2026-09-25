"""rumpun season report — campaign dashboard v2 (P36 surface 2 + skill pass).

Renders from harness-observed files only (engine state, musim yaml, rimba
artifacts): views are derived, never authoritative (DESIGN section 13).
Identical ledger bytes render byte-identical HTML: no clock reads, no
randomness, sorted orders, UTC ISO times, fixed float formats. Provenance
labels [H]/[A]/[D] mark every displayed value.

M1 (codex-review-2026-09-14): every view renders from the PERSISTED season
state.json (read_persisted_status) -- no /proc reads inside a render -- so
a RUNNING season renders byte-identically too. The landing page's live
freshness comes from the state hook's frequent re-renders, not from /proc
reads inside a render.

Design system (ui-ux-pro-max skill pass, 2026-09-14): Dark OLED theme,
density-8 spacing, inline SVG status glyphs beside visible text (never color
alone), campaign strip linking every season. Deviations, deliberate: no
webfont import (self-contained rule outranks the Inter recommendation) and
no motion (determinism; motion dial was 2 anyway).
"""

from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from rumpun.audit import BOOKKEEPING_FILES
from rumpun.engine import EngineError, read_persisted_status, season_dir, state_path

logger = logging.getLogger(__name__)

C_BG = "#020617"
C_CARD = "#0E1223"
C_BORDER = "#334155"
C_FG = "#F8FAFC"
C_MUTED = "#94A3B8"
C_WIN = "#22C55E"
C_LOSS = "#EF4444"
C_NEUTRAL = "#F59E0B"
C_RUN = "#38BDF8"

VERDICT_COLOR = {
    "WIN": C_WIN, "LOSS": C_LOSS, "NEUTRAL": C_NEUTRAL,
    "INVALID": C_MUTED,
}
STATE_COLOR = {
    "completed": C_WIN, "stopped_stall": C_NEUTRAL,
    "stopped_budget": C_NEUTRAL, "stopped_operator": C_RUN,
    "running": C_RUN,
}

_CSS = "\n".join([
    f"body{{background:{C_BG};color:{C_FG};font-family:Inter,ui-sans-serif,"
    "system-ui,sans-serif;margin:0;padding:1.5rem;max-width:64rem;margin-inline:auto}",
    f"a{{color:{C_RUN};text-decoration:none}}a:focus-visible{{outline:2px solid {C_FG}}}",
    f"h1{{font-size:1.25rem;margin:0 0 .25rem}}h2{{font-size:.95rem;color:{C_MUTED};"
    "margin:1.5rem 0 .5rem;text-transform:uppercase;letter-spacing:.08em}}",
    f".card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:8px;"
    "padding:1rem;margin-top:.75rem}",
    "table{border-collapse:collapse;width:100%;margin-top:.5rem}",
    f"th,td{{border:1px solid {C_BORDER};padding:.35rem .6rem;text-align:left;"
    "font-family:ui-monospace,monospace;font-size:.85rem}",
    f"th{{background:{C_BG};color:{C_MUTED};font-weight:600}}",
    ".prov{font-size:.75em;color:" + C_MUTED + ";font-weight:normal}",
    ".policy,.legend-note{color:" + C_MUTED + ";font-size:.85rem}",
    ".legend ul{margin:.3rem 0;padding-left:1.2rem}",
    f".footer{{color:{C_MUTED};font-size:.8rem;margin-top:2rem}}",
    ".strip{display:flex;flex-wrap:wrap;gap:.5rem}",
    ".strip a{display:block;min-width:6.2rem}",
    f".cell{{border:1px solid {C_BORDER};border-radius:8px;padding:.5rem .6rem;"
    f"background:{C_CARD}}}",
    ".cell .sid{font-family:ui-monospace,monospace;font-weight:600}",
    ".cell .ver{font-size:.75rem}",
    ".change dt{margin-top:.5rem}",
    ".change dd{margin:0 0 .25rem;font-family:ui-monospace,monospace;font-size:.85rem}",
    ".bar{fill:" + C_RUN + "}.barloss{fill:" + C_LOSS + "}.barwin{fill:" + C_WIN + "}",
    ".stat{display:flex;gap:1rem;flex-wrap:wrap;margin-top:.5rem}",
    ".stat .card{margin:0;flex:1;min-width:9rem}",
    ".stat .num{font-size:1.6rem;font-family:ui-monospace,monospace}",
    ".stat .lbl{color:" + C_MUTED + ";font-size:.8rem}",
    ".one{font-size:.95rem;margin:.4rem 0 0}",
    ".plain{font-size:1rem;margin:.25rem 0}",
    ".idle{color:" + C_MUTED + "}",
])

_POLICY = (
    '<p class="policy">State policy [D]: exit file 0 -&gt; exited; non-zero -&gt; '
    "failed; no exit file + live pid -&gt; running (stalled after stall_minutes); "
    "no exit file + dead pid -&gt; crashed; engine kill -&gt; terminated.</p>"
)

_LEGEND = """<section class="legend">
<h2>Provenance</h2>
<p class="legend-note">Every value is labeled: where it came from.</p>
<ul>
<li><strong>[H] harness-observed</strong> - recorded by the engine itself:
season identity, status transition, start/end times, route at spawn, exit
codes, wall-clock seconds, artifact existence.</li>
<li><strong>[A] agent-authored</strong> - season YAML text (goal,
primary_change, evidence) and verdicts, quoted verbatim; the harness checks
locators resolve, not that claims are true.</li>
<li><strong>[D] derived</strong> - computed from stated inputs: duration,
agent state policy, strip verdict mapping.</li>
</ul>
</section>"""

_GLYPHS = {
    "WIN": '<path d="M4 10l4 4 8-8" fill="none" stroke-width="2.5"/>',
    "LOSS": '<path d="M4 4l12 12M16 4L4 16" fill="none" stroke-width="2.5"/>',
    "NEUTRAL": '<path d="M3 10h14" fill="none" stroke-width="2.5"/>',
    "INVALID": '<path d="M10 3v9M10 15v2" fill="none" stroke-width="2.5"/>',
    "no state": '<circle cx="10" cy="10" r="7" fill="none" stroke-width="2"/>',
    "running": (
        '<circle cx="10" cy="10" r="7" fill="none" stroke-width="2" '
        'stroke-dasharray="4 3"/>'
    ),
}


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _glyph(name: str, color: str) -> str:
    body = _GLYPHS.get(name, _GLYPHS["no state"])
    return (
        f'<svg width="14" height="14" viewBox="0 0 20 20" aria-hidden="true" '
        f'stroke="{color}" style="vertical-align:-2px">{body}</svg>'
    )


def _verdict_of(root: Path, sid: str) -> str:
    """Season verdict from the last season-level verdicts.jsonl row [H]."""
    verdicts = season_dir(root, sid) / "verdicts.jsonl"
    if not verdicts.is_file():
        return "INVALID"
    last = ""
    with verdicts.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("season") == sid:
                    last = str(row.get("verdict", ""))
    return last or "INVALID"


def _iso(ts: float | None) -> str:
    if ts is None:
        return "-"
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")


def _num(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "-"
    return f"{value:.1f}{suffix}"


def _summary_rows(status: dict[str, Any]) -> list[str]:
    started = status.get("started_at")
    ended = status.get("ended_at")
    dur = None if started is None or ended is None else ended - started
    rows = [
        ("Season", "[H]", status.get("id")),
        ("Status", "[H]", status.get("status")),
        ("Started", "[H]", _iso(started)),
        ("Ended", "[H]", _iso(ended)),
        ("Duration", "[D]", _num(dur, " s")),
    ]
    return [
        f'<dt>{_esc(label)} <span class="prov">{_esc(prov)}</span></dt>'
        f"<dd>{_esc(value)}</dd>"
        for label, prov, value in rows
    ]


def _agent_rows(agents: dict[str, dict[str, Any]]) -> list[str]:
    rows = []
    for name in sorted(agents):
        a = agents[name]
        cells = [
            a.get("name", name),
            a.get("route", "?"),
            a.get("state", "?"),
            "-" if a.get("exit_code") is None else a["exit_code"],
            _num(a.get("seconds"), " s"),
        ]
        row = "".join(f"<td>{_esc(c)}</td>" for c in cells)
        rows.append(f"<tr>{row}</tr>")
    return rows


def _document(status: dict[str, Any]) -> str:
    head = "".join(
        f'<th>{_esc(label)} <span class="prov">{_esc(prov)}</span></th>'
        for label, prov in [
            ("Agent", "[H]"), ("Route", "[H]"), ("State", "[D]"),
            ("Exit code", "[H]"), ("Seconds", "[H]"),
        ]
    )
    body = "".join(_agent_rows(status.get("agents") or {}))
    summary = "".join(_summary_rows(status))
    sid = _esc(status.get("id", "?"))
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>rumpun season {sid} report</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        f"<h1>Season {sid}</h1>\n"
        f"<dl>\n{summary}\n</dl>\n"
        f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table>\n"
        f"{_POLICY}\n{_LEGEND}\n</body>\n</html>\n"
    )


def _season_ids(root: Path) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for path in (root / "musim").glob("s*.yaml"):
        match = re.fullmatch(r"s(\d+)", path.stem)
        if match:
            out.append((int(match.group(1)), path.stem))
    return sorted(set(out))


def _goal_of(root: Path, sid: str) -> str:
    """The season's goal line, verbatim [A]; empty when absent."""
    season_file = root / "musim" / f"{sid}.yaml"
    if not season_file.is_file():
        return ""
    try:
        doc = yaml.safe_load(season_file.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return ""
    if isinstance(doc, dict) and isinstance(doc.get("goal"), str):
        return doc["goal"]
    return ""


def _strip_tally(root: Path, self_sid: str | None) -> tuple[str, str]:
    """Campaign strip cells + tally line. Verdict [D] from verdicts [A]/state [H]."""
    ids = _season_ids(root)
    cells: list[str] = []
    wins = losses = invalids = nostate = 0
    for _, sid_other in ids:
        state_file = state_path(root, sid_other)
        if not state_file.is_file():
            nostate += 1
            color, verdict, dur_txt = C_MUTED, "no state", "-"
        else:
            state = read_persisted_status(root, sid_other)
            verdict = _verdict_of(root, sid_other)
            if verdict == "WIN":
                wins += 1
            elif verdict == "LOSS":
                losses += 1
            else:
                invalids += 1
            color = VERDICT_COLOR.get(verdict, C_NEUTRAL)
            dur = (state.get("ended_at") or 0) - state.get("started_at", 0)
            dur_txt = f"{dur:.0f}s" if dur > 0 else "-"
        if sid_other == self_sid:
            link = "report.html"
        elif (season_dir(root, sid_other) / "report.html").is_file():
            link = f"../{sid_other}/report.html"
        else:
            link = None
        inner = (
            '<div class="cell">'
            f'{_glyph(verdict, color)} <span class="sid">{_esc(sid_other)}</span><br>'
            f'<span class="ver" style="color:{color}">{_esc(verdict)}</span> '
            f'<span class="ver" style="color:{C_MUTED}">{_esc(dur_txt)}</span>'
            "</div>"
        )
        cells.append(f'<a href="{_esc(link)}">{inner}</a>' if link else inner)
    strip = f'<div class="strip">{"".join(cells)}</div>'
    tally = (
        f'<p class="plain">Campaign tally [D]: {wins} WIN &middot; {losses} LOSS '
        f"&middot; {invalids} NEUTRAL/INVALID &middot; {nostate} no state"
        f" &middot; {len(ids)} seasons</p>"
    )
    return strip, tally


def _campaign_section(root: Path, sid: str) -> str:
    """Campaign strip + this season's declared change. [H] file facts, [A] yaml text."""
    strip, tally = _strip_tally(root, sid)
    change_rows: list[str] = []
    season_file = root / "musim" / f"{sid}.yaml"
    if season_file.is_file():
        try:
            doc = yaml.safe_load(season_file.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            doc = None
        if isinstance(doc, dict):
            method = doc.get("methodology") or {}
            change = method.get("primary_change") or {}
            evidence = method.get("evidence") or []
            for field in ("type", "node", "baseline", "expected_band", "eval_window"):
                if change.get(field):
                    change_rows.append(
                        f"<dt>{_esc(field)} <span class='prov'>[A]</span></dt>"
                        f"<dd>{_esc(change[field])}</dd>"
                    )
            for cite in evidence:
                if isinstance(cite, str):
                    change_rows.append(
                        f"<dt>evidence <span class='prov'>[A]</span></dt>"
                        f"<dd>{_esc(cite)}</dd>"
                    )
    change_html = ""
    if change_rows:
        change_html = (
            '<section class="card change"><h2>Declared change this season</h2>'
            f"<dl>{''.join(change_rows)}</dl></section>"
        )
    durations: list[tuple[str, float, str]] = []
    for _, sid_other in _season_ids(root):
        state_file = state_path(root, sid_other)
        if not state_file.is_file():
            continue
        state = read_persisted_status(root, sid_other)
        dur = (state.get("ended_at") or 0) - state.get("started_at", 0)
        if dur > 0:
            durations.append((sid_other, dur, _verdict_of(root, sid_other)))
    bars = ""
    if len(durations) >= 4:
        max_dur = max(d for _, d, _ in durations) or 1
        bar_rows = []
        for sid_other, dur, verdict in durations:
            width = max(2, int(dur / max_dur * 400))
            cls = {"WIN": "barwin", "LOSS": "barloss"}.get(verdict, "bar")
            bar_rows.append(
                f"<text x='0' y='12' font-size='10' fill='{C_MUTED}'>"
                f"{_esc(sid_other)}</text>"
                f"<rect class='{cls}' x='46' y='4' width='{width}' height='10'/>"
                f"<text x='{52 + width}' y='12' font-size='10' fill='{C_MUTED}'>"
                f"{dur:.0f}s {_esc(verdict)}</text>"
            )
        bars = (
            '<section class="card"><h2>Duration per season [H]</h2><svg '
            f"width='560' height='{28 * len(durations)}' role='img' "
            "aria-label='bar chart of season durations in seconds'>"
            + "".join(
                f"<g transform='translate(0,{28 * i})'>{row}</g>"
                for i, row in enumerate(bar_rows)
            )
            + "</svg></section>"
        )
    return (
        '<section class="card"><h2>Campaign progress</h2>'
        f"{strip}{tally}</section>{change_html}{bars}"
    )


_ROUTINE_ID_RE = re.compile(r"^s\d+-harvest$")
_GATE_PREFIXES = ("approve-", "reject-", "rollback-")


def _write_atomic(path: Path, doc: str) -> None:
    """Atomic render write: tmp file then replace (report convention)."""
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(doc, encoding="utf-8")
    tmp.replace(path)


def _discovery_records(root: Path) -> list[dict[str, str]]:
    """Non-routine akar records: the campaign's discoveries [A].

    A discovery is any top-level akar/*.md whose id is not routine
    bookkeeping: <sid>-harvest rows and approve/reject/rollback gate
    paperwork are excluded; audit reflections, defect records, and
    workarounds are the interesting feed. Sorted by filename (date
    prefix), oldest first.
    """
    found: list[dict[str, str]] = []
    akar_dir = root / "akar"
    if not akar_dir.is_dir():
        return found
    for path in sorted(akar_dir.glob("*.md")):
        rid = title = date = ""
        try:
            head = path.read_text(encoding="utf-8").splitlines()[:10]
        except OSError as exc:
            logger.warning("skip unreadable akar record %s: %s", path, exc)
            continue
        for line in head:
            if line.startswith("id: ") and not rid:
                rid = line[4:].strip()
            elif line.startswith("title: ") and not title:
                title = line[7:].strip()
            elif line.startswith("date: ") and not date:
                date = line[6:].strip()
        if not rid:
            rid = path.stem
        if _ROUTINE_ID_RE.match(rid) or rid.startswith(_GATE_PREFIXES):
            continue
        found.append(
            {"id": rid, "title": title or rid, "date": date, "path": path.name}
        )
    return found


def render_discoveries(root: Path, out: Path | None = None) -> Path:
    """Discoveries list + one verbatim page per record under rimba/discoveries/.

    Deterministic; never mutates the ledger (akar is read-only here).
    Returns the list page path.
    """
    records = _discovery_records(root)
    out_dir = root / "rimba" / "discoveries"
    out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for rec in reversed(records):
        items.append(
            f'<li><a href="{_esc(rec["id"])}.html">{_esc(rec["title"])}</a> '
            f'<span class="prov">{_esc(rec["id"])} &middot; '
            f'{_esc(rec["date"])}</span></li>'
        )
    listing = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>rumpun discoveries</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        "<h1>Discoveries</h1>\n"
        '<p class="plain">What the campaign learned about itself and its '
        'tools <span class="prov">[A]</span> &middot; '
        '<a href="../index.html">all progress</a></p>\n'
        f"<ul>{''.join(items)}</ul>\n{_POLICY}\n</body>\n</html>\n"
    )
    list_path = out if out is not None else out_dir / "index.html"
    _write_atomic(list_path, listing)
    for rec in records:
        body = (root / "akar" / rec["path"]).read_text(encoding="utf-8")
        page = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>rumpun discovery {rec['id']}</title>\n"
            f"<style>{_CSS}</style>\n</head>\n<body>\n"
            f"<h1>{_esc(rec['title'])}</h1>\n"
            '<p class="plain">'
            f'<span class="prov">{_esc(rec["id"])} &middot; {_esc(rec["date"])}'
            ' [A]</span> &middot; '
            '<a href="index.html">all discoveries</a></p>\n'
            f"<pre>{_esc(body)}</pre>\n{_POLICY}\n</body>\n</html>\n"
        )
        safe = re.sub(r"[^a-z0-9-]", "-", rec["id"].lower())
        _write_atomic(out_dir / f"{safe}.html", page)
    return list_path


def _short(text: str, limit: int = 72) -> str:
    """One line, whitespace-collapsed, truncated with an ellipsis when long."""
    line = " ".join(text.split())
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"


def render_index(root: Path, out: Path | None = None) -> Path:
    """Landing page: plain-language progress first, details one click away.

    Deterministic like every view: no clock reads, sorted orders. The human
    sentences quote season goal lines, shortened when long [A]; counts and
    states are
    [H]/[D]. Never mutates anything.
    """
    ids = _season_ids(root)
    closed: list[tuple[str, str, float, str]] = []
    running: list[str] = []
    for _, sid_other in ids:
        state_file = state_path(root, sid_other)
        if not state_file.is_file():
            continue
        state = read_persisted_status(root, sid_other)
        dur = (state.get("ended_at") or 0) - state.get("started_at", 0)
        if state.get("status") == "running":
            running.append(sid_other)
        elif dur > 0:
            closed.append(
                (sid_other, _verdict_of(root, sid_other), dur, _goal_of(root, sid_other))
            )
    wins = sum(1 for _, v, _, _ in closed if v == "WIN")
    losses = sum(1 for _, v, _, _ in closed if v == "LOSS")
    goal = _goal_of(root, ids[-1][1]) if ids else ""
    if closed:
        last_sid, last_v, last_dur, last_goal = closed[-1]
        last_line = (
            f'<p class="plain">Last finished: <strong>{_esc(last_sid)} {_esc(last_v)}'
            f"</strong> in {last_dur:.0f}s &mdash; built: "
            f"{_esc(_short(last_goal) or '(no goal line)')}"
            " <span class='prov'>[A]</span></p>"
        )
    else:
        last_line = '<p class="plain idle">Nothing finished yet.</p>'
    if running:
        rid = running[-1]
        run_state = read_persisted_status(root, rid)
        if (season_dir(root, rid) / "report.html").is_file():
            who = (
                f'<a href="{_esc(rid)}/report.html">'
                f"<strong>{_esc(rid)}</strong></a>"
            )
        else:
            who = f"<strong>{_esc(rid)}</strong>"
        building = (
            f'<p class="plain">Building right now: {who}'
            f" &mdash; {_esc(_short(_goal_of(root, rid)) or '(no goal line)')}"
            f" <span class='prov'>[A]</span> &middot; started "
            f"{_esc(_iso(run_state.get('started_at')))} [H]</p>"
        )
    else:
        building = (
            '<p class="plain idle">Idle &mdash; nothing is building right now.</p>'
        )
    recent = ""
    if closed:
        items = []
        for sid_other, verdict, dur, goal_line in reversed(closed[-3:]):
            color = VERDICT_COLOR.get(verdict, C_NEUTRAL)
            items.append(
                f"<li>{_glyph(verdict, color)} <strong>{_esc(sid_other)} "
                f"{_esc(verdict)}</strong> ({dur:.0f}s) &mdash; "
                f"{_esc(_short(goal_line) or '(no goal line)')}</li>"
            )
        recent = (
            '<section class="card"><h2>Latest results</h2><ul>' 
            + "".join(items)
            + "</ul></section>"
        )
    strip, tally = _strip_tally(root, None)
    render_discoveries(root)
    discoveries = _discovery_records(root)
    disc_card = ""
    if discoveries:
        links = "".join(
            f'<li><a href="discoveries/{_esc(rec["id"])}.html">'
            f'{_esc(rec["title"])}</a> '
            f'<span class="prov">{_esc(rec["date"])}</span></li>'
            for rec in reversed(discoveries[-5:])
        )
        disc_card = (
            '<section class="card"><h2>Discoveries [A]</h2><ul>'
            f"{links}</ul>"
            '<p class="plain"><a href="discoveries/index.html">'
            f"all {len(discoveries)} discoveries</a></p></section>"
        )
    head = "<h1>rumpun progress</h1>"
    if goal:
        head += f'<p class="plain">Campaign: {_esc(_short(goal))} <span class="prov">[A]</span></p>'
    summary = (
        f'<p class="plain"><strong>{len(closed)}</strong> seasons built &middot; '
        f'<strong>{wins}</strong> WIN &middot; <strong>{losses}</strong> LOSS'
        " <span class='prov'>[D]</span></p>"
    )
    doc = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>rumpun progress</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        f"{head}{summary}{building}{last_line}{recent}{disc_card}"
        '<section class="card"><h2>Every season</h2>'
        f"{strip}{tally}</section>"
        f"{_POLICY}\n{_LEGEND}\n"
        f'<p class="footer">project {_esc(root.parent.name)} [H] &middot; '
        "deterministic static view\n"
        "</body>\n</html>\n"
    )
    target = out if out is not None else root / "rimba" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(doc, encoding="utf-8")
    tmp.replace(target)
    logger.info("campaign index -> %s", target)
    return target


def _footer(project: str, sid: str, state_sha: str) -> str:
    """Self-identification line [H]: which project, season, and state bytes."""
    return (
        f'<p class="footer">project {_esc(project)} · season {_esc(sid)} · '
        f"state sha256:{state_sha[:12]} [H]</p>"
    )


def _workspace_files(ws: Path) -> list[str]:
    """Workspace files worth linking: agent.log plus every deliverable.

    A file is a deliverable when no component of its workspace-relative
    path is in audit's BOOKKEEPING_FILES (the audit's set — one source of
    truth); agent.log is bookkeeping but linked anyway: it is the agent's
    full stream.
    """
    found = ["agent.log"] if (ws / "agent.log").is_file() else []
    if ws.is_dir():
        for path in sorted(ws.rglob("*")):  # M1: deterministic link order
            if not path.is_file():
                continue
            rel = path.relative_to(ws)
            if any(part in BOOKKEEPING_FILES for part in rel.parts):
                continue
            found.append(rel.as_posix())
    return found


def _workspaces_section(root: Path, sid: str, status: dict[str, Any]) -> str:
    """Per-agent workspace links [D]: the log stream plus deliverables."""
    agents = status.get("agents") or {}
    if not agents:
        return ""
    rows = []
    for name in sorted(agents):
        files = _workspace_files(season_dir(root, sid) / name)
        links = (
            " ".join(
                f'<a href="{_esc(name)}/{_esc(f)}">{_esc(f)}</a>' for f in files
            )
            if files
            else "-"
        )
        rows.append(f"<tr><td>{_esc(name)}</td><td>{links}</td></tr>")
    return (
        '<section class="card"><h2>Workspaces [D]</h2>'
        "<table><thead><tr><th>Agent</th><th>Files</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></section>"
    )


def render_report(root: Path, sid: str, out: Path | None = None) -> Path:
    """Render the dashboard page for season `sid`; returns its path.

    Default target: root/rimba/<sid>/report.html (or `out`). Never mutates
    season state; a missing state.json raises EngineError. The page renders
    from ONE read of the persisted state.json bytes (M1): the footer hash
    covers exactly the bytes the page rendered from -- same bytes, same page.
    """
    state_file = state_path(root, sid)
    try:
        raw = state_file.read_bytes()
    except FileNotFoundError as exc:
        msg = f"no season state for '{sid}'; run 'rumpun season start' first"
        raise EngineError(msg) from exc
    # M1: one read serves both the page and its self-identifying hash, so
    # the footer hash covers exactly the bytes the page rendered from.
    state_sha = hashlib.sha256(raw).hexdigest()
    status = json.loads(raw)
    footer = _footer(root.parent.name, sid, state_sha)
    doc = _document(status)
    campaign = _campaign_section(root, sid)
    workspaces = _workspaces_section(root, sid, status)
    doc = doc.replace(
        _POLICY,
        f"{campaign}{workspaces}{_POLICY}",
    )
    verdict = _verdict_of(root, sid)
    dur = (status.get("ended_at") or 0) - status.get("started_at", 0)
    if dur > 0:
        head_line = (
            f'<p class="one">{_glyph(verdict, VERDICT_COLOR.get(verdict, C_NEUTRAL))} '
            f"<strong>{_esc(verdict) or _esc(status.get('status'))}</strong> &mdash; "
            f"built: {_esc(_goal_of(root, sid) or '(no goal line)')}"
            f" &mdash; {dur:.0f}s <span class='prov'>[A][D]</span> &middot; "
            f"<a href='../index.html'>all progress</a></p>"
        )
        doc = doc.replace(
            f"<h1>Season {_esc(status.get('id', '?'))}</h1>\n",
            f"<h1>Season {_esc(status.get('id', '?'))}</h1>\n{head_line}\n",
            1,
        )
    doc = doc.replace("</body>", f"{footer}\n</body>")
    target = out if out is not None else season_dir(root, sid) / "report.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(doc, encoding="utf-8")
    tmp.replace(target)  # atomic write
    logger.info("season %s report -> %s", sid, target)
    return target
