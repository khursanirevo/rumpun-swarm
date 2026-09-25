"""s91 w2 pins - issue #17's own repro, pinned red-before/green-after.

Spec sources: issue #17 (khursanirevo/rumpun, OPEN: the akar H6 lock
leaks, concurrent same-id appends both succeed 1-in-20 barrier runs on
main e2502ae) and the repro-backed-closure contract (s80, kancil-base
pack: a defect-resolving season closes only against the issue's own
repro). The s80 standard eats its own cooking here: this file pins that
repro directly, red on unfixed main, green once s91 w1's fix lands.

Pin 1 - the h6 barrier harness, the corpus contract unchanged: pairs
of 2 threads, threading.Barrier(2), one record id, fresh ledger root
per pair-round, outcomes from the real akar.append_record; the asserted
signature stays the corpus all-pass shape (0 pair-rounds with both
appends succeeding). Scale: 10000 pair-rounds per run (16 concurrent
pairs x 625 batches). Measured contrast (2026-09-17): the committed
pre-fix tree (fb64683) leaked live in this exact scenario - 2/1500
rounds with both appends succeeding plus six tmp-collision error
rounds, captured via an isolated clone probe - while the tree with
w1's fix applied measured 0 leaks in ~28k rounds across seven shapes
(notes.md). Pre-fix the pin is red when the defect expresses; post-fix
the green is structural.

Pin 2 - the corpus contract holds: the other four repros (the s49 pin's
five minus the h6 row, now pinned directly by pin 1) still run and pass
via the real runner (tools/replay_corpus.py).

Color history (the s80 contract's evidence trail):
- RED captured live 2026-09-17 against fb64683 (the commit the issue
  was filed on): 2/1500 barrier rounds with both appends succeeding,
  plus 6 tmp-collision error rounds, via the isolated clone probe
  (.rumpun/runs/s91/w2/probe_prefix.py). Standing gate reds: the s58
  gate log (1/20, verbatim in notes.md) and the issue's instrumented
  18/7000 with overlaps == both-ok.
- GREEN captured 2026-09-17 against the fixed tree (s91 w1's fix,
  uncommitted in the working tree at run time; that lane was killed
  mid-verification): 0 leaks in ~28k rounds across seven shapes, this
  pin included. The flip commit records the landed fix sha when s91
  w1's fix commits to main.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from rumpun import akar

S91W2_PAIRS = 16
S91W2_BATCHES = 625
S91W2_RUNNER_TIMEOUT_S = 120

S91W2_OTHER_REPROS = (
    "s18/w1-warn-repro.py",
    "s19/w1-repro-h2-h3.py",
    "s20/w1-repro.py",
    "s22/w1-repro-m1.py",
)


def _s91w2_attempt(
    root: Path, barrier: threading.Barrier, k: int, outcomes: list[str]
) -> None:
    barrier.wait()
    try:
        akar.append_record(root, "race-loop", f"t{k}", f"body {k}")
        outcomes.append("ok")
    except akar.AkarError:
        outcomes.append("err")


def test_s91w2_h6_repro_all_pass_signature() -> None:
    """s91 w2 pin 1 (the issue's own repro; red pre-fix, green post-fix).

    The corpus contract (barrier scenario, all-pass signature = 0
    both-append pair-rounds) unchanged; scaled rounds raise the capture
    probability. The red is burst-dependent pre-fix (the measured limit
    lives in the module docstring and notes.md); the green is
    structural post-fix.
    """
    both = 0
    for _ in range(S91W2_BATCHES):
        tds = [tempfile.TemporaryDirectory() for _ in range(S91W2_PAIRS)]
        try:
            outcome_sets: list[list[str]] = [[] for _ in range(S91W2_PAIRS)]
            threads = []
            for pair in range(S91W2_PAIRS):
                barrier = threading.Barrier(2)
                for k in (0, 1):
                    threads.append(
                        threading.Thread(
                            target=_s91w2_attempt,
                            args=(
                                Path(tds[pair].name),
                                barrier,
                                k,
                                outcome_sets[pair],
                            ),
                        )
                    )
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(30)
            for outcomes in outcome_sets:
                if sorted(outcomes) == ["ok", "ok"]:
                    both += 1
        finally:
            for td in tds:
                td.cleanup()
    assert both == 0, (
        "akar H6 lock leaks (issue #17): both same-id appends succeeded "
        f"in {both} of {S91W2_PAIRS * S91W2_BATCHES} barrier pair-rounds "
        f"({S91W2_PAIRS} concurrent pairs x {S91W2_BATCHES} batches); "
        "all-pass signature is 0"
    )


def _s91w2_repo_root() -> Path:
    """The repo root: the first ancestor of this file holding src/rumpun.

    Holds both pre-graft (the pins live under .rumpun/runs/s91/w2/
    inside the repo) and post-graft (tests/).
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "src" / "rumpun").is_dir() and (
            candidate / "tools" / "replay_corpus.py"
        ).is_file():
            return candidate
    msg = "no ancestor of the pins file holds src/rumpun + tools/replay_corpus.py"
    raise AssertionError(msg)


def _s91w2_parse_matrix(text: str) -> dict[str, tuple[str, str, str]]:
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
class _S91W2Corpus:
    """One real full-corpus run by the real runner: the parsed rows."""

    rows: dict[str, tuple[str, str, str]]


def _s91w2_run_corpus(out_dir: Path) -> _S91W2Corpus:
    """One full corpus run by the real runner, subprocess-isolated.

    The runner reads the real evidence tree read-only and writes the
    matrix plus raw per-script logs only under out_dir.
    """
    repo = _s91w2_repo_root()
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
        timeout=S91W2_RUNNER_TIMEOUT_S,
        check=False,
    )
    assert proc.returncode == 0, (proc.returncode, proc.stderr[-800:])
    matrix = out_dir / "replay-matrix.md"
    assert matrix.is_file(), sorted(path.name for path in out_dir.iterdir())
    rows = _s91w2_parse_matrix(matrix.read_text(encoding="utf-8"))
    assert rows, matrix.read_text(encoding="utf-8")[:500]
    return _S91W2Corpus(rows=rows)


@pytest.fixture(scope="module")
def _s91w2_corpus(tmp_path_factory: Any) -> _S91W2Corpus:
    """One shared corpus run for the corpus-contract pin."""
    return _s91w2_run_corpus(tmp_path_factory.mktemp("s91w2-corpus"))


def test_s91w2_other_four_repros_still_pass(
    _s91w2_corpus: _S91W2Corpus,
) -> None:
    """s91 w2 pin 2 (holdfast: green today, must survive w1's fix).

    The s49 pin's five minus the h6 row (pinned directly by pin 1):
    warn repro, s19 H2+H3, s20 H5+H9, and m1 keep running and passing
    via the real runner while akar.py changes lanes.
    """
    for rel in S91W2_OTHER_REPROS:
        assert rel in _s91w2_corpus.rows, sorted(_s91w2_corpus.rows)
        verdict, _first_fail, note = _s91w2_corpus.rows[rel]
        assert verdict == "PASS", (rel, verdict, note)
