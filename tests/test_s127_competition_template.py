"""s127 w1 pins - the competition season stays one command away.

Ground truth measured 2026-09-20 (probe campaign /tmp/s127probe, full
account in .rumpun/runs/s127/w1/notes.md):

- `rumpun init` emits `.rumpun/seasons/_competition.yaml` (the scaffold's
  COMPETITION_TEMPLATE, landed s67 w1). The repo campaign predates that
  emission: the file the guide's table names was absent from
  .rumpun/seasons/ until s127 w1 added it (cp of the init emission,
  byte-identical to scaffold.COMPETITION_TEMPLATE).
- The gate: `rumpun lint .rumpun/seasons/<yaml>`. Measured both sides:
  the template AS EMITTED lints clean with one warning (s67's deliberate
  "honest placeholders" design, pinned by test_s67_w2_pins pin 3); the
  bare FILL-marker shape that REFUSES is the template with every
  FILL-marked value wiped (empty goal/metric are lint blocks, the s28
  quickstart behavior). The s127 brief called the bare emitted template
  the refusal side; the gate does not behave that way and scaffold.py is
  outside this season's edit bounds, so the pins hold both measured
  sides of the gate and notes.md carries the gap.

Contract these pins hold:
1. init emits the template and its fill-in comments name the real
   fields (id, parent, goal, metric, approach, evidence, expected_band,
   rollback, prompt, name, budget).
2. The bare wiped-fill shape refuses with named errors (positive
   control: the gate fires before the clean pass is trusted).
3. A filled copy (every FILL field resolved, evidence citing a sealed
   ledger record through the real akar.append_record path) lints clean,
   and the emitted template stays clean as shipped.
4. The repo campaign carries the template at the guide's path,
   byte-identical to the scaffold constant.
5. The guide's competition section names the actual fill fields.

Red history (measured 2026-09-20): pins 4 and 5 were red for the spec
reasons (template absent from the repo campaign; guide section 1 lacked
the fill fields) before the template cp and the guide paragraph landed.
Pin 2 was red as written on a wrong prediction: the gate checks
approach key presence, not emptiness, so a wiped approach emits no
error; its fragments are the measured 7-error refusal. Pins 1 and 3
were green as written (gate behavior predates s127: s67 landed the
emission and the lint checks). Solo logs: /tmp/s127w1-*.log.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from rumpun import akar, scaffold

logger = logging.getLogger(__name__)

S127W1_TIMEOUT = 240

# The template's fill-in keys (the header comment's own list, minus
# budget/route which are not FILL-marked lines).
FILL_KEYS = (
    "id", "parent", "goal", "metric", "approach",
    "evidence", "expected_band", "rollback", "prompt", "name",
)

# The filled copy's values (the fill-in fields resolved for a fixture
# competition season s900 off parent s1).
S127W1_FILLS = {
    "id": "s900",
    "parent": "s1",
    "goal": "drive the competition above the sealed baseline on its official metric",
    "metric": "submission_scores",
    "approach": "seal the baseline, pre-register the score gate, submit, improve",
    "expected_band": "WIN if best submission >= baseline + 0.01; LOSS otherwise",
    "rollback": "git revert to tag s1 and re-run the s1 config",
    "prompt": "prompts/base/execute.md",
    "name": "kancil-a",
}

# The named errors the bare wiped-fill shape must carry (the lint
# messages as shipped 2026-09-20).
BARE_ERROR_FRAGMENTS = (
    "does not match s<N>",
    "goal is empty",
    "metric is empty",
    "expected_band is required",
    "rollback is required",
    "missing prompt",
    "writer name must be a non-empty string",
)


def _s127w1_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s127w1_env() -> dict[str, str]:
    """Subprocess env: repo src/ prepended to PYTHONPATH."""
    env = dict(os.environ)
    src = str(_s127w1_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s127w1_run(
    cwd: Path, argv: list[str], env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """One `python -m rumpun <argv>` subprocess, bounded."""
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv],
        cwd=str(cwd),
        env=env if env is not None else _s127w1_env(),
        capture_output=True,
        text=True,
        timeout=S127W1_TIMEOUT,
        check=False,
    )


def _s127w1_mark_fill_lines(text: str) -> list[tuple[str, re.Match[str] | None]]:
    out: list[tuple[str, re.Match[str] | None]] = []
    for line in text.splitlines():
        is_fill = "FILL" in line and not line.lstrip().startswith("#")
        match = (
            re.match(r"^(\s*(?:-\s+)?)([\w-]+):(.*)$", line) if is_fill else None
        )
        assert not is_fill or match is not None, f"unmarkable FILL line: {line!r}"
        out.append((line, match))
    return out


def _s127w1_bare(text: str) -> str:
    """The bare shape: every FILL-marked value wiped to an empty string.

    Comment lines pass through; a key line carrying FILL keeps its key
    and loses its value (`id: s68  # FILL: ...` -> `id: ""`). This is
    the unfilled copy an operator gets by stripping the fill-in values;
    the emitted template itself ships non-empty marker values and lints
    clean as shipped (pinned in the filled pin).
    """
    out: list[str] = []
    for line, match in _s127w1_mark_fill_lines(text):
        if match is None:
            out.append(line)
        else:
            out.append(f'{match.group(1)}{match.group(2)}: ""')
    return "\n".join(out) + "\n"


def _s127w1_filled(text: str, cited: str) -> str:
    """Every FILL field resolved; evidence cites the sealed baseline record."""
    out: list[str] = []
    for line, match in _s127w1_mark_fill_lines(text):
        if match is None:
            out.append(line)
        elif match.group(2) == "evidence":
            out.append(f'{match.group(1)}evidence: ["{cited}"]')
        else:
            key = match.group(2)
            out.append(f'{match.group(1)}{key}: "{S127W1_FILLS[key]}"')
    return "\n".join(out) + "\n"


# --- pin 1: the scaffold emits the template ---------------------------------


def _s127w1_init(tmp_path: Path, tag: str) -> tuple[Path, Path]:
    """Fresh `rumpun init` campaign; (proj dir, .rumpun root).

    Asserts the init exit and the template emission (the guide table's
    claim), so every pin's fixture proves the scaffold path first.
    """
    proj = tmp_path / tag / "proj"
    proc = _s127w1_run(tmp_path, ["init", str(proj)])
    assert proc.returncode == 0, (
        f"fixture defect: init failed for {tag}\n{proc.stdout}{proc.stderr}"
    )
    root = proj / ".rumpun"
    emitted = root / "seasons" / "_competition.yaml"
    assert emitted.is_file(), (
        "rumpun init must emit .rumpun/seasons/_competition.yaml; seasons "
        f"holds {sorted(p.name for p in (root / 'seasons').glob('*'))}"
    )
    return proj, root


def test_s127w1_init_emits_the_template(tmp_path: Path) -> None:
    """init emits the competition template naming the real fill fields."""
    _proj, root = _s127w1_init(tmp_path, "emit")
    text = (root / "seasons" / "_competition.yaml").read_text(encoding="utf-8")
    assert "competition" in text.lower()
    for field in (*FILL_KEYS, "budget", "route"):
        assert field in text, f"the template's fill-in text must name {field}"
    logger.info("pin 1 held: init emitted the competition template")


# --- pin 2: the bare wiped-fill shape refuses -------------------------------


def test_s127w1_bare_fill_shape_refuses_with_named_errors(tmp_path: Path) -> None:
    """The bare wiped-fill copy refuses, and the refusal names its errors.

    Positive control: the gate must fire before the clean pass (the
    filled pin) is trusted. The bare shape is the emitted template with
    every FILL-marked value wiped; each empty field comes back as a
    named lint error.
    """
    _proj, root = _s127w1_init(tmp_path, "bare")
    emitted = root / "seasons" / "_competition.yaml"
    bare = root / "seasons" / "competition-bare.yaml"
    bare.write_text(
        _s127w1_bare(emitted.read_text(encoding="utf-8")), encoding="utf-8",
    )
    proc = _s127w1_run(tmp_path, ["lint", str(bare)])
    assert proc.returncode == 1, (
        f"the bare wiped-fill shape must refuse; lint exit {proc.returncode}. "
        f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    combined = proc.stdout + proc.stderr
    for fragment in BARE_ERROR_FRAGMENTS:
        assert fragment in combined, (
            f"the bare refusal must name the error: {fragment!r}.\n{combined}"
        )
    logger.info(
        "pin 2 held: the bare wiped-fill shape refused naming %d error families",
        len(BARE_ERROR_FRAGMENTS),
    )


# --- pin 3: the filled shape lints clean ------------------------------------


def test_s127w1_filled_competition_yaml_lints_clean(tmp_path: Path) -> None:
    """A filled copy lints clean, and the emitted template stays clean.

    The fill runs every FILL field through real values and cites a sealed
    ledger record appended through the real akar.append_record path, so
    the evidence citation must resolve the way a season's would. The
    as-emitted template is also linted: it ships non-empty marker values
    and lints clean as shipped (the s67 design; the brief's refusal side
    is the wiped-fill shape, pinned in pin 2).
    """
    _proj, root = _s127w1_init(tmp_path, "filled")
    body = "baseline submission sealed for the s127 competition pins"
    record = akar.append_record(root, "s127-baseline", "sealed baseline", body)
    assert record.is_file(), f"fixture defect: no sealed record at {record}"
    cited = (
        "ledger:s127-baseline@"
        + hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]
    )
    emitted = root / "seasons" / "_competition.yaml"
    filled = root / "seasons" / "s900.yaml"
    filled.write_text(
        _s127w1_filled(emitted.read_text(encoding="utf-8"), cited),
        encoding="utf-8",
    )
    shipped = _s127w1_run(tmp_path, ["lint", str(emitted)])
    assert shipped.returncode == 0, (
        f"the emitted template must lint clean as shipped; exit "
        f"{shipped.returncode}. stderr:\n{shipped.stderr}\n{shipped.stdout}"
    )
    proc = _s127w1_run(tmp_path, ["lint", str(filled)])
    assert proc.returncode == 0, (
        f"the filled competition yaml must lint clean; exit {proc.returncode}. "
        f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    logger.info("pin 3 held: the filled competition yaml linted clean (%s)", cited)


# --- pin 4: the repo campaign carries the template --------------------------


def test_s127w1_repo_campaign_carries_the_template() -> None:
    """The repo campaign holds the template at the guide table's path.

    Red until s127 w1: the campaign predates the scaffold's emission, so
    the file the guide names was absent from .rumpun/seasons/. The file
    is the cp of the init emission, so it must equal the scaffold
    constant byte for byte.
    """
    template = _s127w1_repo() / ".rumpun" / "seasons" / "_competition.yaml"
    assert template.is_file(), (
        "the repo campaign must carry .rumpun/seasons/_competition.yaml, "
        "the path docs/campaign-guide.md's table names; the campaign predates "
        "the scaffold's emission (s67 w1), so the file is the cp of the init "
        "emission"
    )
    assert template.read_text(encoding="utf-8") == scaffold.COMPETITION_TEMPLATE


# --- pin 5: the guide's competition section names the fields ----------------


def _s127w1_guide_section(repo: Path) -> str:
    """The guide chunk from the _competition.yaml row to the next '## '."""
    text = (repo / "docs" / "campaign-guide.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    row = next(i for i, ln in enumerate(lines) if "_competition.yaml" in ln)
    end = next(
        (i for i in range(row + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[row:end])


def test_s127w1_guide_names_the_competition_fill_fields() -> None:
    """The guide's competition section names the template's actual fields.

    Red until s127 w1: the section carried the path only; the fill
    fields (id, parent, goal, metric, approach, evidence, expected_band,
    rollback, prompt, name, route, budget.minutes) lived in the template
    header comment alone.
    """
    section = _s127w1_guide_section(_s127w1_repo())
    tokens = ("_competition.yaml", "expected_band", "rollback", "budget.minutes")
    missing = [token for token in tokens if token not in section]
    assert missing == [], (
        "the guide's competition section must name the template's fill "
        f"fields; missing {missing}. section:\n{section}"
    )
    logger.info("pin 5 held: the guide's competition section names the fields")
