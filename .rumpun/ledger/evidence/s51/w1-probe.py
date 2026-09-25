"""s51 w1 probe: the extended distill end to end against the real campaign.

Builds a sandbox campaign (repo DESIGN.md + ledger) in /tmp, runs
`plugin distill kaggle-base --source "extended from the campaign"` as a
subprocess, and checks:
  1. exit 0; the draft carries gates, patterns/, templates/ (4 files each)
  2. the manifest digest equals the recomputed digest over the full
     priors/ tree, and equals plugin.priors_digest(draft)
  3. plugin_lint reports zero error findings on the emitted pack
  4. no sid token, no absolute path, no campaign-name token in any
     priors/ filename or content line (the pin-2 shape, all three kinds)
  5. `plugin install` round trip: the installed tree matches the draft
     file-for-file and the registry row carries the pack digest
Logging only; exit 0 on all checks green, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("s51w1.probe")

REPO = Path("/mnt/data/work/rumpun")
WORK = Path("/tmp/s51w1-probe")
PACK_NAME = "kaggle-base"
SOURCE_NOTE = "extended from the campaign"
NAME_RE = re.compile(r"\brumpun\b", re.IGNORECASE)


def _run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    src = str(REPO / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _priors_digest(pack: Path) -> str:
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _priors_texts(pack: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in sorted((pack / "priors").rglob("*")):
        if path.is_file():
            out.append(
                (path.relative_to(pack).as_posix(), path.read_text(encoding="utf-8"))
            )
    return out


def _campaign() -> SimpleNamespace:
    if WORK.exists():
        shutil.rmtree(WORK)
    campaign = WORK / "campaign"
    dot = campaign / ".rumpun"
    (dot / "ledger").mkdir(parents=True)
    shutil.copy2(REPO / "DESIGN.md", campaign / "DESIGN.md")
    for path in sorted((REPO / ".rumpun" / "ledger").glob("*.md")):
        shutil.copy2(path, dot / "ledger" / path.name)
    return SimpleNamespace(campaign=campaign, dot=dot)


def _fail(check: str, detail: str, failures: list[str]) -> None:
    failures.append(f"{check}: {detail}")
    logger.error("FAIL %s: %s", check, detail)


def _check_tree(state: SimpleNamespace, failures: list[str]) -> dict[str, Any]:
    draft = state.campaign / ".rumpun" / "plugins" / f"{PACK_NAME}-draft"
    if not draft.is_dir():
        _fail("tree", f"no draft dir at {draft}", failures)
        return {}
    gates = sorted(p.name for p in (draft / "priors").glob("*.md"))
    patterns = sorted(p.name for p in (draft / "priors" / "patterns").glob("*.md"))
    templates = sorted(p.name for p in (draft / "priors" / "templates").glob("*.md"))
    logger.info("gates:    %s", gates)
    logger.info("patterns: %s", patterns)
    logger.info("templates: %s", templates)
    if len(gates) != 4:
        _fail("tree", f"expected 4 gate files, got {gates}", failures)
    if len(patterns) != 4:
        _fail("tree", f"expected 4 pattern files, got {patterns}", failures)
    if len(templates) != 4:
        _fail("tree", f"expected 4 template files, got {templates}", failures)
    return {"draft": draft}


def _check_digest_and_lint(
    state: SimpleNamespace, ctx: dict[str, Any], failures: list[str]
) -> None:
    sys.path.insert(0, str(REPO / "src"))
    from rumpun import plugin

    draft: Path = ctx["draft"]
    manifest = plugin.load_manifest(draft)
    declared = manifest.get("digest")
    computed = _priors_digest(draft)
    if declared != computed:
        _fail("digest", f"manifest {declared} != recomputed {computed}", failures)
    if plugin.priors_digest(draft) != computed:
        _fail("digest", "plugin.priors_digest disagrees with the probe recompute", failures)
    findings = plugin.plugin_lint(draft, manifest)
    errors = [f.message for f in findings if f.severity == "error"]
    if errors:
        _fail("lint", f"{len(errors)} error finding(s): {errors}", failures)
    for rel, text in _priors_texts(draft):
        if plugin.SID_TOKEN_RE.search(rel) or plugin.SID_TOKEN_RE.search(text):
            _fail("leak", f"sid token in {rel}", failures)
        for pattern in (plugin.ABS_PATH_RE, plugin.WIN_PATH_RE):
            if pattern.search(rel) or pattern.search(text):
                _fail("leak", f"absolute-path token in {rel}", failures)
        if NAME_RE.search(rel) or NAME_RE.search(text):
            _fail("leak", f"campaign-name token in {rel}", failures)
    logger.info(
        "digest+lint checked over %d priors files", len(_priors_texts(draft))
    )


def _check_install(
    state: SimpleNamespace, ctx: dict[str, Any], failures: list[str]
) -> None:
    draft: Path = ctx["draft"]
    proc = _run(state.campaign, ["plugin", "install", str(draft)])
    if proc.returncode != 0:
        _fail("install", f"rc={proc.returncode}: {proc.stdout}{proc.stderr}", failures)
        return
    installed = state.campaign / ".rumpun" / "plugins" / PACK_NAME
    draft_rels = {rel for rel, _ in _priors_texts(draft)}
    installed_rels = {rel for rel, _ in _priors_texts(installed)}
    if installed_rels != draft_rels:
        _fail(
            "install",
            f"installed tree differs: draft-only {sorted(draft_rels - installed_rels)}"
            f" installed-only {sorted(installed_rels - draft_rels)}",
            failures,
        )
    sys.path.insert(0, str(REPO / "src"))
    from rumpun import plugin as plugin_mod

    records = {r["name"]: r for r in plugin_mod.plugin_list(state.campaign)}
    if PACK_NAME not in records:
        _fail("install", f"registry lacks {PACK_NAME}: {sorted(records)}", failures)
    elif records[PACK_NAME]["digest"] != _priors_digest(draft):
        _fail("install", "registry digest != draft digest", failures)
    else:
        logger.info("installed %s files, registry row present", len(installed_rels))


def main() -> int:
    state = _campaign()
    failures: list[str] = []
    proc = _run(
        state.campaign, ["plugin", "distill", PACK_NAME, "--source", SOURCE_NOTE]
    )
    logger.info("distill rc=%d", proc.returncode)
    if proc.returncode != 0:
        _fail("distill", f"rc={proc.returncode}: {proc.stdout}{proc.stderr}", failures)
    else:
        ctx = _check_tree(state, failures)
        if ctx:
            _check_digest_and_lint(state, ctx, failures)
            _check_install(state, ctx, failures)
    if failures:
        logger.error("%d check(s) failed", len(failures))
        return 1
    logger.info("ALL CHECKS GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
