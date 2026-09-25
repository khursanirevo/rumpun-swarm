"""s138 w2 pins - the steady-state season becomes a scaffold shape.

Ground truth measured 2026-09-21 (probe campaign /tmp/s138w2probe, full
account in .rumpun/runs/s138/w2/notes.md):

- `rumpun init` emits `.rumpun/seasons/_steady-state.yaml`, the shape of
  the guide's section-4 steady state: the standing light lanes (the lint
  sweep, the route probes, the rehearsals) as pipeline phases, a light
  writer table under them, and the operator's decision gate carried in
  primary_change.expected_band.
- The gate, both sides measured: the template AS EMITTED lints clean with
  one warning (the honest-placeholders design, the s67/s127 precedent);
  the wiped-fill copy (every FILL-marked value emptied) refuses naming
  its errors (the positive control, the s127 shape).
- Fixture discipline: init in tmp campaigns; the real campaign is never
  written in tests. The repo campaign does not carry the file: landing it
  is outside this lane's bounds (the guide table documents what init
  writes, not what the repo carries).

Contract these pins hold:
1. init emits the template; its text names the light lanes (lint-sweep,
   route-probes, rehearsals), the decision-gate phase, the operator's
   decision gate, and the fill-in fields.
2. The wiped-fill copy refuses with named errors (positive control).
3. The emitted template lints clean as shipped, and the filled copy
   (every FILL field resolved, evidence citing a sealed ledger record
   through the real akar.append_record path) lints clean.
4. The guide's what-lands table names the file, and the guide's
   steady-state section names the shape.

Red history (measured 2026-09-21): all four pins red pre-implementation
(/tmp/s138w2-red.log): pins 1-3 on the missing emission (the fixture
asserts init's emission first), pin 4 on the missing table row. The
BARE_ERROR_FRAGMENTS prediction held on the first landed run (no
s127-style gate correction needed). Green: /tmp/s138w2-green.log, and
/tmp/s138w2-green2.log after the E501 line shortening; 4 passed both
times.

"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from rumpun import akar

logger = logging.getLogger(__name__)

S138W2_TIMEOUT = 240

# The wipe empties every FILL-marked value; the gate answers with these
# named errors (predicted from lint.py, re-measured against the landed
# template; the s127 lesson: the approach wipe emits NO error because the
# gate checks key presence, so approach carries no fragment here).
BARE_ERROR_FRAGMENTS = (
    "does not match s<N>",
    "goal is empty",
    "metric is empty",
    "baseline is required",
    "expected_band is required",
    "rollback is required",
    "eval_window is required",
    "writer name must be a non-empty string",
)

# Per-occurrence fill values in document order (three writer names).
FILL_VALUES: dict[str, list[str]] = {
    "id": ["s900"],
    "parent": ["s1"],
    "goal": ["keep the campaign machinery warm through the steady state"],
    "metric": ["light-lane re-proofs across the standing three"],
    "approach": [
        "re-prove the standing three; heavier work waits behind the "
        "operator's decision gate"
    ],
    "baseline": ["the standing surfaces the last close left green"],
    "expected_band": [
        "WIN if the lanes re-prove clean and the operator's decision gate "
        "opens the next season; LOSS if a lane reports drift"
    ],
    "rollback": [
        "nothing new ships in the steady state; leaving it is the "
        "operator's decision"
    ],
    "eval_window": [
        "the lanes' artifacts: sweep.jsonl, probes.jsonl, rehearsals.jsonl, "
        "gate-report.jsonl"
    ],
    "name": ["sweep", "probes", "rehearsal"],
}


def _s138w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s138w2_env() -> dict[str, str]:
    """Subprocess env: repo src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s138w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s138w2_run(
    cwd: Path, argv: list[str], env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess, bounded."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(cwd),
        env=env if env is not None else _s138w2_env(),
        capture_output=True,
        text=True,
        timeout=S138W2_TIMEOUT,
        check=False,
    )


def _s138w2_mark_fill_lines(text: str) -> list[tuple[str, re.Match[str] | None]]:
    out: list[tuple[str, re.Match[str] | None]] = []
    for line in text.splitlines():
        is_fill = "FILL" in line and not line.lstrip().startswith("#")
        match = (
            re.match(r"^(\s*(?:-\s+)?)([\w-]+):(.*)$", line) if is_fill else None
        )
        assert not is_fill or match is not None, f"unmarkable FILL line: {line!r}"
        out.append((line, match))
    return out


def _s138w2_bare(text: str) -> str:
    """The bare shape: every FILL-marked value wiped to an empty string.

    Comment lines pass through; a key line carrying FILL keeps its key
    and loses its value (`id: s1  # FILL: ...` -> `id: ""`). The emitted
    template ships non-empty marker values and lints clean as shipped
    (the honest-placeholders design); the wiped copy is the refusal side
    of the gate.
    """
    out: list[str] = []
    for line, match in _s138w2_mark_fill_lines(text):
        if match is None:
            out.append(line)
        else:
            out.append(f'{match.group(1)}{match.group(2)}: ""')
    return "\n".join(out) + "\n"


def _s138w2_filled(text: str, cited: str) -> str:
    """Every FILL field resolved; evidence cites the sealed record.

    Values draw per occurrence in document order, so the three FILL-marked
    writer names fill to three distinct names (duplicate names are a lint
    error).
    """
    out: list[str] = []
    used: dict[str, int] = {}
    for line, match in _s138w2_mark_fill_lines(text):
        if match is None:
            out.append(line)
            continue
        key = match.group(2)
        if key == "evidence":
            out.append(f'{match.group(1)}evidence: ["{cited}"]')
            continue
        values = FILL_VALUES.get(key)
        assert values is not None, f"no fill value mapped for FILL key: {key}"
        i = used.get(key, 0)
        assert i < len(values), f"fill values exhausted for key: {key}"
        out.append(f'{match.group(1)}{key}: "{values[i]}"')
        used[key] = i + 1
    return "\n".join(out) + "\n"


def _s138w2_init(tmp_path: Path, tag: str) -> tuple[Path, Path]:
    """Fresh `rumpun init` campaign; (proj dir, .rumpun root).

    Asserts the init exit and the _steady-state.yaml emission (the guide
    table's claim), so every pin's fixture proves the scaffold path first.
    """
    proj = tmp_path / tag / "proj"
    proc = _s138w2_run(tmp_path, ["init", str(proj)])
    assert proc.returncode == 0, (
        f"fixture defect: init failed for {tag}\n{proc.stdout}{proc.stderr}"
    )
    root = proj / ".rumpun"
    emitted = root / "seasons" / "_steady-state.yaml"
    assert emitted.is_file(), (
        "rumpun init must emit .rumpun/seasons/_steady-state.yaml; seasons "
        f"holds {sorted(p.name for p in (root / 'seasons').glob('*'))}"
    )
    return proj, root


# --- pin 1: the scaffold emits the template ---------------------------------


def test_s138w2_init_emits_the_steady_state_template(tmp_path: Path) -> None:
    """init emits the steady-state template naming the lanes and fields."""
    _proj, root = _s138w2_init(tmp_path, "emit")
    text = (root / "seasons" / "_steady-state.yaml").read_text(encoding="utf-8")
    for token in (
        "steady", "lint-sweep", "route-probes", "rehearsal",
        "decision-gate", "operator", "expected_band", "rollback",
        "eval_window", "budget.minutes",
    ):
        assert token in text, f"the template text must name {token}"
    logger.info("pin 1 held: init emitted the steady-state template")


# --- pin 2: the wiped-fill shape refuses ------------------------------------


def test_s138w2_wiped_fill_shape_refuses_with_named_errors(tmp_path: Path) -> None:
    """The wiped-fill copy refuses, and the refusal names its errors.

    Positive control: the gate must fire before the clean pass (the
    filled pin) is trusted. The bare shape is the emitted template with
    every FILL-marked value wiped; each empty field comes back as a
    named lint error.
    """
    _proj, root = _s138w2_init(tmp_path, "bare")
    emitted = root / "seasons" / "_steady-state.yaml"
    bare = root / "seasons" / "steady-state-bare.yaml"
    bare.write_text(
        _s138w2_bare(emitted.read_text(encoding="utf-8")), encoding="utf-8",
    )
    proc = _s138w2_run(tmp_path, ["lint", str(bare)])
    assert proc.returncode == 1, (
        f"the wiped-fill shape must refuse; lint exit {proc.returncode}. "
        f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    combined = proc.stdout + proc.stderr
    for fragment in BARE_ERROR_FRAGMENTS:
        assert fragment in combined, (
            f"the bare refusal must name the error: {fragment!r}.\n{combined}"
        )
    logger.info(
        "pin 2 held: the wiped-fill shape refused naming %d error families",
        len(BARE_ERROR_FRAGMENTS),
    )


# --- pin 3: the shipped template and the filled shape lint clean ------------


def test_s138w2_filled_shape_lints_clean(tmp_path: Path) -> None:
    """The emitted template lints clean, and the filled copy lints clean.

    The fill runs every FILL field through real values and cites a sealed
    ledger record appended through the real akar.append_record path, so
    the evidence citation must resolve the way a season's would. The
    as-emitted template ships non-empty marker values and lints clean as
    shipped (the honest-placeholders design, one warning).
    """
    _proj, root = _s138w2_init(tmp_path, "filled")
    body = "the steady state re-proves the standing surfaces for the s138 pins"
    record = akar.append_record(root, "s138-warm", "sealed steady state", body)
    assert record.is_file(), f"fixture defect: no sealed record at {record}"
    cited = (
        "ledger:s138-warm@"
        + hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]
    )
    emitted = root / "seasons" / "_steady-state.yaml"
    filled = root / "seasons" / "s900.yaml"
    filled.write_text(
        _s138w2_filled(emitted.read_text(encoding="utf-8"), cited),
        encoding="utf-8",
    )
    shipped = _s138w2_run(tmp_path, ["lint", str(emitted)])
    assert shipped.returncode == 0, (
        f"the emitted template must lint clean as shipped; exit "
        f"{shipped.returncode}. stderr:\n{shipped.stderr}\n{shipped.stdout}"
    )
    proc = _s138w2_run(tmp_path, ["lint", str(filled)])
    assert proc.returncode == 0, (
        f"the filled steady-state yaml must lint clean; exit {proc.returncode}. "
        f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    logger.info("pin 3 held: shipped template and filled shape linted clean (%s)", cited)


# --- pin 4: the guide names the shape ----------------------------------------


def _s138w2_steady_section(repo: Path) -> str:
    """The guide chunk from '### The steady state' to the next '## '."""
    text = (repo / "docs" / "campaign-guide.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if ln.startswith("### The steady state")),
        None,
    )
    assert start is not None, "the guide lost its steady-state section"
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_s138w2_guide_names_the_steady_state_shape() -> None:
    """The what-lands table carries the row; the steady-state section names it.

    Red until s138 w2: the table named s1/_template/_competition only, and
    the steady-state section described the mode without pointing at the
    emitted shape.
    """
    repo = _s138w2_repo()
    text = (repo / "docs" / "campaign-guide.md").read_text(encoding="utf-8")
    rows = [
        ln for ln in text.splitlines()
        if ln.startswith("|") and "_steady-state.yaml" in ln
    ]
    assert rows, "the what-lands table needs the .rumpun/seasons/_steady-state.yaml row"
    assert any(
        ("light lanes" in row or "decision gate" in row) for row in rows
    ), f"the table row must describe the shape; got {rows}"
    section = _s138w2_steady_section(repo)
    assert "_steady-state.yaml" in section, (
        "the steady-state section must name the emitted shape; section:\n"
        f"{section}"
    )
    logger.info("pin 4 held: the guide names the steady-state shape")
