"""s91 w1 pins — the akar append lock holds under concurrency (issue #17).

Spec sources: khursanirevo/rumpun#17 (the H6 flock leaks on fresh
trees), the s90 w2 probe evidence (.rumpun/runs/s90/w2/probe_flock.py
and its notes.md), and the corpus row the runner gates on
(evidence/s18/w1-h6-loop.py, pass signature "both-appends-succeeded in
0 of 20").

Root cause these pins hold shut: _append_lock resolved its path through
paths.ledger_dir, the read resolver, which on a tree where neither
ledger/ nor akar/ exists falls back to the legacy akar/ -- while the
publish writes through paths.ledger_new, which falls back to ledger/.
The publish mkdir then flips ledger_dir mid-transaction, so two
barrier-synchronized same-id appenders can flock two different files,
both pass the duplicate and existence checks, and both succeed: the
silent-replacement signature, measured at ~0.26% per round (18/7000
pooled, s90 w2) and 1/20 corpus rows in two recent gates.

The contracts:

1. the barrier contract: 40 fresh-root rounds of two same-id appends,
   each round exactly one success and one AkarError naming the
   duplicate refusal -- the all-pass signature the corpus row asserts
   at N=20, tightened to N=40;
2. the placement contract (the mechanism, deterministic): appending to
   a fresh root creates no legacy akar/ litter and leaves the lock in
   the same tree the record landed in;
3. the sequential contract: well-formed sequential appends keep their
   layout, digests, dedup, and lookup -- the fix moves a lock path,
   nothing else.

Measured red/green evidence: .rumpun/runs/s91/w1/notes.md.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

import pytest

from rumpun import akar

S91W1_ROUNDS = 40


def _s91w1_round(root: Path, outcomes: list[str]) -> None:
    """One corpus-shaped round: two barrier threads, one id, fresh root."""
    barrier = threading.Barrier(2)

    def attempt(k: int) -> None:
        barrier.wait()
        try:
            akar.append_record(root, "race-loop", "t", f"body {k}")
            outcomes.append("ok")
        except akar.AkarError as exc:
            outcomes.append("dup" if "already declared" in str(exc) else "err")

    threads = [threading.Thread(target=attempt, args=(k,)) for k in (0, 1)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(60)


def test_s91w1_barrier_rounds_admit_exactly_one_writer(tmp_path: Path) -> None:
    """The all-pass signature over 40 tightened barrier rounds.

    Pre-fix the both-ok class fired at ~0.26% of rounds, so 40 rounds
    catch a standing leak with roughly nine-in-ten probability per run;
    the placement pin is the deterministic discriminator for the
    mechanism, and this pin holds the end-to-end signature.
    """
    for round_index in range(S91W1_ROUNDS):
        root = tmp_path / f"r{round_index}"
        outcomes: list[str] = []
        _s91w1_round(root, outcomes)
        assert sorted(outcomes) == ["dup", "ok"], (
            f"round {round_index}: expected one writer and one duplicate "
            f"refusal, got {outcomes}"
        )


def test_s91w1_fresh_root_lock_lands_in_the_write_tree(tmp_path: Path) -> None:
    """The lock and the record share one tree; the legacy alias stays shut.

    Pre-fix the lock resolved to akar/ on a fresh root while the record
    landed in ledger/, and the transaction left an empty akar/ holding
    only append.lock -- the fingerprint of the resolver split that let
    two threads flock two different files (issue #17).
    """
    record = akar.append_record(tmp_path, "place-1", "placement", "body\n")
    assert record.parent == tmp_path / "ledger"
    assert (tmp_path / "ledger" / "append.lock").exists()
    assert not (tmp_path / "akar").exists()
    digest = hashlib.sha256(b"body\n").hexdigest()
    assert record.read_text(encoding="utf-8").endswith(f"sha256: {digest}\n")


def test_s91w1_sequential_appends_unchanged(tmp_path: Path) -> None:
    """Well-formed sequential appends keep the pre-fix surface."""
    first = akar.append_record(tmp_path, "seq-1", "first", "one\n")
    second = akar.append_record(tmp_path, "seq-2", "second", "two\n")
    assert first.parent == second.parent == tmp_path / "ledger"
    assert akar.find_record(tmp_path, "seq-1") == first
    assert akar.declared_ids(tmp_path) == {"seq-1": first, "seq-2": second}
    with pytest.raises(akar.AkarError):
        akar.append_record(tmp_path, "seq-1", "dup", "again\n")
