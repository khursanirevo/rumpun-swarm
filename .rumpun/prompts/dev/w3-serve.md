# Task: add season report --serve and a self-identifying footer

Workspace: /mnt/data/work/rumpun/.rumpun/rimba/s4/w3. Write ONLY cli.py,
report.py, notes.md into this workspace. Do not touch anything outside it.

Base both files on the CURRENT repo files
/mnt/data/work/rumpun/src/rumpun/cli.py and
/mnt/data/work/rumpun/src/rumpun/report.py (read them first). Keep every
existing behavior and every existing test passing.

report.py:
- Add _footer(project: str, sid: str, state_sha: str) -> str: one html
  paragraph, class "footer": "project <project> · season <sid> · state
  sha256:<state_sha[:12]> [H]". Add a .footer css rule (muted color).
- render_report composes _document(status) and inserts the footer before
  "</body>" via str.replace; state_sha = sha256 of the season state.json
  bytes (engine.state_path), hexdigest. Deterministic: same state bytes,
  same HTML. _document itself stays unchanged.

cli.py:
- season report gains --serve: after rendering the report, serve the rimba
  directory over HTTP on 127.0.0.1:8611 with
  http.server.ThreadingHTTPServer + functools.partial(SimpleHTTPRequestHandler,
  directory=...). Print the exact URL: http://localhost:8611/<sid>/report.html
  then serve until KeyboardInterrupt; on Ctrl-C exit 0 cleanly. One log line
  on start. No new dependencies.

Rules: stdlib only; logging, never print (the URL print is allowed: it is
the verb's output). ruff clean, line-length 100, py3.10+. notes.md: what
you changed, what you tested, what remains manual.
