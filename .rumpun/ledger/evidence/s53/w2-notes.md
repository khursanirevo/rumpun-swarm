# s53 w2 — spec-first pins for the hub round trip

Worker: w2, season s53, repo /mnt/data/work/rumpun, HEAD 5e56132 with w1's
hub code landed UNCOMMITTED in the shared working tree mid-session
(` M src/rumpun/plugin.py`, ` M src/rumpun/cli.py`). Scope: NEW tests/
additions only — `tests/test_s53_w2_pins.py` (this workspace; graft to
repo tests/ as-is; `_s53w2_` helpers, no collisions). src/ untouched by
w2.

## The pins (4, subprocess E2E, 120s bound per verb)

1. Round trip: `rumpun init` campaign A → `plugin install` the fixture
   pack → `plugin publish kaggle-base --remote <bare>` rc 0 → fresh
   `rumpun init` campaign B → `plugin pull kaggle-base --remote <bare>`
   rc 0 → `plugin list` digests equal on both sides and equal to the
   pack's sealed digest; the pulled install carries manifest.yaml +
   priors/ and no campaign/.
2. Lint refusal (non-vacuous): a clean publish succeeds first, then a
   tampered installed pack (private-vocabulary term injected, manifest
   digest RE-SEALED so only the lint gate can refuse) → publish rc != 0,
   the remote tree keeps the good paths, the tamper marker appears in no
   remote blob.
3. Campaign off the wire: publish rc 0 with refs non-empty; no ref's
   tree carries a campaign/ path; the secret token appears in no blob
   (git grep over every ref).
4. Tampered remote: clone -b <pushed branch> → edit priors/ → commit →
   push → `plugin pull` rc != 0; nothing installed (registry and disk
   both checked).

## Measured red set — baseline 5e56132, 2026-09-16

Method: w1's hub code landed in the shared tree mid-session, so the
working tree no longer exposes the seeded baseline. Red was measured
against `git archive 5e56132` extracted to /tmp/s53w2_base with the pins
file copied into its tests/ (the file's pyproject walk-up resolves that
tree's src/ onto PYTHONPATH; the shared tree was never touched).

Command (from /tmp/s53w2_base): /mnt/data/work/rumpun/.venv/bin/python
-m pytest tests/test_s53_w2_pins.py -v
Log: /tmp/s53w2_red_baseline.txt — 4 failed in 14.62s, rc 1

- RED all four pins, one shared right reason: `rumpun plugin: error:
  argument plugin_command: invalid choice: 'publish' (choose from
  install, list, distill)` (rc 2) at each pin's clean-publish
  precondition. No fixture, import, or collection errors.

An earlier working-tree probe (/tmp/s53w2_red_set.txt: 3 passed, 1
failed) is the mid-flight-landing evidence: three pins went green the
moment w1's verbs appeared. Its single red was w2's own clone bug (the
fix is recorded under Notes), not a contract gap.

## Measured green set — working tree (w1's landed hub code), 2026-09-16

Command (repo root): .venv/bin/python -m pytest
.rumpun/runs/s53/w2/tests/test_s53_w2_pins.py -v
Log: /tmp/s53w2_green_set.txt — 4 passed in 13.94s, exit 0
✅ VERIFIED REAL (subprocess E2E: every verb runs as `python -m rumpun`
in a fresh campaign, git ops on file-path remotes only)

- GREEN pin 1 round trip: publish rc 0; pull rc 0 into a fresh campaign;
  digest equal across publish side, pull side, and the sealed manifest.
- GREEN pin 2 lint refusal: clean publish rc 0, re-sealed tamper refused
  (rc != 0), remote paths unchanged, tamper marker absent from remote
  content.
- GREEN pin 3 campaign off the wire: refs non-empty, zero campaign/
  paths in any ref tree, secret absent from every blob.
- GREEN pin 4 tampered remote: clone-edit-push succeeded (tamper is
  real), pull rc != 0, no registry row, no install dir.

## Suite floor (merged-tree eval window: HEAD + w1's landed src)

Command (repo root): .venv/bin/python -m pytest tests/ -v
Log: /tmp/s53w2_full_suite.txt — 1 failed, 230 passed in 313.33s
✅ VERIFIED REAL

- RED `test_s38_coldstart_checker_leaves_repo_rumpun_untouched` — the
  known standing red, pre-existing and unrelated to the hub arc.
- GREEN s43 pins 8/8 (the task's "s43 pins stay green" clause holds).
- GREEN race pins this run (they are the floor's known flakes; s52's
  harvest already recorded the floor as "race flakes only").
- 0 new reds. The task's "four known reds otherwise unchanged" holds
  conservatively: nothing red beyond the known set; the measured floor
  today is 1 known red plus flakes that happened to pass.

## Notes for the merge

- Graft tests/test_s53_w2_pins.py as-is.
- Pin 4's tamper clone resolves the pushed branch via for-each-ref and
  clones `-b` it; an `init --bare` default-branch HEAD dangles until a
  matching branch lands, and cloning on dangling HEAD yields a rc-0
  EMPTY checkout (the first draft failed exactly there).
- Pin 2 publishes clean first so its refusal clause cannot pass
  vacuously on a tree where the verb is absent (an absent verb also
  "refuses").
- The pins' subprocess env walls git off from the operator config
  (GIT_CONFIG_GLOBAL=/dev/null, GIT_CONFIG_NOSYSTEM=1, explicit
  identity), so publish/pull commit and push on any machine.
- w1's landed contract, which the pins exercise: plugin_publish stages
  priors-only and pushes refs/heads/main; plugin_pull fetches the
  explicit refs/heads/main refspec (no dependence on the remote HEAD);
  both use subprocess git on file-path remotes.

## Status

- Red set: measured ✅ — all 4, right reason, vs the seeded baseline
- Green set: measured ✅ — 4/4 vs w1's landed hub code (green at merge)
- Suite floor: measured ✅ — 1 known red unchanged, s43 8/8, 0 new reds
- ruff: clean, line-length 100 via pyproject walk-up ✅
