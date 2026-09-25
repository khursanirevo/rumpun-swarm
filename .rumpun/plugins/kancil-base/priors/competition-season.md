# A competition season owes an external outcome and a named baseline

## The prior

A competition season is judged by the world, not by the campaign. The
scaffold emits the competition-season shape (`.rumpun/seasons/_competition.yaml`,
baseline -> validate -> submit -> improve; the guide's competition shape
section names it). The shape alone owes nothing; three things are owed
no matter how the fill fields land:

- An external outcome. The close names the competition's own measure
  (submission scores, the leaderboard) and reads the verdict from it.
- A named baseline. The season seals one baseline before submitting,
  and every WIN/LOSS call reads against it by name.
- The honest unmeasured note. When the external outcome never got
  measured (no submission, no leaderboard read) and no baseline was
  named, the close says exactly that: what is unmeasured, why, and
  what evidence the season produced instead.

## Why this holds

The scaffold emits the shape; the shape's truth lives outside the
tree. A season can end with every internal gate green and still owe
its verdict, because internal pins cannot manufacture a submission
score or a baseline standing. The falsify gate reads submission
scores; with no baseline named, it has nothing to falsify against and
a WIN claim has no source. The unmeasured note is not a downgrade. It
is the measured fact about a season whose external measure never
landed, and it is the only verdict the record can honestly carry.

## How to apply

- Copy `.rumpun/seasons/_competition.yaml` (the guide's competition
  shape section) and fill every FILL field before the first lint.
- Seal the baseline first. The baseline phase writes baseline.jsonl;
  the expected_band names the metric delta over it.
- Call WIN or LOSS only from the competition's own metric, read from
  the season's submissions plus the leaderboard, never from internal
  pins alone.
- When neither the external outcome nor the named baseline exists at
  close, write the unmeasured note: what was not measured, why, and
  what evidence the season produced instead.
