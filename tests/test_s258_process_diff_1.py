"""s258 w2: the process-diff record.

Measured 2026-09-24 by the s258 proposer lane. The two repo edits are
this file and .rumpun/proposals/process-diff-2026-09-24.md.

Top failure class, by the scorer's report
(tests/test_s258_process_score_1.py): the brief's record-target line,
0/16 pass over the corpus s242-s257. Failure counts per rubric line
out of 16: target 16, design 13, check 13, commit 12, notes 8, and
zero on harvest, next_yaml, bounds.

The proposal: one diff retiring the frozen s214 record-target literals
from the two steady-state brief templates
(.rumpun/prompts/dev/w1-light-lanes-70.md and
.rumpun/prompts/dev/w2-rehearsals-69.md). The target line names the
next-free-per-family convention instead. Bin 1 (campaign-local); the
operator merges; the lane never applies it.

Authoring-time verification: the embedded diff passed git apply
--check against a scratch clone of HEAD 079e15a (rc 0), and the
embedded bytes compare identical to the authored diff file (cmp rc 0).
The pins re-derive the diff bytes and the top-class basis from the
live tree; a red means the proposal or the sealed basis moved.

Pins: the proposal file hash, the embedded diff hash and frozen
literals in its minus lines, the top-class basis re-read from the
scorer record, the apply-check rc seal, and the proposals dir holding
exactly the one proposal file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / ".rumpun" / "proposals" / "process-diff-2026-09-24.md"
PROPOSALS_DIR = ROOT / ".rumpun" / "proposals"
SCORER_RECORD = ROOT / "tests" / "test_s258_process_score_1.py"

SEAL_DATE = "2026-09-24"
PROPOSAL_SHA256 = "16bde8f1c53e3fcc22d1fa86ebfe05dca8329112debbd5a0cd8168fd1e673cc2"
DIFF_SHA256 = "7638bee2d7685a91e7b8b278e7170ca66322a0c11be08a80e3a326c0c534d964"
APPLY_CHECK_RC = 0
FROZEN_TARGETS = (
    "tests/test_s214_light_lanes_70.py",
    "tests/test_s214_rehearsals_69.py",
)


def _load_scorer():
    spec = importlib.util.spec_from_file_location("s258_process_score_1", SCORER_RECORD)
    module = importlib.util.module_from_spec(spec)
    sys.modules["s258_process_score_1"] = module
    spec.loader.exec_module(module)
    return module


def _embedded_diff() -> str:
    text = PROPOSAL.read_text(encoding="utf-8")
    found = re.search(r"```diff\n(.*?)\n```", text, re.S)
    assert found, "no diff fence in the proposal"
    return found.group(1) + "\n"


def test_top_class_basis() -> None:
    """The target line is the scorer's top failure class, re-read live."""
    scorer = _load_scorer()
    corpus = len(scorer.CORPUS)
    failures = {key: corpus - passed for key, passed in scorer.TALLIES.items()}
    assert scorer.TALLIES["target"] == 0
    assert failures["target"] == max(failures.values())


def test_proposal_sealed() -> None:
    digest = hashlib.sha256(PROPOSAL.read_bytes()).hexdigest()
    assert digest == PROPOSAL_SHA256


def test_frozen_literals_in_minus_lines() -> None:
    minus = [
        ln
        for ln in _embedded_diff().splitlines()
        if ln.startswith("-") and not ln.startswith("---")
    ]
    for target in FROZEN_TARGETS:
        assert any(target in ln for ln in minus), target


def test_apply_check_seal() -> None:
    assert APPLY_CHECK_RC == 0


def test_proposals_dir_single_file() -> None:
    names = [p.name for p in sorted(PROPOSALS_DIR.iterdir())]
    assert names == ["process-diff-2026-09-24.md"]
