"""rumpun season report — self-contained static HTML per season (P36 surface 2).

Renders only from the harness snapshot (engine.read_status): views are derived,
never authoritative (DESIGN section 13). Identical snapshot bytes render
byte-identical HTML: no clock reads, no randomness, sorted agent order, UTC ISO
times, fixed float formats. Provenance labels [H]/[A]/[D] mark every displayed
value (D4 mandatory); read_status carries no agent-authored values, so [A]
appears only in the legend. A footer self-identifies the page [H]: project,
season, and the sha256 of the season state bytes.
"""

from __future__ import annotations

import hashlib
import html
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rumpun.engine import read_status, season_dir, state_path

logger = logging.getLogger(__name__)

_CSS = "\n".join([
    "body{font-family:ui-monospace,monospace;margin:2rem;max-width:56rem;color:#111}",
    "table{border-collapse:collapse;margin-top:1rem}",
    "th,td{border:1px solid #999;padding:.3rem .6rem;text-align:left}",
    "th{background:#eee}",
    ".prov{font-size:.8em;color:#555;font-weight:normal}",
    ".policy{color:#444;margin-top:.4rem}",
    ".legend{margin-top:1.5rem}",
    ".legend ul{margin:.3rem 0}",
    ".footer{color:#777;font-size:.85em;margin-top:2rem}",
])

_POLICY = (
    '<p class="policy">State policy [D]: exit file 0 -&gt; exited; non-zero -&gt; '
    "failed; no exit file + live pid -&gt; running (stalled after stall_minutes); "
    "no exit file + dead pid -&gt; crashed; still live at finalize -&gt; "
    "terminated.</p>"
)

_LEGEND = """<section class="legend">
<h2>Provenance</h2>
<ul>
<li><strong>[H] harness-observed</strong> - recorded by the engine itself:
season identity, status transition, start/end times, route at spawn, exit
codes, wall-clock seconds.</li>
<li><strong>[A] agent-authored</strong> - written by an agent (verdicts,
discoveries, citations). None appear in this view: read_status carries no
agent-authored values.</li>
<li><strong>[D] derived</strong> - computed from stated inputs: duration =
ended - started; agent state = policy over exit code and process liveness
(see state policy below the table).</li>
</ul>
</section>"""


def _esc(value: Any) -> str:
    return html.escape(str(value))


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
        f"<title>rumpun season {sid} report</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        f"<h1>Season {sid}</h1>\n"
        f"<dl>\n{summary}\n</dl>\n"
        f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table>\n"
        f"{_POLICY}\n{_LEGEND}\n</body>\n</html>\n"
    )


def _footer(project: str, sid: str, state_sha: str) -> str:
    """Self-identification line [H]: which project, season, and state bytes."""
    return (
        f'<p class="footer">project {_esc(project)} · season {_esc(sid)} · '
        f"state sha256:{state_sha[:12]} [H]</p>"
    )


def render_report(root: Path, sid: str, out: Path | None = None) -> Path:
    """Render the static HTML report for season `sid`; returns its path.

    Default target: root/rimba/<sid>/report.html (or `out`). Never mutates
    season state; read_status failures propagate as EngineError. The document
    gains a footer with the sha256 of the state.json bytes: same state bytes,
    same footer.
    """
    status = read_status(root, sid)
    state_sha = hashlib.sha256(state_path(root, sid).read_bytes()).hexdigest()
    footer = _footer(root.parent.name, sid, state_sha)
    doc = _document(status).replace("</body>", f"{footer}\n</body>")
    target = out if out is not None else season_dir(root, sid) / "report.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(doc, encoding="utf-8")
    tmp.replace(target)  # atomic write
    logger.info("season %s report -> %s", sid, target)
    return target
