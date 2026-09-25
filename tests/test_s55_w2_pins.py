"""s55 w2 pins — the independent artifact check, specified before it exists.

w1 lands tools/artifact_check.py: `python tools/artifact_check.py <sid>
<close-commit>` re-verifies the named season's landed ships from artifacts
alone: extract the close commit to a temp tree (git archive only), run the
season's merged pins there (repo venv, PYTHONPATH from that tree), recompute
any claimed pack digests, and diff the DESIGN ships row against the tree.
It writes a check-<sid> ledger record carrying the commands run, the pins
outcome, the digest comparisons, the ships-row diff (each named ship MATCH
or the named delta), and a verdict line VERIFIED or DELTA. CLI wiring:
`rumpun check <sid> <close-commit>`.

Interface these pins hold (the tools/replay_corpus.py flag precedent):
    python tools/artifact_check.py <sid> <close-commit>
        [--repo ROOT] [--out-dir DIR]
--repo is the git tree the check runs against (default: the pyproject
walk-up from the tool file). --out-dir receives the check-<sid> record and
any logs, created when missing (default: <repo>/.rumpun/ledger). Every pin
redirects --out-dir into tmp_path, so no pin ever writes the real ledger;
the tampered scenarios build whole git fixtures in tmp_path and never edit
the real ledger or DESIGN.md.

Red against current main (tools/artifact_check.py is absent, so every pin
fails at the subprocess launch for exactly that reason); green at merge via
w1's tool. The honest-close pin runs against the real repo and the real
s54 close commit; refusals and tampered scenarios run against fixtures.
Digest ground truth: the s54 close commit carries zero installed packs, so
its honest record shows an empty digest section, not digest rows.

Grafting: drop this file into tests/ as-is. Helpers carry the _s55w2_
prefix, so nothing collides with existing defs. Every checker run is a
subprocess bounded by S55W2_TIMEOUT (the spec's 240s bound).
"""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

S55W2_TIMEOUT = 240  # the spec bound for one checker run
S55W2_TOOL = "tools/artifact_check.py"
S55W2_CLOSE = "614aabf5a4a017e84b08caa60c57f7098afdc627"  # "s54 finishes the rename; s55 seeded"
S55W2_S54_PINS = "tests/test_s54_w2_rename_pins.py"
S55W2_GHOST = "src/rumpun/ghost.py"  # the ships row names it; the tree lacks it
S55W2_PACK = "kaggle-base"
S55W2_FAKE_DIGEST = "f" * 64  # well-formed, recomputes DIFFERENT

S55W2_DESIGN = """\
# fixture design

## 15. campaign log

### {sid} — the fixture season (2026-09-16)

| season | outcome | ships |
|---|---|---|
| {sid} | WIN (all band clauses met) | src/rumpun/__init__.py ships the fixture surface; \
tests/test_{sid}_w2_pins.py green{extra} |
"""

S55W2_PINS = '''\
"""s{sid} fixture pins: the merged pins of a one-ship fixture season."""


def test_s{sid}_surface_exists() -> None:
    """The named ship exists in the tree the pins run in."""
    root = next(
        p for p in Path(__file__).resolve().parents
        if (p / "pyproject.toml").is_file()
    )
    assert (root / "src" / "rumpun" / "__init__.py").is_file()
'''

S55W2_PINS_BROKEN = "def test_s901_broken(:\n"  # fails to collect


def _s55w2_repo() -> Path:
    """The repo root: the first pyproject.toml walking up from this file."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s55w2_check(
    root: Path, out_dir: Path, sid: str, commit: str,
) -> subprocess.CompletedProcess[str]:
    """One bounded checker subprocess against root, record into out_dir."""
    argv = [
        sys.executable, str(_s55w2_repo() / S55W2_TOOL),
        sid, commit, "--repo", str(root), "--out-dir", str(out_dir),
    ]
    try:
        return subprocess.run(
            argv, cwd=str(_s55w2_repo()),
            capture_output=True, text=True, timeout=S55W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"artifact_check {sid} {commit} exceeded {S55W2_TIMEOUT}s"
        ) from exc


def _s55w2_git_env() -> dict[str, str]:
    """Git walled off from the operator's config (fixture commits land anywhere)."""
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_AUTHOR_NAME"] = "s55 w2 pins"
    env["GIT_AUTHOR_EMAIL"] = "pins@s55w2.invalid"
    env["GIT_COMMITTER_NAME"] = "s55 w2 pins"
    env["GIT_COMMITTER_EMAIL"] = "pins@s55w2.invalid"
    return env


def _s55w2_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """One bounded git subprocess; callers assert the rc."""
    try:
        return subprocess.run(
            ["git", *args], cwd=str(cwd), env=_s55w2_git_env(),
            capture_output=True, text=True, timeout=S55W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"git {' '.join(args)} exceeded {S55W2_TIMEOUT}s") from exc


def _s55w2_priors_digest(pack_dir: Path) -> str:
    """The declared v1 digest: sha256 over sorted priors/ (rel, NUL, bytes)."""
    digest = hashlib.sha256()
    for path in sorted(p for p in (pack_dir / "priors").rglob("*") if p.is_file()):
        digest.update(path.relative_to(pack_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _s55w2_fixture(
    tmp_path: Any, sid: str, *,
    ghost_ship: bool = False, bad_pack: bool = False, broken_pins: bool = False,
) -> tuple[Path, str]:
    """One committed season close as a git repo; each flag tampers one thing.

    The base fixture is honest: a DESIGN ships row naming two files the tree
    carries, a green pins file, an empty ledger. ghost_ship adds a ships-row
    path the tree lacks; bad_pack installs a pack whose manifest digest
    recomputes different; broken_pins swaps the pins file for one pytest
    cannot collect. Returns (repo root, close-commit sha).
    """
    root = tmp_path / f"fix-{sid}"
    (root / "src" / "rumpun").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / ".rumpun" / "ledger").mkdir(parents=True)
    (root / "src" / "rumpun" / "__init__.py").write_text("", encoding="utf-8")
    extra = f"; {S55W2_GHOST} carries the ghost surface" if ghost_ship else ""
    (root / "DESIGN.md").write_text(
        S55W2_DESIGN.format(sid=sid, extra=extra), encoding="utf-8",
    )
    pins = root / "tests" / f"test_{sid}_w2_pins.py"
    pins.write_text(
        S55W2_PINS_BROKEN if broken_pins else S55W2_PINS.format(sid=sid),
        encoding="utf-8",
    )
    if bad_pack:
        pack_dir = root / ".rumpun" / "plugins" / S55W2_PACK
        (pack_dir / "priors" / "patterns").mkdir(parents=True)
        (pack_dir / "priors" / "patterns" / "baseline.md").write_text(
            "baseline\n", encoding="utf-8",
        )
        (pack_dir / "manifest.yaml").write_text(
            f"name: {S55W2_PACK}\nversion: 0.1.0\ndigest: {S55W2_FAKE_DIGEST}\n"
            "private_vocabulary: []\nsource: fixture pack\n",
            encoding="utf-8",
        )
        (root / ".rumpun" / "plugins.yml").write_text(
            f"plugins:\n  {S55W2_PACK}:\n    version: 0.1.0\n    digest: {S55W2_FAKE_DIGEST}\n",
            encoding="utf-8",
        )
    for args in (("init", "-b", "main"), ("add", "-A"), ("commit", "-m", f"close s{sid}")):
        proc = _s55w2_git(root, *args)
        assert proc.returncode == 0, proc.stdout + proc.stderr
    head = _s55w2_git(root, "rev-parse", "HEAD")
    assert head.returncode == 0, head.stdout + head.stderr
    return root, head.stdout.strip()


def _s55w2_record(out_dir: Path, sid: str) -> str:
    """The check-<sid> record text: the out_dir file carrying `id: check-<sid>`."""
    if not out_dir.is_dir():
        raise AssertionError(f"out dir missing (checker wrote nothing): {out_dir}")
    marker = f"id: check-{sid}"
    hits: list[str] = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="replace"):
            hits.append(path.read_text(encoding="utf-8", errors="replace"))
    if not hits:
        listing = "\n".join(sorted(str(p) for p in out_dir.rglob("*")))
        raise AssertionError(f"no record carrying {marker!r} under {out_dir}:\n{listing}")
    return hits[0]


# --- spec 1: the honest close verifies ---------------------------------------


def test_s55w2_honest_close_s54_verifies(tmp_path: Any) -> None:
    import subprocess as _sp
    import pytest
    if _sp.run(["git", "-C", str(Path(__file__).resolve().parents[1]), "cat-file", "-e",
                "614aabf5a4a017e84b08caa60c57f7098afdc627^{commit}"],
               capture_output=True).returncode != 0:
        pytest.skip("live-campaign pin: anchors a campaign-history commit absent from this clone")
    """`artifact_check s54 <close-commit>` exits 0 on the honest close.

    Against the real repo and the real s54 close commit: exit 0; the record
    is check-s54 with verdict VERIFIED and no DELTA; the pins re-ran green
    in the extracted tree (a "N passed" pytest summary, no failed count);
    the record cites the commands it ran (pytest on the s54 pins file, the
    git archive extraction, a digest section even though s54 claims no
    packs).
    """
    out_dir = tmp_path / "check-s54"
    proc = _s55w2_check(_s55w2_repo(), out_dir, "s54", S55W2_CLOSE)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    record = _s55w2_record(out_dir, "s54")
    assert "VERIFIED" in record, record
    assert "DELTA" not in record, record
    for token in ("pytest", S55W2_S54_PINS, "archive", "digest"):
        assert token in record, f"record must cite {token!r}:\n{record}"
    assert re.search(r"\b\d+ passed\b", record), record
    assert not re.search(r"\b[1-9]\d* failed\b", record), record


# --- spec 2: the dishonest close is detected ---------------------------------


def test_s55w2_ships_tamper_yields_delta(tmp_path: Any) -> None:
    """A ships row naming a file the tree lacks yields DELTA and exit 1.

    The fixture is honest except one clause: the ships row names
    src/rumpun/ghost.py, which the committed tree lacks. The checker exits
    1, the record's verdict is DELTA, and the delta names the missing file.
    """
    root, sha = _s55w2_fixture(tmp_path, "s900", ghost_ship=True)
    out_dir = tmp_path / "out-ships"
    proc = _s55w2_check(root, out_dir, "s900", sha)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    record = _s55w2_record(out_dir, "s900")
    assert "DELTA" in record, record
    assert "VERIFIED" not in record, record
    assert S55W2_GHOST in record, record


def test_s55w2_digest_tamper_yields_delta(tmp_path: Any) -> None:
    """A digest that recomputes different yields DELTA and exit 1.

    The fixture is honest except the pack manifest: it seals digest
    ffff... while the priors/ tree recomputes to another value. The
    checker exits 1, the record's verdict is DELTA, and the comparison
    names the pack, the declared digest, and the recomputed digest. (The
    fixture ships and pins are green, so the digest is the only delta
    source.)
    """
    root, sha = _s55w2_fixture(tmp_path, "s900", bad_pack=True)
    out_dir = tmp_path / "out-digest"
    proc = _s55w2_check(root, out_dir, "s900", sha)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    record = _s55w2_record(out_dir, "s900")
    assert "DELTA" in record, record
    assert "VERIFIED" not in record, record
    assert S55W2_PACK in record, record
    actual = _s55w2_priors_digest(root / ".rumpun" / "plugins" / S55W2_PACK)
    assert S55W2_FAKE_DIGEST in record, record
    assert actual in record, record


# --- spec 3: refusals are loud ------------------------------------------------


def test_s55w2_missing_commit_refuses(tmp_path: Any) -> None:
    """A close commit git cannot resolve refuses nonzero, naming the sha."""
    missing = "f" * 40
    proc = _s55w2_check(_s55w2_repo(), tmp_path / "out-mc", "s54", missing)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert missing in proc.stdout + proc.stderr, (
        f"refusal must name the missing commit:\n{proc.stdout}\n{proc.stderr}"
    )


def test_s55w2_unknown_sid_refuses(tmp_path: Any) -> None:
    import subprocess as _sp
    import pytest
    if _sp.run(["git", "-C", str(Path(__file__).resolve().parents[1]), "cat-file", "-e",
                "614aabf5a4a017e84b08caa60c57f7098afdc627^{commit}"],
               capture_output=True).returncode != 0:
        pytest.skip("live-campaign pin: anchors a campaign-history commit absent from this clone")
    """An unknown season id refuses nonzero, naming the sid."""
    proc = _s55w2_check(_s55w2_repo(), tmp_path / "out-us", "s999", S55W2_CLOSE)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "s999" in proc.stdout + proc.stderr, (
        f"refusal must name the unknown season:\n{proc.stdout}\n{proc.stderr}"
    )


def test_s55w2_pins_collect_failure_refuses(tmp_path: Any) -> None:
    """Season pins that fail to collect refuse nonzero, naming the pins file."""
    root, sha = _s55w2_fixture(tmp_path, "s901", broken_pins=True)
    out_dir = tmp_path / "out-collect"
    proc = _s55w2_check(root, out_dir, "s901", sha)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "test_s901_w2_pins.py" in proc.stdout + proc.stderr, (
        f"refusal must name the pins that failed to collect:"
        f"\n{proc.stdout}\n{proc.stderr}"
    )
