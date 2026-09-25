"""s68 w2 pins — spec-first pins for campaign schema versioning.

Directive seq 6: rumpun must survive its own structural change — version
the schema, document it, and make readers refuse what they cannot read.
Spec source: .rumpun/prompts/dev/w2-schema-version.md; ledger anchor
s67-harvest@704ae8de (suite 291/291); the s54 rename's benih back-compat
read is the versioned-read precedent. Bounds: version 1 IS today's
format; no format migration this season; the refusal path is the
deliverable; the benih alias read stays. Fixture-shape assumptions the
harness reconciles at merge live in .rumpun/runs/s68/w2/notes.md.

Contract these pins hold:

1. Scaffold: every campaign scaffold writes `schema: 1` at the top of
   rumpun.yaml (plain `rumpun init` and the `init --plugin` pack-first
   fallback path) and ships .rumpun/CHANGELOG.md. A campaign without the
   schema key reads as version 1 and never refuses.
2. Refusal: a campaign whose rumpun.yaml carries `schema: 99` refuses
   the next mutating verb (season start, evolve apply) with an error
   naming the supported range and pointing at .rumpun/CHANGELOG.md.
   Read-only verbs (kanban, season status, lint) still work, and kanban
   gains no new cards — the refusal message is the surface.
3. CHANGELOG: one line per schema version, newest first, prunable with
   RESUME.md's prune discipline (the newest five rows survive).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

S68W2_TIMEOUT = 240  # bounds one CLI subprocess (the task bound)
S68W2_RANGE = "1..1"
S68W2_CHANGELOG = "CHANGELOG.md"


def _s68w2_strip_clock(text: str) -> str:
    """Neutralize wall-clock stamps so byte-equality stays deterministic.

    The kanban header carries the current minute; two subprocess runs
    straddling a minute boundary differ only there. Every other byte
    stays asserted.
    """
    return re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", "<clock>", text)

S68W2_SEASON = """\
# seasons/s99.yaml — s68w2 fixture: seed shape, filled goal/metric, lint-clean.
id: s99
parent: null
goal: "s68w2 fixture: the schema refusal is the only thing this start tests"
metric: schema_refusal
mode: fight
methodology:
  approach: "s68w2 fixture reference pipeline"
  evidence: []
  pipeline:
    - phase: execute
      primitive: execute
      agents: writers
      prompt: prompts/base/execute.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agent: judge
      prompt: prompts/base/evaluate.md
      reads: results.jsonl
      writes: verdicts.jsonl
writers:
  - name: a1
    route: fable
    lane: s68w2-schema
    prompt: prompts/base/execute.md
    knowledge: full
    budget: {minutes: 1}
stop:
  "on": [all_exited, {stall_minutes: 45}, budget_exhausted]
"""


def _s68w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s68w2_env() -> dict[str, str]:
    """Subprocess env with the repo's src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s68w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s68w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess, 240s bounded."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(cwd),
        env=_s68w2_env(),
        capture_output=True,
        text=True,
        timeout=S68W2_TIMEOUT,
        check=False,
    )


def _s68w2_campaign(tmp_path: Path, schema: int | None, name: str = "campaign") -> Path:
    """A fresh scaffolded campaign with the fixture season in seasons/.

    schema=99 prepends the key to rumpun.yaml; None leaves the scaffolded
    file exactly as init wrote it (the no-key read-as-1 twin). name keeps
    the root and twin campaigns in distinct directories under one tmp_path.
    """
    root = tmp_path / name
    run = _s68w2_run(tmp_path, ["init", str(root)])
    assert run.returncode == 0, f"init failed: {run.stderr}"
    season = root / ".rumpun" / "seasons" / "s99.yaml"
    season.parent.mkdir(parents=True, exist_ok=True)
    season.write_text(S68W2_SEASON, encoding="utf-8")
    if schema is not None:
        cfg_path = root / ".rumpun" / "rumpun.yaml"
        text = cfg_path.read_text(encoding="utf-8")
        if "schema:" in text:
            lines = [
                f"schema: {schema}" if line.startswith("schema:") else line
                for line in text.splitlines()
            ]
            text = "\n".join(lines) + "\n"
        else:
            text = f"schema: {schema}\n" + text
        cfg_path.write_text(text, encoding="utf-8")
    return root


def _s68w2_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s68w2_pack(tmp_path: Path) -> Path:
    """A minimal hand-built pack: manifest + one prior; carries no
    rumpun.yaml and no CHANGELOG.md, so the pack-first scaffold falls
    back to the base tree for every scaffold output."""
    pack = tmp_path / "pack"
    (pack / "priors").mkdir(parents=True)
    (pack / "priors" / "gates.md").write_text("# a prior\n", encoding="utf-8")
    manifest = (
        "name: s68w2-pack\n"
        "version: 0.1.0\n"
        f"digest: {_s68w2_digest(pack)}\n"
        "private_vocabulary: [s68w2]\n"
        "source: s68 w2 pin fixture pack\n"
    )
    (pack / "manifest.yaml").write_text(manifest, encoding="utf-8")
    return pack


def _s68w2_changelog_rows(changelog: Path) -> list[str]:
    lines = changelog.read_text(encoding="utf-8").splitlines()
    return [line for line in lines if line.startswith("- schema ")]


def test_s68w2_init_writes_schema_1_at_top_and_changelog(tmp_path):
    root = tmp_path / "campaign"
    run = _s68w2_run(tmp_path, ["init", str(root)])
    assert run.returncode == 0, run.stderr
    cfg_path = root / ".rumpun" / "rumpun.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert cfg["schema"] == 1, "the scaffold must write schema: 1"
    text = cfg_path.read_text(encoding="utf-8")
    assert text.index("schema: 1") < text.index("campaign:"), "schema sits at the top"
    changelog = root / ".rumpun" / "CHANGELOG.md"
    assert changelog.is_file(), "init must ship .rumpun/CHANGELOG.md"
    rows = _s68w2_changelog_rows(changelog)
    assert len(rows) == 1, f"one line per version, got {rows}"
    assert rows[0].startswith("- schema 1:")


def test_s68w2_plugin_scaffold_fallback_writes_schema_and_changelog(tmp_path):
    pack = _s68w2_pack(tmp_path)
    root = tmp_path / "campaign"
    run = _s68w2_run(tmp_path, ["init", str(root), "--plugin", str(pack)])
    assert run.returncode == 0, run.stderr
    cfg_path = root / ".rumpun" / "rumpun.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert cfg["schema"] == 1, "the pack-first fallback must write schema: 1"
    text = cfg_path.read_text(encoding="utf-8")
    assert text.index("schema: 1") < text.index("campaign:")
    changelog = root / ".rumpun" / "CHANGELOG.md"
    assert changelog.is_file(), "the pack-first fallback must ship CHANGELOG.md"
    rows = _s68w2_changelog_rows(changelog)
    assert len(rows) == 1 and rows[0].startswith("- schema 1:")


def test_s68w2_missing_schema_key_reads_as_version_1(tmp_path):
    from rumpun import yamlio

    root = _s68w2_campaign(tmp_path, schema=None, name="twin")
    dot = root / ".rumpun"
    assert yamlio.campaign_schema(dot) == 1, "a missing key reads as version 1"
    assert yamlio.require_supported_schema(dot) == 1, "version 1 never refuses"


def test_s68w2_schema_99_blocks_season_start_names_range_and_changelog(tmp_path):
    root = _s68w2_campaign(tmp_path, schema=99)
    run = _s68w2_run(root, ["season", "start", ".rumpun/seasons/s99.yaml"])
    assert run.returncode == 1, f"the mutating verb must refuse: {run.stderr}"
    assert S68W2_RANGE in run.stderr, f"must name the supported range: {run.stderr}"
    assert S68W2_CHANGELOG in run.stderr, f"must point at the changelog: {run.stderr}"
    twin = _s68w2_campaign(tmp_path, schema=None, name="twin")
    twin_run = _s68w2_run(twin, ["season", "start", ".rumpun/seasons/s99.yaml"])
    assert S68W2_RANGE not in twin_run.stderr, (
        "the schema-less twin must not refuse for schema reasons"
    )


def test_s68w2_schema_99_blocks_evolve_apply_names_range_and_changelog(tmp_path):
    root = _s68w2_campaign(tmp_path, schema=99)
    run = _s68w2_run(root, ["evolve", "apply", ".rumpun/seasons/s99.yaml"])
    assert run.returncode == 1, f"the mutating verb must refuse: {run.stderr}"
    assert S68W2_RANGE in run.stderr, f"must name the supported range: {run.stderr}"
    assert S68W2_CHANGELOG in run.stderr, f"must point at the changelog: {run.stderr}"
    twin = _s68w2_campaign(tmp_path, schema=None, name="twin")
    twin_run = _s68w2_run(twin, ["evolve", "apply", ".rumpun/seasons/s99.yaml"])
    assert twin_run.returncode == 0, f"the twin must pass lint cleanly: {twin_run.stderr}"
    assert S68W2_RANGE not in twin_run.stderr


def test_s68w2_read_only_verbs_still_work_on_schema_99(tmp_path):
    root = _s68w2_campaign(tmp_path, schema=99)
    twin = _s68w2_campaign(tmp_path, schema=None, name="twin")
    lint_run = _s68w2_run(root, ["lint", ".rumpun/seasons/s99.yaml"])
    assert lint_run.returncode == 0, f"lint must still work: {lint_run.stderr}"
    assert S68W2_RANGE not in lint_run.stderr
    status99 = _s68w2_run(root, ["season", "status", "s99"])
    status_twin = _s68w2_run(twin, ["season", "status", "s99"])
    assert status99.returncode == status_twin.returncode, (
        f"status must not gain a schema refusal: {status99.stderr}"
    )
    assert _s68w2_strip_clock(status99.stdout) == _s68w2_strip_clock(
        status_twin.stdout
    ), "status output must not change"
    assert S68W2_RANGE not in status99.stderr


def test_s68w2_kanban_gains_no_cards_on_schema_99(tmp_path):
    root = _s68w2_campaign(tmp_path, schema=99)
    twin = _s68w2_campaign(tmp_path, schema=None, name="twin")
    board99 = _s68w2_run(root, ["kanban"])
    board_twin = _s68w2_run(twin, ["kanban"])
    assert board99.returncode == 0, f"kanban must still work: {board99.stderr}"
    assert _s68w2_strip_clock(board99.stdout) == _s68w2_strip_clock(board_twin.stdout), (
        "the board must be identical without the schema key — no new cards"
    )
    assert S68W2_RANGE not in board99.stdout
    assert "schema" not in board99.stdout, "the refusal names no kanban card"


def test_s68w2_changelog_prunes_like_resume_after_five_bumps(tmp_path):
    from rumpun import scaffold

    root = _s68w2_campaign(tmp_path, schema=None, name="twin")
    changelog = root / ".rumpun" / "CHANGELOG.md"
    rows = [f"- schema {n}: bump {n}" for n in range(8, 0, -1)]  # newest first
    changelog.write_text(
        "# CHANGELOG — campaign schema\n\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    scaffold.prune_changelog(root / ".rumpun")
    kept = _s68w2_changelog_rows(changelog)
    assert [row.split(":")[0] for row in kept] == [
        "- schema 8",
        "- schema 7",
        "- schema 6",
        "- schema 5",
        "- schema 4",
    ], f"the newest five rows survive, in order: {kept}"
    assert "bump 3" not in changelog.read_text(encoding="utf-8"), "older rows drop"
    assert changelog.read_text(encoding="utf-8").startswith("# CHANGELOG"), (
        "the header survives"
    )
    before = changelog.read_text(encoding="utf-8")
    scaffold.prune_changelog(root / ".rumpun")
    assert changelog.read_text(encoding="utf-8") == before, "a second prune is a no-op"
