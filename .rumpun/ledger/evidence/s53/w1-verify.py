"""s53 w1 verify probe: hub v1 publish -> pull over a local bare git remote.

Round trip: sandbox campaign A (repo DESIGN.md + ledger records) -> plugin
distill kaggle-base -> plugin install the draft -> plugin publish to a bare
remote (git init --bare -b main) -> fresh `rumpun init` campaign B -> plugin
pull -> digest A == digest B == remote manifest digest, and plugin list in B
shows the pack. Guardrails on the wire: a lint-failing pack refuses to
publish (remote unchanged); campaign/ planted inside the installed pack never
reaches the remote; a tampered remote (priors edited after sealing) fails the
pull with digest mismatch and leaves B's registry at one record; a wrong-name
pull and an uninstalled-name publish refuse. Exit 0 all green, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("s53w1.probe")

REPO = Path("/mnt/data/work/rumpun")
WORK = Path("/tmp/s53w1")
PACK = "kaggle-base"
FAILURES: list[str] = []


def _run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One subprocess: the rumpun CLI via -m rumpun (PYTHONPATH=repo/src), or
    a bare git command when argv[0] is git."""
    env = dict(os.environ)
    src = str(REPO / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    cmd = argv if argv[0] == "git" else [sys.executable, "-m", "rumpun", *argv]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    logger.info("$ %s (rc %d)", " ".join(argv), proc.returncode)
    if proc.returncode:
        for line in (proc.stderr or "").strip().splitlines()[-3:]:
            logger.info("   | %s", line)
    return proc


def _digest(pack: Path) -> str:
    """Independent digest helper (the s46w2 pinned convention): sha256 over
    sorted pack-relative POSIX paths, NUL, file bytes."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _ck(cond: bool, label: str, detail: str = "") -> None:
    if cond:
        logger.info("OK   %s", label)
    else:
        logger.error("FAIL %s: %s", label, detail)
        FAILURES.append(f"{label}: {detail}")


def _setup_a() -> Path:
    """Sandbox campaign A: repo DESIGN.md + ledger records, so the distill
    finds its evidenced classes."""
    if WORK.exists():
        shutil.rmtree(WORK)
    a = WORK / "a"
    adot = a / ".rumpun"
    (adot / "ledger").mkdir(parents=True)
    shutil.copy2(REPO / "DESIGN.md", a / "DESIGN.md")
    for path in sorted((REPO / ".rumpun" / "ledger").glob("*.md")):
        shutil.copy2(path, adot / "ledger" / path.name)
    return a


def _bare(name: str) -> Path:
    hub = WORK / name
    subprocess.run(
        ["git", "init", "--bare", "-b", "main", str(hub)],
        capture_output=True,
        text=True,
        check=True,
    )
    return hub


def _remote_tree(remote: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(remote), "ls-tree", "-r", "main", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.split()


def _remote_digest(remote: Path) -> str:
    """The digest declared by the remote's main:manifest.yaml."""
    out = subprocess.run(
        ["git", "-C", str(remote), "show", "main:manifest.yaml"],
        capture_output=True,
        text=True,
        check=True,
    )
    return str(yaml.safe_load(out.stdout)["digest"])


def _verdict() -> int:
    if FAILURES:
        logger.error("%d check(s) failed", len(FAILURES))
        for line in FAILURES:
            logger.error("  %s", line)
        return 1
    logger.info("ALL CHECKS GREEN")
    return 0


def main() -> int:
    a = _setup_a()
    adot = a / ".rumpun"
    draft = adot / "plugins" / "kaggle-base-draft"
    installed_a = adot / "plugins" / PACK
    hub = _bare("hub.git")
    b = WORK / "b"
    bdot = b / ".rumpun"

    proc = _run(a, ["plugin", "distill", PACK, "--source", "s53 w1 hub v1 verify"])
    _ck(proc.returncode == 0, "distill")
    if proc.returncode:
        return _verdict()
    proc = _run(a, ["plugin", "install", str(draft)])
    _ck(proc.returncode == 0, "install")
    if proc.returncode:
        return _verdict()
    proc = _run(a, ["plugin", "publish", PACK, "--remote", str(hub)])
    _ck(proc.returncode == 0, "publish")
    if proc.returncode:
        return _verdict()
    tree = _remote_tree(hub)
    _ck(not any("campaign" in p for p in tree), "remote-no-campaign", str(tree)[:200])
    _ck("manifest.yaml" in tree, "remote-manifest")
    priors_n = len([p for p in tree if p.startswith("priors/")])
    _ck(priors_n == 12, "remote-12-priors", f"got {priors_n}")
    if any("campaign" in p for p in tree) or priors_n != 12:
        return _verdict()

    _run(WORK, ["init", str(b)])
    proc = _run(b, ["plugin", "pull", PACK, "--remote", str(hub)])
    _ck(proc.returncode == 0, "pull")
    if proc.returncode:
        return _verdict()
    digest_a = _digest(installed_a)
    digest_b = _digest(bdot / "plugins" / PACK)
    digest_remote = _remote_digest(hub)
    logger.info("digest A installed: %s", digest_a)
    logger.info("digest B installed: %s", digest_b)
    logger.info("digest remote manifest: %s", digest_remote)
    _ck(digest_a == digest_b == digest_remote, "digest-equal", "A/B/remote differ")
    proc = _run(b, ["plugin", "list"])
    row = f"{PACK}  0.1.0  {digest_b}"
    _ck(proc.returncode == 0 and row in proc.stdout, "plugin-list",
        f"want {row!r}, got {proc.stdout.strip()[:200]!r}")

    bad = adot / "plugins" / "bad-pack"
    (bad / "priors").mkdir(parents=True)
    (bad / "priors" / "leak.md").write_text("seeded from s36 gates\n", encoding="utf-8")
    manifest = {
        "name": "bad-pack",
        "version": "0.1.0",
        "digest": _digest(bad),
        "private_vocabulary": ["sid"],
        "source": "guardrail probe",
    }
    (bad / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    proc = _run(a, ["plugin", "install", str(bad)])
    _ck(proc.returncode == 1, "bad-pack-install-refused", f"rc {proc.returncode}")
    proc = _run(a, ["plugin", "publish", "bad-pack", "--remote", str(hub)])
    _ck(proc.returncode == 1, "publish-lint-gate", f"rc {proc.returncode}")
    _ck("lint error" in proc.stderr, "publish-lint-gate-finding",
        proc.stderr.strip()[-150:])
    _ck(_remote_tree(hub) == tree, "publish-lint-gate-remote-unchanged")

    planted = installed_a / "campaign"
    planted.mkdir()
    (planted / "private.md").write_text("s53 w1 private note\n", encoding="utf-8")
    hub2 = _bare("hub2.git")
    proc = _run(a, ["plugin", "publish", PACK, "--remote", str(hub2)])
    _ck(proc.returncode == 0, "publish-with-campaign-source")
    tree2 = _remote_tree(hub2)
    _ck(not any("campaign" in p for p in tree2), "campaign-invisible", str(tree2)[:200])
    shutil.rmtree(planted)
    shutil.rmtree(bad)

    remote2 = _bare("remote2.git")
    clone = WORK / "tamper"
    subprocess.run(["git", "clone", "-q", str(hub), str(clone)],
                   capture_output=True, text=True, check=True)
    target = clone / "priors" / "falsify-enforcement.md"
    target.write_text(
        target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8"
    )
    for argv in (
        ["add", "-A"],
        ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "t"],
        ["push", "-q", str(remote2), "HEAD:refs/heads/main"],
    ):
        subprocess.run(["git", "-C", str(clone), *argv],
                       capture_output=True, text=True, check=True)
    proc = _run(b, ["plugin", "pull", PACK, "--remote", str(remote2)])
    _ck(proc.returncode == 1, "pull-tampered", f"rc {proc.returncode}")
    _ck("digest mismatch" in proc.stderr, "pull-tampered-reason",
        proc.stderr.strip()[-150:])
    proc = _run(b, ["plugin", "list"])
    rows = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    _ck(len(rows) == 1 and rows[0].startswith(PACK), "registry-after-refusal",
        f"rows: {rows}")

    proc = _run(b, ["plugin", "pull", "not-kaggle", "--remote", str(hub)])
    _ck(proc.returncode == 1 and "not 'not-kaggle'" in proc.stderr,
        "pull-wrong-name", proc.stderr.strip()[-150:])
    proc = _run(b, ["plugin", "publish", "no-such-pack", "--remote", str(hub)])
    _ck(proc.returncode == 1 and "no installed pack" in proc.stderr,
        "publish-uninstalled", proc.stderr.strip()[-150:])
    return _verdict()


if __name__ == "__main__":
    sys.exit(main())
