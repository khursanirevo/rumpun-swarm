"""s53 w2 pins — the hub round trip and its on-the-wire guardrails.

w1 lands plugin_publish + plugin_pull (hub v1: pack = repo, publish =
push; pull = fetch + digest verify + the s46 install path) with cli
wiring: `rumpun plugin publish <name> --remote <url>` and `rumpun plugin
pull <name> --remote <url>`. These pins hold that contract over a LOCAL
bare git remote (file path, no network). Red against current main (the
verbs do not exist yet); green at merge.

Grafting: drop this file into tests/ as-is. Helpers carry the _s53w2_
prefix, so nothing collides with existing defs. Every verb runs in a
subprocess bounded by S53W2_TIMEOUT; every git op uses a file-path
remote. campaign/ content (the secret token) must never reach the
remote; a tampered remote must refuse the pull.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

S53W2_PACK_NAME = "kaggle-base"
S53W2_TERM = "sampleterm"
S53W2_SECRET = "operator-token-s53w2"
S53W2_TIMEOUT = 120


def _s53w2_repo() -> Path:
    """The repo root: the first pyproject.toml walking up from this file."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s53w2_env() -> dict[str, str]:
    """The subprocess env: repo src/ on PYTHONPATH; git walled off from the
    operator's config (publish/pull must commit and push on any machine)."""
    env = dict(os.environ)
    src = str(_s53w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_AUTHOR_NAME"] = "s53 w2 pins"
    env["GIT_AUTHOR_EMAIL"] = "pins@s53w2.invalid"
    env["GIT_COMMITTER_NAME"] = "s53 w2 pins"
    env["GIT_COMMITTER_EMAIL"] = "pins@s53w2.invalid"
    return env


def _s53w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess from cwd, bounded."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(cwd),
            env=_s53w2_env(),
            capture_output=True,
            text=True,
            timeout=S53W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"rumpun {' '.join(argv)} exceeded {S53W2_TIMEOUT}s") from exc


def _s53w2_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """One bounded `git` subprocess; callers assert the rc."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            env=_s53w2_env(),
            capture_output=True,
            text=True,
            timeout=S53W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"git {' '.join(args)} exceeded {S53W2_TIMEOUT}s") from exc


def _s53w2_priors_digest(pack: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    priors = pack / "priors"
    for path in sorted(p for p in priors.rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s53w2_manifest(digest: str) -> dict[str, Any]:
    """The valid manifest body; digest comes from _s53w2_priors_digest."""
    return {
        "name": S53W2_PACK_NAME,
        "version": "0.1.0",
        "digest": digest,
        "private_vocabulary": [S53W2_TERM],
        "source": "seed pack distilled from a prior campaign's proven gates",
    }


def _s53w2_pack(tmp_path: Any) -> Path:
    """A lint-clean pack whose manifest digest matches its priors/ tree.

    priors/ carries a pattern and a prompts/base/execute.md template;
    campaign/ carries a secret that must never reach the remote.
    """
    pack = tmp_path / "kaggle-base-pack"
    (pack / "priors" / "patterns").mkdir(parents=True)
    (pack / "priors" / "patterns" / "baseline.md").write_text(
        "Start from a fast, complete baseline before tuning anything.\n",
        encoding="utf-8",
    )
    (pack / "priors" / "prompts" / "base").mkdir(parents=True)
    (pack / "priors" / "prompts" / "base" / "execute.md").write_text(
        "# Execute, pack edition\n\nRun the assigned experiments exactly as committed.\n",
        encoding="utf-8",
    )
    (pack / "campaign").mkdir()
    (pack / "campaign" / "verdicts.jsonl").write_text(
        f'{{"sid": "s45", "secret": "{S53W2_SECRET}"}}\n',
        encoding="utf-8",
    )
    digest = _s53w2_priors_digest(pack)
    (pack / "manifest.yaml").write_text(
        yaml.safe_dump(_s53w2_manifest(digest), sort_keys=False),
        encoding="utf-8",
    )
    return pack


def _s53w2_campaign(tmp_path: Any, name: str) -> Path:
    """A fresh campaign root via `rumpun init`."""
    root = Path(tmp_path) / name
    proc = _s53w2_run(Path(tmp_path), ["init", str(root)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return root


def _s53w2_publish(campaign: Path, remote: Path) -> subprocess.CompletedProcess[str]:
    """`plugin publish <name> --remote <path>` from the campaign root."""
    return _s53w2_run(
        campaign, ["plugin", "publish", S53W2_PACK_NAME, "--remote", str(remote)]
    )


def _s53w2_pull(campaign: Path, remote: Path) -> subprocess.CompletedProcess[str]:
    """`plugin pull <name> --remote <path>` from the campaign root."""
    return _s53w2_run(
        campaign, ["plugin", "pull", S53W2_PACK_NAME, "--remote", str(remote)]
    )


def _s53w2_list(campaign: Path) -> dict[str, str]:
    """`plugin list` parsed to {name: digest}."""
    proc = _s53w2_run(campaign, ["plugin", "list"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) == 3:
            out[parts[0]] = parts[2]
    return out


def _s53w2_bare(tmp_path: Any) -> Path:
    """A fresh local bare remote (file path)."""
    remote = Path(tmp_path) / "hub.git"
    proc = _s53w2_git(Path(tmp_path), "init", "--bare", str(remote))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return remote


def _s53w2_refs(remote: Path) -> list[str]:
    """Every ref the remote carries (empty before any publish)."""
    proc = _s53w2_git(remote, "for-each-ref", "--format=%(refname)")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout.split()


def _s53w2_remote_paths(remote: Path) -> list[str]:
    """Sorted unique paths across every ref's tree."""
    paths: set[str] = set()
    for ref in _s53w2_refs(remote):
        proc = _s53w2_git(remote, "ls-tree", "-r", "--name-only", ref)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        paths.update(proc.stdout.split())
    return sorted(paths)


def _s53w2_remote_grep(remote: Path, needle: str) -> bool:
    """True when needle appears in any ref's content (git grep rc 0 = hit)."""
    for ref in _s53w2_refs(remote):
        proc = _s53w2_git(remote, "grep", "-l", needle, ref)
        if proc.returncode == 0:
            return True
        assert proc.returncode == 1, proc.stdout + proc.stderr
    return False


# --- pin 1: the publish->pull round trip over a local bare remote ------------


def test_s53w2_publish_pull_round_trip_lands_identical_pack(tmp_path: Any) -> None:
    """Publish installs to a bare remote; pull lands the identical pack.

    `plugin publish` exits 0 behind the lint gate and the digest verify;
    `plugin pull` installs into a fresh `rumpun init` campaign; the pulled
    digest equals the published digest (both == the pack's sealed digest)
    and plugin list records the pack on both sides.
    """
    campaign_a = _s53w2_campaign(tmp_path, "campaign-a")
    pack = _s53w2_pack(tmp_path)
    proc = _s53w2_run(campaign_a, ["plugin", "install", str(pack)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    remote = _s53w2_bare(tmp_path)

    published = _s53w2_publish(campaign_a, remote)
    assert published.returncode == 0, published.stdout + published.stderr

    campaign_b = _s53w2_campaign(tmp_path, "campaign-b")
    pulled = _s53w2_pull(campaign_b, remote)
    assert pulled.returncode == 0, pulled.stdout + pulled.stderr

    declared = _s53w2_priors_digest(pack)
    digests_a = _s53w2_list(campaign_a)
    digests_b = _s53w2_list(campaign_b)
    assert S53W2_PACK_NAME in digests_a, digests_a
    assert S53W2_PACK_NAME in digests_b, digests_b
    assert digests_a[S53W2_PACK_NAME] == declared, digests_a
    assert digests_b[S53W2_PACK_NAME] == declared, digests_b

    installed_b = campaign_b / ".rumpun" / "plugins" / S53W2_PACK_NAME
    assert (installed_b / "manifest.yaml").is_file()
    assert (installed_b / "priors" / "patterns" / "baseline.md").is_file()
    assert not (installed_b / "campaign").exists()


# --- pin 2: a lint-failing pack refuses to publish ---------------------------


def test_s53w2_publish_refuses_lint_failing_pack(tmp_path: Any) -> None:
    """A tampered installed pack re-seals its digest, so ONLY the lint gate
    can refuse it: the injected private-vocabulary term is an error finding.
    A clean publish succeeds first (the verb exists; the remote carries the
    good pack), the re-sealed tamper then refuses, and the remote keeps the
    good tree: the lint-failing tree never replaces it."""
    campaign_a = _s53w2_campaign(tmp_path, "campaign-a")
    pack = _s53w2_pack(tmp_path)
    proc = _s53w2_run(campaign_a, ["plugin", "install", str(pack)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = campaign_a / ".rumpun" / "plugins" / S53W2_PACK_NAME

    remote = _s53w2_bare(tmp_path)
    first = _s53w2_publish(campaign_a, remote)
    assert first.returncode == 0, first.stdout + first.stderr
    paths_before = _s53w2_remote_paths(remote)
    assert paths_before, "publish pushed no refs; the refusal check is vacuous"

    leak = installed / "priors" / "patterns" / "baseline.md"
    text = leak.read_text(encoding="utf-8")
    leak.write_text(text + f"seeded from {S53W2_TERM} campaign records\n", encoding="utf-8")
    manifest_path = installed / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["digest"] = _s53w2_priors_digest(installed)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    published = _s53w2_publish(campaign_a, remote)
    assert published.returncode != 0, published.stdout + published.stderr
    assert _s53w2_remote_paths(remote) == paths_before, (
        "the lint-failing tree replaced the good tree at the remote"
    )
    assert not _s53w2_remote_grep(remote, "seeded from"), (
        "the tampered content reached the remote"
    )


# --- pin 3: campaign/ content never appears at the remote --------------------


def test_s53w2_publish_keeps_campaign_off_the_remote(tmp_path: Any) -> None:
    """The pack carries campaign/verdicts.jsonl with the secret token. The
    publish succeeds (campaign/ is never linted), and no ref at the remote
    carries a campaign/ path or the secret in any blob."""
    campaign_a = _s53w2_campaign(tmp_path, "campaign-a")
    pack = _s53w2_pack(tmp_path)
    proc = _s53w2_run(campaign_a, ["plugin", "install", str(pack)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    remote = _s53w2_bare(tmp_path)

    published = _s53w2_publish(campaign_a, remote)
    assert published.returncode == 0, published.stdout + published.stderr

    refs = _s53w2_refs(remote)
    assert refs, "publish pushed no refs; the campaign-absence check is vacuous"
    paths = _s53w2_remote_paths(remote)
    campaign_paths = [p for p in paths if "campaign" in Path(p).parts]
    assert not campaign_paths, f"campaign/ reached the remote: {campaign_paths}"
    assert not _s53w2_remote_grep(remote, S53W2_SECRET), (
        "the campaign secret appears in remote content"
    )


# --- pin 4: a tampered remote fails the pull ---------------------------------


def test_s53w2_pull_refuses_tampered_remote(tmp_path: Any) -> None:
    """After a clone-edit-push tampers the remote's priors/ tree, the pull's
    digest verify fails: pull exits non-zero and installs nothing."""
    campaign_a = _s53w2_campaign(tmp_path, "campaign-a")
    pack = _s53w2_pack(tmp_path)
    proc = _s53w2_run(campaign_a, ["plugin", "install", str(pack)])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    remote = _s53w2_bare(tmp_path)

    published = _s53w2_publish(campaign_a, remote)
    assert published.returncode == 0, published.stdout + published.stderr

    clone = tmp_path / "tamper-clone"
    heads = _s53w2_git(remote, "for-each-ref", "refs/heads", "--format=%(refname:short)")
    assert heads.returncode == 0, heads.stdout + heads.stderr
    branches = heads.stdout.split()
    assert branches, "publish pushed no branch; the tamper cannot run"
    tamper = _s53w2_git(tmp_path, "clone", "-b", branches[0], str(remote), str(clone))
    assert tamper.returncode == 0, tamper.stdout + tamper.stderr
    target = clone / "priors" / "patterns" / "baseline.md"
    text = target.read_text(encoding="utf-8")
    target.write_text(text + "tampered after publish\n", encoding="utf-8")
    tamper = _s53w2_git(clone, "commit", "-am", "tamper the priors tree")
    assert tamper.returncode == 0, tamper.stdout + tamper.stderr
    tamper = _s53w2_git(clone, "push", "origin", "HEAD")
    assert tamper.returncode == 0, tamper.stdout + tamper.stderr

    campaign_b = _s53w2_campaign(tmp_path, "campaign-b")
    pulled = _s53w2_pull(campaign_b, remote)
    assert pulled.returncode != 0, pulled.stdout + pulled.stderr
    assert S53W2_PACK_NAME not in _s53w2_list(campaign_b), "the tampered pack installed"
    installed_b = campaign_b / ".rumpun" / "plugins" / S53W2_PACK_NAME
    assert not installed_b.exists(), "the tampered pack landed on disk"
