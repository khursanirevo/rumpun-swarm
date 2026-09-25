"""s94 w1 pins - the aggregate reconciles as a label split; the stop is checkable.

Spec sources: audit-46's two governance candidates (verbatim in the s93
w1 notes), the measured ledger (probe_aggregate.py + probe_aggregate.out
in .rumpun/runs/s94/w1, 2026-09-18), the s62 salvage-mark contract, the
s64 whole-ledger slot table, and the s87/s88 usefulness assessment
(USEFULNESS_VERDICTS = CONTINUE | PAUSE | EXHAUSTED, fronts with owner
and next-action, sealed per close).

Measured reconciliation (probe_aggregate.out, 94 season yamls, s94 in
flight): the candidate's premise "earlier salvaged seasons retain LOSS"
is FALSE -- every LOSS final is a plain LOSS whose history holds no WIN
row (pin 4 re-checks the shape live). The real gap the candidate
pointed at: the WIN slot holds 5 post-stop integration wins
(s20 s30 s32 s59 s67, all stopped_stall closes), while the counts line
disclosed only the 1 post-s62 salvaged mark (s67). The landed
reconciliation is the label split: the WIN cell reads
"N WIN (I in-lane, P post-stop integration, of which M salvaged)" when
any post-stop WIN exists, total N unchanged. A plain ledger renders
byte-identical to the pre-s94 shape; the WIN mark alone (no state
json) still counts post-stop and renders the same paren split.

The stopping rule is distilled as the pack draft template
priors/templates/stopping-rule.md: four checkable clauses (empty
fronts, zero candidates twice, no operator front moved, green floor)
with the reset rule; pins 5-6 hold the seal and the parse.

Offline: fixture pins run the composer surfaces through a bounded
subprocess driver over throwaway trees; the real-ledger pin is
capture-only for the render line and asserts only season-proof
contracts (no WIN-row-then-LOSS-final shape, the sum invariant). No
pin mutates the repo, the ledger, or akar; no audit is run.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from rumpun import plugin

logger = logging.getLogger(__name__)

S94W1_TIMEOUT = 240  # bounds one driver subprocess (the task bound)

S94W1_DRIVER = '''\
"""s94 w1 pin driver: the composer's counting surfaces, one JSON payload.

stdout is the data channel (exactly one JSON line); diagnostics go to
stderr through logging. Any composer-surface error lands in the
payload's "error" key with traceback context - the pins assert on it.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import sys
import traceback
from dataclasses import fields as _dc_fields
from dataclasses import is_dataclass as _is_dataclass
from pathlib import Path

logger = logging.getLogger("s94w1-driver")


def _load_composer(repo: str):
    path = Path(repo) / "tools" / "usefulness_audit.py"
    spec = importlib.util.spec_from_file_location("usefulness_audit_s94w1", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _season_number(name: str) -> int:
    digits = "".join(ch for ch in name if ch.isdigit())
    return int(digits) if digits else -1


def main() -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    root = Path(sys.argv[1])
    repo = sys.argv[2]
    payload: dict = {"root": str(root)}
    try:
        module = _load_composer(repo)
        seasons = sorted(
            (p for p in (root / "seasons").glob("s*.yaml")),
            key=lambda p: _season_number(p.stem),
        )
        rows = []
        loss_after_win = []
        for path in seasons:
            sid = path.stem
            row = module._last_season_row(root, sid)
            status = module._season_status(root, sid)
            hist = []
            vpath = root / "runs" / sid / "verdicts.jsonl"
            if vpath.is_file():
                for raw in vpath.read_text(encoding="utf-8").splitlines():
                    if not raw.strip():
                        continue
                    try:
                        obj = json.loads(raw)
                    except ValueError:
                        hist.append("CORRUPT")
                        continue
                    if isinstance(obj, dict) and obj.get("season") == sid:
                        hist.append(str(obj.get("verdict", "")))
            final = str(row.get("verdict", "")) if row else None
            salv = bool(row and row.get("salvaged") is True)
            rows.append(
                {
                    "sid": sid,
                    "status": status,
                    "final": final,
                    "salv": salv,
                    "history": hist,
                }
            )
            if final == "LOSS" and any(v == "WIN" for v in hist):
                loss_after_win.append(sid)
        counts = module.ledger_counts(root)
        payload["slots"] = {
            f.name: getattr(counts, f.name) for f in _dc_fields(counts)
        } if _is_dataclass(counts) else dict(counts)
        payload["render"] = counts.render()
        payload["seasons"] = rows
        payload["loss_after_win"] = loss_after_win
        payload["yaml_total"] = len(seasons)
        history = [
            (r["sid"], r["final"] or "none", r["salv"])
            for r in rows
        ]
        brief = module.compose_brief(
            decade=1,
            count=len(seasons),
            run_count=len(seasons),
            drafted_count=0,
            history=history,
            design_text="sections 13-16 stub",
            counts=counts,
        )
        payload["brief"] = brief
    except Exception:  # the payload carries the reason; never silent
        payload["error"] = traceback.format_exc()
    sys.stdout.write(json.dumps(payload) + "\\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def _s94w1_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w1 workspace (pre-graft) and
    in tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


S94W1_REPO = _s94w1_repo()
S94W1_DRAFT = S94W1_REPO / ".rumpun" / "plugins" / "kancil-base-draft"


def _s94w1_driver(tmp_path: Path, tag: str, root: Path) -> dict:
    """One bounded driver subprocess; the parsed JSON payload back."""
    path = tmp_path / f"driver_{tag}.py"
    path.write_text(S94W1_DRIVER, encoding="utf-8")
    argv = [sys.executable, str(path), str(root), str(S94W1_REPO)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(S94W1_REPO / "src")
    ran = subprocess.run(
        argv, capture_output=True, text=True, timeout=S94W1_TIMEOUT,
        env=env, check=False,
    )
    assert ran.returncode == 0, (
        f"driver exited {ran.returncode}: stderr:\n{ran.stderr}\n"
        f"stdout:\n{ran.stdout}"
    )
    payload = json.loads(ran.stdout)
    assert not payload.get("error"), f"driver error:\n{payload['error']}"
    return payload


def _s94w1_fixture(tmp_path: Path, tag: str, seasons: dict) -> Path:
    """One throwaway ledger tree; the s64 w2 fixture shape.

    seasons maps sid -> {"state": {...} | None, "rows": [row, ...]}.
    A state dict writes runs/<sid>/_season/state.json; rows write
    runs/<sid>/verdicts.jsonl, one JSON object per line.
    """
    root = tmp_path / tag / "rumpun"
    for sid, spec in seasons.items():
        (root / "seasons").mkdir(parents=True, exist_ok=True)
        (root / "seasons" / f"{sid}.yaml").write_text(f"id: {sid}\n", encoding="utf-8")
        state = spec.get("state")
        if state is not None:
            state_path = root / "runs" / sid / "_season" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(state), encoding="utf-8")
        rows = spec.get("rows") or []
        if rows:
            rows_path = root / "runs" / sid / "verdicts.jsonl"
            rows_path.parent.mkdir(parents=True, exist_ok=True)
            body = "".join(json.dumps(row) + "\n" for row in rows)
            rows_path.write_text(body, encoding="utf-8")
    return root


# --- the label split ---------------------------------------------------------------


def test_s94w1_poststop_split_reads_through(tmp_path: Path) -> None:
    """A stopped WIN splits the WIN cell; the WIN total is unchanged.

    Fixture: s201 is a WIN whose season stopped_stall with no mark (the
    s30 shape), s202 a plain completed WIN, s203 a WIN stopped_stall
    with the s62 mark (the s67 shape), s204 a LOSS that stopped_stall
    (a stopped non-win stays a plain LOSS). The slot holds 3 WIN total;
    the label splits 1 in-lane + 2 post-stop integration, of which 1
    salvaged; the brief carries the same split.
    """
    seasons = {
        "s201": {
            "state": {"status": "stopped_stall"},
            "rows": [{"season": "s201", "verdict": "WIN"}],
        },
        "s202": {
            "state": {"status": "completed"},
            "rows": [{"season": "s202", "verdict": "WIN"}],
        },
        "s203": {
            "state": {"status": "stopped_stall"},
            "rows": [{"season": "s203", "verdict": "WIN", "salvaged": True}],
        },
        "s204": {
            "state": {"status": "stopped_stall"},
            "rows": [{"season": "s204", "verdict": "LOSS"}],
        },
    }
    root = _s94w1_fixture(tmp_path, "split", seasons)
    data = _s94w1_driver(tmp_path, "split", root)
    slots = data["slots"]
    assert slots["slots"]["WIN"] == 3, slots
    assert slots["poststop"]["WIN"] == 2, slots
    assert slots["salvaged"]["WIN"] == 1, slots
    assert slots["slots"]["LOSS"] == 1, slots
    render = data["render"]
    assert render == (
        "season verdict slots: 3 WIN (1 in-lane, 2 post-stop integration, "
        "of which 1 salvaged), 1 LOSS, 0 NEUTRAL, 0 INVALID, 0 MISSING; "
        "0 running"
    ), render
    assert "(1 in-lane, 2 post-stop integration" in data["brief"], data["brief"]


def test_s94w1_inlane_wins_render_unchanged(tmp_path: Path) -> None:
    """A ledger with no post-stop WIN renders the pre-s94 WIN cell.

    Two plain completed WINs: no in-lane label, no salvage mention, the
    poststop slot reads zero.
    """
    seasons = {
        "s201": {
            "state": {"status": "completed"},
            "rows": [{"season": "s201", "verdict": "WIN"}],
        },
        "s202": {
            "state": {"status": "completed"},
            "rows": [{"season": "s202", "verdict": "WIN"}],
        },
    }
    root = _s94w1_fixture(tmp_path, "inlane", seasons)
    data = _s94w1_driver(tmp_path, "inlane", root)
    assert data["slots"]["poststop"]["WIN"] == 0, data["slots"]
    render = data["render"]
    assert "2 WIN" in render, render
    assert "in-lane" not in render, render
    assert "salvaged" not in render, render


def test_s94w1_mark_only_without_state_counts_poststop(tmp_path: Path) -> None:
    """A marked WIN with no readable state still counts post-stop.

    The s62 mark alone (no state.json) counts the WIN as post-stop
    integration; the paren split renders with a zero in-lane count.
    """

    seasons = {
        "s206": {
            "state": None,
            "rows": [{"season": "s206", "verdict": "WIN", "salvaged": True}],
        },
    }
    root = _s94w1_fixture(tmp_path, "markonly", seasons)
    data = _s94w1_driver(tmp_path, "markonly", root)
    assert data["slots"]["poststop"]["WIN"] == 1, data["slots"]
    render = data["render"]
    assert "1 WIN (0 in-lane, 1 post-stop integration, of which 1 salvaged)" in render, render


# --- the real ledger, capture-only -------------------------------------------------


def test_s94w1_real_ledger_holds_no_loss_after_win(tmp_path: Path, caplog) -> None:
    """The candidate's premise re-checks live: no WIN row retains LOSS.

    Against the real campaign ledger: no season's season-level history
    holds a WIN row while its final verdict is LOSS (the alleged
    aggregate inconsistency shape). The render line is logged for the
    notes (capture-only, values never asserted). The sum invariant
    (slots + running == season yamls) is asserted - the standing s64
    contract.
    """
    with caplog.at_level(logging.INFO):
        data = _s94w1_driver(tmp_path, "real", S94W1_REPO / ".rumpun")
    logger.info("real ledger render: %s", data["render"])
    assert data["loss_after_win"] == [], (
        "the alleged inconsistency exists: seasons with a WIN row "
        f"retaining a LOSS final: {data['loss_after_win']}"
    )
    slots = data["slots"]
    total = sum(slots["slots"].values()) + len(slots["running"])
    assert total == data["yaml_total"], (total, data["yaml_total"], data["render"])


# --- the stopping-rule template ----------------------------------------------------


def test_s94w1_draft_pack_seals_the_stopping_rule() -> None:
    """The draft pack seals digest-verified with the template aboard.

    The digest is probed live (plugin.priors_digest), never hardcoded:
    a template added without re-sealing turns this pin red, and so does
    a sealed digest that no longer matches the tree. plugin_lint stays
    at zero findings.
    """
    template = S94W1_DRAFT / "priors" / "templates" / "stopping-rule.md"
    assert template.is_file(), template
    manifest = plugin.load_manifest(S94W1_DRAFT)
    computed = plugin.priors_digest(S94W1_DRAFT)
    assert manifest.get("digest") == computed, (manifest.get("digest"), computed)
    assert plugin.plugin_lint(S94W1_DRAFT, manifest) == [], "lint findings"


def test_s94w1_stopping_rule_template_parses() -> None:
    """The template's parse contract: headings, clauses, vocabulary.

    The three sibling-shaped headings stand in order; the four threshold
    clauses stand in order inside the threshold section; the verdict
    vocabulary and the reset rule are named; no season-id token and no
    absolute path survives (the lint regexes, reused verbatim).
    """
    template = S94W1_DRAFT / "priors" / "templates" / "stopping-rule.md"
    text = template.read_text(encoding="utf-8")
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == [
        "## What it is",
        "## The threshold",
        "## How to apply",
    ], headings
    threshold = text.split("## The threshold", 1)[1].split("## How to apply", 1)[0]
    clauses = [
        "- Empty fronts:",
        "- Zero candidates twice:",
        "- No operator front moved:",
        "- Green floor:",
    ]
    positions = [threshold.find(clause) for clause in clauses]
    assert all(p >= 0 for p in positions), f"missing clause: {threshold}"
    assert positions == sorted(positions), positions
    assert "CONTINUE | PAUSE | EXHAUSTED" in text, text
    assert "resets the count" in threshold, threshold
    from rumpun.plugin import ABS_PATH_RE, SID_TOKEN_RE

    assert SID_TOKEN_RE.search(text) is None, "season-id token in pack text"
    assert ABS_PATH_RE.search(text) is None, "absolute path in pack text"
