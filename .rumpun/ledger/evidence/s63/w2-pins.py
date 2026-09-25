"""s63 w2 pins — the ships classifier learns runtime artifacts.

Spec-first pins (red against current code) for the s63 contract (w1 brief
.rumpun/runs/s63/w1/prompt.md; ledger anchor 2026-09-16_check-s61 — the
s61 close was marked DELTA on the clause "the engine's finalize writes
results.jsonl from the final snaps", because every file-shaped token was
judged a committed-tree claim — plus s62-harvest and check-s62). Spec
anchors, the measured red set, and surface assumptions:
.rumpun/runs/s63/w2/notes.md.

Contract these pins hold — every pin builds a throwaway close (a fresh
git repo: src, one green pin, a DESIGN.md ships row, the run artifact
in the campaign runs state .rumpun/runs/<sid>/ — worktree-only, never
committed (the repo gitignores .rumpun/runs) — commits it, and runs
the real tools/artifact_check.py over the close commit as a bounded
subprocess:

1. The classification: a ships clause whose file-shaped token is framed
   as run-time output ("writes results.jsonl") checks through when the
   artifact sits in runs/<sid>/ — MATCH, exit 0 — and the clause
   evidence records the classification.
2. The no-bailout guard: a clause claiming a committed file the tree
   genuinely lacks still yields DELTA exit 1 after the distinction
   lands; the runtime reading may never relax a committed claim.
3. The evidence names each file-shaped token's classification:
   runtime-checked (against runs/<sid>/) vs committed-tree claim.

Red history (measured; the full runs in notes.md): against the
season-start checker (git HEAD, pre-s63) pins 1 and 3 fail with DELTA
on the runtime clause (missing file: results.jsonl, the check-s61
false positive) and pin 2 passes; against the landed s63 classifier
all three pass.

Grafting: drop this file into tests/ as the season's pins file. Helpers
carry the _s63w2_ prefix, so nothing collides with existing defs. No pin
touches the real repo, ledger, or any live season: every fixture is a
fresh git repo under pytest tmp_path and the check record goes to a tmp
--out-dir. Each run is bounded by S63W2_TIMEOUT (240s, the task bound)
on the checker subprocess; the checker itself bounds git, the import
probe, and the pins run.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

S63W2_TIMEOUT = 240  # bounds one checker subprocess (the task bound)
S63W2_SID_RUNTIME = "s631"  # the runtime-framed clause fixture
S63W2_SID_GHOST = "s632"  # the ghost committed-file fixture
S63W2_SID_BOTH = "s633"  # the both-classifications fixture

S63W2_RESULTS_ROW = '{"unit": "u1", "verdict": "PASS"}\n'

S63W2_PIN_FILE = """\
def test_{sid}_fixture_close_is_green() -> None:
    '''The season's one merged pin: green by construction.'''
    assert True
"""


# --- helpers -----------------------------------------------------------------------


def _s63w2_root() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root. Post-graft inside an
    extraction, the walk-up lands in the extraction, so the pins exercise
    that extraction's checker.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s63w2_git(proj: Path, *argv: str) -> str:
    """One bounded git command inside the fixture repo; stdout on success."""
    ran = subprocess.run(
        ["git", "-C", str(proj), *argv],
        capture_output=True, text=True, timeout=S63W2_TIMEOUT, check=False,
    )
    assert ran.returncode == 0, f"git {' '.join(argv)} failed: {ran.stderr}"
    return ran.stdout


def _s63w2_fixture(
    tmp_path: Path, sid: str, ships_cell: str, extra_files: dict[str, str],
    runtime_files: dict[str, str] | None = None,
) -> tuple[Path, str]:
    """One throwaway close: a committed git repo holding src, one green
    pin, a DESIGN.md ships row, and extra_files (committed files:
    repo-relative path -> body). runtime_files are written into the
    worktree but excluded from the close commit: the campaign runs
    state is untracked, so a runtime artifact at .rumpun/runs/<sid>/
    exists only in the live tree the checker's runs-state read binds
    to. Returns (repo root, close commit sha)."""
    proj = tmp_path / sid / "proj"
    files: dict[str, str] = {
        "src/rumpun/__init__.py": '"""fixture package."""\n',
        f"tests/test_{sid}_w2_pins.py": S63W2_PIN_FILE.format(sid=sid),
        "DESIGN.md": (
            "# DESIGN\n\n"
            "| sid | outcome | ships |\n"
            "|---|---|---|\n"
            f"| {sid} | WIN | {ships_cell} |\n"
        ),
    }
    files.update(extra_files)
    for rel, body in files.items():
        path = proj / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    for rel, body in (runtime_files or {}).items():
        (proj / rel).parent.mkdir(parents=True, exist_ok=True)
        (proj / rel).write_text(body, encoding="utf-8")
    _s63w2_git(proj, "init", "-q")
    _s63w2_git(
        proj, "add", "DESIGN.md", "src", "tests", *(extra_files or {}),
    )
    _s63w2_git(
        proj, "-c", "user.name=pin", "-c", "user.email=pin@fixture.test",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", f"{sid} close",
    )
    return proj, _s63w2_git(proj, "rev-parse", "HEAD").strip()


def _s63w2_check(
    proj: Path, sid: str, commit: str, out_dir: Path,
) -> subprocess.CompletedProcess[str]:
    """One bounded artifact_check subprocess over the fixture close."""
    out_dir.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            sys.executable, str(_s63w2_root() / "tools" / "artifact_check.py"),
            sid, commit, "--repo", str(proj), "--out-dir", str(out_dir),
        ],
        capture_output=True, text=True, timeout=S63W2_TIMEOUT, check=False,
    )


def _s63w2_record(out_dir: Path, sid: str) -> str:
    """The written check record (exactly one <date>_check-<sid>.md)."""
    matches = sorted(out_dir.glob(f"*check-{sid}.md"))
    assert len(matches) == 1, (
        f"expected exactly one check-{sid} record in {out_dir}, got {matches}"
    )
    return matches[0].read_text(encoding="utf-8")


def _s63w2_clause_rows(record: str) -> list[tuple[str, str, str]]:
    """The ships-diff rows as (clause text, verdict, evidence) triples."""
    lines = record.splitlines()
    start = next(
        i for i, ln in enumerate(lines) if ln.startswith("| named ship |")
    )
    rows: list[tuple[str, str, str]] = []
    for ln in lines[start + 2:]:
        if not ln.startswith("| "):
            break
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) != 3:
            break
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def _s63w2_one_row(
    rows: list[tuple[str, str, str]], token: str,
) -> tuple[str, str, str]:
    """The one ships-diff row naming token; fails loudly otherwise."""
    hits = [row for row in rows if token in row[0]]
    assert len(hits) == 1, (
        f"expected exactly one clause row naming {token}, got {hits}"
    )
    return hits[0]


# --- pin 1: the runtime-framed clause checks through -------------------------------


def test_s63w2_runtime_framed_clause_matches_with_artifact_in_runs(tmp_path: Path) -> None:
    """A run-time framed file token checks against runs/<sid>/, not the tree.

    The fixture close's ships row claims "the engine's finalize writes
    results.jsonl" — run-time framing — and
    .rumpun/runs/s631/results.jsonl sits in the campaign runs state
    (worktree-only, untracked). The clause must yield MATCH and the check must
    exit 0 VERIFIED, with the clause evidence recording the
    classification. On main today every file-shaped token is a
    committed-tree claim, so the clause DELTAs with "missing file:
    results.jsonl" (the check-s61 false positive) and the pin stays red
    until w1's change lands.
    """
    proj, commit = _s63w2_fixture(
        tmp_path, S63W2_SID_RUNTIME,
        "the engine's finalize writes results.jsonl from the final snaps, 1 pins",
        {},
        {f".rumpun/runs/{S63W2_SID_RUNTIME}/results.jsonl": S63W2_RESULTS_ROW},
    )
    out_dir = tmp_path / S63W2_SID_RUNTIME / "out"
    ran = _s63w2_check(proj, S63W2_SID_RUNTIME, commit, out_dir)
    record = _s63w2_record(out_dir, S63W2_SID_RUNTIME)
    _text, verdict, evidence = _s63w2_one_row(
        _s63w2_clause_rows(record), "results.jsonl",
    )
    assert verdict == "MATCH", (
        f"the runtime-framed clause DELTAs with the artifact in runs/"
        f"{S63W2_SID_RUNTIME}/ (the check-s61 false positive): {verdict};"
        f" {evidence}"
    )
    assert "runtime" in evidence.lower(), (
        f"the clause evidence does not record the runtime classification:"
        f" {evidence}"
    )
    assert ran.returncode == 0, (
        f"artifact_check exited {ran.returncode}, want 0 VERIFIED;"
        f" stderr:\n{ran.stderr}\nrecord:\n{record}"
    )
    logger.info("pin 1 held: runtime-framed clause MATCH with the classification recorded")


# --- pin 2: the ghost committed file still DELTAs ----------------------------------


def test_s63w2_ghost_committed_file_still_deltas(tmp_path: Path) -> None:
    """A committed-file claim the tree lacks keeps biting: DELTA, exit 1.

    The fixture row claims "adds src/rumpun/ghost.py" — plain committed
    framing — and no such file exists anywhere in the close. The clause
    must yield DELTA, the missing file must be named in the record, and
    the check must exit 1. This is the no-bailout guard: the runtime
    distinction may only cover run-time framing, never relax a
    committed-tree claim. Green on main today by construction; it must
    stay green at merge.
    """
    proj, commit = _s63w2_fixture(
        tmp_path, S63W2_SID_GHOST,
        "the season adds src/rumpun/ghost.py for the new finalize, 1 pins",
        {},
    )
    out_dir = tmp_path / S63W2_SID_GHOST / "out"
    ran = _s63w2_check(proj, S63W2_SID_GHOST, commit, out_dir)
    record = _s63w2_record(out_dir, S63W2_SID_GHOST)
    _text, verdict, evidence = _s63w2_one_row(
        _s63w2_clause_rows(record), "ghost.py",
    )
    assert verdict == "DELTA", (
        f"a genuinely missing committed file must stay DELTA:"
        f" {verdict}; {evidence}"
    )
    assert ran.returncode == 1, (
        f"artifact_check exited {ran.returncode}, want 1 DELTA;"
        f" stderr:\n{ran.stderr}\nrecord:\n{record}"
    )
    assert "ghost.py" in record, f"the record does not name the missing file:\n{record}"
    logger.info("pin 2 held: ghost committed file DELTA exit 1, file named")


# --- pin 3: the evidence names the classification per token ------------------------


def test_s63w2_evidence_names_classification_per_token(tmp_path: Path) -> None:
    """Each file-shaped token's evidence says runtime-checked or committed.

    One close, two claims in one ships row: "the finalize writes
    results.jsonl into the run dir" (run-time framing; the artifact
    sits in the campaign runs state at
    .rumpun/runs/s633/results.jsonl, worktree-only) and "the season adds
    src/rumpun/finalize.py" (committed framing; the module is committed
    in the tree). Both clauses must MATCH, and each evidence cell must
    name its token and its classification kind: the runtime artifact
    checked against runs/<sid>/, the module as a committed-tree claim. On
    main today the runtime clause DELTAs and no evidence cell names any
    classification, so the pin stays red until w1's change lands.
    """
    proj, commit = _s63w2_fixture(
        tmp_path, S63W2_SID_BOTH,
        "the finalize writes results.jsonl into the run dir,"
        " the season adds src/rumpun/finalize.py, 1 pins",
        {"src/rumpun/finalize.py": '"""the finalize module."""\n'},
        {f".rumpun/runs/{S63W2_SID_BOTH}/results.jsonl": S63W2_RESULTS_ROW},
    )
    out_dir = tmp_path / S63W2_SID_BOTH / "out"
    ran = _s63w2_check(proj, S63W2_SID_BOTH, commit, out_dir)
    record = _s63w2_record(out_dir, S63W2_SID_BOTH)
    rows = _s63w2_clause_rows(record)
    _rt, rt_verdict, rt_evidence = _s63w2_one_row(rows, "results.jsonl")
    _ct, ct_verdict, ct_evidence = _s63w2_one_row(rows, "finalize.py")
    assert rt_verdict == "MATCH" and ct_verdict == "MATCH", (
        f"both claims check through: runtime clause {rt_verdict},"
        f" committed clause {ct_verdict}; {rt_evidence}; {ct_evidence}"
    )
    assert "results.jsonl" in rt_evidence and "runtime" in rt_evidence.lower(), (
        f"the runtime token's evidence does not name the runtime check:"
        f" {rt_evidence}"
    )
    assert "finalize.py" in ct_evidence and "committed" in ct_evidence.lower(), (
        f"the committed token's evidence does not name the committed claim:"
        f" {ct_evidence}"
    )
    assert ran.returncode == 0, (
        f"artifact_check exited {ran.returncode}, want 0 VERIFIED;"
        f" stderr:\n{ran.stderr}\nrecord:\n{record}"
    )
    logger.info("pin 3 held: evidence names runtime vs committed per token")
