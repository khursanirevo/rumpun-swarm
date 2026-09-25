"""s95 w2 pins — the season grammar admits "fix" as a change type.

Spec source: the s95 w2 note (the recorded annoyance, made structural).
The RESUME conventions line retired the retune euphemism at seed time;
these pins hold the code to that record: a draft typed fix applies
clean, the eight legacy types still apply (no regression), and an
unknown type still refuses naming the gate and the full nine-type
list. Offline: tmp_path campaigns, local subprocesses only.

Contract these pins hold:

1. apply admits primary_change.type: fix — a fixture yaml typed fix
   passes `evolve apply` (rc 0).
2. the eight pre-s95 change types still apply clean (no regression).
3. an unknown type still refuses: rc 1, the error names the gate and
   every legal type, fix included.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

S95W2_TIMEOUT = 240  # bounds one CLI subprocess (the s68 convention)

# The pre-s95 enum, hardcoded (never imported): a regression pin that
# imported the live set could not fail when the set regresses.
S95W2_LEGACY_TYPES = (
    "add", "emergency", "free_bundle", "pipeline_switch",
    "remove", "retune", "rewire", "rollback_restore",
)
S95W2_LEGAL_TYPES = (*S95W2_LEGACY_TYPES, "fix")

# s95w2 fixture draft: the s68 twin's proven lint-clean seed shape,
# grown up (parent + primary_change). __SID__/__TYPE__ are plain
# replace tokens — str.format would eat the yaml braces.
S95W2_DRAFT_TEMPLATE = """\
# seasons/__SID__.yaml — s95w2 fixture: non-seed draft, only type varies
id: __SID__
parent: s1
goal: "s95w2 fixture: the change-type gate is the only thing this apply tests"
metric: change_type_gate
mode: fight
methodology:
  approach: "s95w2 fixture reference pipeline"
  evidence: []
  primary_change:
    type: __TYPE__
    node: execute
    baseline: "s95w2 fixture: parent best, the fixture's own apply gate"
    expected_band: "WIN if apply exits 0; LOSS if it refuses"
    rollback: "git revert the s95 w2 commit"
    eval_window: "this pin run"
  pipeline:
    - phase: execute
      primitive: execute
      agents: writers
      prompt: prompts/base/execute.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agent: judge
      prompt: prompts/base/evaluate.md
      reads: results.jsonl
      writes: verdicts.jsonl
writers:
  - name: a1
    route: fable
    lane: s95w2-fix
    prompt: prompts/base/execute.md
    knowledge: full
    budget: {minutes: 1}
stop:
  "on": [all_exited, {stall_minutes: 45}, budget_exhausted]
"""


def _s95w2_repo() -> Path:
    """The repo root: the first ancestor holding pyproject.toml."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s95w2_env() -> dict[str, str]:
    """Subprocess env with the repo's src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s95w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s95w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess, 240s bounded."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(cwd),
        env=_s95w2_env(),
        capture_output=True,
        text=True,
        timeout=S95W2_TIMEOUT,
        check=False,
    )


def _s95w2_campaign(tmp_path: Path) -> Path:
    """A fresh scaffolded campaign; the s68 helper shape."""
    root = tmp_path / "campaign"
    run = _s95w2_run(tmp_path, ["init", str(root)])
    assert run.returncode == 0, f"init failed: {run.stderr}"
    return root


def _s95w2_write_draft(root: Path, sid: str, ctype: str) -> None:
    """Write the fixture draft with sid and change type substituted."""
    drafted = root / ".rumpun" / "seasons" / f"{sid}.yaml"
    drafted.parent.mkdir(parents=True, exist_ok=True)
    drafted.write_text(
        S95W2_DRAFT_TEMPLATE.replace("__SID__", sid).replace("__TYPE__", ctype),
        encoding="utf-8",
    )


def _s95w2_stage_panel(root: Path) -> None:
    """free_bundle's documented precondition: autonomy.stage panel|free."""
    cfg = root / ".rumpun" / "rumpun.yaml"
    text = cfg.read_text(encoding="utf-8")
    assert "stage: manual" in text, "the scaffold must write stage: manual"
    cfg.write_text(text.replace("stage: manual", "stage: panel"), encoding="utf-8")


def test_s95w2_fix_type_applies_clean(tmp_path):
    root = _s95w2_campaign(tmp_path)
    _s95w2_write_draft(root, "s950", "fix")
    run = _s95w2_run(root, ["evolve", "apply", ".rumpun/seasons/s950.yaml"])
    assert run.returncode == 0, f"fix must apply clean: {run.stderr}{run.stdout}"


@pytest.mark.parametrize("ctype", S95W2_LEGACY_TYPES)
def test_s95w2_legacy_change_types_still_apply(tmp_path, ctype):
    root = _s95w2_campaign(tmp_path)
    if ctype == "free_bundle":
        _s95w2_stage_panel(root)
    sid = f"s95{S95W2_LEGACY_TYPES.index(ctype) + 1}"
    _s95w2_write_draft(root, sid, ctype)
    run = _s95w2_run(root, ["evolve", "apply", f".rumpun/seasons/{sid}.yaml"])
    assert run.returncode == 0, f"{ctype} must still apply clean: {run.stderr}{run.stdout}"


def test_s95w2_unknown_type_still_refuses(tmp_path):
    root = _s95w2_campaign(tmp_path)
    _s95w2_write_draft(root, "s959", "refactor")
    run = _s95w2_run(root, ["evolve", "apply", ".rumpun/seasons/s959.yaml"])
    assert run.returncode == 1, f"unknown type must refuse: {run.stderr}{run.stdout}"
    assert "primary_change.type must be one of" in run.stderr
    for name in S95W2_LEGAL_TYPES:
        assert f"'{name}'" in run.stderr, f"the gate must name {name}: {run.stderr}"
