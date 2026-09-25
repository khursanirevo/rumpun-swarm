# s83 w1 — fix issue #10: distill runs the content lint (and close #8, #9)

Drafts could seal uninstallable because distill skipped the lint that
install runs. Fix the placement, then retire the two findings s82
already resolved.

## Ground truth (measured 2026-09-17)
- issue #10: distill sealed the kancil-base draft with zero findings;
  the s81 install gate refused on `/error-exp` in a code span
  (ABS_PATH_RE, plugin.py:79)
- issue #8 (FIXED in s82): installed_kancil_version reads the route
  binary; the issue #8 repro renders the card (the s82 pins)
- issue #9 (RESOLVED by design): the ledger's one-request-per-season
  rule means panel-s79-error is the final record for s79

## Task
1. Fix: plugin_distill runs the same content lint as install before
   sealing the draft. Findings at distill = the draft refuses to seal
   (or seals with the findings recorded in the manifest — pick per the
   code's shape; the contract is: an uninstallable draft cannot seal
   silently).
2. Pins (tests/test_s83_w1_pins.py, _s83w1_ prefix, offline): a draft
   with a violating token refuses to seal; a clean draft seals with
   the manifest digest; the install gate passes on the sealed draft.
3. Retire the findings: comment issue #8 with the s82 fix evidence
   (the surface fix + the repro card pin) and CLOSE it; comment issue
   #9 with the one-request rule as the design resolution and CLOSE it.
4. Verify: re-distill the kancil-base draft in a fixture campaign —
   the reworded skills file now passes the lint it never saw. Notes.md
   REQUIRED: the fix shape, the pin list, the issue urls.

## Bounds
- Edits: src/rumpun/plugin.py, tests/. No priors content edits. No
  live route call.
