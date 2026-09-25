"""rumpun kanban — the campaign board (s66 w1; directives seq 7 + seq 8).

Four columns rendered from state that already exists on disk: the ledger,
the runs tree, the season yamls, and rumpun.yaml. No new state file -- every
card re-derives from the same harness-observed sources the other verbs read.

BACKLOG: armed audit candidates (the `candidate:` lines of the highest
audit-<N> ledger record) plus drafted-only season seeds (a seasons/<sid>.yaml
whose season has no runs state and no harvest record).
DOING: seasons whose persisted state says running.
NEED HUMAN: the unset budget.campaign_cost_cap, season-start containment
blocks (engine.containment_block for the next season id), and pending
operator directives. Every card carries the seq 8 four sentences: what
happened, what needs doing, why it needs a human, what happens if nobody
acts.
DONE: harvested seasons, one card per s<N>-harvest ledger record; verdict
and the salvage mark come from the record itself. The five newest render;
the rest collapse into one honest counts line.
"""

from __future__ import annotations

import logging
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from rumpun import akar, collab, engine, paths, yamlio

logger = logging.getLogger(__name__)

DONE_SHOW = 5
HARVEST_ID = re.compile(r"^(s\d+)-harvest$")
AUDIT_ID = re.compile(r"^audit-(\d+)$")
VERDICTS = ("WIN", "LOSS", "NEUTRAL", "INVALID")


def _season_num(sid: str) -> int:
    m = re.fullmatch(r"s(\d+)", sid)
    return int(m.group(1)) if m else -1


def _next_season_id(root: Path) -> str:
    numbers = [
        n
        for n in (_season_num(p.stem) for p in paths.seasons_dir(root).glob("s*.yaml"))
        if n >= 0
    ]
    return f"s{max(numbers) + 1 if numbers else 1}"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        logger.exception("kanban cannot read %s", path)
        raise


def _latest_audit(root: Path) -> tuple[str, list[str]]:
    """(record id, candidate lines) of the highest audit-<N> ledger record."""
    audits = [
        (int(m.group(1)), path)
        for rid, path in akar.declared_ids(root).items()
        if (m := AUDIT_ID.match(rid)) is not None
    ]
    if not audits:
        return "", []
    n, path = max(audits)
    rid = f"audit-{n}"
    lines = [
        line.removeprefix("candidate: ").strip()
        for line in _read(path).splitlines()
        if line.startswith("candidate: ")
    ]
    logger.debug("kanban backlog: %d candidates from %s", len(lines), rid)
    return rid, lines


def _drafted_only(root: Path) -> list[str]:
    """Season ids with a yaml, no runs state, and no harvest record."""
    harvested = {
        m.group(1)
        for rid in akar.declared_ids(root)
        if (m := HARVEST_ID.match(rid)) is not None
    }
    seeds: list[tuple[int, str]] = []
    for path in paths.seasons_dir(root).glob("s*.yaml"):
        sid = path.stem
        if sid in harvested:
            continue
        if engine.state_path(root, sid).is_file():
            continue
        seeds.append((_season_num(sid), sid))
    return [sid for _n, sid in sorted(seeds)]


def _doing_cards(root: Path) -> list[str]:
    cards: list[str] = []
    yamls = paths.seasons_dir(root).glob("s*.yaml")
    for path in sorted(yamls, key=lambda p: _season_num(p.stem)):
        sid = path.stem
        if not engine.state_path(root, sid).is_file():
            continue
        state = engine.read_persisted_status(root, sid)
        if state.get("status") != "running":
            continue
        started = float(state["started_at"])
        ended = state.get("ended_at") or time.time()
        agents = state.get("agents") or state.get("spawned") or {}
        names = ", ".join(sorted(agents)) or "no agents"
        cards.append(f"- {sid}: running {int(ended - started)}s ({names})")
    return cards


def _need_card(title: str, citation: str, sentences: list[str]) -> list[str]:
    """One NEED HUMAN card: the title line plus the seq 8 four sentences."""
    lines = [f"- {title}  [{citation}]"]
    lines += [f"    {sentence}" for sentence in sentences]
    return lines


def _cap_cards(root: Path) -> list[str]:
    cfg = yamlio.load(root / "rumpun.yaml")
    budget = cfg.get("budget") if isinstance(cfg, dict) else None
    cap = budget.get("campaign_cost_cap") if isinstance(budget, dict) else None
    if cap is not None:
        return []
    return _need_card(
        "campaign_cost_cap is unset",
        "rumpun.yaml budget",
        [
            "what happened: budget.campaign_cost_cap is null, unset since"
            " campaign start (P9).",
            "what needs doing: set a number, or record the standing no-cap"
            " decision (directive seq 9).",
            "why it needs a human: only the operator sets or releases the"
            " budget invariant.",
            "what happens if nobody acts: every audit re-flags it (F6) and"
            " the card stays on the board.",
        ],
    )


def _containment_cards(root: Path) -> list[str]:
    nxt = _next_season_id(root)
    detail = engine.containment_block(root, nxt)
    if detail is None:
        return []
    return _need_card(
        f"season start {nxt} is contained",
        "ledger check record",
        [
            f"what happened: {detail}",
            "what needs doing: rerun the close check to VERIFIED, or append"
            " the operator waiver (rumpun waive).",
            "why it needs a human: the waiver is the operator's explicit,"
            " sha-sealed release.",
            "what happens if nobody acts: every season start for the next id"
            " refuses, naming this record.",
        ],
    )


def _directives_cards(root: Path) -> list[str]:
    ledger = paths.ledger_dir(root)
    lane = {
        "file": str(ledger / "directives.jsonl"),
        "lock": str(ledger / "directives.lock"),
    }
    if not Path(lane["file"]).is_file():
        return []
    events = collab.read_events(lane)
    pending = [e for e in events if e.get("status") == "pending"]
    if not pending:
        return []
    seqs = ", ".join(str(e.get("seq", "?")) for e in pending)
    return _need_card(
        f"{len(pending)} operator directives pending (seq {seqs})",
        "ledger/directives.jsonl",
        [
            "what happened: the operator appended directives; their status"
            " is still pending.",
            "what needs doing: act on each directive, then mark its status"
            " consumed in the lane.",
            "why it needs a human: only the operator's side retires a"
            " directive; the board never edits the lane.",
            "what happens if nobody acts: the card stays; directives never"
            " expire on their own.",
        ],
    )


def _harvest_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rid, path in akar.declared_ids(root).items():
        m = HARVEST_ID.match(rid)
        if m is None:
            continue
        title = ""
        verdict = ""
        for line in _read(path).splitlines():
            if line.startswith("title: "):
                title = line.removeprefix("title: ")
            elif line.startswith("verdict: "):
                verdict = line.removeprefix("verdict: ").strip()
        rows.append(
            {
                "n": int(m.group(1)[1:]),
                "sid": m.group(1),
                "verdict": verdict or "-",
                "salvaged": "(salvaged)" in title,
            }
        )
    return sorted(rows, key=lambda r: r["n"])


def _done_cards(root: Path) -> list[str]:
    rows = _harvest_rows(root)
    counts = Counter(r["verdict"] for r in rows)
    salvaged = sum(1 for r in rows if r["salvaged"])
    cards = [
        f"- {r['sid']}: {r['verdict']}" + (" (salvaged)" if r["salvaged"] else "")
        for r in rows[-DONE_SHOW:]
    ]
    if len(rows) > DONE_SHOW:
        parts = ", ".join(f"{counts.get(v, 0)} {v}" for v in VERDICTS)
        cards.append(
            f"  ...and {len(rows) - DONE_SHOW} more ({parts}; {salvaged} salvaged)"
        )
    return cards


def render(root: Path) -> str:
    """The board: four column sections from existing state; no writes."""
    rid, candidates = _latest_audit(root)
    backlog = [f"- {text}  [{rid}]" for text in candidates]
    backlog += [
        f"- seed {sid}: drafted, never started  [seasons/{sid}.yaml]"
        for sid in _drafted_only(root)
    ]

    doing = _doing_cards(root)
    need: list[str] = []
    need += _cap_cards(root)
    need += _containment_cards(root)
    need += _directives_cards(root)
    done = _done_cards(root)
    if done:
        done = [f"- {len(done)} harvested", *done]

    lines = [f"rumpun kanban {time.strftime('%Y-%m-%d %H:%M')}"]
    for name, cards in (
        ("BACKLOG", backlog),
        ("DOING", doing),
        ("NEED HUMAN", need),
        ("DONE", done),
    ):
        n_cards = sum(1 for line in cards if line.startswith("- "))
        lines.append("")
        lines.append(f"{name} ({n_cards})")
        lines += cards or ["  (no cards)"]
    logger.debug("kanban board rendered: %d lines", len(lines))
    return "\n".join(lines)
