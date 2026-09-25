"""s58 w2 pins — the epic rollup, pinned before it exists.

Spec-first pins (red against current code) for the s58 contract (season
goal .rumpun/seasons/s58.yaml; w1's brief .rumpun/prompts/dev/w1-epics.md;
operator directive seq 5: epics as DATA, records stay append-only and
byte-identical; ledger anchors 2026-09-16_s56-harvest and
2026-09-16_audit-40 -- the rollup reads what harvest writes). Spec
anchors, the interface contract, and the measured red set:
.rumpun/runs/s58/w2/notes.md.

Interface these pins hold:

    rumpun epics [--init]

cwd inside the campaign (the verb resolves the project from cwd like
every verb). The declaration lives at .rumpun/epics.yaml: mapping epic
id -> {title, goal, seasons: [...]}. Verdicts are read where harvest
writes them: the season-level rows in .rumpun/runs/<sid>/verdicts.jsonl,
and run state from .rumpun/runs/<sid>/_season/state.json. Every pin
builds its own miniature campaign under pytest tmp_path and runs the verb
as a bounded subprocess (S58W2_TIMEOUT, the spec's 120s bound). No pin
ever writes the real ledger: rendering is stdout-only data output (the
season-list convention), refusals exit nonzero naming what is wrong, and
a missing epics.yaml is a flat stdout hint at exit 0, never an error.

Red against current main (cli.py carries no `epics` verb -- argparse
rejects it, exit 2), green at merge via w1's wiring. Graft: land this
file in tests/ as-is (additions-only; existing suite files stay
untouched). Helpers carry the _s58w2_ prefix, so nothing collides with
existing defs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

S58W2_TIMEOUT = 120  # the spec bound for one verb run

S58W2_ALL_IDS = ("s61", "s62", "s63", "s64", "s65")
# season id -> harvest verdict for members WITH run state; s65 stays stateless
S58W2_VERDICTS = {"s61": "WIN", "s62": "LOSS", "s63": "WIN", "s64": "INVALID"}

S58W2_EPICS_TEXT = """\
epic-a:
  title: Alpha arc
  goal: roll the alpha arc verdicts
  seasons: [s61, s62]
epic-b:
  title: Beta arc
  goal: honesty when run state is missing
  seasons: [s63, s64, s65]
"""

# s63 in both epics: the duplicate-membership lint input (spec 2)
S58W2_DUP_TEXT = """\
epic-a:
  title: Alpha arc
  goal: roll the alpha arc verdicts
  seasons: [s61, s62, s63]
epic-b:
  title: Beta arc
  goal: honesty when run state is missing
  seasons: [s63, s64, s65]
"""

# s99 has no .rumpun/seasons/s99.yaml (the builder writes s61-s65 only)
S58W2_NOYAML_TEXT = """\
epic-a:
  title: Alpha arc
  goal: roll the alpha arc verdicts
  seasons: [s61, s62]
epic-b:
  title: Beta arc
  goal: honesty when run state is missing
  seasons: [s63, s64, s99]
"""


def _s58w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and
    grafted into tests/ (post-graft), and inside a clone: both sit under
    a pyproject.toml root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s58w2_env() -> dict[str, str]:
    """The subprocess env: the tree under test's src/ first on PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s58w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s58w2_run(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    """One bounded `python -m rumpun <argv>` run with cwd inside the campaign."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(cwd),
            env=_s58w2_env(),
            capture_output=True,
            text=True,
            timeout=S58W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"rumpun {' '.join(argv)} exceeded {S58W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s58w2_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _s58w2_campaign(root: Path, epics_text: str | None) -> Path:
    """The s58 fixture campaign under root.

    Five member seasons: s61-s64 with terminal run state and a harvest
    verdict row (WIN, LOSS, WIN, INVALID), s65 with a season yaml but no
    run state at all. The ledger carries one record, one directive line,
    and the append lock. epics_text None builds the missing-declaration
    world; s99 (pin 3) exists nowhere.
    """
    rump = root / ".rumpun"
    _s58w2_write(rump / "rumpun.yaml", "campaign: s58w2-epics-fixture\n")
    for sid in S58W2_ALL_IDS:
        _s58w2_write(rump / "seasons" / f"{sid}.yaml", f"id: {sid}\n")
    for sid, verdict in S58W2_VERDICTS.items():
        state = {
            "id": sid,
            "status": "completed",
            "started_at": 1789500000.0,
            "ended_at": 1789500060.0,
            "agents": {},
        }
        _s58w2_write(
            rump / "runs" / sid / "_season" / "state.json",
            json.dumps(state, indent=2) + "\n",
        )
        row = {
            "season": sid,
            "verdict": verdict,
            "metric": "",
            "band": "",
            "observed": "",
            "implies": "s58w2 fixture row",
        }
        _s58w2_write(rump / "runs" / sid / "verdicts.jsonl", json.dumps(row) + "\n")
    _s58w2_write(
        rump / "ledger" / "2026-09-16_s61-harvest.md",
        "# akar record: s61-harvest\nid: s61-harvest\ndate: 2026-09-16\n"
        "title: season s61 harvest\nverdict: WIN\nimplies: fixture row\n",
    )
    directive = {"from": "operator", "seq": 0, "status": "pending", "text": "fixture"}
    _s58w2_write(rump / "ledger" / "directives.jsonl", json.dumps(directive) + "\n")
    _s58w2_write(rump / "ledger" / "append.lock", "")
    if epics_text is not None:
        _s58w2_write(rump / "epics.yaml", epics_text)
    return root


def _s58w2_epic_line(stdout: str, epic_id: str) -> str:
    """The single rendered stdout line carrying epic_id."""
    hits = [ln for ln in stdout.splitlines() if re.search(rf"\b{epic_id}\b", ln)]
    assert len(hits) == 1, (
        f"expected exactly one rendered line for {epic_id}, got {len(hits)}:\n{stdout}"
    )
    return hits[0]


def _s58w2_ledger_digest(root: Path) -> dict[str, str]:
    """rel path -> sha256 for every file under the fixture's ledger dir."""
    ledger = root / ".rumpun" / "ledger"
    return {
        str(p.relative_to(ledger)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ledger.rglob("*"))
        if p.is_file()
    }


# --- spec 1: the declared two-epic rollup -------------------------------------


def test_s58w2_epics_rolls_up_two_declared_epics(tmp_path: Any) -> None:
    """`rumpun epics` renders one line per epic: id, span, rollup, title.

    epic-a (s61 WIN, s62 LOSS): "1 WIN / 1 LOSS / 0 other" over the
    s61-s62 span. epic-b (s63 WIN, s64 INVALID, s65 stateless):
    "1 WIN / 0 LOSS / 1 other" -- the INVALID verdict falls into other --
    over the s63-s65 span. s65 contributes no verdict (an exact rollup
    match rejects the fabricated count) and the line carries the honest
    "no state" mark (spec 3's honesty clause).
    """
    root = _s58w2_campaign(tmp_path / "fx", S58W2_EPICS_TEXT)
    proc = _s58w2_run(root, "epics")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    line_a = _s58w2_epic_line(proc.stdout, "epic-a")
    assert re.search(r"s61[^a-z0-9]+s62", line_a), line_a
    assert re.search(r"(?<![0-9])1\s+WIN\s*/\s*1\s+LOSS\s*/\s*0\s+other\b", line_a)
    assert "Alpha arc" in line_a, line_a
    line_b = _s58w2_epic_line(proc.stdout, "epic-b")
    assert re.search(r"s63[^a-z0-9]+s65", line_b), line_b
    assert re.search(r"(?<![0-9])1\s+WIN\s*/\s*0\s+LOSS\s*/\s*1\s+other\b", line_b)
    assert "Beta arc" in line_b, line_b
    assert "no state" in line_b, line_b


# --- spec 2: membership lints out loudly --------------------------------------


def test_s58w2_duplicate_membership_lints_out(tmp_path: Any) -> None:
    """`rumpun epics` with s63 in both epics refuses nonzero, naming all three."""
    root = _s58w2_campaign(tmp_path / "fx", S58W2_DUP_TEXT)
    proc = _s58w2_run(root, "epics")
    streams = proc.stdout + proc.stderr
    assert proc.returncode != 0, streams
    for token in ("s63", "epic-a", "epic-b"):
        assert token in streams, f"the lint refusal must name {token}:\n{streams}"


def test_s58w2_member_without_season_yaml_lints_out(tmp_path: Any) -> None:
    """`rumpun epics` with member s99 (no season yaml) refuses nonzero naming s99."""
    root = _s58w2_campaign(tmp_path / "fx", S58W2_NOYAML_TEXT)
    proc = _s58w2_run(root, "epics")
    streams = proc.stdout + proc.stderr
    assert proc.returncode != 0, streams
    assert "s99" in streams, f"the lint refusal must name the member:\n{streams}"


# --- spec 3: the missing declaration is a hint, not an error ------------------


def test_s58w2_missing_epics_yaml_hints_and_exits_zero(tmp_path: Any) -> None:
    """No epics.yaml: one flat stdout hint naming epics.yaml, exit 0."""
    root = _s58w2_campaign(tmp_path / "fx", None)
    proc = _s58w2_run(root, "epics")
    streams = proc.stdout + proc.stderr
    assert proc.returncode == 0, streams
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert len(lines) == 1, proc.stdout
    assert "epics.yaml" in lines[0], proc.stdout


# --- spec 4: the ledger is never written --------------------------------------


def test_s58w2_verb_and_init_leave_ledger_byte_identical(tmp_path: Any) -> None:
    """The verb and `epics --init` never change any ledger byte.

    Directive seq 5: records stay append-only and byte-identical, no
    merging or rewriting of ledger history. Two campaigns: the declared
    one runs the plain verb (renders, reads verdict rows and states);
    the fresh one runs --init, which must exit 0 and scaffold
    .rumpun/epics.yaml from the season yamls. Before/after sha256
    digests over every ledger file must be equal through both runs.
    """
    declared = _s58w2_campaign(tmp_path / "declared", S58W2_EPICS_TEXT)
    before = _s58w2_ledger_digest(declared)
    assert before, "fixture ledger is empty"
    proc = _s58w2_run(declared, "epics")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _s58w2_ledger_digest(declared) == before, "the verb mutated the ledger"
    fresh = _s58w2_campaign(tmp_path / "fresh", None)
    before_init = _s58w2_ledger_digest(fresh)
    init_proc = _s58w2_run(fresh, "epics", "--init")
    init_streams = init_proc.stdout + init_proc.stderr
    assert init_proc.returncode == 0, init_streams
    assert (fresh / ".rumpun" / "epics.yaml").is_file(), (
        "epics --init did not create .rumpun/epics.yaml"
    )
    assert _s58w2_ledger_digest(fresh) == before_init, "--init mutated the ledger"
