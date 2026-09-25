"""s113 w1 pins — the audit --last listing names the second opinion.

Spec-first pins (red against current code) for the s113 w1 contract
(seasons/s113.yaml, lane audit-panel-col): the audit --last output gains
the panel column — one row per window season naming its judge verdict
(the epics resolution, epics.season_verdict: the LAST verdicts.jsonl row
naming the season; WIN and LOSS verbatim, any other harvested word
renders as `other`, a season with no verdict row names no judge
verdict), its latest panel verdict (epics._latest_verdict_id: the
highest generation holding a panel-<sid>[-<gen>]-verdict record wins;
pending requests and error records never hide it) rendered as
'<record-id>@<sha8> (<verdict word>)', the bare record id when the
record lacks its seal trailer; and the s112 dissent flag
(epics._dissent_mark, 'dissent:<word>') when both sides exist and
differ. Seasons without panel records stay bare; no invented verdicts.
The audit record body stays byte-identical (its shape is pinned
byte-exact in test_rumpun.py goldens); the rows are the verb's output,
printed by cmd_audit before the candidate lines.

Fixture: the s108 pattern — the campaign's real season yamls and real
panel records copied from the ledger, verdict rows embedded compact
verbatim as measured 2026-09-20 (s12 keeps its two real unit rows, so
the season-row rule reads real mixed content), run state never copied
from .rumpun/runs/. No hand-sealed records needed: the real families
cover every boundary (s69's pending -> gen-2 error -> gen-3 verdict
ladder, the s79/s83/s84 rerun generations, s70's agreeing WIN, s12's
judge-only LOSS, s1's bare no-evidence row). Helpers carry the
_s113panel_ prefix, so nothing collides with existing defs.

Measured red against the pre-s113 audit (2026-09-20): 5 failed,
1 passed in 0.20s. The five contract pins red for one reason —
AttributeError: module 'rumpun.audit' has no attribute
'season_review_lines' (the verb pin hit the same gap as a stdout
without the listing, its rc-0 assert already passed). The record-body
guard pin green by design (it pins the current shape).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

# The real verdict rows per season, verbatim as measured 2026-09-20
# (compact form, the s112 fixture convention: season and verdict are the
# fields the resolution reads). s12 keeps its two real unit rows verbatim:
# the season-row rule must skip them and take the row naming s12.
_RUN_VERDICTS = {
    "s12": (
        '{"unit": "w2 README sync", "verdict": "WIN", "implies": '
        '"lifecycle docs match the lean 2-phase reality; audit verb '
        'documented"}\n'
        '{"unit": "w1 scaffold trim", "verdict": "INVALID", "implies": '
        '"tool-less spawn #7; harness applied the audit-1-determined trim '
        'post-season with fresh-init proof"}\n'
        '{"season": "s12", "verdict": "LOSS", "metric": '
        '"modules_integrated"}\n'
    ),
    "s69": '{"season": "s69", "verdict": "NEUTRAL"}\n',
    "s70": '{"season": "s70", "verdict": "WIN"}\n',
    "s79": '{"season": "s79", "verdict": "WIN"}\n',
    "s83": '{"season": "s83", "verdict": "WIN"}\n',
    "s84": '{"season": "s84", "verdict": "WIN"}\n',
}

# The real panel record families, verbatim as measured 2026-09-20: the
# pending requests and errors ride along so the generation-aware latest
# selection reads a real ladder, never a lone verdict.
_PANEL_FILES = (
    "2026-09-20_panel-s69.md",
    "2026-09-20_panel-s69-2.md",
    "2026-09-20_panel-s69-2-error.md",
    "2026-09-20_panel-s69-3.md",
    "2026-09-20_panel-s69-3-verdict.md",
    "2026-09-17_panel-s70.md",
    "2026-09-17_panel-s70-verdict.md",
    "2026-09-17_panel-s79.md",
    "2026-09-17_panel-s79-error.md",
    "2026-09-20_panel-s79-2.md",
    "2026-09-20_panel-s79-2-verdict.md",
    "2026-09-17_panel-s83.md",
    "2026-09-17_panel-s83-error.md",
    "2026-09-20_panel-s83-2.md",
    "2026-09-20_panel-s83-2-verdict.md",
    "2026-09-17_panel-s84.md",
    "2026-09-17_panel-s84-error.md",
    "2026-09-20_panel-s84-2.md",
    "2026-09-20_panel-s84-2-verdict.md",
)

# The window seasons: s1 (no runs, no panel), s12 (judge-only), s69
# (other vs LOSS), s70 (agreeing WIN), s79/s83/s84 (the brief's three
# dissents plus the s84 agreement).
_SEASONS = ("s1", "s12", "s69", "s70", "s79", "s83", "s84")


def _s113panel_repo() -> Path:
    """Repo root by the s70 w2 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s113panel_listing(root: Path) -> list[str]:
    """The render under test; a missing function fails naming the spec
    reason."""
    try:
        from rumpun import audit
    except ImportError as exc:
        pytest.fail(f"src/rumpun/audit.py missing/unimportable: {exc}")
    return audit.season_review_lines(root, last_n=32)


def _s113panel_sha8(root: Path, rid: str) -> str:
    """The fixture record's sha8, read off the sealed file (probe, never
    assume)."""
    from rumpun import akar, epics

    return epics._seal8(akar.find_record(root, rid))


def _s113panel_fx(tmp_path: Path) -> Path:
    """The s108 fixture pattern: the campaign's real yamls and records, no
    network, no stubs. Real season yamls for the seven window seasons,
    real panel families copied into the fixture ledger, measured verdict
    rows embedded under runs/. A minimal rumpun.yaml rides along for the
    verb pin's _project_root walk-up; the listing functions never read
    it."""
    repo = _s113panel_repo()
    root = tmp_path / "s113proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "runs").mkdir()
    for sid in _SEASONS:
        src = repo / ".rumpun" / "seasons" / f"{sid}.yaml"
        assert src.is_file(), f"fixture source missing: {src}"
        shutil.copyfile(src, root / "seasons" / f"{sid}.yaml")
    for sid, rows in _RUN_VERDICTS.items():
        (root / "runs" / sid).mkdir(parents=True)
        (root / "runs" / sid / "verdicts.jsonl").write_text(
            rows, encoding="utf-8"
        )
    (root / "ledger").mkdir()
    for name in _PANEL_FILES:
        src = repo / ".rumpun" / "ledger" / name
        assert src.is_file(), f"fixture source missing: {src}"
        shutil.copyfile(src, root / "ledger" / name)
    (root / "rumpun.yaml").write_text("budget: {}\n", encoding="utf-8")
    return root


def _s113panel_expected(root: Path) -> dict[str, str]:
    """The seven expected rows, sha8s probed off the copied records."""
    p70 = _s113panel_sha8(root, "panel-s70-verdict")
    p83 = _s113panel_sha8(root, "panel-s83-2-verdict")
    p84 = _s113panel_sha8(root, "panel-s84-2-verdict")
    return {
        "s1": "  s1",
        "s12": "  s12  judge LOSS",
        "s69": (
            "  s69  judge other  "
            "panel-s69-3-verdict@51f2d014 (LOSS) dissent:LOSS"
        ),
        "s70": f"  s70  judge WIN  panel-s70-verdict@{p70} (WIN)",
        "s79": (
            "  s79  judge WIN  "
            "panel-s79-2-verdict@387fa6ac (NEUTRAL) dissent:NEUTRAL"
        ),
        "s83": (
            "  s83  judge WIN  "
            f"panel-s83-2-verdict@{p83} (INCONCLUSIVE) dissent:INCONCLUSIVE"
        ),
        "s84": f"  s84  judge WIN  panel-s84-2-verdict@{p84} (WIN)",
    }


def test_s113panel_dissent_rows_name_both(tmp_path: Path) -> None:
    """The brief's three real dissents: judge other/WIN/WIN against panel
    LOSS/NEUTRAL/INCONCLUSIVE — the s111 mark with the verdict word, then
    the s112 dissent token."""
    root = _s113panel_fx(tmp_path)
    expected = _s113panel_expected(root)
    lines = _s113panel_listing(root)
    assert expected["s69"] in lines, lines
    assert expected["s79"] in lines, lines
    assert expected["s83"] in lines, lines


def test_s113panel_agreement_is_bare(tmp_path: Path) -> None:
    """Agreement is not news: s84 (judge WIN vs panel WIN) and s70 (the
    same shape, gen-1 family) name the mark with the verdict word and no
    dissent token."""
    root = _s113panel_fx(tmp_path)
    expected = _s113panel_expected(root)
    lines = _s113panel_listing(root)
    assert expected["s84"] in lines, lines
    assert expected["s70"] in lines, lines


def test_s113panel_bare_rows(tmp_path: Path) -> None:
    """No invented verdicts: s1 (no verdict row, no panel record) renders
    the bare sid; s12 (LOSS judge verdict, no panel record) names the
    judge verdict and nothing else."""
    root = _s113panel_fx(tmp_path)
    expected = _s113panel_expected(root)
    lines = _s113panel_listing(root)
    assert expected["s1"] in lines, lines
    assert expected["s12"] in lines, lines


def test_s113panel_full_listing_shape(tmp_path: Path) -> None:
    """The whole listing: seven rows, numeric order, one per window
    season, nothing else."""
    root = _s113panel_fx(tmp_path)
    expected = _s113panel_expected(root)
    assert _s113panel_listing(root) == [
        expected["s1"],
        expected["s12"],
        expected["s69"],
        expected["s70"],
        expected["s79"],
        expected["s83"],
        expected["s84"],
    ]


def test_s113panel_verb_prints_listing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """The verb prints the listing before the candidates. gh is stripped
    from PATH, so board_mod.issue_trail hits the designed degrade path
    (the audit runs without the board leg) and the pin stays offline; the
    appended audit record lands in the fixture ledger."""
    root = _s113panel_fx(tmp_path)
    monkeypatch.chdir(root.parent)
    monkeypatch.setenv("PATH", "/nonexistent-s113-no-gh")
    from rumpun import cli

    args = cli.build_parser().parse_args(["audit", "--last", "7"])
    rc = args.func(args)
    assert rc == 0
    out = capsys.readouterr().out
    printed = out.splitlines()
    expected = _s113panel_expected(root)
    for sid in _SEASONS:
        assert expected[sid] in printed, printed


def test_s113panel_record_body_untouched(tmp_path: Path) -> None:
    """The listing is verb output, not record body: the appended audit
    record keeps the pre-s113 body shape (scope line first, no season
    rows), so the byte-exact goldens elsewhere stay true."""
    root = _s113panel_fx(tmp_path)
    from rumpun import audit

    record = audit.run_audit(root, last_n=7)
    body = record.read_text(encoding="utf-8").splitlines()
    assert body[4] == (
        "scope: last 7 seasons (s1,s12,s69,s70,s79,s83,s84); "
        "engine seasons with runs/ (6): s12,s69,s70,s79,s83,s84"
    )
    assert not any(line.startswith("  s") for line in body[4:]), body
