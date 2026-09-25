"""s16 w1 scratch replay: patched engine stream scan + finalize over fixtures.

Fixtures: copies of both real s15 streams (fresh offsets), two synthetic
branches (text-only log, ToolSearch-only stream), and one incremental
two-pass replay of a truncated-then-completed stream. Also an A/B finalize
byte-compare: base repo engine vs patched engine on an identical synthetic
season, comparing _season/state.json bytes and the read_status dict bytes.

Run from repo root: uv run python .rumpun/rimba/s16/w1/replay.py
Results: .rumpun/rimba/s16/w1/replay-results.json (atomic write).
"""
from __future__ import annotations

import importlib.util
import json
import logging
import shutil
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent
REPO = Path("/mnt/data/work/rumpun")
SCRATCH = WS / "scratch"
S15 = REPO / ".rumpun" / "rimba" / "s15"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("replay")


def load_engine(tag: str, path: Path):
    """Load one engine.py as its own module; log which file was loaded."""
    spec = importlib.util.spec_from_file_location(f"engine_{tag}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"engine_{tag}"] = mod
    spec.loader.exec_module(mod)
    logger.info("loaded engine_%s from %s", tag, path)
    logger.info("engine_%s.__file__ = %s", tag, mod.__file__)
    return mod


def make_ws(root: Path, sid: str, name: str, log_src: Path | None) -> Path:
    """One workspace under root/rimba/sid/name: log copy + bare meta."""
    ws = root / "rimba" / sid / name
    ws.mkdir(parents=True)
    if log_src is not None:
        shutil.copyfile(log_src, ws / "agent.log")
    else:
        (ws / "agent.log").write_text("hello\nworld\n", encoding="utf-8")
    meta = {
        "name": name,
        "route": "fable",
        "pid": 1,
        "proc_start": None,
        "started_at": 0.0,
    }
    (ws / "state.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return ws


def run_scan_flow(engine, ws: Path) -> dict:
    """Fresh-offset scan, read-back, then finalize; full observation dict."""
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    engine._scan_agent_stream(ws, meta)
    after_scan = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    root, sid = ws.parents[2], ws.parent.name
    engine._finalize_agent_stream(root, sid, ws)
    after_fin = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    text = (ws / "agent.log").read_text(encoding="utf-8", errors="replace")
    return {
        "scan": {
            "file_tools": after_scan.get("file_tools", "absent"),
            "stream_offset": after_scan.get("stream_offset", "absent"),
        },
        "finalize": {
            "file_tools": after_fin.get("file_tools", "absent"),
            "stream_offset": after_fin.get("stream_offset", "absent"),
        },
        "log_size": (ws / "agent.log").stat().st_size,
        "parseable_events": sum(1 for _ in engine._parse_stream_events(text)),
        "tool_names": sorted(engine.stream_tool_names(text)),
    }


def main() -> int:
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    results: dict = {"engine_loaded": str(WS / "engine.py")}
    patched = load_engine("patched", WS / "engine.py")

    # 1+2: the two real s15 streams, fresh offsets.
    for name in ("w1", "w2"):
        ws = make_ws(SCRATCH, "replay", name, S15 / name / "agent.log")
        results[name] = run_scan_flow(patched, ws)
        logger.info(
            "%s: scan file_tools=%s offset=%s; finalize file_tools=%s; "
            "events=%d names=%s",
            name,
            results[name]["scan"]["file_tools"],
            results[name]["scan"]["stream_offset"],
            results[name]["finalize"]["file_tools"],
            results[name]["parseable_events"],
            results[name]["tool_names"],
        )

    # 3: text-only log -> zero parseable events -> key stays absent.
    ws = make_ws(SCRATCH, "replay", "w3", None)
    results["w3_text_only"] = run_scan_flow(patched, ws)
    logger.info("w3_text_only: %s", json.dumps(results["w3_text_only"]))

    # 4: ToolSearch-only stream -> parseable events, never a file tool.
    ws = make_ws(SCRATCH, "replay", "w4", None)
    (ws / "agent.log").write_text(
        json.dumps({"type": "system", "subtype": "boot"}) + "\n"
        + json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "id": "t1", "name": "ToolSearch"}
                    ],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    results["w4_toolsearch_only"] = run_scan_flow(patched, w4 := ws)
    logger.info("w4_toolsearch_only: %s", json.dumps(results["w4_toolsearch_only"]))

    # 5: incremental: truncated stream (cuts mid-line), scan, append, scan.
    ws = make_ws(SCRATCH, "replay", "w5", None)
    full = (S15 / "w1" / "agent.log").read_bytes()
    (ws / "agent.log").write_bytes(full[:4096])
    meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    engine_scan_offsets = []
    patched._scan_agent_stream(ws, meta)
    engine_scan_offsets.append(
        json.loads((ws / "state.json").read_text(encoding="utf-8")).get(
            "stream_offset"
        )
    )
    with (ws / "agent.log").open("ab") as fh:
        fh.write(full[4096:])
    patched._scan_agent_stream(ws, meta)
    second_meta = json.loads((ws / "state.json").read_text(encoding="utf-8"))
    results["w5_incremental"] = {
        "offset_after_scan1": engine_scan_offsets[0],
        "offset_after_scan2": second_meta.get("stream_offset"),
        "file_tools": second_meta.get("file_tools", "absent"),
        "log_size": (ws / "agent.log").stat().st_size,
    }
    logger.info("w5_incremental: %s", json.dumps(results["w5_incremental"]))

    # 6: A/B finalize bytes: base engine vs patched engine, same season.
    for tag, path in (("base", REPO / "src/rumpun/engine.py"), ("patched", WS / "engine.py")):
        root = SCRATCH / f"ab-{tag}"
        ws = make_ws(root, "s99", "t1", None)
        (ws / "agent.log").write_text(
            json.dumps({"type": "system"}) + "\n"
            + json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "id": "t2", "name": "WebFetch"}
                        ],
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        eng = load_engine(tag, path)
        root.mkdir(parents=True, exist_ok=True)
        season = root / "rimba" / "s99" / "_season"
        season.mkdir(parents=True, exist_ok=True)
        season.joinpath("state.json").write_text(
            json.dumps(
                {
                    "id": "s99",
                    "status": "running",
                    "started_at": 0.0,
                    "spawned": {"t1": {"pid": 1, "proc_start": None}},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        eng._finalize(root, "s99", "completed", {})
        results[f"ab_{tag}"] = {
            "season_state": json.loads(
                (season / "state.json").read_text(encoding="utf-8")
            ),
            "read_status": eng.read_status(root, "s99"),
        }

    def _norm(obj: dict) -> str:
        """Serialization for content compare; ended_at is wall-clock timing."""
        return json.dumps(
            {k: v for k, v in obj.items() if k != "ended_at"}, sort_keys=True
        )

    base_ab, patched_ab = results["ab_base"], results["ab_patched"]
    same_state = _norm(base_ab["season_state"]) == _norm(patched_ab["season_state"])
    same_status = _norm(base_ab["read_status"]) == _norm(patched_ab["read_status"])
    results["ab_bytes_identical"] = {
        "season_state": same_state,
        "read_status": same_status,
        "ended_at_only_delta": (
            base_ab["season_state"].get("ended_at")
            != patched_ab["season_state"].get("ended_at")
        ),
    }
    logger.info("ab_bytes_identical: %s", json.dumps(results["ab_bytes_identical"]))

    tmp = WS / "replay-results.json.tmp"
    tmp.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    tmp.replace(WS / "replay-results.json")
    logger.info("results written to %s", WS / "replay-results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
