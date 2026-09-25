"""s49 w2 pins - the superseded-repro skip retires the s22 m5 drift row.

Spec sources: akar records audit-37 + s48-harvest, and the runner w1
owns (tools/replay_corpus.py). audit-37 re-proposes the s22 m5 DRIFT
candidate every audit ("band: WIN when s22/w1-repro-m5.py is updated or
re-sealed to current main behavior"); s48-harvest rules the arming
correct but already paid: "the re-seal landed" at evidence/s48/
(w1-repro.py), "and the drift row is retired". The runner still adapts
and runs the superseded script, so the DRIFT row and its audit
candidate never retire. These pins specify the retirement:

1. the runner's matrix carries a SKIP row for s22/w1-repro-m5.py citing
   the supersession (the s48 re-seal at evidence/s48/);
2. the audit after the skip carries no s22 m5 DRIFT candidate;
3. the other five repros still run and pass (holdfast: green today);
4. regression: the existing suite stays green. Verified out-of-band, as
   in the s30 pin-5 precedent: notes.md carries the suite evidence; no
   test runs the suite from inside itself.

Measured red set (current main 6876de8): pins 1-2 red for the spec
reason, pin 3 green. Full evidence in .rumpun/runs/s49/w2/notes.md.

Mechanics: pins 1-3 drive the REAL runner via subprocess (bounded at
120s) with --out-dir into a tmp dir, so the runner reads the real
evidence tree read-only and writes nothing into the repo. Pin 2 feeds
that fresh matrix to audit.run_audit on the s30 fixture ledger, so no
real akar record is appended.

Grafting: land this file in tests/ as-is (additions-only; existing
suite files stay untouched and their tests stay green). Helpers carry
the _s49w2_ prefix so nothing collides with existing defs.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from rumpun import audit as audit_mod

S49W2_M5_REL = "s22/w1-repro-m5.py"

# The five adapter rows that must keep running and passing (pin 3).
S49W2_OTHER_REPROS = (
    "s18/w1-h6-loop.py",
    "s18/w1-warn-repro.py",
    "s19/w1-repro-h2-h3.py",
    "s20/w1-repro.py",
    "s22/w1-repro-m1.py",
)

S49W2_RUNNER_TIMEOUT_S = 120

S49W2_RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

# The season fixture is the suite's s30 audit fixture, renamed. Two
# seasons with an execute/evaluate pipeline; runs/s1 completed with its
# state.json; runs/s2 empty.
S49W2_AUDIT_SEASON = """\
id: {sid}
goal: "fixture"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    rollback: "git revert"
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: verdicts.jsonl
benih:
  - name: w1
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""


def _s49w2_repo_root() -> Path:
    """The repo root: the first ancestor of this file holding src/rumpun.

    Holds both pre-graft (the pins live under .rumpun/runs/s49/w2/ inside
    the repo) and post-graft (tests/).
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "src" / "rumpun").is_dir() and (
            candidate / "tools" / "replay_corpus.py"
        ).is_file():
            return candidate
    msg = "no ancestor of the pins file holds src/rumpun + tools/replay_corpus.py"
    raise AssertionError(msg)


def _s49w2_parse_matrix(text: str) -> dict[str, tuple[str, str, str]]:
    """script -> (verdict, first failing line, note) from the matrix table.

    Mirrors the audit's committed ingestion rules: header-anchored, the
    separator row skipped, escaped pipes unescaped, malformed rows
    dropped.
    """
    lines = text.splitlines()
    try:
        head = lines.index("| script | verdict | first failing line | note |")
    except ValueError:
        return {}
    rows: dict[str, tuple[str, str, str]] = {}
    for line in lines[head + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 5 or cells[0] or cells[-1]:
            continue
        script, verdict, first_fail, note = (
            cell.replace("\\|", "|") for cell in cells[1:5]
        )
        if not script or not verdict:
            continue
        rows[script] = (verdict, first_fail, note)
    return rows


@dataclass(frozen=True)
class _S49W2Corpus:
    """One real full-corpus run: parsed rows plus the fresh matrix path."""

    rows: dict[str, tuple[str, str, str]]
    matrix: Path


def _s49w2_run_corpus(out_dir: Path) -> _S49W2Corpus:
    """One full corpus run by the real runner, subprocess-isolated.

    The runner reads the real evidence tree read-only and writes the
    matrix plus raw per-script logs only under out_dir. The 120s bound
    is the spec's (the s20 repro alone runs ~8s; the full corpus ~12s).
    """
    repo = _s49w2_repo_root()
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "tools" / "replay_corpus.py"),
            "--repo",
            str(repo),
            "--out-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=S49W2_RUNNER_TIMEOUT_S,
        check=False,
    )
    assert proc.returncode == 0, (proc.returncode, proc.stderr[-800:])
    matrix = out_dir / "replay-matrix.md"
    assert matrix.is_file(), sorted(path.name for path in out_dir.iterdir())
    text = matrix.read_text(encoding="utf-8")
    rows = _s49w2_parse_matrix(text)
    assert rows, text[:500]
    return _S49W2Corpus(rows=rows, matrix=matrix)


@pytest.fixture(scope="module")
def _s49w2_corpus(tmp_path_factory: Any) -> _S49W2Corpus:
    """One shared corpus run for the skip pin and the holdfast pins."""
    return _s49w2_run_corpus(tmp_path_factory.mktemp("s49w2-corpus"))


def _s49w2_write_proj(base: Path) -> Path:
    """Audit fixture (the s30 w2 shape): a .rumpun root with two seasons.

    The suite's audit-fixture contract, renamed: two season yamls with
    an execute/evaluate pipeline, runs/s1 completed with its state.json,
    runs/s2 empty, prompts/dev/dummy.md present.
    """
    root = base / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S49W2_RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text(
        "prompt body\n", encoding="utf-8"
    )
    for sid in ("s1", "s2"):
        (root / "seasons" / f"{sid}.yaml").write_text(
            S49W2_AUDIT_SEASON.format(sid=sid), encoding="utf-8"
        )
    season = root / "runs" / "s1"
    season.mkdir(parents=True)
    (season / "results.jsonl").write_text('{"n": 1}\n', encoding="utf-8")
    (season / "verdicts.jsonl").write_text('{"v": "WIN"}\n', encoding="utf-8")
    state = season / "_season"
    state.mkdir()
    state_row = {"id": "s1", "status": "completed", "started_at": 1.0, "ended_at": 2.0}
    (state / "state.json").write_text(json.dumps(state_row), encoding="utf-8")
    (root / "runs" / "s2").mkdir(parents=True)
    return root


# --- pin 1: the superseded s22 m5 row is a SKIP citing the s48 re-seal ------


def test_s49w2_m5_row_is_skip_citing_the_s48_reseal(
    _s49w2_corpus: _S49W2Corpus,
) -> None:
    """s49 pin 1 (red today: the m5 row is DRIFT — the runner re-runs the
    superseded script into a fresh DRIFT verdict every corpus run).

    s48-harvest: the arming was correct, the re-seal landed, and the
    drift row is retired. The runner's matrix must carry the m5 row as
    SKIP, with the note citing the supersession (the s48 re-seal at
    evidence/s48/), instead of re-running it.
    """
    assert S49W2_M5_REL in _s49w2_corpus.rows, sorted(_s49w2_corpus.rows)
    verdict, _first_fail, note = _s49w2_corpus.rows[S49W2_M5_REL]
    assert verdict == "SKIP", (verdict, note)
    assert re.search("s48", note), note
    assert re.search("supersed|re-seal", note, re.IGNORECASE), note


# --- pin 2: no s22 m5 DRIFT candidate in the audit after the skip -----------


def test_s49w2_audit_after_skip_has_no_m5_drift_candidate(
    tmp_path: Any,
    _s49w2_corpus: _S49W2Corpus,
) -> None:
    """s49 pin 2 (red today: run_audit arms "drift mismatch:
    s22/w1-repro-m5.py" from the fresh matrix's DRIFT row - the exact
    candidate audit-37 re-proposes each audit).

    The audit runs on the s30 fixture ledger fed the REAL fresh matrix,
    so the pin exercises the true runner -> ingestion chain without
    appending any record to the real ledger.
    """
    proj = _s49w2_write_proj(tmp_path)
    record = audit_mod.run_audit(proj, corpus_matrix=_s49w2_corpus.matrix)
    candidates = audit_mod.candidate_lines(record)
    drifts = [line for line in candidates if "drift mismatch:" in line]
    assert drifts == [], drifts


# --- pin 3: the other five repros still run and pass ------------------------


def test_s49w2_other_five_repros_still_pass(
    _s49w2_corpus: _S49W2Corpus,
) -> None:
    """s49 pin 3 (holdfast: green today, must survive w1's skip).

    Retiring the m5 adapter row must not touch the five repros that pass
    on main: h6 loop, warn repro, s19 H2+H3, s20 H5+H9, and m1.
    """
    for rel in S49W2_OTHER_REPROS:
        assert rel in _s49w2_corpus.rows, sorted(_s49w2_corpus.rows)
        verdict, _first_fail, note = _s49w2_corpus.rows[rel]
        assert verdict == "PASS", (rel, verdict, note)
