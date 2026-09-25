"""s61 w2 pins — the pipeline's truth, specified before it exists.

Spec-first pins (red against current code) for the s61 contract (season
goal .rumpun/seasons/s61.yaml; w1 brief .rumpun/prompts/dev/
w1-pipeline-truth.md; ledger anchors 2026-09-16_s60-harvest and
2026-09-16_audit-41 — the phase-liveness candidate: results.jsonl written
in 0 of 10 engine seasons while every yaml declares execute->evaluate).
Spec anchors, the measured red set, and surface assumptions:
.rumpun/runs/s61/w2/notes.md.

Contract these pins hold — every pin runs the real verbs end to end
(`rumpun season start` / `rumpun lint` / `rumpun audit` as bounded
subprocesses over tmp .rumpun projects):

1. Whatever route w1 takes, the new truth holds one way or the other:
   either a season run through the pipeline path lands results.jsonl in
   its ledger dir (.rumpun/runs/<sid>/results.jsonl, non-empty), or a
   season yaml without the pipeline block lints clean and starts to a
   terminal state. Neither holds on main today.
2. The finding retires honestly: a fresh `rumpun audit` over a synthetic
   two-season campaign no longer arms the "exercise or trim phase
   execute" candidate — either because the exercised seasons count in
   the F1 numerator (EXERCISE), or because the trimmed campaign carries
   no declared pipeline at all (TRIM).
3. No regression: the falsify gate still demands a reachable reader for
   any DECLARED write (a pipeline whose evaluate reads an artifact
   nothing writes must lint-fail naming falsify_required), and the s60
   stall_stop record shape is untouched (rule text, stall_s match, and
   the dead-agent evidence: empty sources, no tool_use, ws_bytes
   baseline, last_progress_age_s >= the stall window).

Red history (measured; full runs in notes.md): w1's EXERCISE
implementation landed in the shared tree (src/rumpun/engine.py,
_write_results) before this file's first clean run, so the live-tree
measurement is 4/4 green: pin 1 holds on the EXERCISE branch
(results.jsonl lands non-empty at the season ledger), pin 2 on the
EXERCISE retirement (fresh audit: no candidate; F1 counts 2 of 2).
The spec-first red set was measured against a HEAD 1dd951d extraction:
pins 1 and 2 red on the TRIM half — the completed season left no ledger
artifact and the pipeline-less yaml was refused at lint
("methodology.pipeline must be a non-empty list of nodes"); pins 3a and
3b green at HEAD (the guards the season must not weaken). Campaign A's
fresh audit on HEAD was read but its arming was not separately
asserted; audit-41's arming on the real campaign is the ledger-recorded
evidence.

Grafting: drop this file into tests/ as-is. Helpers carry the _s61w2_
prefix, so nothing collides with existing defs. No pin touches the real
repo, ledger, or any live season: every fixture lives in pytest
tmp_path. Each run is bounded twice — S61W2_TIMEOUT on the subprocess
and each benih's own 1-minute budget inside the engine — and the dead
stub self-exits at 91s, so a wedged engine ends the run itself and the
suite never hangs.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

S61W2_TIMEOUT = 120  # bounds one subprocess; the benih budget bounds it harder
S61W2_STALL_MINUTES = 0.1  # the 6s stall window pin 3b exercises
S61W2_SID_A = "s611"  # lint requires the s<N> id shape; no real row is touched
S61W2_SID_B = "s612"

S61W2_ROUTES = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  stub: 'printf ''%s\\n'' ''{"unit":"u1","verdict":"PASS"}'' > results.jsonl'
  plain: 'cat {prompt} > /dev/null'
  dead: 'i=0; while [ "$i" -le 90 ]; do i=$((i+1)); sleep 1; done'
"""

S61W2_PIPELINE_YAML = """\
id: {sid}
goal: "fixture"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    rollback: "git revert"
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
writers:
  - name: w1
    route: {route}
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [{stop}]
"""

S61W2_TRIM_YAML = """\
id: {sid}
goal: "fixture"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    rollback: "git revert"
    eval_window: "{sid}"
writers:
  - name: w1
    route: {route}
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [{stop}]
"""

S61W2_UNREACHABLE_YAML = """\
id: {sid}
goal: "fixture"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
    rollback: "git revert"
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agent: judge
      prompt: prompts/dev/dummy.md
      reads: measurements.jsonl
      writes: verdicts.jsonl
writers:
  - name: w1
    route: plain
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""


def _s61w2_root() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s61w2_proj(tmp_path: Path) -> tuple[Path, Path]:
    """One tmp campaign (.rumpun layout) under a fresh directory.

    Returns (project dir, .rumpun root). The routes are shell stubs: `stub`
    consumes the prompt, writes one results.jsonl row in its own workspace,
    and exits 0 (raw material for an EXERCISE implementation to promote);
    `plain` consumes the prompt and exits 0; `dead` prints and writes
    nothing for 91s. The 1-minute benih budget bounds any wedged watcher
    inside the engine itself.
    """
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    (root / "runs").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S61W2_ROUTES, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    return root.parent, root


def _s61w2_season(
    root: Path, sid: str, template: str, route: str, stop: str,
) -> Path:
    """Write one season yaml into the campaign's seasons dir; return its path."""
    season = root / "seasons" / f"{sid}.yaml"
    season.write_text(
        template.format(sid=sid, route=route, stop=stop), encoding="utf-8",
    )
    return season


def _s61w2_env() -> dict[str, str]:
    """Subprocess env: PYTHONPATH pins the repo src over any editable .pth."""
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        str(_s61w2_root() / "src") + os.pathsep + env.get("PYTHONPATH", "")
    )
    return env


def _s61w2_run(proj: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    """One bounded CLI verb over the campaign; cwd = the project dir, so the
    audit's root walk-up from cwd resolves this campaign."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(proj), env=_s61w2_env(), capture_output=True, text=True,
        timeout=S61W2_TIMEOUT,
    )


def _s61w2_start(tmp_path: Path, season: Path) -> subprocess.Popen[str]:
    """Launch the watcher CLI over the fixture; PYTHONPATH pins the repo src."""
    return subprocess.Popen(
        [sys.executable, "-m", "rumpun", "season", "start", str(season)],
        cwd=str(tmp_path), env=_s61w2_env(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )


def _s61w2_terminal(proc: subprocess.Popen[str], root: Path, sid: str) -> dict[str, Any]:
    """Bounded wait for any terminal status; the persisted state, read fresh.

    The watcher rewrites state.json atomically (tmp + replace), so a read
    is never torn; polling stops at the first terminal status.
    """
    state_path = root / "runs" / sid / "_season" / "state.json"

    def read_terminal() -> dict[str, Any] | None:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return None if state.get("status") == "running" else state

    deadline = time.monotonic() + S61W2_TIMEOUT
    while time.monotonic() < deadline:
        state = read_terminal()
        if state is not None:
            return state
        if proc.poll() is not None:
            _out, err = proc.communicate(timeout=30)
            raise AssertionError(
                f"watcher exited before a terminal state (rc={proc.returncode});"
                f" stderr:\n{err}"
            )
        time.sleep(0.05)
    raise AssertionError(
        f"season {sid} never reached a terminal state in {S61W2_TIMEOUT}s"
    )


def _s61w2_finish(proc: subprocess.Popen[str]) -> tuple[int, str]:
    """Drain the watcher subprocess, bounded; (returncode, stderr)."""
    try:
        _out, err = proc.communicate(timeout=S61W2_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise
    return proc.returncode, err


def _s61w2_complete(
    tmp_path: Path, root: Path, sid: str, season: Path,
) -> tuple[dict[str, Any], int, str]:
    """Run one season start to a terminal state; (state, watcher rc, stderr)."""
    proc = _s61w2_start(tmp_path, season)
    state = _s61w2_terminal(proc, root, sid)
    rc, err = _s61w2_finish(proc)
    return state, rc, err


def _s61w2_audit(proj: Path, root: Path) -> str:
    """One fresh `rumpun audit` over the campaign; the new record's text."""
    ran = _s61w2_run(proj, "audit", "--last", "10")
    assert ran.returncode == 0, (
        f"rumpun audit exited {ran.returncode}; stderr:\n{ran.stderr}"
    )
    records = sorted((root / "ledger").glob("*audit-*.md"))
    assert records, f"the audit wrote no record into {root / 'ledger'}"
    return records[-1].read_text(encoding="utf-8")


def _s61w2_armed(record: str) -> list[str]:
    """The record's candidate lines that arm the phase-liveness trigger."""
    return [
        line
        for line in record.splitlines()
        if line.startswith("candidate:") and "exercise or trim phase" in line
    ]


# --- pin 1: the pipeline tells the truth, one way or the other ------------------


def test_s61w2_pipeline_truth_route_holds(tmp_path: Path) -> None:
    """EXERCISE or TRIM: whichever route lands, its truth must hold.

    A pipeline-declaring season runs end to end over a real campaign. If
    the season's ledger lands results.jsonl (non-empty), the EXERCISE
    route is live and the pin holds there. Otherwise the TRIM route must
    be live: a pipeline-less yaml lints with zero errors and the same
    start path takes it to a completed season. On main today neither
    holds: the completed season leaves no ledger artifact, and the
    pipeline-less yaml is refused at lint (methodology.pipeline is
    required), so the pin is red until w1's change lands.
    """
    _proj, root = _s61w2_proj(tmp_path)
    season = _s61w2_season(
        root, S61W2_SID_A, S61W2_PIPELINE_YAML, "stub", "all_exited",
    )
    state, rc, err = _s61w2_complete(tmp_path, root, S61W2_SID_A, season)
    assert state["status"] == "completed", (
        f"season ended {state['status']}, not completed; stderr:\n{err}"
    )
    assert rc == 0, f"season start exit {rc}:\n{err}"
    agent = (state.get("agents") or {}).get("w1") or {}
    assert agent.get("state") == "exited" and agent.get("exit_code") == 0, (
        f"agent snap: {agent}"
    )
    artifact = root / "runs" / S61W2_SID_A / "results.jsonl"
    if artifact.is_file():
        assert artifact.stat().st_size > 0, (
            f"the landed {artifact.name} carries no bytes: the ledger still "
            "holds nothing a reader could use"
        )
        logger.info("EXERCISE truth held: %s landed non-empty", artifact)
        return
    logger.info("EXERCISE truth absent; holding the TRIM truth")
    trim_proj, trim_root = _s61w2_proj(tmp_path / "trim")
    trim_season = _s61w2_season(
        trim_root, S61W2_SID_A, S61W2_TRIM_YAML, "plain", "all_exited",
    )
    linted = _s61w2_run(trim_proj, "lint", str(trim_season))
    assert linted.returncode == 0, (
        f"the pipeline-less yaml does not lint; stderr:\n{linted.stderr}"
    )
    trim_state, trim_rc, trim_err = _s61w2_complete(
        tmp_path / "trim", trim_root, S61W2_SID_A, trim_season,
    )
    assert trim_state["status"] == "completed", (
        f"the pipeline-less season ended {trim_state['status']}; stderr:\n{trim_err}"
    )
    assert trim_rc == 0, f"pipeline-less season start exit {trim_rc}:\n{trim_err}"


# --- pin 2: the finding retires honestly -----------------------------------------


def test_s61w2_fresh_audit_does_not_rearm_phase_liveness(tmp_path: Path) -> None:
    """A fresh audit over the campaign no longer arms the candidate.

    Two pipeline-declaring seasons run to completion, then one fresh
    `rumpun audit` reads the campaign. If the seasons' ledgers hold
    results.jsonl (EXERCISE), the candidate must be gone and the F1 line
    must count the exercised seasons in the numerator. Otherwise (TRIM)
    a pipeline-less yaml must lint clean, the same campaign rebuilt on
    trimmed seasons must audit with no phase-liveness candidate, and the
    F1 finding retires with the declaration. On main today the fresh
    audit arms the candidate exactly as audit-41 did, and the TRIM half
    is refused at lint, so the pin is red until w1's change lands.
    """
    proj, root = _s61w2_proj(tmp_path)
    for sid in (S61W2_SID_A, S61W2_SID_B):
        season = _s61w2_season(
            root, sid, S61W2_PIPELINE_YAML, "stub", "all_exited",
        )
        state, rc, err = _s61w2_complete(tmp_path, root, sid, season)
        assert state["status"] == "completed", (
            f"season {sid} ended {state['status']}; stderr:\n{err}"
        )
        assert rc == 0, f"season {sid} start exit {rc}:\n{err}"
    record_a = _s61w2_audit(proj, root)
    exercised = [
        sid
        for sid in (S61W2_SID_A, S61W2_SID_B)
        if (root / "runs" / sid / "results.jsonl").is_file()
    ]
    if len(exercised) == 2:
        armed = _s61w2_armed(record_a)
        assert not armed, (
            "both ledgers hold results.jsonl yet the fresh audit still arms "
            f"the phase-liveness candidate: {armed}"
        )
        m = re.search(
            r"F1 phase liveness: phase execute \(writes results\.jsonl\) "
            r"wrote its artifact in (\d+) of (\d+)",
            record_a,
        )
        assert m, f"the fresh audit carries no F1 execute line:\n{record_a}"
        assert int(m.group(1)) >= 1, (
            f"the exercised season must count in the numerator: {m.group(0)}"
        )
        logger.info("EXERCISE retirement held: F1 counts %s of %s", m.group(1), m.group(2))
        return
    logger.info("EXERCISE truth absent; holding the TRIM truth")
    trim_season = _s61w2_season(
        root, "s613", S61W2_TRIM_YAML, "plain", "all_exited",
    )
    linted = _s61w2_run(proj, "lint", str(trim_season))
    assert linted.returncode == 0, (
        f"the pipeline-less yaml does not lint; stderr:\n{linted.stderr}"
    )
    for sid in ("s613", "s614"):
        season = _s61w2_season(
            root, sid, S61W2_TRIM_YAML, "plain", "all_exited",
        )
        state, rc, err = _s61w2_complete(tmp_path, root, sid, season)
        assert state["status"] == "completed", (
            f"trimmed season {sid} ended {state['status']}; stderr:\n{err}"
        )
        assert rc == 0, f"trimmed season {sid} start exit {rc}:\n{err}"
    record_b = _s61w2_audit(proj, root)
    assert not _s61w2_armed(record_b), (
        "the trimmed campaign still arms the phase-liveness candidate:\n"
        f"{[line for line in record_b.splitlines() if line.startswith('candidate:')]}"
    )


# --- pin 3a: the falsify gate keeps guarding declared writes ---------------------


def test_s61w2_falsify_gate_still_guards_declared_writes(tmp_path: Path) -> None:
    """A declared write with no reachable reader still fails lint.

    The pipeline declares evaluate reading measurements.jsonl, an
    artifact nothing writes. The falsify gate (s34/s43: a reachable
    reader for every declared write) must name the season and refuse,
    before and after whatever w1 lands: trimming the requirement to
    declare a pipeline must not trim the gate over the pipelines still
    declared. Green pre-graft by design; the guard the season must not
    weaken.
    """
    proj, root = _s61w2_proj(tmp_path)
    season = _s61w2_season(
        root, S61W2_SID_A, S61W2_UNREACHABLE_YAML, "plain", "all_exited",
    )
    linted = _s61w2_run(proj, "lint", str(season))
    assert linted.returncode != 0, (
        f"an unreachable declared read linted clean; stderr:\n{linted.stderr}"
    )
    assert "falsify_required" in linted.stderr, (
        "the refusal must name the falsify gate, not another lint error;"
        f" stderr:\n{linted.stderr}"
    )


# --- pin 3b: the s60 stall record stays ------------------------------------------


def test_s61w2_stall_record_shape_untouched(tmp_path: Path) -> None:
    """A stopped_stall season still carries the auditable stop record.

    Same dead-stub fixture as the s60 pins (a 0.1-minute stall window,
    an agent that writes nothing), the record side: the persisted
    state.json must carry a top-level "stall_stop" object — the rule
    text, the season's stall_s, and per-agent evidence: sources == {}
    (no event of any class counted), tool_use_count None, ws_bytes an
    int (the recorded baseline), and a finite last_progress_age_s >= the
    stall window. Green pre-graft by design; the s60 contract the season
    must not weaken.
    """
    _proj, root = _s61w2_proj(tmp_path)
    season = _s61w2_season(
        root,
        S61W2_SID_A,
        S61W2_PIPELINE_YAML,
        "dead",
        f"all_exited, {{stall_minutes: {S61W2_STALL_MINUTES}}}",
    )
    state, _rc, err = _s61w2_complete(tmp_path, root, S61W2_SID_A, season)
    assert state["status"] == "stopped_stall", (
        f"season ended {state['status']}; stderr:\n{err}"
    )
    record = state.get("stall_stop")
    assert isinstance(record, dict), (
        f"stop record carries no rule; state keys: {sorted(state)}"
    )
    assert isinstance(record.get("rule"), str) and record["rule"], (
        f"stop record must name the rule: {record}"
    )
    assert float(record.get("stall_s", -1.0)) == float(state.get("stall_s", -2.0)), (
        f"stop record stall_s must match the season: {record}"
    )
    agent = (record.get("agents") or {}).get("w1") or {}
    snap = (state.get("agents") or {}).get("w1") or {}
    assert snap.get("state") == "terminated" and not snap.get("terminated_budget"), (
        f"the stall rule must stop the agent, not the budget: {snap}"
    )
    age = agent.get("last_progress_age_s")
    assert isinstance(age, (int, float)) and not isinstance(age, bool), (
        f"last_progress_age_s must be a number: {agent}"
    )
    window = float(state.get("stall_s", 0.0))
    assert math.isfinite(float(age)) and float(age) >= window, (
        f"last-progress age {age} must be >= the stall window {window}: {agent}"
    )
    assert agent.get("sources") == {}, (
        f"a dead agent counted no event of any class: {agent}"
    )
    assert agent.get("tool_use_count") is None, (
        f"no tool_use event ever parsed for a dead agent: {agent}"
    )
    assert isinstance(agent.get("ws_bytes"), int), (
        f"the watched-bytes scan ran (baseline recorded): {agent}"
    )
