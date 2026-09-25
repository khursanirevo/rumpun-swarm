"""s105 w1 pins - issue #21: the writer lanes' tools restored at the spawn site.

Ground truth measured 2026-09-18 (full trail in .rumpun/runs/s105/w1/notes.md):
- the s13-era lanes (and the a1-era fight lanes before them; DESIGN.md's
  season example names benih a1 on the glm route) spawned bare
  `claude -p --dangerously-skip-permissions` with the operator's
  model-mapping env inherited; the [1m] suffix reached the relay and the
  relay's degraded toolset stripped the writer's core tools
  (akar glm-toolless-spawn, cited in .rumpun/seasons/s5.yaml).
- the s91-s104 fable routes carry the full guard set (env -u on the four
  ANTHROPIC_DEFAULT_*_MODEL vars plus a --model pin) and boot with the
  full tool set; behavioral probes (two fable -p spawns, direct
  first-action Bash, zero tool errors) measured the current spawn shape
  booting eager.
- the strip's spawn-shape cause survived verbatim in the tree's glm route
  until this lane. Fix surface: engine._validate_benih refuses an
  unguarded claude route at season start (refuse, per the issue's
  refuse-or-correct); rumpun.yaml glm route guarded + --model glm-5.2;
  the ToolSearch-class recovery documented in the routes block.

Offline: no season spawns, no network calls; the real .rumpun/rumpun.yaml
is read-only here; engine behavior is pinned through a tmp_path fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from rumpun import engine

# The recorded s13 w1/w2 spawn command (state.json, .rumpun/runs/s13/w1/):
# the literal stripped shape issue #21 names.
S13_STRIPPED_CMD = (
    "cat /mnt/data/work/rumpun/.rumpun/rimba/s13/w1/prompt.md"
    " | claude -p --dangerously-skip-permissions"
)
# The a1-era minimal shape (DESIGN.md's season example: benih a1, glm route).
A1_ERA_TEMPLATE = "cat {prompt} | claude -p --dangerously-skip-permissions"

# The preserved s91-s104 writer shape, parsed value of the fable route.
FABLE_PRESERVED = (
    "env -u ANTHROPIC_BASE_URL -u ANTHROPIC_AUTH_TOKEN -u ANTHROPIC_API_KEY"
    " -u ANTHROPIC_DEFAULT_SONNET_MODEL -u ANTHROPIC_DEFAULT_OPUS_MODEL"
    " -u ANTHROPIC_DEFAULT_HAIKU_MODEL -u ANTHROPIC_DEFAULT_FABLE_MODEL"
    " sh -c 'cat {prompt} | claude -p --output-format stream-json --verbose"
    " --dangerously-skip-permissions --model claude-fable-5-1'"
)

# The s13/a1 divergence shape corrected: the guarded glm route.
# s125 w2: the pinned version moved glm-5.2 -> glm-5.3 after a probe-backed
# one-call check; the guard set this pin protects is unchanged.
GLM_GUARDED = (
    "env -u ANTHROPIC_DEFAULT_SONNET_MODEL -u ANTHROPIC_DEFAULT_OPUS_MODEL"
    " -u ANTHROPIC_DEFAULT_HAIKU_MODEL -u ANTHROPIC_DEFAULT_FABLE_MODEL"
    " sh -c 'cat {prompt} | claude -p --dangerously-skip-permissions"
    " --model glm-5.3'"
)

EXPECTED_GUARDS = [
    "-u ANTHROPIC_DEFAULT_SONNET_MODEL",
    "-u ANTHROPIC_DEFAULT_OPUS_MODEL",
    "-u ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "-u ANTHROPIC_DEFAULT_FABLE_MODEL",
    "--model pin",
]


def _repo_root() -> Path:
    """Walk up from this file to the pyproject.toml holding the repo root."""
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("repo root with pyproject.toml not found")


def _season(route_name: str, tmp_path: Path) -> dict:
    """One-writer season fixture bound to a route name under tmp_path."""
    prompt = tmp_path / "prompts" / "lane.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("lane prompt\n", encoding="utf-8")
    return {
        "benih": [
            {"name": "a1", "route": route_name, "prompt": "prompts/lane.md"},
        ],
    }


def test_s105w1_helper_s13_shape_reports_missing_guards():
    missing = engine._claude_route_missing_guards(S13_STRIPPED_CMD)
    assert missing == EXPECTED_GUARDS


def test_s105w1_helper_a1_era_template_reports_missing_guards():
    missing = engine._claude_route_missing_guards(A1_ERA_TEMPLATE)
    assert missing == EXPECTED_GUARDS


def test_s105w1_helper_guarded_shapes_pass():
    assert engine._claude_route_missing_guards(FABLE_PRESERVED) == []
    assert engine._claude_route_missing_guards(GLM_GUARDED) == []


def test_s105w1_helper_non_claude_routes_exempt():
    assert engine._claude_route_missing_guards("cat {prompt} > /dev/null") is None
    assert engine._claude_route_missing_guards("codex exec -m gpt-5.5 {prompt}") is None
    assert engine._claude_route_missing_guards(
        "kancil loop --prompt {prompt} --iteration-timeout 1800",
    ) is None


def test_s105w1_stripped_route_refused_at_validate(tmp_path):
    season = _season("stripped", tmp_path)
    with pytest.raises(engine.EngineError) as err:
        engine._validate_benih(
            season, {"stripped": A1_ERA_TEMPLATE}, tmp_path, "s1",
        )
    msg = str(err.value)
    assert "spawns unguarded" in msg
    assert "glm-toolless-spawn" in msg
    assert "--model pin" in msg
    assert "ANTHROPIC_DEFAULT_SONNET_MODEL" in msg


def test_s105w1_guarded_route_passes_validate(tmp_path):
    season = _season("guarded", tmp_path)
    engine._validate_benih(season, {"guarded": GLM_GUARDED}, tmp_path, "s1")


def test_s105w1_real_routes_guarded_and_fable_preserved():
    raw = (_repo_root() / ".rumpun" / "rumpun.yaml").read_text(encoding="utf-8")
    routes = yaml.safe_load(raw)["routes"]
    claude_routes = {
        name: value
        for name, value in routes.items()
        if "claude -p" in value
    }
    assert set(claude_routes) == {"glm", "fable"}
    for name, value in claude_routes.items():
        assert engine._claude_route_missing_guards(value) == [], name
    assert routes["fable"] == FABLE_PRESERVED
    assert routes["glm"] == GLM_GUARDED
    for name, value in routes.items():
        if name not in ("glm", "fable"):
            assert "claude -p" not in value, name


def test_s105w1_recovery_documented_in_spawn_docs():
    raw = (_repo_root() / ".rumpun" / "rumpun.yaml").read_text(encoding="utf-8")
    assert "ToolSearch select:Bash,Read,Edit,Write,Grep" in raw
    assert "glm-toolless-spawn" in raw
    assert "InputValidationError" in raw
