"""Build the s14 w2 test deliverable from the repo test file.

Reads tests/test_rumpun.py, inserts the s14 toolcheck section (docstring
paragraph, three stdlib imports, one appended test section), and writes
test_rumpun.py into this workspace. The corpus constants are generated as
byte-exact Python literals from the recorded rimba agent.logs, so any
classifier that classifies the akar corpus correctly classifies them the
same way. The build refuses to write unless the diff against the repo file
is additions-only.
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("make_tests")

# <repo>/.rumpun/rimba/s14/w2/make_tests.py -> repo root is parents[4].
REPO = Path(__file__).resolve().parents[4]
WORKSPACE = Path(__file__).resolve().parent
BASE = REPO / "tests" / "test_rumpun.py"

CORPUS = {
    "TOOLLESS_LOG_S12": ("s12/w1", True),
    "TOOLLESS_LOG_S4": ("s4/w1", True),
    "CLEAN_LOG_S13": ("s13/w2", False),
    "CLEAN_LOG_S11": ("s11/w1", False),
}

DOCSTRING_PARA = """\
The toolcheck tests are spec-first (s14, w2): log_signature_toolless lands
at integration (w1's detector) under the ratified contract — a pure bool
classifier over agent.log text (recorded tool-less corpus true, recorded
clean logs false, empty and whitespace-only false, the signature true even
surrounded by clean content, the shared two-line boot header false); the
existing watcher cycle sets snap["toolless"] = true in _season/state.json
while the season still runs, never unsets it (a later clean-looking log
does not clear the mark), and the snap still finalizes by the pre-s14
rules; the mark is an additive key — report._document output and
run_audit's F4 route counts are identical with and without it; and the
detector rides the existing watcher cycle (spy, no extra threads, source
wired at the snap path), never a new poller. Corpus fixtures are byte-
exact copies of the recorded rimba agent.logs (tool-less s4/w1 and s12/w1;
clean s11/w1 and s13/w2) that the s14 band replays over.
"""

# '''-quoted on purpose: the section body itself uses """ docstrings.
# Raw on purpose: the body contains \n escapes that must survive verbatim.
SECTION = r'''

# --- spawn tool-check (w2 s14 scope, spec-first) --------------------------------
#
# Contract source: musim/s14.yaml primary_change band + akar records
# glm-toolless-spawn and audit-2 (candidate 1). rumpun.engine lands
# log_signature_toolless at integration (w1's detector); these tests pin
# the ratified shape and are expected to FAIL against current code.
#
# The corpus constants below are byte-exact copies of the recorded rimba
# agent.logs the s14 band replays over. Any deterministic classifier that
# classifies the akar corpus per its band (tool-less corpus true, clean
# deliverable logs false) classifies these copies the same way; the
# surrounded-by-clean case additionally pins presence-based semantics.

def _toolcheck_yaml(route_cmd):
    """One-route rumpun.yaml whose glm command is route_cmd verbatim."""
    return (
        "autonomy:\n"
        "  stage: manual\n"
        "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
        "routes:\n"
        f'  glm: "{route_cmd}"\n'
    )


def _mark_walk(obj):
    """True when any dict inside obj carries "toolless": True.

    Shape-agnostic on purpose: mid-run storage of live snaps is w1's to
    choose, the contract only demands the mark lands in _season/state.json.
    """
    if isinstance(obj, dict):
        if obj.get("toolless") is True:
            return True
        return any(_mark_walk(v) for v in obj.values())
    return False


def _wait_state(root, sid, pred, timeout):
    """Poll _season/state.json until pred(state) or deadline; last state."""
    path = engine.state_path(root, sid)
    deadline = time.monotonic() + timeout
    state = None
    while time.monotonic() < deadline:
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = None
        if state is not None and pred(state):
            return state
        time.sleep(0.05)
    return state


def _season_subprocess(tmp_path, route_cmd):
    """One-benih season through the CLI, dual-start style; returns the proc."""
    root, season = _write_proj(
        tmp_path, SEASON_S1, project_yaml=_toolcheck_yaml(route_cmd)
    )
    cmd = [sys.executable, "-m", "rumpun", "season", "start", str(season)]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(tmp_path),
    )
    return proc, root


@pytest.mark.parametrize("text", [TOOLLESS_LOG_S12, TOOLLESS_LOG_S4])
def test_log_signature_toolless_true_on_recorded_toolless_logs(text):
    """Tool-less signature present -> true, over the recorded corpus."""
    assert engine.log_signature_toolless(text) is True


@pytest.mark.parametrize("text", [CLEAN_LOG_S13, CLEAN_LOG_S11])
def test_log_signature_toolless_false_on_recorded_clean_logs(text):
    """A clean boot log (deliverable-producing agent) -> false."""
    assert engine.log_signature_toolless(text) is False


@pytest.mark.parametrize("text", ["", "   \n\t\n", "\n \n"])
def test_log_signature_toolless_false_on_empty_and_whitespace(text):
    """Empty and whitespace-only input never classify as tool-less."""
    assert engine.log_signature_toolless(text) is False


def test_log_signature_toolless_true_when_signature_surrounded_by_clean():
    """The signature stays detected inside clean content: presence-based.

    The first form is clean-before-and-after (the log "grew" the signature
    between clean chunks); the second is the tool-less log followed by a
    clean tail. Both pin that detection keys on the signature's presence,
    not on what surrounds it.
    """
    assert engine.log_signature_toolless(
        CLEAN_LOG_S13 + TOOLLESS_LOG_S12 + CLEAN_LOG_S11
    ) is True
    assert engine.log_signature_toolless(TOOLLESS_LOG_S4 + CLEAN_LOG_S13) is True


def test_log_signature_toolless_false_on_shared_boot_header():
    """The boot header every log shares is not itself the signature.

    Both corpora open with these exact two lines, so a classifier that
    fired on them alone would mark every clean boot tool-less.
    """
    assert engine.log_signature_toolless(BOOT_HEADER) is False


def test_log_signature_toolless_repeated_calls_agree():
    """Pure classifier: identical input, identical bool, every call."""
    for text in (TOOLLESS_LOG_S12, CLEAN_LOG_S13):
        first = engine.log_signature_toolless(text)
        assert engine.log_signature_toolless(text) is first


def test_watcher_marks_toolless_snap_and_finalizes(tmp_path):
    """A live snap whose agent.log grows the signature is marked, then
    finalizes by the existing rules with the mark still in place.

    The route cats the recorded tool-less log into agent.log and stays
    alive: the watcher must put the toolless mark into _season/state.json
    while the season still runs (spawn-time detection, the s14 goal — not
    a close-time one), and the snap must still reach exited/completed.
    """
    sig = tmp_path / "toolless-agent.log"
    sig.write_text(TOOLLESS_LOG_S12, encoding="utf-8")
    proc, root = _season_subprocess(tmp_path, f"cat '{sig}'; sleep 8")
    try:
        seen = _wait_state(root, "s1", _mark_walk, 30.0)
        assert seen is not None and _mark_walk(seen), (
            "toolless mark never appeared in state.json; "
            f"last state: {json.dumps(seen)}"
        )
        assert seen.get("status") == "running", (
            "mark only appeared after the season left running: "
            "detection is not at spawn time"
        )
        _out, err = proc.communicate(timeout=120)
    except BaseException:
        proc.kill()
        raise
    assert proc.returncode == 0, f"season start failed; stderr: {err}"
    final = json.loads(engine.state_path(root, "s1").read_text(encoding="utf-8"))
    assert final["status"] == "completed"
    snap = final["agents"]["w1"]
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert snap["toolless"] is True


def test_watcher_toolless_mark_never_unset_by_log_change(tmp_path):
    """Once marked, the mark survives the log later looking clean.

    The route writes the tool-less log, lets the watcher mark it, then
    overwrites agent.log with a clean boot log before exiting 0. The
    finalized snap must keep toolless true: never unset, even though the
    on-disk log no longer carries the signature at close.
    """
    sig = tmp_path / "toolless-agent.log"
    sig.write_text(TOOLLESS_LOG_S12, encoding="utf-8")
    clean = tmp_path / "clean-agent.log"
    clean.write_text(CLEAN_LOG_S13, encoding="utf-8")
    log_path = tmp_path / "proj" / ".rumpun" / "rimba" / "s1" / "w1" / "agent.log"
    route = f"cat '{sig}'; sleep 4; cat '{clean}' > '{log_path}'; sleep 3"
    proc, root = _season_subprocess(tmp_path, route)
    try:
        _out, err = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        _out, err = proc.communicate()
        pytest.fail(f"season start did not finish in 120s; stderr={err}")
    assert proc.returncode == 0, f"season start failed; stderr: {err}"
    assert log_path.read_text(encoding="utf-8") == CLEAN_LOG_S13  # flip really ran
    final = json.loads(engine.state_path(root, "s1").read_text(encoding="utf-8"))
    assert final["status"] == "completed"
    snap = final["agents"]["w1"]
    assert snap["state"] == "exited"
    assert snap["toolless"] is True


def test_watcher_clean_agent_log_gets_no_toolless_mark(tmp_path):
    """A clean boot log never sets the mark; finalize stays on the old rules.

    Control for the watcher marking tests: no signature, no mark, and the
    snap finalizes exactly as before s14. Green against current code by
    design (nothing marks today); guards the patch against over-marking.
    """
    clean = tmp_path / "clean-agent.log"
    clean.write_text(CLEAN_LOG_S13, encoding="utf-8")
    proc, root = _season_subprocess(tmp_path, f"cat '{clean}'; sleep 3")
    try:
        _out, err = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        _out, err = proc.communicate()
        pytest.fail(f"season start did not finish in 120s; stderr={err}")
    assert proc.returncode == 0, f"season start failed; stderr: {err}"
    final = json.loads(engine.state_path(root, "s1").read_text(encoding="utf-8"))
    assert final["status"] == "completed"
    snap = final["agents"]["w1"]
    assert snap["state"] == "exited"
    assert snap["exit_code"] == 0
    assert snap.get("toolless") is not True


def test_watcher_classifies_live_agents_from_existing_cycle(tmp_path, monkeypatch):
    """The detector rides the existing watcher cycle, not a new poller.

    With the classifier spied to False, one live agent holding a non-empty
    log is classified at least twice across watcher cycles (~3s live
    window), the engine leaves no poller thread behind, and the classifier
    is wired into the watcher's snap path (an engine function whose source
    also touches agent.log or the snap machinery). Structure-level by
    contract: no wall-clock cadence is asserted.
    """
    seen: list[int] = []

    def spy(text):
        seen.append(len(text))
        return False

    monkeypatch.setattr(engine, "log_signature_toolless", spy)
    clean = tmp_path / "clean-agent.log"
    clean.write_text(CLEAN_LOG_S13, encoding="utf-8")
    root, season = _write_proj(
        tmp_path, SEASON_S1, project_yaml=_toolcheck_yaml(f"cat '{clean}'; sleep 3")
    )
    before = threading.active_count()
    state = engine.start_season(season, root)
    assert state["status"] == "completed"
    assert len(seen) >= 2, f"classifier ran {len(seen)} time(s) for a live agent"
    assert threading.active_count() == before, "a poller thread outlived the season"
    wired = False
    for obj in vars(engine).values():
        if inspect.isfunction(obj) and obj.__module__ == engine.__name__:
            src = inspect.getsource(obj)
            if "log_signature_toolless" in src and any(
                token in src for token in ("_agent_snap", "snaps", "agent.log")
            ):
                wired = True
    assert wired, "classifier is not wired into the watcher snap path"


def test_report_document_unchanged_by_toolless_mark():
    """A snap carrying the additive toolless key renders the same bytes."""
    status = {
        "id": "s1",
        "status": "completed",
        "started_at": 1.0,
        "ended_at": 2.0,
        "agents": {
            "w1": {
                "name": "w1",
                "route": "glm",
                "state": "exited",
                "exit_code": 0,
                "seconds": 1.0,
            }
        },
    }
    marked = {
        **status,
        "agents": {"w1": {**status["agents"]["w1"], "toolless": True}},
    }
    base = report._document(status)
    doc = report._document(marked)
    assert doc == base  # the mark must not leak into the rendered report
    assert report._document(marked) == doc  # determinism holds with the mark


def test_audit_f4_route_counts_unchanged_by_toolless_mark(tmp_path):
    """run_audit's F4 outcome counts ignore the additive toolless mark.

    Same fixture, two audit runs, the only delta being toolless: true
    stamped onto both finalized snaps between them: the per-route line
    must come out identical.
    """
    root = _write_audit_proj(tmp_path)
    _write_rimba_season(root, "s1")
    _write_rimba_season(root, "s2")
    _write_spawn(root, "s1", "t1", "glm", "clean-deliverable")
    _write_spawn(root, "s2", "t2", "glm", "clean-empty")
    want = (
        "route glm: 1 clean-deliverable, 1 clean-empty, 0 failed, "
        "0 not-exited over 2 spawns"
    )
    before = audit.run_audit(root).read_text(encoding="utf-8")
    assert want in before
    for sid, name in (("s1", "t1"), ("s2", "t2")):
        path = root / "rimba" / sid / "_season" / "state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["agents"][name]["toolless"] = True
        path.write_text(json.dumps(state), encoding="utf-8")
    after = audit.run_audit(root).read_text(encoding="utf-8")
    glm_before = [ln for ln in before.splitlines() if "route glm:" in ln]
    glm_after = [ln for ln in after.splitlines() if "route glm:" in ln]
    assert glm_after == glm_before
    assert want in after
'''


def constant_block(name: str, log_dir: str, is_toolless: bool) -> str:
    """Render one agent.log as a parenthesized byte-exact Python literal."""
    raw = (REPO / ".rumpun" / "rimba" / log_dir / "agent.log").read_bytes()
    text = raw.decode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    kind = "tool-less boot" if is_toolless else "clean boot"
    lines = [
        f"# Byte-exact copy of .rumpun/rimba/{log_dir}/agent.log "
        f"({kind}, akar",
        f"# glm-toolless-spawn corpus); sha256 {digest}",
        f"{name} = (",
    ]
    for line in text.splitlines(keepends=True):
        piece = line
        first = True
        while piece:
            take = piece
            while len(repr(take)) + 4 > 96:
                take = take[: max(1, (len(take) * 95) // 100)]
            lines.append(f"    {repr(take)}")
            piece = piece[len(take):]
            first = False
        if first:  # pragma: no cover - splitlines(keepends) never yields ""
            lines.append('    ""')
    lines.append(")")
    return "\n".join(lines) + "\n"


def build_constants() -> str:
    blocks = [constant_block(name, log, tool) for name, (log, tool) in CORPUS.items()]
    full = (REPO / ".rumpun" / "rimba" / "s13" / "w2" / "agent.log").read_text(
        encoding="utf-8"
    )
    header = "".join(full.splitlines(keepends=True)[:2])
    for log, _tool in CORPUS.values():
        other = (REPO / ".rumpun" / "rimba" / log / "agent.log").read_text(
            encoding="utf-8"
        )
        if not other.startswith(header):
            msg = f"shared boot header is not a prefix of {log}"
            raise SystemExit(msg)
    blocks.append(
        "# The two boot lines every recorded log (both corpora) opens with;\n"
        "# sha256 of the two-line prefix "
        f"{hashlib.sha256(header.encode('utf-8')).hexdigest()}\n"
        "BOOT_HEADER = (\n"
        + "".join(f"    {line!r}\n" for line in header.splitlines(keepends=True))
        + ")"
    )
    return "\n\n".join(blocks) + "\n"


def main() -> int:
    base = BASE.read_text(encoding="utf-8")
    assert base.endswith("\n"), "repo test file lost its trailing newline"

    doc_anchor = 'and musim/ plus rimba/ still byte-identical after run_audit.\n"""\n'
    assert base.count(doc_anchor) == 1, "docstring anchor not unique"
    para = DOCSTRING_PARA.rstrip("\n")
    step1 = base.replace(
        doc_anchor,
        f'and musim/ plus rimba/ still byte-identical after run_audit.\n\n{para}\n"""\n',
    )

    anchor_imports = "import hashlib\nimport json\nimport subprocess\nimport sys\n"
    assert step1.count(anchor_imports) == 1, "import anchor not unique"
    step2 = step1.replace(
        anchor_imports,
        "import hashlib\nimport inspect\nimport json\n"
        "import subprocess\nimport sys\nimport threading\nimport time\n",
    )

    built = step2.rstrip("\n") + "\n" + build_constants() + SECTION.rstrip("\n") + "\n"

    diff = list(
        difflib.unified_diff(base.splitlines(), built.splitlines(), lineterm="", n=0)
    )
    changed = [ln for ln in diff if ln[:1] in ("+", "-") and not ln.startswith(("+++", "---"))]
    removed = [ln for ln in changed if ln.startswith("-")]
    if removed:
        for ln in removed:
            logger.error("non-addition line: %s", ln)
        return 1

    tree = ast.parse(built)
    funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    test_funcs = [f for f in funcs if f.startswith("test_")]
    base_funcs = [
        n.name
        for n in ast.parse(base).body
        if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
    ]
    kept = [f for f in test_funcs if f in base_funcs]
    logger.info(
        "base test functions kept: %d/%d; total test functions: %d",
        len(kept), len(base_funcs), len(test_funcs),
    )

    out = WORKSPACE / "test_rumpun.py"
    out.write_text(built, encoding="utf-8")
    logger.info("wrote %s (%d bytes)", out, len(built.encode("utf-8")))
    logger.info("added lines: %d; removed lines: 0", len(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
