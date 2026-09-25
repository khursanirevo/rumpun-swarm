# s37 w1 — tools/coldstart_check.py notes

Shipped: tools/coldstart_check.py (340 lines, stdlib only, logging only).
It runs the README quickstart end to end in a temp dir against a stub sh
route: init, minimal edit, lint, season start, harvest, audit.

Verification, all measured this session:

- ✅ Checker run: 6/6 steps PASS, exit 0. Temp dir kept:
  /mnt/data/tmp/rumpun-coldstart-pwxgcx3i
- ✅ Artifacts on disk in that temp dir: akar 2026-09-15_s1-harvest.md and
  2026-09-15_audit-1.md; rimba/s1/verdicts.jsonl season row WIN;
  stub results.jsonl rows in both benih workspaces (a1, a2).
- ✅ Fault injection: --init-target on a read-only dir -> exit 1, "STEP 1 FAIL"
  logged with the PermissionError context, temp dir still printed.
- ✅ ruff check --no-respect-gitignore: All checks passed (rc 0).
- ✅ Suite: 175 passed in 52.71s, rc 0 (.venv/bin/python -m pytest tests/ -q).

Interface notes for the w2 pins:

- Per-step lines: "STEP <n> PASS/FAIL: <command>"; summary "COLDSTART CHECK:
  6/6 steps PASS"; the temp path is on the "temp dir:" line, PASS or FAIL.
- --init-target DIR exists for the sabotaged-init pin (read-only DIR).
- The CLI runs as sys.executable -m rumpun, cwd at the temp project.

Incident: three corrupted single-shot Write calls while emitting this file
(truncated call paren, placeholder body, garbled duplicates). Recovered by
rm plus 22 chunked quoted-heredoc appends (<=15 lines) with per-chunk tail
readback; the final file was read back clean before any gate ran. Logged in
the verify-state-writes memory.
