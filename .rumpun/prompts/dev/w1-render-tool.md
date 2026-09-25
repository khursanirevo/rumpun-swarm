# s27 w1 — tools/render_dashboard.py (maintained render loop)

You are w1 in season s27 (repo root: the parent of this .rumpun tree). Read
DESIGN.md sections 13-15, src/rumpun/report.py (render_report,
render_index, render_discoveries, _season_ids), and akar record audit-15.
FILE TOOLS directly. WRITE ONLY inside your workspace. 40 minutes.

## Deliverable: tools/render_dashboard.py (workspace copy)

The harness has refreshed the dashboard every close with a session-local
script; it dies with the session. Land it as maintained tooling:
- render the index (which also renders the discoveries pages), then every
  season that HAS a state file (the s15-rule: no state, no render, one
  logged skip reason per skipped season);
- atomic writes are already inside the report functions - do not add more;
- log one line per rendered artifact at INFO, one per skip at INFO;
- exit 0 when at least the index rendered; nonzero only on total failure;
- accept an optional root argument (default: cwd/.rumpun);
- the state-check rule comes from engine.state_path - import it, do not
  duplicate the path logic.

## Constraints

- logging, never print; ruff clean (line-length 100); py3.10+; stdlib.
- Do not modify src/ or tests/ (w2 owns the pins; the harness merges).
- The 129-test suite stays green.

## Verify before finishing

Repro: a fixture root with two stateful seasons + one stateless renders
2 reports + index + discoveries; a second consecutive run is
byte-identical (hash the outputs). Suite green. All in notes.md.
