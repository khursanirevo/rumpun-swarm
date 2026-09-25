"""s67 w2 pins — spec-first pins for the kancil route and the scaffold.

Spec-first pins for s67: the kancil route (directive seq 2's driver gap and
the s67 season band "a kancil-routed season completes with the stub proving
the prompt handoff"), the kancil-base pack chain (directive seq 2 named
kancil-base the first pack), and the competition season template (the s67
goal's "first research-season template"). Ledger anchors: s66-harvest and
audit-42; directives seq 2/9/10. Seq 9 (no cost cap, ever) is why the
budget.campaign_cost_cap: null line stays unset in every fixture here; seq
10 (i-have-adhd preinstall) landed in s66 and is out of this season's pin
scope. Spec anchors, the measured red set, and fixture-shape assumptions:
.rumpun/runs/s67/w2/notes.md.

Contract these pins hold:

1. The kancil route spawns. The pin copies the REPO's live routes map
   (rumpun.yaml, the file w1 owns) into a throwaway campaign, puts a stub
   `kancil` on PATH, and drives a real `season start`: the stub must
   receive the rendered prompt (marker text in its capture file) and the
   season must persist status completed. The route is real, not a config
   line: red until rumpun.yaml carries a kancil entry that actually
   invokes a PATH-resolvable kancil with {prompt} substituted.
2. The kancil-base chain: `plugin distill kancil-base` in a campaign
   carrying the real ratified corpus emits the reviewable draft; `plugin
   install` into a FRESH scaffolded campaign lands it digest-verified;
   `plugin list` shows it. Every step is a subprocess.
3. The competition template: discoverable (init-emitted seasons file
   naming competition, or a scaffold module constant), lints clean AS
   SHIPPED through `rumpun lint`, and names the fill-in fields
   competition, metric, band.

Red history (measured 2026-09-16; logs /tmp/s67w2-run*.log): see notes.md.

Grafting: drop this file into tests/ as the season's pins file. Helpers
carry the _s67w2_ prefix, so nothing collides with existing defs.
Fixture-shape assumptions the harness reconciles at merge:

(a) Pin 1 reads the routes map from <repo>/.rumpun/rumpun.yaml at pin
    runtime. The fixture campaign inherits w1's merged route; the pin is
    green only when the live config carries a kancil entry, so the config
    line alone never passes it — the stub spawn must succeed end to end.
(b) The stub is named exactly `kancil`, resolves on the prepended PATH,
    captures argv, the contents of any file-valued argv, and stdin into
    $S67W2_KANCIL_CAPTURE, and exits 0. Any w1 route shape (stdin pipe or
    file-path argument) lands the prompt text in the capture.
(c) Pin 2's distill corpus overlay is exactly the _distill_corpus surface
    (plugin.py): ledger/*.md plus DESIGN.md plus GLOSSARY.md, copied into
    the fixture campaign. The real campaign is never mutated: the distill
    runs in the fixture campaign, never at the repo root.
(d) Pin 3's template discovery order: (1) a seasons/ file emitted by
    `rumpun init` (other than s1.yaml and _template.yaml) whose text
    names competition; (2) an uppercase scaffold module constant whose
    value names competition and reads as a season yaml. The template must
    lint clean as shipped: placeholder fill-in fields carry non-empty
    marker text (an empty goal or metric is a lint block, the s28
    quickstart behavior), so "lints clean" pins honest placeholders.
(e) Pin 2's chain machinery (distill s50, install/list s46) predates this
    season; the pin may measure green today and then serves as the merge
    guard for the band clause "installs into a fresh scaffolded campaign
    (digest verified)". The measured color is recorded in notes.md.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

S67W2_TIMEOUT = 240  # bounds one CLI subprocess (the task bound)
S67W2_MARKER = "KANCIL STUB PROMPT HANDOFF s67w2"
S67W2_PACK = "kancil-base"
S67W2_SOURCE = "distilled from a 67-season campaign"


def _s67w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s67w2_env(extra_path: Path | None = None, **vars: str) -> dict[str, str]:
    """Subprocess env: repo src/ prepended to PYTHONPATH, optional PATH
    prepend, arbitrary extra variables. _child_env strips only the model
    suffix vars at spawn, so PATH and these variables reach the stub."""
    env = dict(os.environ)
    src = str(_s67w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    if extra_path is not None:
        env["PATH"] = os.pathsep.join([str(extra_path), env.get("PATH", "")])
    env.update(vars)
    return env


def _s67w2_run(
    cwd: Path, argv: list[str], env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess, 240s bounded."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(cwd),
        env=env if env is not None else _s67w2_env(),
        capture_output=True,
        text=True,
        timeout=S67W2_TIMEOUT,
        check=False,
    )


def _s67w2_priors_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s67w2_stub_kancil(tmp_path: Path) -> tuple[Path, Path]:
    """A stub `kancil` on PATH; (stub dir, capture file).

    The stub echoes the prompt into a file: argv on line one, the contents
    of every file-valued argument (the rendered prompt path case), then
    stdin (the piped-prompt case), into $S67W2_KANCIL_CAPTURE. Exit 0, so
    the engine's exit-file wrapper records a clean writer exit.
    """
    stub_dir = tmp_path / "stub-bin"
    stub_dir.mkdir(parents=True, exist_ok=True)
    capture = tmp_path / "kancil-capture.txt"
    script = (
        "#!/bin/sh\n"
        "{\n"
        "  printf 'argv:'\n"
        '  for a in "$@"; do printf \' %s\' "$a"; done\n'
        "  printf '\\n'\n"
        '  for a in "$@"; do\n'
        '    if [ -f "$a" ]; then printf -- \'--- file %s\\n\' "$a"; cat "$a"; fi\n'
        "  done\n"
        "  printf -- '--- stdin\\n'\n"
        "  cat\n"
        '} > "$S67W2_KANCIL_CAPTURE"\n'
        "exit 0\n"
    )
    stub = stub_dir / "kancil"
    stub.write_text(script, encoding="utf-8")
    stub.chmod(0o755)
    return stub_dir, capture


def _s67w2_campaign(tmp_path: Path, tag: str, routes: dict[str, str]) -> tuple[Path, Path]:
    """One throwaway campaign; (campaign .rumpun root, campaign proj dir).

    rumpun.yaml carries the given routes map verbatim (pin 1 passes the
    repo's live map) plus the manual-stage autonomy block; the layout
    matches the scaffolded shape (seasons/, ledger/, runs/, prompts/dev/).
    """
    root = tmp_path / tag / "proj" / ".rumpun"
    proj = root.parent
    for sub in ("seasons", "ledger", "runs", "prompts/dev"):
        (root / sub).mkdir(parents=True)
    (root / "prompts" / "dev" / "dummy.md").write_text(
        f"{S67W2_MARKER}\n" "stub prompt body\n", encoding="utf-8",
    )
    (root / "rumpun.yaml").write_text(
        "autonomy:\n"
        "  stage: manual\n"
        "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
        "routes:\n"
        # single-quoted one-line scalars, the live config's own style; YAML
        # doubles internal single quotes, so sh -c '...' route bodies survive
        + "".join(
            f"  {name}: '" + cmd.replace("'", "''") + "'\n"
            for name, cmd in routes.items()
        ),
        encoding="utf-8",
    )
    return root, proj


def _s67w2_season(root: Path, sid: str, route: str) -> Path:
    """One lint-clean single-writer season yaml; returns its path.

    Seed season (no primary_change), fight mode, one execute phase that
    reads and writes results.jsonl (the s34 falsify_required shape), one
    writer on the given route with the marker prompt.
    """
    path = root / "seasons" / f"{sid}.yaml"
    path.write_text(
        f"id: {sid}\n"
        "parent: null\n"
        f'goal: "fixture season for the s67 kancil pins"\n'
        'metric: "m"\n'
        "mode: fight\n"
        "methodology:\n"
        '  approach: "stub close for the s67 pins"\n'
        "  evidence: []\n"
        "  pipeline:\n"
        "    - phase: execute\n"
        "      primitive: execute\n"
        "      agents: benih\n"
        "      prompt: prompts/dev/dummy.md\n"
        "      writes: results.jsonl\n"
        "      reads: results.jsonl\n"
        "writers:\n"
        "  - name: w1\n"
        f"    route: {route}\n"
        "    prompt: prompts/dev/dummy.md\n"
        "    knowledge: none\n"
        "    budget: {minutes: 1}\n"
        'stop:\n'
        '  "on": [all_exited, {stall_minutes: 0.1}]\n',
        encoding="utf-8",
    )
    return path


# --- pin 1: the kancil route spawns -----------------------------------------


def test_s67w2_kancil_route_spawns_stub_writer(tmp_path: Path) -> None:
    """A kancil-routed season start hands the prompt to a real spawn.

    The routes map comes from the repo's live rumpun.yaml (w1's file), so
    the fixture campaign is exactly what a merged tree gives a campaign.
    The stub `kancil` sits first on PATH; `season start` must exit 0, the
    season must persist status completed, and the stub's capture file must
    carry the marker text from the writer's rendered prompt. On today's
    tree no kancil entry exists and _validate_benih refuses the start
    naming the writer -- the red the route landing turns green.
    """
    repo = _s67w2_repo()
    config = yaml.safe_load((repo / ".rumpun" / "rumpun.yaml").read_text(encoding="utf-8"))
    routes = config.get("routes") or {}
    root, _proj = _s67w2_campaign(tmp_path, "kancil-spawn", routes)
    season = _s67w2_season(root, "s670", "kancil")
    stub_dir, capture = _s67w2_stub_kancil(tmp_path)
    env = _s67w2_env(extra_path=stub_dir, S67W2_KANCIL_CAPTURE=str(capture))
    proc = _s67w2_run(
        tmp_path, ["season", "start", str(season)], env,
    )
    assert proc.returncode == 0, (
        f"season start exit {proc.returncode}; a kancil-routed season must complete "
        f"through the stub (route 'kancil' present in the live routes map: "
        f"{'kancil' in routes}). stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    state_path = root / "runs" / "s670" / "_season" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state.get("status") == "completed", (
        f"season s670 persisted {state.get('status')!r}, not completed; "
        f"stderr:\n{proc.stderr}"
    )
    assert capture.is_file(), (
        f"the stub kancil was never invoked (no capture file at {capture}); "
        f"the route must invoke a PATH-resolvable kancil. stderr:\n{proc.stderr}"
    )
    captured = capture.read_text(encoding="utf-8", errors="replace")
    assert S67W2_MARKER in captured, (
        f"the rendered prompt never reached the stub; capture:\n{captured}"
    )
    logger.info(
        "pin 1 held: kancil-routed season completed; the stub capture carries "
        "the rendered prompt marker"
    )


# --- pin 2: the kancil-base pack chain --------------------------------------


def test_s67w2_kancil_base_pack_installs_into_fresh_campaign(tmp_path: Path) -> None:
    """distill -> fresh init -> digest-verified install -> list, all real.

    Campaign A carries the real ratified corpus (the exact _distill_corpus
    surface: ledger/*.md, DESIGN.md, GLOSSARY.md); `plugin distill
    kancil-base` must emit the reviewable draft. Campaign B is a fresh
    `rumpun init` with no overlay; `plugin install` of the draft must land
    manifest.yaml plus the same priors/ tree with the digest verified
    against an independent recompute, and `plugin list` must show the pack
    name and digest. Every step is a subprocess; the real campaign is
    never written (the distill runs in fixture A, never at the repo root).
    """
    repo = _s67w2_repo()
    # Campaign A: fresh init, then the corpus overlay the distill scans.
    a_proj = tmp_path / "distill-campaign"
    proc = _s67w2_run(tmp_path, ["init", str(a_proj)])
    assert proc.returncode == 0, (
        f"fixture defect: init failed for the distill campaign\n{proc.stdout}{proc.stderr}"
    )
    ledger_dst = a_proj / ".rumpun" / "ledger"
    ledger_dst.mkdir(parents=True, exist_ok=True)
    for record in sorted((repo / ".rumpun" / "ledger").glob("*.md")):
        shutil.copy2(record, ledger_dst / record.name)
    for name in ("DESIGN.md", "GLOSSARY.md"):
        source = repo / name
        if source.is_file():
            shutil.copy2(source, a_proj / name)
    proc = _s67w2_run(
        a_proj, ["plugin", "distill", S67W2_PACK, "--source", S67W2_SOURCE],
    )
    assert proc.returncode == 0, (
        f"plugin distill kancil-base exit {proc.returncode}; the draft must emit "
        f"from the ratified corpus. stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    draft = a_proj / ".rumpun" / "plugins" / f"{S67W2_PACK}-draft"
    assert draft.is_dir(), f"no draft pack at {draft}; stdout:\n{proc.stdout}"
    # Campaign B: a fresh scaffolded campaign, no overlay.
    b_proj = tmp_path / "fresh-campaign"
    proc = _s67w2_run(tmp_path, ["init", str(b_proj)])
    assert proc.returncode == 0, (
        f"fixture defect: init failed for the fresh campaign\n{proc.stdout}{proc.stderr}"
    )
    proc = _s67w2_run(b_proj, ["plugin", "install", str(draft)])
    assert proc.returncode == 0, (
        f"plugin install exit {proc.returncode}; the draft must install into the "
        f"fresh campaign. stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    installed = b_proj / ".rumpun" / "plugins" / S67W2_PACK
    assert (installed / "manifest.yaml").is_file(), (
        f"no manifest at {installed}; install did not land the pack"
    )
    draft_digest = _s67w2_priors_digest(draft)
    installed_digest = _s67w2_priors_digest(installed)
    manifest = yaml.safe_load((installed / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest.get("digest") == installed_digest == draft_digest, (
        f"digest mismatch: manifest {manifest.get('digest')!r}, installed tree "
        f"{installed_digest!r}, draft tree {draft_digest!r}"
    )
    proc = _s67w2_run(b_proj, ["plugin", "list"])
    assert proc.returncode == 0, (
        f"plugin list exit {proc.returncode}; stderr:\n{proc.stderr}"
    )
    list_out = proc.stdout
    assert S67W2_PACK in list_out, (
        f"plugin list must show the installed pack; output:\n{list_out}"
    )
    assert draft_digest in list_out, (
        f"plugin list must show the pack digest; output:\n{list_out}"
    )
    logger.info(
        "pin 2 held: kancil-base distilled, installed into the fresh campaign "
        "digest-verified, listed with the digest"
    )


# --- pin 3: the competition template ----------------------------------------


def _s67w2_competition_template(repo: Path, tmp_path: Path) -> tuple[str, Path]:
    """Find the competition season template; (text, campaign proj dir).

    Discovery order (documented in the module docstring): a seasons/ file
    emitted by `rumpun init` other than s1.yaml/_template.yaml whose text
    names competition, else an uppercase scaffold module constant whose
    value names competition and reads as a season yaml. The campaign proj
    dir is the fresh init the pin lints inside.
    """
    proj = tmp_path / "template-campaign"
    proc = _s67w2_run(tmp_path, ["init", str(proj)])
    assert proc.returncode == 0, (
        f"fixture defect: init failed for the template campaign\n"
        f"{proc.stdout}{proc.stderr}"
    )
    seasons = proj / ".rumpun" / "seasons"
    for path in sorted(seasons.glob("*.yaml")):
        if path.name in ("s1.yaml", "_template.yaml"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"competition", text, re.IGNORECASE):
            return text, proj
    from rumpun import scaffold

    for name, value in sorted(vars(scaffold).items()):
        if not name.isupper() or not isinstance(value, str):
            continue
        if "competition" in value.lower() and "id:" in value and "pipeline:" in value:
            target = seasons / "competition.yaml"
            target.write_text(value, encoding="utf-8")
            return value, proj
    raise AssertionError(
        "no competition season template found: rumpun init emits none under "
        "seasons/ and scaffold.py carries no competition template constant"
    )


def test_s67w2_competition_template_lints_clean_and_names_fields(tmp_path: Path) -> None:
    """The competition template lints clean and names its fill-in fields.

    The template must ship lint-clean as written: placeholder fill-in
    fields carry non-empty marker text (empty goal/metric is a lint block,
    the s28 quickstart behavior), so an operator can lint before filling.
    The fill-in fields named: competition, metric, band.
    """
    repo = _s67w2_repo()
    text, proj = _s67w2_competition_template(repo, tmp_path)
    season = proj / ".rumpun" / "seasons" / "competition.yaml"
    if not season.is_file():  # init-emitted variant: lint the file in place
        candidates = []
        for path in sorted((proj / ".rumpun" / "seasons").glob("*.yaml")):
            if path.name in ("s1.yaml", "_template.yaml"):
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r"competition", body, re.IGNORECASE):
                candidates.append(path)
        assert candidates, "template campaign lost its competition season file"
        season = candidates[0]
    proc = _s67w2_run(tmp_path, ["lint", str(season)])
    assert proc.returncode == 0, (
        f"the competition template must lint clean as shipped; lint exit "
        f"{proc.returncode}. stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    lowered = text.lower()
    missing = [field for field in ("competition", "metric", "band") if field not in lowered]
    assert missing == [], (
        f"the competition template must name the fill-in fields; missing: {missing}"
    )
    logger.info("pin 3 held: the competition template linted clean and named its fields")
