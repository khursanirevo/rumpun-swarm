"""s56 w2 pins — the check verb, wired before it exists.

Spec-first pins (red against current code) for the s56 contract (season
goal seasons/s56.yaml; w1's brief .rumpun/prompts/dev/w1-check-verb.md;
ledger anchors 2026-09-16_s55-harvest — "the check verb wiring is the
disclosed residual" — and 2026-09-16_audit-39, the usefulness residual
the checker closes). Spec anchors, the interface contract, and the
measured red set: .rumpun/runs/s56/w2/notes.md.

Interface these pins hold (w1's s55 tool plus the w1-check-verb brief):

    python -m rumpun check <sid> <close-commit> [--out-dir DIR]

cwd inside the repo (the verb resolves the project from cwd like every
verb), the record into DIR when given, else the project's ledger dir.
Every pin redirects --out-dir into tmp_path, so no pin writes the real
ledger. Refusals exit nonzero naming what is missing (the checker's own
refusal contract, carried through the verb): an unresolvable close
commit names the sha; an unknown season id names the sid.

Red against current main (cli.py carries no `check` verb; three "rimba"
occurrences survive in audit.py — module docstring, the _season_running
docstring, the F1 block comment — all user-visible), green at merge via
w1's wiring. The honest-close pin runs the verb and the direct tool
against the real s54 close commit and asserts the two records carry the
same VERIFIED verdict. Grafting: land this file in tests/ as-is
(additions-only; existing suite files stay untouched). Helpers carry
the _s56w2_ prefix, so nothing collides with existing defs. Every verb
and tool run is a subprocess bounded by S56W2_TIMEOUT (the spec's 240s
bound).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

S56W2_TIMEOUT = 240  # the spec bound for one verb or tool run
S56W2_SID = "s54"
# "s54 finishes the rename; s55 seeded" — the s54 close commit
S56W2_CLOSE = "614aabf5a4a017e84b08caa60c57f7098afdc627"
S56W2_TOOL = "tools/artifact_check.py"
S56W2_AUDIT = "src/rumpun/audit.py"
S56W2_BAD_SHA = "f" * 40  # well-formed, unresolvable
S56W2_UNKNOWN_SID = "s999"


def _s56w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and
    grafted into tests/ (post-graft): both sit under the repo root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s56w2_env() -> dict[str, str]:
    """The subprocess env: repo src/ on PYTHONPATH ahead of any inherited value."""
    env = dict(os.environ)
    src = str(_s56w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s56w2_verb(
    cwd: Path, sid: str, commit: str, out_dir: Path,
) -> subprocess.CompletedProcess[str]:
    """One bounded `python -m rumpun check <sid> <commit> --out-dir` run."""
    argv = [
        sys.executable, "-m", "rumpun", "check", sid, commit,
        "--out-dir", str(out_dir),
    ]
    try:
        return subprocess.run(
            argv, cwd=str(cwd), env=_s56w2_env(), capture_output=True,
            text=True, timeout=S56W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"rumpun check {sid} {commit} exceeded {S56W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s56w2_tool(
    cwd: Path, sid: str, commit: str, out_dir: Path,
) -> subprocess.CompletedProcess[str]:
    """One bounded direct tools/artifact_check.py run (the s55 pin shape)."""
    argv = [
        sys.executable, str(_s56w2_repo() / S56W2_TOOL),
        sid, commit, "--repo", str(cwd), "--out-dir", str(out_dir),
    ]
    try:
        return subprocess.run(
            argv, cwd=str(cwd), env=_s56w2_env(), capture_output=True,
            text=True, timeout=S56W2_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"artifact_check {sid} {commit} exceeded {S56W2_TIMEOUT}s"
        raise AssertionError(msg) from exc


def _s56w2_record(out_dir: Path, sid: str) -> str:
    """The check-<sid> record text: the out_dir file carrying `id: check-<sid>`."""
    if not out_dir.is_dir():
        msg = f"out dir missing (the run wrote nothing): {out_dir}"
        raise AssertionError(msg)
    marker = f"id: check-{sid}"
    hits: list[str] = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            if marker in text:
                hits.append(text)
    if not hits:
        listing = "\n".join(sorted(str(p) for p in out_dir.rglob("*")))
        msg = f"no record carrying {marker!r} under {out_dir}:\n{listing}"
        raise AssertionError(msg)
    return hits[0]


def _s56w2_verdict(record: str) -> str:
    """The verdict token of the record's `verdict:` line."""
    found = re.search(r"^verdict: (\S+)", record, re.M)
    assert found is not None, f"record carries no verdict line:\n{record}"
    return found.group(1)


# --- spec 1: the honest close verifies through the verb -----------------------


def test_s56w2_check_verb_honest_close_s54_verifies(tmp_path: Any) -> None:
    import subprocess as _sp
    import pytest
    if _sp.run(["git", "-C", str(Path(__file__).resolve().parents[1]), "cat-file", "-e",
                "614aabf5a4a017e84b08caa60c57f7098afdc627^{commit}"],
               capture_output=True).returncode != 0:
        pytest.skip("live-campaign pin: anchors a campaign-history commit absent from this clone")
    """`rumpun check s54 <close>` exits 0; its record agrees with the tool's.

    Against the real repo and the real s54 close commit: the verb exits 0
    and writes the check-s54 record carrying verdict VERIFIED with no
    DELTA; the direct tools/artifact_check.py run on the same inputs
    produces the same verdict (parity is asserted on the parsed verdict
    lines of both records).
    """
    repo = _s56w2_repo()
    verb_dir = tmp_path / "verb"
    proc = _s56w2_verb(repo, S56W2_SID, S56W2_CLOSE, verb_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    record = _s56w2_record(verb_dir, S56W2_SID)
    assert "VERIFIED" in record, record
    assert "DELTA" not in record, record
    tool_dir = tmp_path / "tool"
    tool_proc = _s56w2_tool(repo, S56W2_SID, S56W2_CLOSE, tool_dir)
    assert tool_proc.returncode == 0, tool_proc.stdout + tool_proc.stderr
    tool_record = _s56w2_record(tool_dir, S56W2_SID)
    assert _s56w2_verdict(record) == _s56w2_verdict(tool_record) == "VERIFIED"


# --- spec 2: the audit comments speak the real path names ---------------------


def test_s56w2_audit_comments_name_the_runs_path() -> None:
    """No "rimba" survives in src/rumpun/audit.py.

    The audit F1 phase-liveness comment (the "existence at rimba/<sid>/"
    block, ~line 547 today) must name the real runs path. The sweep is
    the s54 rename shape: the banned token absent from the whole source
    file. Red today: three survivors, all in user-visible comments — the
    module docstring (line 5), the _season_running docstring (line 169),
    and the F1 block comment (line 551).
    """
    source = (_s56w2_repo() / S56W2_AUDIT).read_text(encoding="utf-8")
    assert "rimba" not in source, 'legacy token "rimba" survives in audit.py'


# --- spec 3: refusals are loud through the verb -------------------------------


def test_s56w2_unresolvable_commit_refuses(tmp_path: Any) -> None:
    """`rumpun check s54 <unresolvable>` refuses nonzero, naming the sha.

    A well-formed sha git cannot resolve exits nonzero through the verb,
    and stdout+stderr name it (the checker's refusal line carries the
    full git args, so the sha appears; w1's wiring must let stderr flow).
    """
    out_dir = tmp_path / "refuse-commit"
    proc = _s56w2_verb(_s56w2_repo(), S56W2_SID, S56W2_BAD_SHA, out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode != 0, streams
    assert S56W2_BAD_SHA in streams, (
        f"refusal must name the unresolvable commit:\n{streams}"
    )


def test_s56w2_unknown_sid_refuses(tmp_path: Any) -> None:
    """`rumpun check s999 <close>` refuses nonzero, naming the sid."""
    out_dir = tmp_path / "refuse-sid"
    proc = _s56w2_verb(_s56w2_repo(), S56W2_UNKNOWN_SID, S56W2_CLOSE, out_dir)
    streams = proc.stdout + proc.stderr
    assert proc.returncode != 0, streams
    assert S56W2_UNKNOWN_SID in streams, (
        f"refusal must name the unknown season id:\n{streams}"
    )
