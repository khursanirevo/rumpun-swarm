"""Warning-transition repro for s18 w1: count file-tool WARNINGs.

Synthetic stream: three separate watcher cycles each see one new file-tool
event (Read, Write, Bash). The fix logs the WARNING (and lane event) once on
the false->true transition; per-sighting alerting was the s17 live defect.
Run against the patched scratch tree:

    PYTHONPATH=/tmp/s18w1-scratch/src .venv/bin/python .rumpun/rimba/s18/w1/warn_repro.py

Exit 0 + PASS when exactly one WARNING and one lane event fired and the
mark/offset behavior is unchanged. Run with PYTHONPATH=<repo>/src instead to
see the unpatched behavior (three warnings).
"""

import json
import logging
import tempfile
from pathlib import Path

from rumpun import engine


def _stream_line(tool: str) -> str:
    event = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": f"call_{tool}",
                    "name": tool,
                    "input": {},
                }
            ],
        },
    }
    return json.dumps(event) + "\n"


class _Catch(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "proj" / ".rumpun"
        ws = root / "rimba" / "s1" / "w1"
        ws.mkdir(parents=True)
        (ws / "state.json").write_text(
            json.dumps(
                {
                    "name": "w1",
                    "route": "fable",
                    "cmd": "x",
                    "pid": 1,
                    "proc_start": 987654321,
                    "started_at": 0.0,
                    "collab": "dev",
                }
            ),
            encoding="utf-8",
        )
        log = ws / "agent.log"
        catch = _Catch()
        eng_logger = logging.getLogger("rumpun.engine")
        eng_logger.addHandler(catch)
        try:
            for tool in ("Read", "Write", "Bash"):
                with log.open("a", encoding="utf-8") as fh:
                    fh.write(_stream_line(tool))
                meta = json.loads(
                    (ws / "state.json").read_text(encoding="utf-8")
                )
                engine._scan_agent_stream(ws, meta)
        finally:
            eng_logger.removeHandler(catch)

        warnings = [
            r
            for r in catch.records
            if r.levelno == logging.WARNING and r.name == "rumpun.engine"
        ]
        lane = root / "rimba" / "s1" / "_season" / "lane-dev.jsonl"
        lane_lines = 0
        if lane.is_file():
            lane_lines = sum(
                1
                for line in lane.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        final = json.loads((ws / "state.json").read_text(encoding="utf-8"))
        print("engine module:", engine.__file__)
        print(f"WARNING count: {len(warnings)} (expect 1)")
        if warnings:
            print("warning text:", warnings[0].getMessage())
        print(f"lane file_tools events: {lane_lines} (expect 1)")
        print(f"file_tools: {final.get('file_tools')} (expect True)")
        print(
            f"stream_offset {final.get('stream_offset')} of "
            f"{log.stat().st_size} log bytes"
        )
        ok = (
            len(warnings) == 1
            and lane_lines == 1
            and final.get("file_tools") is True
            and final.get("stream_offset") == log.stat().st_size
        )
        print("PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
