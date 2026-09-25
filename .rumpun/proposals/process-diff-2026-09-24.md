# process-diff 2026-09-24 — retire the frozen record target

One diff for the operator to merge. The s258 w2 lane drafted it and
never applies it. Routing: bin 1 (campaign-local).

## Top failure class

The scorer's report (tests/test_s258_process_score_1.py) tallies the
brief's record-target line at 0/16 pass over the corpus s242-s257:
the highest-frequency failure class. Pass counts on the other lines:
design 3/16, check 3/16, commit 4/16, notes 8/16, harvest 16/16,
next_yaml 16/16, bounds 16/16.

## Evidence

- every w1 brief seeds verbatim from .rumpun/prompts/dev/w1-light-lanes-70.md;
  its Task step 1 and Bounds line name tests/test_s214_light_lanes_70.py
- every w2 brief seeds verbatim from .rumpun/prompts/dev/w2-rehearsals-69.md;
  it names tests/test_s214_rehearsals_69.py the same way
- the seed step copies the brief byte-identical (prompt-meta.yaml carries
  template and template_sha256); nothing fills the target per season
- landed records carry per-season names (test_s242_light_lanes_97.py
  through test_s257_light_lanes_112.py); the scorer's target findings
  cite the mismatch season by season
- closes since s215 disclose the same adaptation every cycle ("drift
  none beyond the named frozen-target adaptation", s256 and s257 DESIGN
  entries)

## The fix

One diff, both family briefs. Retire the frozen s214 literals; the
target line names the next-free-per-family convention instead. Lanes
already adapt under that convention; the template stops shipping a
wrong literal. One diff file, four hunks.

## The diff

```diff
diff --git a/.rumpun/prompts/dev/w1-light-lanes-70.md b/.rumpun/prompts/dev/w1-light-lanes-70.md
index 4e50efa..2406677 100644
--- a/.rumpun/prompts/dev/w1-light-lanes-70.md
+++ b/.rumpun/prompts/dev/w1-light-lanes-70.md
@@ -82,9 +82,10 @@ probe re-confirms, the sweep record lands.
 
 ## Task
 1. Run the guards fresh; re-probe one route bounded; name any drift.
-   Land the sweep record in tests/test_s214_light_lanes_70.py (the
-   record shape: the guards' sha256 versions, the probe result, the
-   date; reads only).
+   Land the sweep record under tests/ at the next free per-family
+   name (test_<season>_<family>_<n>.py; never overwrite a landed
+   record; the record shape: the guards' sha256 versions, the
+   probe result, the date; reads only).
 2. Verify: solo pins green; full suite green vs the known reds
    (solo-run any new red); ruff clean.
 3. notes.md REQUIRED before ending the turn (the gate watches now;
@@ -92,4 +93,4 @@ probe re-confirms, the sweep record lands.
   background job at turn end.
 
 ## Bounds
-- Edits: tests/test_s214_light_lanes_70.py only. notes.md REQUIRED.
+- Edits: the one new record file under tests/, next free per-family name. notes.md REQUIRED.
diff --git a/.rumpun/prompts/dev/w2-rehearsals-69.md b/.rumpun/prompts/dev/w2-rehearsals-69.md
index bb92858..897616a 100644
--- a/.rumpun/prompts/dev/w2-rehearsals-69.md
+++ b/.rumpun/prompts/dev/w2-rehearsals-69.md
@@ -19,9 +19,10 @@ any drift names itself, the reconfirmation record lands.
 
 ## Task
 1. Run both rehearsal guards fresh; confirm green; name any drift.
-   Record the reconfirmation in tests/test_s214_rehearsals_69.py (the
-   record shape: the date, the outcome, one pinned sha256 per guard;
-   reads only).
+   Record the reconfirmation under tests/ at the next free per-family
+   name (test_<season>_<family>_<n>.py; never overwrite a landed
+   record; the record shape: the date, the outcome, one pinned sha256
+   per guard; reads only).
 2. Verify: solo pins green; full suite green vs the known reds
    (solo-run any new red); ruff clean.
 3. notes.md REQUIRED before ending the turn (the gate watches now;
@@ -29,4 +30,4 @@ any drift names itself, the reconfirmation record lands.
   background job at turn end.
 
 ## Bounds
-- Edits: tests/test_s214_rehearsals_69.py only. notes.md REQUIRED.
+- Edits: the one new record file under tests/, next free per-family name. notes.md REQUIRED.
```

## Merge gate

- the operator merges; this lane never applies its own proposal to
  rules files, templates, or CLAUDE.md
- bin 1: campaign-local, landed through a normal close
- promotion to bin 2 (user-global reference) or bin 3 (skills plugin)
  needs evidence of use beyond this campaign; none is claimed
