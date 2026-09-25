"""s64 w2 pins — the composer's counts read the whole ledger.

Spec-first pins (red against current code) for the s64 count-honesty
contract (w1 brief .rumpun/runs/s64/w1/prompt.md; ledger anchors
usefulness-decade-5 and audit-41 — decade-5's residual "Salvaged stopped
seasons earn WIN alongside completed seasons. Aggregate verdicts obscure
execution reliability and intervention costs." is the residual this
lands). Spec anchors, the measured red set, and surface assumptions:
.rumpun/runs/s64/w2/notes.md.

Contract these pins hold — the composer (tools/usefulness_audit.py)
grows a slot-counting surface over the ledger root that classifies every
season yaml into exactly one slot — WIN, LOSS, NEUTRAL, INVALID,
running, or MISSING — carries the s62 salvage marks ("salvaged": true
on the verdict row; audit.py F3's "X WIN (Y salvaged)" is the agreed
split shape) through to the counts, and the composed auditor brief
names those counts. Every pin runs a bounded subprocess driver
(S64W2_TIMEOUT = 240s, the task bound) that imports the composer by
path and calls its surfaces read-only over a throwaway fixture .rumpun
tree (pins 1-2) or the real campaign ledger (pin 3, capture-only): no
pin mutates the repo, the ledger, or akar.

Why a driver and not the composer CLI: the composer's decade gate
refuses before composing when the ledger owes no decade (due_decade is
None when floor(count / SEASONS_PER_DECADE) == 0), so a spec-sized
6-season fixture can never reach compose_brief through run(); the pins
bind the counting surfaces directly and leave the full CLI path to w1.

1. The arithmetic: a fixture ledger of 6 seasons (4 verdict rows, 1
   running, 1 missing) yields 4 classified + 1 running + 1 missing,
   the slot surface reports each slot, the six slots sum to the season
   total, and the composed brief names the counts — nothing blurs into
   the old run/drafted-only split.
2. The salvaged split: a fixture with one stopped_stall-salvaged WIN
   ("salvaged": true on the verdict row, the s62 mark) shows the split
   in the counts — the win total and the salvaged-of-win read as
   distinct slots; the s62 marks read through.
3. The real ledger's counts are reported, not asserted: the driver runs
   the slot surface over the real campaign ledger and the pin logs the
   counts for the notes; only the surface's structural shape is
   asserted — every value assertion lives in the fixture pins.


Red history (measured 2026-09-16; logs /tmp/s64w2-pytest-run*.log):
against season-start git da2f444 all three pins failed on the right
spec reason — the only counting surface was season_split's
(run, drafted-only) tuple, so the fixtures read "(5, 1)" and "(3, 1)"
and the real ledger "(63, 1)" (64 pattern-matched season yamls; the
dir also holds _template.yaml), with no classified slots, no salvage
split, and a brief naming none of the counts (run1). Against w1's
landed ledger_counts/LedgerCounts and the counts render in
compose_brief, all three pass (run4: 3 passed in 0.63s). One
mid-landing driver defect sat between those measurements: importlib
loading without sys.modules registration breaks dataclass processing
on py3.12+ (KW_ONLY resolution) — fixed in the driver, never a spec
reason. Surface bindings that reconciled to the landed shapes: the
candidate list hit ledger_counts; compose_brief's required counts
param is auto-filled with the counter's own result; history rows are
the landed (sid, verdict, salvaged) triples.
Grafting: drop this file into tests/ as the season's pins file. Helpers
carry the _s64w2_ prefix, so nothing collides with existing defs. No
pin touches the real repo state: fixture trees live under pytest
tmp_path and the driver writes nothing anywhere. Surface assumptions
the harness reconciles at merge if w1's shapes differ: (a) the slot
counter binds by candidate name (season_slots, season_counts,
ledger_counts, count_season_slots, season_split); (b) compose_brief is
called with today's kwarg names (decade, count, run_count,
drafted_count, history, design_text), skipping unknown optionals and
refusing unfillable required params.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

S64W2_TIMEOUT = 240  # bounds one driver subprocess (the task bound)
S64W2_DRIVER = '''\
"""s64 w2 pin driver: the composer's surfaces, read-only, one JSON payload.

stdout is the data channel (exactly one JSON line); diagnostics go to
stderr through logging. Any composer-surface error lands in the
payload's "error" key with traceback context — the pins assert on it.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import logging
import sys
import traceback
from dataclasses import fields as _dc_fields
from dataclasses import is_dataclass as _is_dataclass
from pathlib import Path

logger = logging.getLogger("s64w2-driver")

# First callable hit wins; the candidate list is documented in the pins
# file docstring so the harness can reconcile cheaply at merge.
_SLOT_CANDIDATES = (
    "season_slots",
    "season_counts",
    "ledger_counts",
    "count_season_slots",
    "season_split",
)


def _load_composer(repo: str):
    path = Path(repo) / "tools" / "usefulness_audit.py"
    spec = importlib.util.spec_from_file_location("usefulness_audit_s64w2", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _bind_slot_counter(module):
    for name in _SLOT_CANDIDATES:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return name, candidate
    return None, None


def _to_mapping(result):
    if _is_dataclass(result) and not isinstance(result, type):
        return {f.name: getattr(result, f.name) for f in _dc_fields(result)}
    if hasattr(result, "_asdict"):
        return dict(result._asdict())
    if isinstance(result, dict):
        return {str(k): v for k, v in result.items()}
    return None


def _brief_text(module, kwargs_json: str, root, counts_obj):
    """The composed brief text, filling the landed parameter shapes.

    Fixture kwargs fill today's names (decade, count, run_count,
    drafted_count, history, design_text); the landed counts parameter
    gets the counter's own result and root gets the ledger root. A
    required param still unfillable refuses in the payload, never
    silently.
    """
    func = getattr(module, "compose_brief", None)
    if not callable(func):
        return None, "no compose_brief callable on the composer"
    params = inspect.signature(func).parameters
    wanted = json.loads(kwargs_json)
    special = {"counts": counts_obj, "root": root}
    known = {}
    for name in params:
        if name in wanted:
            known[name] = wanted[name]
        elif name in special and special[name] is not None:
            known[name] = special[name]
    unfillable = [
        name
        for name, param in params.items()
        if param.default is inspect.Parameter.empty
        and name not in known
        and param.kind
        in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    ]
    if unfillable:
        return None, f"compose_brief needs params the driver cannot fill: {unfillable}"
    try:
        return str(func(**known)), ""
    except Exception:  # the payload carries the reason; never silent
        return None, "compose_brief call failed:\\n" + traceback.format_exc()


def main() -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    mode, root, repo = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    kwargs_json = sys.argv[4] if len(sys.argv) > 4 else "{}"
    payload: dict = {"mode": mode, "root": str(root)}
    try:
        module = _load_composer(repo)
        name, counter = _bind_slot_counter(module)
        if counter is None:
            payload["error"] = "no slot-counting surface on the composer"
        else:
            payload["surface"] = name
            result = counter(root)
            mapping = _to_mapping(result)
            payload["slots"] = mapping
            payload["raw"] = "" if mapping is not None else repr(result)
            if mode == "fixture":
                payload["brief"], payload["brief_error"] = _brief_text(
                    module, kwargs_json, root, result
                )
    except Exception:  # the payload carries the reason; never silent
        payload["error"] = traceback.format_exc()
    sys.stdout.write(json.dumps(payload) + "\\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


# --- helpers -----------------------------------------------------------------------


def _s64w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


S64W2_REPO = _s64w2_repo()


def _s64w2_fixture(tmp_path: Path, tag: str, seasons: dict) -> Path:
    """One throwaway .rumpun ledger tree: season yamls, runs state, rows.

    seasons maps sid -> {"state": {...} | None, "rows": [row, ...]}. A
    state dict writes runs/<sid>/_season/state.json; rows write
    runs/<sid>/verdicts.jsonl, one JSON object per line (the s62 mark is
    "salvaged": true on the row).
    """
    root = tmp_path / tag / "rumpun"
    for sid, spec in seasons.items():
        (root / "seasons").mkdir(parents=True, exist_ok=True)
        yaml_path = root / "seasons" / f"{sid}.yaml"
        yaml_path.write_text(f"id: {sid}\n", encoding="utf-8")
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


def _s64w2_driver(
    tmp_path: Path, mode: str, root: Path, brief_kwargs: dict | None
) -> dict:
    """One bounded driver subprocess; the parsed JSON payload back."""
    path = tmp_path / f"driver_{mode}.py"
    path.write_text(S64W2_DRIVER, encoding="utf-8")
    argv = [sys.executable, str(path), mode, str(root), str(S64W2_REPO)]
    if brief_kwargs is not None:
        argv.append(json.dumps(brief_kwargs))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(S64W2_REPO / "src")
    ran = subprocess.run(
        argv, capture_output=True, text=True, timeout=S64W2_TIMEOUT,
        env=env, check=False,
    )
    assert ran.returncode == 0, (
        f"driver exited {ran.returncode}: stderr:\n{ran.stderr}\nstdout:\n{ran.stdout}"
    )
    return json.loads(ran.stdout)


def _s64w2_named(text: str, word: str, number: int) -> bool:
    """True when word and number stand near each other, either order.

    Tolerates "1 WIN", "WIN: 1", "1 win," — the s62 agreed shapes —
    without letting sid tokens (s101) fake a standalone count.
    """
    pattern = (
        rf"(?i)\b{word}\b[^0-9]{{0,15}}\b{number}\b"
        rf"|\b{number}\b[^0-9]{{0,15}}\b{word}\b"
    )
    return re.search(pattern, text) is not None


def _s64w2_slot(slots: dict, name: str, *needles: str) -> int | None:
    """The slot count for name, flattened case-insensitively.

    Handles the landed shapes: a flat mapping, or the nested
    LedgerCounts mapping (slots/salvaged sub-dicts, running/missing sid
    lists). UPPERCASE slot keys match lowercase names; a nested dict
    namespaces as parent.child (salvaged.win) plus a parent total; a
    list counts its items (len of the running/missing sids). The exact
    flat name wins, then slots.<name>, then substring needles.
    """
    flat: dict[str, int] = {}
    for key, value in slots.items():
        low = str(key).lower()
        if isinstance(value, dict):
            total = 0
            for inner_key, inner in value.items():
                try:
                    inner_count = int(inner)
                except (TypeError, ValueError):
                    continue
                flat[f"{low}.{str(inner_key).lower()}"] = inner_count
                total += inner_count
            flat[low] = total
        elif isinstance(value, list):
            flat[low] = len(value)
        else:
            try:
                flat[low] = int(value)
            except (TypeError, ValueError):
                continue
    if name in flat:
        return flat[name]
    if f"slots.{name}" in flat:
        return flat[f"slots.{name}"]
    for key in sorted(flat):
        if all(n in key for n in (needles or (name,))):
            return flat[key]
    return None


# --- pin 1: the counts sum to the season total, and the counts say so --------------


def test_s64w2_slot_counts_sum_to_the_season_total(tmp_path: Path) -> None:
    """Six fixture seasons classify 4 + 1 + 1, and the brief names it.

    The fixture ledger holds six season yamls: s101-s104 carry verdict
    rows (WIN, LOSS, NEUTRAL, INVALID) with done state files, s105 runs
    (state.json status "running", no verdict row), s106 is missing (no
    state, no rows). The slot surface must report each of the six slots
    as exactly 1, the slots must sum to the season total 6 (exactly one
    slot per season yaml), and the composed brief must name the counts
    — classified 4, running 1, missing 1, each verdict 1, total 6 — so
    nothing blurs into the old run/drafted-only split. On git da2f444
    the binding falls to season_split's (run, drafted-only) tuple: no
    slots, and a brief that says "1 drafted-only" where the counts must
    say "1 missing" — red until w1's counts land.
    """
    seasons = {
        "s101": {
            "state": {"status": "done"},
            "rows": [{"season": "s101", "verdict": "WIN"}],
        },
        "s102": {
            "state": {"status": "done"},
            "rows": [{"season": "s102", "verdict": "LOSS"}],
        },
        "s103": {
            "state": {"status": "done"},
            "rows": [{"season": "s103", "verdict": "NEUTRAL"}],
        },
        "s104": {
            "state": {"status": "done"},
            "rows": [{"season": "s104", "verdict": "INVALID"}],
        },
        "s105": {"state": {"status": "running"}, "rows": []},
        "s106": {},
    }
    root = _s64w2_fixture(tmp_path, "slot-sum", seasons)
    brief_kwargs = {
        "decade": 1,
        "count": 6,
        "run_count": 5,
        "drafted_count": 1,
        "history": [
            ["s101", "WIN", False],
            ["s102", "LOSS", False],
            ["s103", "NEUTRAL", False],
            ["s104", "INVALID", False],
            ["s105", "none", False],
            ["s106", "none", False],
        ],
        "design_text": "fixture design text",
    }
    data = _s64w2_driver(tmp_path, "fixture", root, brief_kwargs)
    assert not data.get("error"), f"driver error:\n{data['error']}"
    slots = data.get("slots")
    assert isinstance(slots, dict) and slots, (
        f"the slot surface {data.get('surface')!r} carries no classified "
        f"slots over the 6-season fixture (raw: {data.get('raw')!r}); "
        f"wanted win/loss/neutral/invalid/running/missing"
    )
    found = {name: _s64w2_slot(slots, name) for name in
             ("win", "loss", "neutral", "invalid", "running", "missing")}
    absent = [name for name, count in found.items() if count is None]
    assert not absent, (
        f"the slot surface {data.get('surface')!r} carries no {absent} "
        f"slots: {slots}"
    )
    for name, count in found.items():
        assert count == 1, (
            f"slot {name} counts {count}, want exactly 1 (the fixture "
            f"holds one {name} season): {slots}"
        )
    slot_sum = sum(count for count in found.values() if count is not None)
    assert slot_sum == 6, (
        f"the six slots sum to {slot_sum}, want 6: every season yaml "
        f"contributes exactly one slot: {slots}"
    )
    classified = _s64w2_slot(slots, "classified", "classif")
    if classified is not None:
        assert classified == 4, f"classified counts {classified}, want 4: {slots}"
    total = _s64w2_slot(slots, "total", "total")
    if total is not None:
        assert total == 6, f"total counts {total}, want 6: {slots}"
    brief = data.get("brief")
    assert brief, (
        f"no brief text captured from the composer: {data.get('brief_error')}"
    )
    for word, number in (
        ("win", 1), ("loss", 1), ("neutral", 1), ("invalid", 1),
        ("running", 1), ("missing", 1), ("total", 6),
    ):
        assert _s64w2_named(brief, word, number), (
            f"the brief does not name {word} {number}; the counts must "
            f"say so, nothing blurs. brief:\n{brief}"
        )
    if re.search(r"(?i)\bclassified\b", brief):
        assert _s64w2_named(brief, "classified", 4), (
            f"the brief names classified without the count 4. brief:\n{brief}"
        )
    logger.info(
        "pin 1 held: 6 seasons classify 4 classified + 1 running + 1 "
        "missing, slots sum to the total, brief names the counts"
    )


# --- pin 2: the salvaged split reads through to the counts -------------------------


def test_s64w2_salvaged_split_reads_through(tmp_path: Path) -> None:
    """One stopped_stall-salvaged WIN splits the counts, s62 marks on.

    The fixture holds four seasons: s201 is a WIN whose verdict row
    carries "salvaged": true (the s62 mark for a stopped_stall
    salvage), s202 a plain WIN, s203 a LOSS, s204 missing. The counts
    must carry the split: win totals 2, the salvaged slot reads 1 (of
    the wins), loss 1, missing 1, and the slots sum to 4. On git
    da2f444 the counts drop both the verdict split and the salvaged
    mark entirely (season_split sees only run/drafted presence) — red
    until w1's counts carry the split.
    """
    seasons = {
        "s201": {
            "state": {"status": "done"},
            "rows": [{"season": "s201", "verdict": "WIN", "salvaged": True}],
        },
        "s202": {
            "state": {"status": "done"},
            "rows": [{"season": "s202", "verdict": "WIN"}],
        },
        "s203": {
            "state": {"status": "done"},
            "rows": [{"season": "s203", "verdict": "LOSS"}],
        },
        "s204": {},
    }
    root = _s64w2_fixture(tmp_path, "salvage-split", seasons)
    data = _s64w2_driver(tmp_path, "fixture", root, None)
    assert not data.get("error"), f"driver error:\n{data['error']}"
    slots = data.get("slots")
    assert isinstance(slots, dict) and slots, (
        f"the slot surface {data.get('surface')!r} carries no classified "
        f"slots over the salvage fixture (raw: {data.get('raw')!r})"
    )
    win = _s64w2_slot(slots, "win")
    salvaged = _s64w2_slot(slots, "salvaged", "salvage")
    assert win is not None, f"no win slot: {slots}"
    assert salvaged is not None, (
        f"the s62 salvage marks do not read through to the counts "
        f"(no salvaged slot on {data.get('surface')!r}): {slots}"
    )
    assert win == 2, f"win counts {win}, want 2 (one salvaged, one plain): {slots}"
    assert salvaged == 1, (
        f"salvaged counts {salvaged}, want 1 (the stopped_stall mark "
        f"on s201's row): {slots}"
    )
    assert salvaged < win, (
        f"the split must stay visible: salvaged {salvaged} of win {win}"
    )
    for name, want in (("loss", 1), ("missing", 1)):
        count = _s64w2_slot(slots, name)
        assert count == want, f"slot {name} counts {count}, want {want}: {slots}"
    slot_sum = sum(
        count if (count := _s64w2_slot(slots, name)) is not None else 0
        for name in ("win", "loss", "neutral", "invalid", "running", "missing")
    )
    assert slot_sum == 4, (
        f"the slots sum to {slot_sum}, want 4: every season yaml "
        f"contributes exactly one slot: {slots}"
    )
    logger.info(
        "pin 2 held: the salvaged split reads through (2 win, 1 salvaged)"
    )


# --- pin 3: the real ledger's counts are captured, not asserted --------------------


def test_s64w2_real_ledger_counts_captured_for_notes(tmp_path: Path) -> None:
    """The composer's counts over the real ledger land in the run log.

    The driver binds the slot surface and runs it over the real
    campaign ledger (.rumpun) read-only; the pin logs the full payload
    so notes.md captures the real counts, and asserts only the
    surface's structural shape — the six slots exist. No real value is
    asserted here: the fixture pins hold the arithmetic.
    """
    data = _s64w2_driver(tmp_path, "real", S64W2_REPO / ".rumpun", None)
    logger.info(
        "real-ledger counts (captured for notes.md): %s",
        json.dumps(data, sort_keys=True),
    )
    assert not data.get("error"), f"driver error:\n{data['error']}"
    slots = data.get("slots")
    assert isinstance(slots, dict) and slots, (
        f"the slot surface {data.get('surface')!r} carries no classified "
        f"slots over the real ledger (raw: {data.get('raw')!r})"
    )
    for name in ("win", "loss", "neutral", "invalid", "running", "missing"):
        assert _s64w2_slot(slots, name) is not None, (
            f"the slot surface {data.get('surface')!r} carries no {name} "
            f"slot over the real ledger: {slots}"
        )
    logger.info("pin 3 held: real-ledger counts captured, shape intact")
