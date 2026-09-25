
### s14/w1 — engine spawn tool-check

⚠️ **WARNING: EXPECTED/PROJECTED** — every claim below is authored blind. No log on disk was read by this worker; no suite was run.

#### 1. Blockers

- No file/exec tools (table above). Empirical signature comparison, replay, and suite run: **not performed**.
- Per task rules I did not fabricate a confusion matrix or diff context lines.

#### 2. Signature analysis — hypothesis, not verdict

- Task-cited shape of tool-less spawns: substantial streamed plan, zero file writes, exit 0.
- Discriminator family (one mechanism): *log is non-trivial AND carries no tool-invocation evidence*. Deterministic: substring markers only — no timestamps, pids, or varying paths.
- Two parameterizations, same mechanism; calibration table picks one:
  - **H1** generic markers (`tool_use`, `tool_result`, `function_call`).
  - **H2** file/exec-specific evidence (needed if tool-less logs contain non-file tool calls — my own s14/w1 transcript is exactly that case).
- I cannot certify a deterministic discriminator. Counterexamples require reading the corpora; whoever runs `replay_toolless.py` produces the deciding table in one command.

#### 3. Patch — authored blind, anchors described, context lines NOT fabricated

**New code, verbatim, insert in `src/rumpun/engine.py` near the other module helpers:**

```python
_TOOLLESS_MIN_BYTES = 512
# CALIBRATION: frozen from replay_toolless.py output over s3-s13 corpus.
# H1 default; switch to H2 markers if the table shows hits in the tool-less corpus.
_TOOL_EVIDENCE_MARKERS = (
    "tool_use",
    "tool_result",
    "function_call",
)


def log_signature_toolless(text: str) -> bool:
    """Classify an agent.log body as a tool-less spawn signature.

    True when the log holds substantial streamed content but shows no
    evidence of any tool invocation. Pure and deterministic: matches on
    literal markers only, never on timestamps, pids, or paths.
    """
    if len(text.strip()) < _TOOLLESS_MIN_BYTES:
        return False
    return not any(marker in text for marker in _TOOL_EVIDENCE_MARKERS)
```

**Watcher integration — reference implementation; snap key names are illustrative, bind to the real schema at merge:**

```python
def _check_toolless(self, snap: dict) -> None:
    """One tool-less check per watcher cycle for one live agent."""
    if snap.get("toolless") or snap.get("exit_file"):
        return
    log_path = Path(snap["workspace"]) / "agent.log"
    try:
        text = log_path.read_text(errors="replace")
    except FileNotFoundError:
        return
    if log_signature_toolless(text):
        snap["toolless"] = True
        logger.warning(
            "toolless spawn detected: season=%s worker=%s log=%s bytes=%d",
            snap.get("season"),
            snap.get("worker"),
            log_path,
            len(text),
        )
        self._lane_event(snap, "collab", "toolless-signature")
```

Insertion points (semantic anchors, since engine.py was unreadable from this spawn):

- Call `_check_toolless(snap)` inside the existing watcher cycle, per live agent, after the exit-file check, before the cycle's existing sleep. No new loop, no new cadence.
- `_lane_event` binds to the existing `_child_env` collab-lane wiring; one event per first positive.
- WARNING carries file path and byte count only — never log content or token values.
- Additive only: sets `snap["toolless"] = True`, rewrites no existing keys; `report.py`/`audit.py` untouched and must keep working unchanged.
- Re-check semantics: early-return guard means once marked, never re-evaluated, never unmarked; later exit files still classify the snap under existing rules.
- `logging` throughout; py3.10+; ruff line-length 100.

#### 4. Verification — scripts provided, NOT RUN by me

Save as a physical file and run from repo root:

```python
"""replay_toolless.py — replay the classifier over the s3-s13 rimba corpus.

Prints the confusion matrix against labeled corpora plus a per-marker
calibration table. Never prints log content or token values.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rumpun.engine import _TOOL_EVIDENCE_MARKERS, log_signature_toolless

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RIMBA = Path(".rumpun") / "rimba"
TOOLLESS = ("s4/w1", "s5/w2", "s6/w1", "s6/w3", "s7/w1", "s8/w2", "s12/w1")
CLEAN = ("s13/w1", "s13/w2", "s11/w1", "s11/w2")
CALIBRATION_MARKERS = (*_TOOL_EVIDENCE_MARKERS, "Write", "Edit", "Bash")


def read(ws: str) -> str:
    return (RIMBA / ws / "agent.log").read_text(errors="replace")


def main() -> None:
    tp = sum(log_signature_toolless(read(ws)) for ws in TOOLLESS)
    fn = len(TOOLLESS) - tp
    fp = sum(log_signature_toolless(read(ws)) for ws in CLEAN)
    tn = len(CLEAN) - fp
    logger.info("confusion: tp=%d fn=%d fp=%d tn=%d", tp, fn, fp, tn)
    for ws in TOOLLESS:
        if not log_signature_toolless(read(ws)):
            logger.error("miss toolless->clean: %s", ws)
    for ws in CLEAN:
        if log_signature_toolless(read(ws)):
            logger.error("miss clean->toolless: %s", ws)
    for marker in CALIBRATION_MARKERS:
        hits_t = sum(marker in read(ws) for ws in TOOLLESS)
        hits_c = sum(marker in read(ws) for ws in CLEAN)
        logger.info(
            "marker %r: toolless=%d/%d clean=%d/%d",
            marker,
            hits_t,
            len(TOOLLESS),
            hits_c,
            len(CLEAN),
        )
    all_logs = sorted(RIMBA.glob("s*/w*/agent.log"))
    for path in all_logs:
        logger.info(
            "corpus %s bytes=%d classified=%s",
            path.relative_to(RIMBA),
            path.stat().st_size,
            log_signature_toolless(path.read_text(errors="replace")),
        )


if __name__ == "__main__":
    main()
```

Suite check in a scratch copy (apply the patch there first):

```
tmp=$(mktemp -d) && cp -r . "$tmp" && cd "$tmp" && uv run pytest
```

Required result for merge: zero tool-less misses, zero clean false-positives, suite green. **Status: not run — no exec tool in this spawn.**

#### 5. w2 handoff — pinned contract

- `from rumpun.engine import log_signature_toolless`; pure `str -> bool`.
- Empty/short text → False. Non-trivial + no marker hits → True.
- Watcher calls it once per live agent per cycle, only while no exit file; first positive sets `snap["toolless"] = True`, one WARNING, one collab lane event; never unmarked; existing keys untouched.

#### 6. Future candidates (not built — one-mechanism rule)

- File/exec-specific marker regex (H2) if H1 under-detects; my s14/w1 log is the test case.
- Byte-offset memo to avoid re-reading full logs each cycle.
- State-based cross-check at finalize: marked toolless + no exit file + exit 0.

