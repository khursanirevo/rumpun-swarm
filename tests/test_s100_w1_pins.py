"""s100 w1 pins - the design-entry ships-row surface gate.

Spec sources: RESUME's corrections line (the 8-fire record, check-s67
through check-s94), the s99 w2 front table naming the class, and the
s55 checker (tools/artifact_check.py) itself - the gate reuses the
checker's own clause classifier (split_clauses + analyze_clause) at
design-writing time, so a row naming a surface the tree does not carry
errors one whole commit before check time.

Offline: fixture DESIGN.md files over throwaway trees (the real
checker copied in as the classifier) plus root-override runs against
the repo tree for the correction-record rows and the current rows. No
pin mutates the repo, the ledger, or the runs state; no network; no
route calls. The real-repo pins assert season-proof contracts (the bad
correction rows fail naming their token; every current DESIGN row
lints clean), never live values.
"""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

from rumpun import cli as cli_mod
from rumpun import lint as lint_mod

logger = logging.getLogger(__name__)


def _s100w1_repo() -> Path:
    """The repo root: the first ancestor of this file holding
    pyproject.toml (identical in the lane, in tests/, and in the
    checker's archive extract)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


REPO = _s100w1_repo()



def _s100w1_tree(tmp_path: Path, tag: str) -> Path:
    """One throwaway tree: src modules, the real checker copied in as
    the classifier, an empty tests/ dir."""
    root = tmp_path / tag / "tree"
    (root / "src" / "rumpun").mkdir(parents=True)
    (root / "tools").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (root / "src" / "rumpun" / "engine.py").write_text(
        'NAME = "engine"\n', encoding="utf-8"
    )
    (root / "src" / "rumpun" / "cli.py").write_text(
        'NAME = "cli"\n', encoding="utf-8"
    )
    shutil.copy2(
        REPO / "tools" / "artifact_check.py",
        root / "tools" / "artifact_check.py",
    )
    return root


def _s100w1_design(root: Path, rows: list[str]) -> Path:
    """A DESIGN.md carrying exactly the given rows."""
    path = root / "DESIGN.md"
    body = "| season | outcome | ships |\n|---|---|---|\n"
    body += "".join(f"{row}\n" for row in rows)
    path.write_text(body, encoding="utf-8")
    return path


def _s100w1_row(sid: str, ships: str) -> str:
    return f"| {sid} | WIN (band clauses met) | {ships} |"


def _s100w1_errors(findings: list) -> dict[str, list[str]]:
    """Error messages grouped by the row sid named in the message."""
    out: dict[str, list[str]] = {}
    for finding in findings:
        if finding.severity != "error":
            continue
        if finding.message.startswith("ships row "):
            sid = finding.message.split(" ")[2]
        out.setdefault(sid, []).append(finding.message)
    return out


def test_s100w1_bad_file_token_shapes_fail_naming_the_token(tmp_path: Path) -> None:
    """The 8-fire file-token shapes die at design time: each bad row
    errors naming its exact token; the corrected rows naming real
    committed surfaces lint clean in the same tree."""
    root = _s100w1_tree(tmp_path, "shapes")
    skills = root / ".rumpun" / "plugins" / "kancil-base-draft" / "priors" / "skills"
    skills.mkdir(parents=True)
    (skills / "kancil-2.2-skills.md").write_text("skills\n", encoding="utf-8")
    (root / ".rumpun").mkdir(exist_ok=True)
    (root / ".rumpun" / "epics.yaml").write_text("epics: {}\n", encoding="utf-8")
    design = _s100w1_design(
        root,
        [
            # the s77 fire shape: a kancil-side basename
            _s100w1_row(
                "s201", "the sweep named loop.py (1224L, the stop sentinel) "
                "as the sentinel"
            ),
            # the s94 fire shape: a pack-relative short path
            _s100w1_row(
                "s202", "the stopping rule distilled into the pack "
                "(priors/templates/stopping-rule.md, the threshold checkable)"
            ),
            # the s89 fire shape: a bare basename (real file sits at
            # .rumpun/epics.yaml in this tree)
            _s100w1_row(
                "s203", "the board-arc epic extended "
                "(epics.yaml 4 insertions + 1 deletion, lint OK)"
            ),
            # the short module path (real file is src/rumpun/engine.py)
            _s100w1_row("s204", "the engine ships src/engine.py (the clocks)"),
            # the corrected shapes bind
            _s100w1_row(
                "s205", "the skills prompt at .rumpun/plugins/kancil-base-draft"
                "/priors/skills/kancil-2.2-skills.md re-sealed"
            ),
            _s100w1_row("s206", "the engine landed src/rumpun/engine.py"),
        ],
    )
    findings = lint_mod.lint_design(design)
    by_sid = _s100w1_errors(findings)
    assert any("loop.py" in msg for msg in by_sid.get("s201", [])), by_sid
    assert any(
        "priors/templates/stopping-rule.md" in msg for msg in by_sid.get("s202", [])
    ), by_sid
    assert any("epics.yaml" in msg for msg in by_sid.get("s203", [])), by_sid
    assert any("src/engine.py" in msg for msg in by_sid.get("s204", [])), by_sid
    assert by_sid.get("s205", []) == [], by_sid
    assert by_sid.get("s206", []) == [], by_sid


def test_s100w1_prose_colon_trap_fails_and_the_reword_passes(tmp_path: Path) -> None:
    """The s92 fire shape: a prose colon after a noun reads as a key token
    the tree never satisfies. It errors naming the token; the s92-3 reword
    naming the real pack template binds clean."""
    root = _s100w1_tree(tmp_path, "colon")
    templates = (
        root / ".rumpun" / "plugins" / "kancil-base-draft" / "priors" / "templates"
    )
    templates.mkdir(parents=True)
    (templates / "baseline-comparison.md").write_text(
        "contract\n", encoding="utf-8"
    )
    bad_row = _s100w1_row(
        "s212", "the baseline-comparison contract distilled into the pack "
        "(three paired metrics: time-to-fix, defect escape rate, repair "
        "recurrence) with the first honest slice measured"
    )
    good_row = _s100w1_row(
        "s213", "the baseline-comparison contract distilled into the pack at "
        ".rumpun/plugins/kancil-base-draft/priors/templates/"
        "baseline-comparison.md (time-to-fix, defect escape rate, repair "
        "recurrence) with the first honest slice measured"
    )
    findings = lint_mod.lint_design(_s100w1_design(root, [bad_row, good_row]))
    by_sid = _s100w1_errors(findings)
    assert any("metrics" in msg for msg in by_sid.get("s212", [])), by_sid
    assert by_sid.get("s213", []) == [], by_sid


def test_s100w1_removal_marker_mirrors_the_check_contract(tmp_path: Path) -> None:
    """A surface-absent clause with a removal marker stays MATCH-by-prose
    (the checker judges removal claims by the pins); the same clause
    without the marker errors naming the token."""
    root = _s100w1_tree(tmp_path, "removal")
    design = _s100w1_design(
        root,
        [
            _s100w1_row(
                "s221", "the legacy benih: writer table retired "
                "(the writers form supersedes it)"
            ),
            _s100w1_row(
                "s222", "the legacy benih: writer table "
                "(the writers form supersedes it)"
            ),
        ],
    )
    findings = lint_mod.lint_design(design)
    by_sid = _s100w1_errors(findings)
    assert by_sid.get("s221", []) == [], by_sid
    assert any("benih:" in msg for msg in by_sid.get("s222", [])), by_sid


def test_s100w1_runtime_framing_binds_the_runs_state(tmp_path: Path) -> None:
    """A runtime-framed token binds the tree's live runs state: present
    artifact clean; absent artifact errors naming the token; no runs
    state binds committed and errors the same way."""
    token_row = _s100w1_row(
        "s231", "the finalize writes runs/s231/verdicts.jsonl (sorted, atomic)"
    )
    good_root = _s100w1_tree(tmp_path, "runtime-good")
    runs = good_root / ".rumpun" / "runs" / "s231"
    runs.mkdir(parents=True)
    (runs / "verdicts.jsonl").write_text("[]\n", encoding="utf-8")
    assert lint_mod.lint_design(_s100w1_design(good_root, [token_row])) == []

    bad_root = _s100w1_tree(tmp_path, "runtime-bad")
    (bad_root / ".rumpun" / "runs" / "s231").mkdir(parents=True)
    findings = lint_mod.lint_design(_s100w1_design(bad_root, [token_row]))
    by_sid = _s100w1_errors(findings)
    assert any(
        "runs/s231/verdicts.jsonl" in msg for msg in by_sid.get("s231", [])
    ), by_sid

    none_root = _s100w1_tree(tmp_path, "runtime-none")
    findings = lint_mod.lint_design(_s100w1_design(none_root, [token_row]))
    by_sid = _s100w1_errors(findings)
    assert any(
        "runs/s231/verdicts.jsonl" in msg for msg in by_sid.get("s231", [])
    ), by_sid


def test_s100w1_metric_and_external_tokens_pass(tmp_path: Path) -> None:
    """Pure-numeric slash tokens are metrics, single-slash dot-free tokens
    are external references; neither is a tree surface, so neither can
    miss one."""
    root = _s100w1_tree(tmp_path, "tokens")
    design = _s100w1_design(
        root,
        [
            _s100w1_row(
                "s241", "reconciles 243/243 with the khursani8/rumpun board "
                "contract; suite 12/12"
            )
        ],
    )
    assert lint_mod.lint_design(design) == []


def test_s100w1_correction_record_rows_fail_naming_the_token(tmp_path: Path) -> None:
    """Step-3 verification against the real ledger: the verbatim bad rows
    of the five recorded fires (check-s77, check-s80, check-s89, check-s92,
    check-s94) fail the lint against today's tree, each naming its exact
    token. The records are committed, so this holds in the extract too."""
    ledger = REPO / ".rumpun" / "ledger"
    rows = []
    for sid in ("s77", "s80", "s89", "s92", "s94"):
        matches = sorted(ledger.glob(f"*check-{sid}.md"))
        assert len(matches) == 1, (sid, matches)
        text = matches[0].read_text(encoding="utf-8")
        prefix = "ships row (verbatim): "
        line = next(
            rec_line for rec_line in text.splitlines() if rec_line.startswith(prefix)
        )
        rows.append(_s100w1_row(sid, line[len(prefix):]))
    fire_root = tmp_path / "fires"
    fire_root.mkdir(parents=True)
    findings = lint_mod.lint_design(
        _s100w1_design(fire_root, rows), root=REPO
    )
    by_sid = _s100w1_errors(findings)
    expected = {
        "s77": "loop.py",
        "s80": "priors/templates/repro-backed-closure.md",
        "s89": "epics.yaml",
        "s94": "priors/templates/stopping-rule.md",
    }
    for sid, token in expected.items():
        assert any(
            token in msg for msg in by_sid.get(sid, [])
        ), (sid, token, by_sid)
    # s92 exception: the fire row binds against the tree of today because
    # the metrics: literal exists in src (the design-entry gate comment
    # carries it), so the key-token search resolves. This assert tracks
    # that reason; if the literal moves, the s92 row errors again and
    # belongs back in the expected dict above.
    src_with_token = [
        path
        for path in sorted((REPO / "src").rglob("*.py"))
        if "metrics:" in path.read_text(encoding="utf-8", errors="replace")
    ]
    assert src_with_token, "the s92 metrics: reason vanished; re-add s92"


def test_s100w1_current_design_rows_lint_clean() -> None:
    """The gate's standing contract over the live DESIGN.md: every row
    names real surfaces (the four pre-checker-era rows and s67 were
    reworded to real surfaces at s100 w1; the five fire rows were
    reworded by their corrections). Runs identically in the extract: the
    assert binds committed state only."""
    findings = lint_mod.lint_design(REPO / "DESIGN.md")
    errors = [f.message for f in findings if f.severity == "error"]
    assert errors == [], errors
    logger.info("design lint: all current DESIGN rows clean")


def test_s100w1_lint_verb_and_close_gate_wire_the_lint(tmp_path: Path) -> None:
    """The invocation paths: `rumpun lint DESIGN.md` exits 1 on a bad row
    and 0 on a good one; the close gate's input (design_blockers) is
    empty for a good row and names the token for a bad one."""
    root = _s100w1_tree(tmp_path, "cli")
    bad = _s100w1_design(
        root,
        [
            _s100w1_row(
                "s201", "the sweep named loop.py (1224L) as the sentinel"
            )
        ],
    )
    assert cli_mod.cmd_lint(argparse.Namespace(file=str(bad))) == 1
    assert lint_mod.design_blockers(bad, "s201"), "blockers must name the token"
    good = _s100w1_design(
        root, [_s100w1_row("s206", "the engine landed src/rumpun/engine.py")]
    )
    assert cli_mod.cmd_lint(argparse.Namespace(file=str(good))) == 0
    assert lint_mod.design_blockers(good, "s206") == []
