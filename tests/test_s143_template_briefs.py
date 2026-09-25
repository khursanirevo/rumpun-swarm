"""s143 w1 pins - the steady-state template's phases get real briefs.

Ground truth measured 2026-09-21 (init probe campaigns under tmp_path;
full account in .rumpun/runs/s143/w1/notes.md):

- The s142 LOSS named the defect: the steady-state template's execute
  phases and its three writers all pointed at prompts/base/execute.md,
  a prompt carrying no lane work, so the s142 production fill produced
  nothing. The engine spawns each writer from the writer's own prompt
  field (engine.py copies root/<writer prompt> to the workspace), so
  both the phases and the writers must carry the lane briefs.
- The fix: init emits three per-lane briefs beside the template
  (seasons/_steady-state-lint-sweep.md, seasons/_steady-state-route-probes.md,
  seasons/_steady-state-rehearsals.md), adapted from the s139 lanes'
  real briefs (.rumpun/prompts/dev/w1-light-lanes-sweep.md and
  .rumpun/prompts/dev/w2-rehearsals-reconfirm.md). Each brief names its
  lane work, its artifact, and the notes contract. The template's three
  execute phases and its three writers point at the matching briefs;
  the decision gate keeps prompts/base/evaluate.md.
- The lint gate couples the two sides: a phase or writer prompt path
  must exist under .rumpun/ (lint.py node and writer checks), so the
  emitted template only lints clean because init emitted the briefs.
- Fixture discipline: init and lint run in tmp campaigns; the real
  campaign is never written in tests. The repo's carried copy of the
  template is outside this lane's bounds.

Contract these pins hold:
1. init emits the three briefs beside the template; each names its lane
   work, its artifact (sweep/probes/rehearsals .jsonl), and notes.md.
2. The emitted template's three execute phases and its three writers
   point at the matching lane briefs with matching artifacts; the
   decision gate keeps the evaluate prompt.
3. The emitted template lints clean as shipped (the coupling gate: the
   pointers are only clean because the briefs exist).

Red history (measured 2026-09-21): pins 1 and 2 red pre-implementation
(/tmp/s143w1-red.log): pin 1 on the three missing files, pin 2 on the
prompts/base/execute.md pointers. Pin 3 is the coupling guard and was
green pre-implementation (the old shape lints clean); it goes red the
moment a pointer lands without the emission behind it.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

S143W1_TIMEOUT = 240

# The three light lanes: lane name -> (brief path beside the template,
# the lane's artifact). The decision-gate phase is absent on purpose:
# it keeps prompts/base/evaluate.md (pin 2 holds that too).
LANE_BRIEFS: dict[str, tuple[str, str]] = {
    "lint-sweep": ("seasons/_steady-state-lint-sweep.md", "sweep.jsonl"),
    "route-probes": ("seasons/_steady-state-route-probes.md", "probes.jsonl"),
    "rehearsals": ("seasons/_steady-state-rehearsals.md", "rehearsals.jsonl"),
}

# Per-brief tokens naming the lane work (pin 1). Every brief must carry
# its artifact name and the notes contract; the work tokens are the
# lane's own words from the s139 briefs.
BRIEF_WORK_TOKENS: dict[str, tuple[str, ...]] = {
    "lint-sweep": ("lint-sweep", "guards", "sweep.jsonl", "notes.md"),
    "route-probes": ("route-probes", "probe", "serve table", "probes.jsonl",
                     "notes.md"),
    "rehearsals": ("rehearsals", "exhaustion rehearsal", "guide walkthrough",
                   "rehearsals.jsonl", "notes.md"),
}


def _s143w1_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s143w1_env() -> dict[str, str]:
    """Subprocess env: repo src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s143w1_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s143w1_run(
    cwd: Path, argv: list[str], env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess, bounded."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(cwd),
        env=env if env is not None else _s143w1_env(),
        capture_output=True,
        text=True,
        timeout=S143W1_TIMEOUT,
        check=False,
    )


def _s143w1_init(tmp_path: Path, tag: str) -> tuple[Path, Path]:
    """Fresh `rumpun init` campaign; (proj dir, .rumpun root).

    Asserts the init exit and the template emission, so every pin's
    fixture proves the scaffold path first.
    """
    proj = tmp_path / tag / "proj"
    proc = _s143w1_run(tmp_path, ["init", str(proj)])
    assert proc.returncode == 0, (
        f"fixture defect: init failed for {tag}\n{proc.stdout}{proc.stderr}"
    )
    root = proj / ".rumpun"
    emitted = root / "seasons" / "_steady-state.yaml"
    assert emitted.is_file(), (
        "rumpun init must emit .rumpun/seasons/_steady-state.yaml; seasons "
        f"holds {sorted(p.name for p in (root / 'seasons').glob('*'))}"
    )
    return proj, root


# --- pin 1: init emits the three lane briefs ---------------------------------


def test_s143w1_init_emits_three_lane_briefs(tmp_path: Path) -> None:
    """init emits the briefs beside the template; each names work+artifact+notes."""
    _proj, root = _s143w1_init(tmp_path, "emit")
    for lane, (brief_path, _artifact) in LANE_BRIEFS.items():
        brief = root / brief_path
        assert brief.is_file(), (
            f"init must emit {brief_path} beside the template; seasons holds "
            f"{sorted(p.name for p in (root / 'seasons').glob('*'))}"
        )
        text = brief.read_text(encoding="utf-8")
        for token in BRIEF_WORK_TOKENS[lane]:
            assert token in text, f"the {lane} brief must name {token!r}"
        logger.info("pin 1 held: %s emitted with its work tokens", brief_path)


# --- pin 2: the template's phases and writers point at the briefs ------------


def test_s143w1_template_phases_point_at_lane_briefs(tmp_path: Path) -> None:
    """Each execute phase and its writer carry the lane brief; the gate keeps evaluate."""
    _proj, root = _s143w1_init(tmp_path, "point")
    doc = yaml.safe_load(
        (root / "seasons" / "_steady-state.yaml").read_text(encoding="utf-8")
    )
    phases = {p["phase"]: p for p in doc["methodology"]["pipeline"]}
    for lane, (brief_path, artifact) in LANE_BRIEFS.items():
        assert phases[lane]["prompt"] == brief_path, (
            f"phase {lane} must point at {brief_path}; "
            f"got {phases[lane]['prompt']}"
        )
        assert phases[lane]["writes"] == artifact
    assert phases["decision-gate"]["prompt"] == "prompts/base/evaluate.md", (
        "the decision gate keeps the evaluate prompt; "
        f"got {phases['decision-gate']['prompt']}"
    )
    writers = {w["name"]: w for w in doc["writers"]}
    writer_for_lane = {
        "lint-sweep": "sweep",
        "route-probes": "probes",
        "rehearsals": "rehearsal",
    }
    for lane, (brief_path, _artifact) in LANE_BRIEFS.items():
        writer = writers[writer_for_lane[lane]]
        assert writer["prompt"] == brief_path, (
            f"writer {writer['name']} must point at {brief_path}; "
            f"got {writer['prompt']}"
        )
        assert writer["lane"] == lane
    logger.info("pin 2 held: phases and writers point at the lane briefs")


# --- pin 3: the emitted template lints clean as shipped (coupling gate) ------


def test_s143w1_emitted_template_lints_clean(tmp_path: Path) -> None:
    """The emitted template lints clean because the briefs exist.

    The gate behind the s142 LOSS: a prompt path that init does not emit
    refuses at lint (prompt not found). This pin is green both before
    (the old pointers) and after (the briefs emitted); it goes red if a
    pointer lands without the emission.
    """
    _proj, root = _s143w1_init(tmp_path, "lint")
    emitted = root / "seasons" / "_steady-state.yaml"
    proc = _s143w1_run(tmp_path, ["lint", str(emitted)])
    assert proc.returncode == 0, (
        f"the emitted template must lint clean as shipped; exit "
        f"{proc.returncode}. stderr:\n{proc.stderr}\n{proc.stdout}"
    )
    logger.info("pin 3 held: the emitted template linted clean as shipped")
