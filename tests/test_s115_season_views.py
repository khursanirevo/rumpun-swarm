"""s115 w1 pins — the season views stop guessing (issues #31 and #35).

Two filed defects, one surface pair, both observed by the khursani tick
driver on 2026-09-20:

#31 — `rumpun season list` row order flipped newest-last -> newest-first
(the #26 wave, commit 4f04d48) and the ask is a documented order contract.
The tree already renders newest-first and the --help text names the order;
pins 1 and 2 hold that contract as regression guards (green-on-arrival by
design — the flip is the wanted state, the help text is the contract).

#35 — `rumpun season status <sid>` on a drafted-only season (the yaml
exists under .rumpun/seasons/, no run state under .rumpun/runs/<sid>/)
logged "ERROR no season state" and exited 1 while the list rendered the
same season as "no state". The contract: status prints the named line
"no state (drafted)" with exit 0, so a driver can probe what list
already printed without try/except. Pins 3 and 4 were red-first against
the erroring verb. A sid with no yaml at all stays an error (pin 5) —
typo protection must not soften into a drafted line.

The s108 fixture pattern: no rumpun imports, subprocess and file reads
only; the tmp campaign synthesizes drafted-only state (real-shaped
season yamls, no runs dirs). Helpers carry the _s115w1_ prefix, so
nothing collides with existing defs.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

S115W1_TIMEOUT = 60  # seconds; a local CLI run, no network


def _s115w1_repo() -> Path:
    """The repo root: first ancestor of this file holding pyproject.toml."""
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s115w1_env() -> dict[str, str]:
    """Subprocess env with the repo's src/ first on PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s115w1_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s115w1_campaign(tmp_path: Path) -> Path:
    """A minimal rumpun campaign: config marker + three drafted-only yamls.

    The season yamls carry the real draft shape (id, parent, goal,
    metric). No .rumpun/runs/<sid> exists for any of them, so every
    season here is drafted-only: exactly the state issue #35 names.
    s1, s2, s10 pin the numeric sort (s10 must beat s2, s1).
    """
    root = tmp_path / "camp"
    seasons = root / ".rumpun" / "seasons"
    seasons.mkdir(parents=True)
    (root / ".rumpun" / "rumpun.yaml").write_text("", encoding="utf-8")
    for sid, parent in (("s1", None), ("s2", "s1"), ("s10", "s2")):
        lines = [f"id: {sid}"]
        if parent:
            lines.append(f"parent: {parent}")
        lines.append("goal: fixture season for the s115 view pins")
        lines.append("metric: modules_integrated")
        (seasons / f"{sid}.yaml").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    return root


def _s115w1_run(root: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    """One bounded CLI subprocess run with cwd at the campaign root."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=root,
        env=_s115w1_env(),
        capture_output=True,
        text=True,
        timeout=S115W1_TIMEOUT,
    )


def test_s115_list_newest_first(tmp_path) -> None:
    """#31 contract: the newest season id is the first row, exit 0."""
    root = _s115w1_campaign(tmp_path)
    proc = _s115w1_run(root, "season", "list")
    assert proc.returncode == 0, proc.stderr
    rows = proc.stdout.strip().splitlines()
    assert [row.split()[0] for row in rows] == ["s10", "s2", "s1"]


def test_s115_list_help_names_order(tmp_path) -> None:
    """#31 ask (a): the season help names the newest-first contract.

    The help= text renders in the parent listing (rumpun season --help),
    wrapped to width -- normalize whitespace before matching.
    """
    root = _s115w1_campaign(tmp_path)
    proc = _s115w1_run(root, "season", "--help")
    assert proc.returncode == 0, proc.stderr
    assert "newest first" in " ".join(proc.stdout.split())


def test_s115_status_drafted_line(tmp_path) -> None:
    """#35 contract: drafted-only status prints the named line, exit 0."""
    root = _s115w1_campaign(tmp_path)
    proc = _s115w1_run(root, "season", "status", "s2")
    assert proc.returncode == 0, proc.stderr
    assert "no state (drafted)" in proc.stdout
    assert "ERROR" not in proc.stderr


def test_s115_status_drafted_agrees_with_list(tmp_path) -> None:
    """#35: the row list renders as no state probes clean on status."""
    root = _s115w1_campaign(tmp_path)
    listing = _s115w1_run(root, "season", "list")
    assert listing.returncode == 0, listing.stderr
    assert "s2  no state" in listing.stdout
    status = _s115w1_run(root, "season", "status", "s2")
    assert status.returncode == 0, status.stderr
    assert "no state (drafted)" in status.stdout


def test_s115_status_unknown_sid_errors(tmp_path) -> None:
    """No yaml at all stays an error: the drafted line names drafted only."""
    root = _s115w1_campaign(tmp_path)
    proc = _s115w1_run(root, "season", "status", "s404")
    assert proc.returncode != 0
    assert "no season state" in proc.stderr
