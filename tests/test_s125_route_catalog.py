"""s125 w2 pins - the route catalog states the truth.

Ground truth measured 2026-09-20 (probe trail in .rumpun/runs/s125/w2/notes.md):
- the operator named glm 5.3; the glm route template pinned glm-5.2; the
  model catalog warned at the four-review dispatch that glm-5.2 is not
  described by this version's catalog.
- one bounded probe (the exact glm route shape with --model glm-5.3,
  2026-09-20): rc=0, reply "ok". The same catalog-warning class fires
  for glm-5.3 as for glm-5.2, so the warning is CLI-side catalog text,
  not a serving error. glm-5.3 serves.
- landing: the glm route template pins glm-5.3; the guide states the
  served version; routes.family_label() on the template reports
  glm-5.3, so the detector output agrees with the template.

Offline: no spawns, no network; the real rumpun.yaml and
docs/campaign-guide.md are read-only here.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from rumpun import routes

# The probed-and-served version (one bounded call, 2026-09-20).
SERVED = "glm-5.3"

# The s105 guard set every claude route must carry (env-strip prefix on
# the four ANTHROPIC_DEFAULT_*_MODEL vars, skip-permissions, model pin).
GUARDS = (
    "-u ANTHROPIC_DEFAULT_SONNET_MODEL",
    "-u ANTHROPIC_DEFAULT_OPUS_MODEL",
    "-u ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "-u ANTHROPIC_DEFAULT_FABLE_MODEL",
    "--dangerously-skip-permissions",
)


def _repo_root() -> Path:
    """Walk up from this file to the pyproject.toml holding the repo root."""
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("repo root with pyproject.toml not found")


def _glm_route() -> str:
    """The real glm route template from .rumpun/rumpun.yaml."""
    raw = (_repo_root() / ".rumpun" / "rumpun.yaml").read_text(encoding="utf-8")
    route = yaml.safe_load(raw)["routes"]["glm"]
    assert isinstance(route, str)
    return route


def _guide() -> str:
    """The route-claims doc: docs/campaign-guide.md."""
    return (_repo_root() / "docs" / "campaign-guide.md").read_text(
        encoding="utf-8",
    )


def test_s125w2_glm_template_serves_probed_version():
    route = _glm_route()
    assert f"--model {SERVED}" in route
    assert "glm-5.2" not in route
    for guard in GUARDS:
        assert guard in route, guard


def test_s125w2_detector_labels_template_served_version():
    # Explicit --model wins in family_label; env={} keeps the check
    # hermetic (no inherited proxy/tier vars in the label path).
    assert routes.family_label(_glm_route(), env={}) == SERVED


def test_s125w2_template_and_guide_agree_on_version():
    m = re.search(r"the `glm` route serves `([^`]+)`", _guide(), re.IGNORECASE)
    assert m, "guide must state which version the glm route serves"
    route_versions = set(re.findall(r"glm-[0-9][0-9.]*", _glm_route()))
    assert m.group(1) in route_versions
