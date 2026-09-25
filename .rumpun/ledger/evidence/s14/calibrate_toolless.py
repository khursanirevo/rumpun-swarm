"""Harness calibration: does ANY deterministic text rule separate the corpora?

Rule under test (w1 s14 H1/H2): toolless = bytes >= 512 AND no tool marker.
Prints per-log bytes, marker hits, rule verdict, and the known label from
akar glm-toolless-spawn + audit-2 + s14 close. Never prints log content.
"""
from pathlib import Path

RIMBA = Path("/mnt/data/work/rumpun/.rumpun/rimba")
TOOLLESS = {"s4/w1", "s5/w2", "s6/w1", "s6/w3", "s7/w1", "s8/w2", "s12/w1", "s14/w1"}
MARKERS = ("tool_use", "tool_result", "function_call", '"Write"', '"Edit"', '"Read"', '"Bash"')

tp = fn = fp = tn = 0
for path in sorted(RIMBA.glob("s*/w*/agent.log")):
    ws = str(path.relative_to(RIMBA).parent)
    label = "toolless" if str(ws) in TOOLLESS else "clean-or-other"
    text = path.read_text(errors="replace")
    hits = [m for m in MARKERS if m in text]
    verdict = len(text.strip()) >= 512 and not hits
    if label == "toolless":
        tp, fn = (tp + 1, fn) if verdict else (tp, fn + 1)
    elif verdict:
        fp += 1
    else:
        tn += 1
    print(f"{str(ws):8s} bytes={len(text):6d} label={label:14s} "
          f"rule={'toolless' if verdict else 'not-toolless'} hits={hits or '-'}")
print(f"\nconfusion: tp={tp} fn={fn} fp={fp} tn={tn}")
print("verdict: marker+size rule " + ("SEPARATES the corpora" if fp == 0 and fn == 0 else "FAILS"))
