"""s126 w1 pins — models --write re-reads a filled campaign.

Ground truth measured 2026-09-20 (the s125 w2 finding, DESIGN.md s125
disclosure):
- `rumpun models --write` refuses a filled campaign: routes.write_routes
  demands the `routes: {}` scaffold placeholder and raises RoutesError
  ("no empty routes: {} line to fill") on the filled block.
- the truth a re-detect must respect: a filled routes block carries
  hand-tuned templates (glm moved to 5.3 by probe at s125; fable carries
  the stream-json writer flags) — a redetect writes only newly detected
  route KEYS as new lines. Existing lines byte-untouched. Idempotent.
- the verb shape: diff detected routes against the config, write the
  named additions, print what changed.

Offline: tmp campaigns only — the real .rumpun/rumpun.yaml is never
written in tests. Detection is stubbed at routes.route_table (and the
print helpers for the CLI pin); the /bin/sh -n validation runs locally.
No spawns, no network, no quota.

Grafting: drop into tests/; helpers carry the _s126 prefix; no def collides.
"""

from __future__ import annotations

import logging
import subprocess

import pytest

from rumpun import cli, routes, scaffold, yamlio

# Hermetic detection table for the pins: glm overlaps a hand-tuned key,
# claude and newkid are additions, and every command /bin/sh -n-valid.
TABLE = [
    {
        "family": "glm",
        "desc": "proxy glm",
        "command": "cat {prompt} | claude -p --model glm-5.3",
    },
    {
        "family": "claude",
        "desc": "login",
        "command": (
            "env -u ANTHROPIC_BASE_URL sh -c"
            " 'cat {prompt} | claude -p --model claude-fable-5-1'"
        ),
    },
    {
        "family": "newkid",
        "desc": "new codex slug",
        "command": "codex exec -m newkid {prompt}",
    },
]

# A filled campaign whose routes block is hand-tuned: values the redetect
# must never touch, a comment inside the block, a top-level key after it.
FILLED = """\
schema: 1
campaign:
  goal: "probe goal"
routes:
  # hand-tuned: never clobber
  glm: 'HAND-TUNED glm-5.3 {prompt}'
  fable: 'HAND-TUNED fable {prompt}'
lint:
  max_warnings: 5
"""


def _filled_campaign(tmp_path):
    """A tmp campaign whose rumpun.yaml has the filled routes block."""
    root = tmp_path / "proj"
    (root / ".rumpun").mkdir(parents=True)
    cfg = root / ".rumpun" / "rumpun.yaml"
    cfg.write_text(FILLED, encoding="utf-8")
    return root, cfg


def test_s126w1_redetect_fills_placeholder(tmp_path, monkeypatch):
    """On the scaffold placeholder, redetect IS the full fill: every
    detected family lands, the file parses, commands stay sh-valid (the
    M11 rule carried into the re-detect path)."""
    target = tmp_path / "proj"
    scaffold.init_project(target)
    cfg = target / ".rumpun" / "rumpun.yaml"
    monkeypatch.setattr(routes, "route_table", lambda: TABLE)
    added = routes.redetect_routes(cfg)
    assert added == ["glm", "claude", "newkid"]
    data = yamlio.load(cfg)
    assert set(data["routes"]) == {"glm", "claude", "newkid"}
    for cmd in data["routes"].values():
        proc = subprocess.run(
            ["/bin/sh", "-n"],
            input=cmd.replace("{prompt}", "prompt.md"),
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, f"/bin/sh -n rejected: {cmd}\n{proc.stderr}"


def test_s126w1_redetect_adds_only_new_keys(tmp_path, monkeypatch):
    """The s125 finding, landed: on a filled block the redetect appends
    only the newly detected keys after the last existing entry. The
    hand-tuned lines (and the block comment) stay byte-untouched, the
    strict loader still parses, and the clobber attempt does not exist."""
    _root, cfg = _filled_campaign(tmp_path)
    before = cfg.read_text(encoding="utf-8")
    monkeypatch.setattr(routes, "route_table", lambda: TABLE)
    added = routes.redetect_routes(cfg)
    assert added == ["claude", "newkid"]
    after = cfg.read_text(encoding="utf-8")
    for line in before.splitlines():
        assert line in after.splitlines(), f"existing line disturbed: {line!r}"
    data = yamlio.load(cfg)
    assert data["routes"]["glm"] == "HAND-TUNED glm-5.3 {prompt}"
    assert data["routes"]["fable"] == "HAND-TUNED fable {prompt}"
    assert data["routes"]["claude"].startswith("env -u ANTHROPIC_BASE_URL")
    assert data["routes"]["newkid"] == "codex exec -m newkid {prompt}"
    lines = after.splitlines()
    claude_line = f"  claude: '{TABLE[1]['command'].replace(chr(39), chr(39) * 2)}'"
    assert lines.index("  fable: 'HAND-TUNED fable {prompt}'") + 1 == lines.index(
        claude_line
    )


def test_s126w1_redetect_idempotent_second_run(tmp_path, monkeypatch):
    """A second run finds no new keys: empty return, zero bytes written."""
    _root, cfg = _filled_campaign(tmp_path)
    monkeypatch.setattr(routes, "route_table", lambda: TABLE)
    routes.redetect_routes(cfg)
    once = cfg.read_text(encoding="utf-8")
    again = routes.redetect_routes(cfg)
    assert again == []
    assert cfg.read_text(encoding="utf-8") == once


def test_s126w1_redetect_refuses_no_routes_block(tmp_path, monkeypatch):
    """No `routes:` key at all is a refusal, not a rewrite: RoutesError
    and the file keeps its bytes."""
    root = tmp_path / "proj"
    (root / ".rumpun").mkdir(parents=True)
    cfg = root / ".rumpun" / "rumpun.yaml"
    cfg.write_text('schema: 1\ncampaign:\n  goal: "x"\n', encoding="utf-8")
    before = cfg.read_text(encoding="utf-8")
    monkeypatch.setattr(routes, "route_table", lambda: TABLE)
    with pytest.raises(routes.RoutesError):
        routes.redetect_routes(cfg)
    assert cfg.read_text(encoding="utf-8") == before


def test_s126w1_cli_write_prints_diff_on_filled(tmp_path, monkeypatch, caplog):
    """The verb on a filled campaign: exit 0 (the refusal is gone), the
    log line names the added keys as the diff, and a second run prints
    the no-op without touching the file."""
    root, cfg = _filled_campaign(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(routes, "route_table", lambda: TABLE)
    monkeypatch.setattr(routes, "detect_clis", lambda *a, **k: [])
    monkeypatch.setattr(routes, "claude_routes", lambda env=None: [])
    monkeypatch.setattr(routes, "codex_model_routes", lambda: [])
    args = cli.build_parser().parse_args(["models", "--write"])
    with caplog.at_level(logging.INFO, logger="rumpun"):
        assert cli.cmd_models(args) == 0
        assert "+ claude, newkid" in caplog.text
    once = cfg.read_text(encoding="utf-8")
    with caplog.at_level(logging.INFO, logger="rumpun"):
        assert cli.cmd_models(args) == 0
        assert "no new routes" in caplog.text
    assert cfg.read_text(encoding="utf-8") == once
