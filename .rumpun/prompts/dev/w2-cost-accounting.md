# s94 w2 — the cost accounting contract (the composer's third candidate)

"The campaign supplies no total cost accounting. The last explicit
cost-cap status remains unset despite a declared budget invariant."
Design what would count as cost, and measure the first honest slice
from data that exists.

## Ground truth (measured 2026-09-18)
- audit-46's candidate (the fresh composer run); directive seq 9 set
  NO cost cap deliberately — the residual is not about a cap, it is
  about VISIBILITY: what the campaign spends is unrecorded
- what exists in the ledger: every harvest record carries the season
  duration and the per-writer table (route, seconds); the board
  issues carry filed-to-closed timestamps
- what does NOT exist: token counts, API costs, the operator's
  manual-time counterweight

## Task
1. Design the cost-accounting contract: what is measurable honestly
   (writer-seconds per season, seasons per week, the board defects'
   filed-to-closed elapsed times) versus what is NOT (tokens, API
   cost — unrecorded and unrecordable retroactively), and the
   visibility fix going forward (a per-harvest spend line derived
   from the writer table). Distill into the kancil-base pack as
   priors/templates/cost-accounting.md.
2. Measure the first slice from the ledger: total writer-seconds
   across all harvested seasons, the per-season table for the last
   ten, and the zero-recurrence record. The table proves nothing
   alone and says so.
3. Comment the contract + the table on audit-46's composer thread...
   no issue exists for this candidate (it emerged fresh). File it as
   a board issue (one live call, disclosed), then comment the slice
   on it. The issue stays OPEN.
4. notes.md REQUIRED: the design, the tables, the issue url.

## Bounds
- Edits: the pack draft dir (one template), tests/ if the spend-line
  shape is pinned (test_s94_w2_pins.py, _s94w2_ prefix). One live gh
  call pair (disclosed). notes.md REQUIRED.
