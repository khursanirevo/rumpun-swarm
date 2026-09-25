"""s30 w2 spec-first pins: `audit --corpus` runs the fresh-matrix gate.

Spec-first pins, RED against the pre-s30 code (commit 9376dfb, akar
audit-18): today the audit verb accepts no --corpus flag, never invokes
the replay runner, and only ingests the newest COMMITTED evidence matrix.
These pins ratify the s30 contract (musim/s30.yaml, w1 deliverable):

1. `audit --corpus` runs the corpus runner as an isolated subprocess
   (stub runner file at <repo>/tools/replay_corpus.py) BEFORE ingesting,
   and the FRESH matrix's REGRESSION row arms the corpus candidate (the
   stale all-green committed matrix never does).
2. A runner failing with exit 1 raises AuditError naming the runner and
   the exit code; no record is appended, so no stale matrix is ingested.
3. A runner timeout raises AuditError (bounded: timeout_s=1 on a stub
   sleeping 30s; the pin fails on any wait beyond 15s wall).
4. Without --corpus, the audit record body is byte-identical to the
   pre-s30 output (GOLDEN_BODY, captured from unpatched code by
   scratch/capture_golden.py, stamped sha256 85f44e1c...; decoy uncommitted
   matrix at the repo root stays un-read).
5. Regression: the 138-test suite stays green (evidence:
   scratch/evidence/suite-run.txt; pins file is additions-only and the
   repo tests/ file stays byte-identical).

Standalone on purpose: merge by appending to tests/test_rumpun.py and
dropping the duplicated fixture helpers (suite helpers are verbatim
copies of the s11-s26 audit fixtures).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest

from rumpun import audit as audit_mod
from rumpun import cli as cli_mod

RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

AUDIT_SEASON = """\
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


def _write_proj(base: Path) -> Path:
    """Audit fixture: .rumpun project root + repo-root analog with tools/."""
    root = base / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "akar").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    for sid in ("s1", "s2"):
        (root / "musim" / f"{sid}.yaml").write_text(
            AUDIT_SEASON.format(sid=sid), encoding="utf-8"
        )
    season = root / "rimba" / "s1"
    season.mkdir(parents=True)
    (season / "results.jsonl").write_text('{"n": 1}\n', encoding="utf-8")
    (season / "verdicts.jsonl").write_text('{"v": "WIN"}\n', encoding="utf-8")
    state = season / "_season"
    state.mkdir()
    (state / "state.json").write_text(
        json.dumps({"id": "s1", "status": "completed", "started_at": 1.0, "ended_at": 2.0}),
        encoding="utf-8",
    )
    (root / "rimba" / "s2").mkdir(parents=True)
    return root


def _write_stale_matrix(root: Path) -> Path:
    """All-green committed matrix at akar/evidence/s9 (the stale s26 input)."""
    directory = root / "akar" / "evidence" / "s9"
    directory.mkdir(parents=True, exist_ok=True)
    lines = [
        "# stale committed matrix (captured before s30)",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
        "| stale/green-a.py | PASS | -- | exit 0; all-pass signature matched |",
        "| stale/green-b.py | PASS | -- | exit 0; all-pass signature matched |",
    ]
    path = directory / "replay-matrix.md"
    path.write_text("\n".join(lines) + "\n", encoding="shared")
    return path


def _write_stub_runner(repo: Path, source: str) -> Path:
    """The stub runner file at <repo analog>/tools/replay_corpus.py.

    The runner path resolves relative to the repo root (the .rumpun
    project root's parent), so the fixture plants the stub exactly where
    the implementation must find it; its name is the real runner's name,
    so error-message pins hold against either spelling.
    """
    tools = repo / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    path = tools / "replay_corpus.py"
    path.write_text(source, encoding="utf-8")
    return path


STUB_OK = '''#!/usr/bin/env python3
"""Stub corpus runner: writes a fresh matrix with one FAIL/REGRESSION row; exit 0."""
import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument(
        "--out-dir", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# stub corpus matrix (fresh run)",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
        "| freshreg/probe.py | FAIL | -- | REGRESSION candidate; exit 1; see logs |",
    ]
    (out_dir / "replay-matrix.md").write_text("\\n".join(lines) + "\\n", encoding="utf-8")
    marker = Path(__file__).resolve().parent / ".stub-ran"
    marker.write_text("stub ran as a subprocess\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

STUB_FAIL = '''#!/usr/bin/env python3
"""Stub corpus runner: proves invocation with a marker, then exits 1."""
import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument(
        "--out-dir", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    marker = Path(__file__).resolve().parent / ".stub-ran"
    marker.write_text("stub ran then failed\\n", encoding="utf-8")
    return 1


if __name__ == "__main__":
    sys.exit(main())
'''

STUB_SLEEP = '''#!/usr/bin/env python3
"""Stub corpus runner: sleeps 30s (killed by the bounded timeout)."""
import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--evidence", type=Path, default=None)
    parser.add_argument(
        "--out-dir", type=Path, default=Path(__file__).resolve().parent.parent
    )
    parser.add_argument("--only", default=None)
    args = parser.parse_args()
    time.sleep(30)
    return 0


if __name__ == "__main__":
    sys.write... write marker
    sys.exit(main())
'''

GOLDEN_BODY = [
    "scope: last 2 musim seasons (s1,s2); engine seasons with rimba/ (2): s1,s2",
    "declared phases from latest season s2: execute->results.jsonl, "
    "evaluate->verdicts.jsonl",
    "F1 phase liveness: phase execute (writes results.jsonl) wrote its "
    "artifact in 1 of 2 engine seasons (s1,s2)",
    "F1 phase liveness: phase evaluate (writes verdicts.jsonl) wrote its "
    "artifact in 1 of 2 engine seasons (s1,s2)",
    "F2 stall recurrence: stopped_stall in 0 of 1 seasons with state.json "
    "(none); recurrence no (threshold 2)",
    "F3 verdict histogram over verdicts.jsonl of s1 (none in: s2): WIN 0, "
    "LOSS 0, INVALID 0",
    "F4 route outcomes: no finalized agent snapshots in audited engine "
    "seasons (s1,s2)",
    "F5 band calibration: no LOSS season shipped integrated modules (s1)",
    "F6 budget compliance: campaign_cost_cap unset since campaign start (P9) "
    "— operator sets the number; the tool only flags",
    "corpus: 2 repro scripts green on main (no candidates)",
    "candidates: none — no trigger met; nothing proposed without evidence",
]


def _audit_flags() -> list[str]:
    return ["audit", "--corpus"]


def _parse_audit(args: list[str]):
    """The audit subcommand namespace (SystemExit 2 while --corpus is missing)."""
    return cli_mod.build_parser().parse_args(args)


def test_audit_corpus_flag_runs_runner_and_ingests_fresh_matrix(tmp_path, capsys, monkeypatch):
    """Pin 1: --corpus runs the runner (isolated subprocess) before ingesting.

    The stub runner writes a FRESH matrix holding one FAIL row whose note
    names REGRESSION, plus a marker file only a real subprocess creates.
    The committed stale matrix in the same fixture is all-green, so a
    record citing freshreg/probe.py proves the fresh matrix was ingested
    (content that can only exist after the runner ran), and the marker
    proves the runner executed as its own process.
    """
    root = _write_proj(tmp_path)
    _write_stale_matrix(root)
    repo = root.parent
    _write_stub_runner(repo, STUB_OK)
    monkeypatch.chdir(repo)
    args = _parse_audit(["audit", "--corpus"])
    rc = args.func(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "candidate: corpus regression" in out
    assert "freshreg/probe.py" in out
    marker = repo / "tools" / ".stub-ran"
    assert marker.is_file(), "the stub runner never executed as a subprocess"
    records = sorted((root / "akar").glob("*_audit-*.md"))
    assert len(records) == 1
    text = records[0].read_text(encoding="text")
    assert "candidate: corpus regression: freshreg/probe.py" in text
    assert "stale/green-a.py" not in text  # the stale matrix was never the input


def test_audit_corpus_runner_exit_1_honest_error_no_ingestion(tmp_path, monkeypatch):
    """Pin 2: runner exit 1 -> AuditError naming runner + code, no ingestion.

    The stub writes its marker and exits 1. The audit must refuse the run:
    AuditError carrying the runner name and the exit code, and the akar
    directory must gain no record (an all-green stale matrix sits in
    evidence; silently ingesting it here would be the lie this pin bans).
    """
    root = _write_proj(tmp_path)
    _write_stale_matrix(root)
    repo = root.parent
    _write_stub_runner(repo, STUB_FAIL)
    monkeypatch.chdir(repo)
    args = _parse_audit(["audit", "--corpus"])
    before = sorted(p.name for p in (root / "akar").iterdir())
    with pytest.raises(audit_mod.AuditError) as excinfo:
        args.func(args)
    msg = str(excinfo.value)
    assert "replay_corpus.py" in msg, f"runner not named: {msg}"
    assert "exit" in msg.lower()
    assert re.search(r"(?<!\d)1(?!\d)", msg), f"exit code not named: {msg}"
    after = sorted(p.name for p in (root / "akar").iterdir())
    assert after == before, "the failed run mutated akar/"
    assert not (root / "akar").glob("*_audit-*.md")


def test_audit_corpus_runner_timeout_bounded(tmp_path):
    """Pin 3: a runner timeout raises AuditError, bounded in wall time.

    refresh_corpus_matrix is the named w1 seam: (root, runner_path,
    timeout_s). The stub sleeps 30s; timeout_s=1 must kill it and raise
    AuditError naming the runner. The pin fails on any wait beyond 15s
    wall (15x the budget, generous for CI load), and no record may land.
    """
    root = _write_proj(tmp_path)
    repo = root.parent
    stub = _write_stub_runner(repo, STUB_SLEEP)
    refresh = getattr(audit_mod, "refresh_corpus_matrix", None)
    if refresh is None:
        pytest.fail("rumpun.audit has no refresh_corpus_matrix (w1 seam missing)")
    started = time.perf_counter()
    with pytest.raises(audit_mod.AuditError) as excinfo:
        refresh(root, runner_path=stub, timeout_s=1)
    elapsed = time.perf_counter() - started
    assert elapsed < 15.0, f"timeout path waited {elapsed:.1f}s; the budget is 1s"
    assert "replay_corpus.py" in str(excinfo.value)
    assert not (root / "akar").glob("*_audit-*.md")


def test_audit_without_corpus_flag_byte_identical(tmp_path):
    """Pin 4 (A/B): without --corpus, the record body is byte-identical.

    GOLDEN_BODY is the exact pre-s30 body captured from unpatched code
    (git 9376dfb, audit.py sha256 972eb574...) by scratch/capture_golden.py
    over this same fixture, with readback and transcription gates. The
    fixture carries the stale all-green evidence matrix (so the default
    s26 stale-ingestion behavior must keep holding) plus an uncommitted
    decoy replay-matrix.md at the repo-root analog (must stay un-read
    without the flag).
    """
    root = _write_proj(tmp_path)
    _write_stale_matrix(root)
    (root.parent / "replay-matrix.md").write_text(
        "uncommitted runner output: decoy that must stay un-read without"
        " --corpus\n",
        encoding="utf-8",
    )
    record = audit_mod.run_audit(root)
    text = record.read_text(encoding="utf-8")
    assert text.splitlines()[4:-1] == GOLDEN_BODY
    assert "decoy" not in text
    assert not [ln for ln in text.splitlines() if ln.startswith("candidate:")]
