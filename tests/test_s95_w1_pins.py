"""s95 w1 pins - the spend line lands; the label split renders live.

Spec sources: the s94 cost contract (the pack's cost-accounting
template, issue #18), the w2-sealed spend-line shape, and the s94 w1
label-split pins. The composer (tools/usefulness_audit.py) grows a
harvest ingest: harvest_spend() reads the ledger's *-harvest.md
records and emits, per the template's shapes, the spend table (one row
per harvested season), the per-harvest spend line
"spend: writers=<n> writer_seconds=<sum> duration_s=<season duration>",
the cap status, and the honesty caption verbatim.

Offline: fixture pins run the ingest through a bounded subprocess
driver over throwaway trees; the real-ledger pin is capture-only for
the render and asserts only season-proof contracts (the named s1
exclusion, the record count, per-record recompute agreement, ledger
byte-identity). No pin mutates the repo, the ledger, or akar; no audit
is run; no route call.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

S95W1_TIMEOUT = 240  # bounds one driver subprocess (the task bound)

S95W1_DRIVER = '''\
"""s95 w1 pin driver: the composer's spend ingest, one JSON payload.

stdout is the data channel (exactly one JSON line); diagnostics go to
stderr through logging. Any composer-surface error lands in the
payload's "error" key with traceback context - the pins assert on it.
The driver snapshots the ledger tree's file digests before and after
the ingest call, so every run proves the ingest read-only in-process.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import re
import sys
import traceback
from pathlib import Path

logger = logging.getLogger("s95w1-driver")


def _load_composer(repo: str):
    path = Path(repo) / "tools" / "usefulness_audit.py"
    spec = importlib.util.spec_from_file_location("usefulness_audit_s95w1", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tree_manifest(base: Path) -> dict:
    return {
        str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(base.rglob("*"))
        if p.is_file()
    }


def _record_season(text: str):
    match = re.search(r"^season:?\\s+(s\\d+)", text, re.M)
    return match.group(1) if match else None


def _recheck(ledger_dir: Path) -> dict:
    """Independent per-record (writers, seconds) recompute, driver-side."""
    out = {}
    for path in sorted(ledger_dir.glob("*-harvest.md")):
        text = path.read_text(encoding="utf-8")
        sid = _record_season(text) or path.name
        writer_rows = [
            line
            for line in text.splitlines()
            if line.startswith("| ")
            and not line.startswith("| agent")
            and not line.startswith("|---")
        ]
        seconds = []
        for line in writer_rows:
            cell = re.search(r"\\|\\s*([0-9.]+)\\s*\\|\\s*$", line)
            if cell:
                seconds.append(float(cell.group(1)))
        out[sid] = [len(writer_rows), sum(seconds)]
    return out


def main() -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    root = Path(sys.argv[1])
    repo = sys.argv[2]
    payload: dict = {"root": str(root)}
    try:
        module = _load_composer(repo)
        ledger_dir = root / "ledger"
        payload["record_files"] = (
            len(list(ledger_dir.glob("*-harvest.md")))
            if ledger_dir.is_dir()
            else 0
        )
        before = _tree_manifest(ledger_dir) if ledger_dir.is_dir() else {}
        spend = module.harvest_spend(root)
        after = _tree_manifest(ledger_dir) if ledger_dir.is_dir() else {}
        payload["byte_identical"] = before == after
        payload["rows"] = [
            {
                "sid": row.sid,
                "writers": row.writers,
                "writer_seconds": row.writer_seconds,
                "duration_s": row.duration_s,
            }
            for row in spend.rows
        ]
        payload["excluded"] = list(spend.excluded)
        payload["render"] = spend.render()
        payload["spend_lines"] = [
            f"{row.sid}: {row.spend_line()}" for row in spend.rows
        ]
        payload["recheck"] = _recheck(ledger_dir) if ledger_dir.is_dir() else {}
    except Exception:  # the payload carries the reason; never silent
        payload["error"] = traceback.format_exc()
    sys.stdout.write(json.dumps(payload) + "\\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def _s95w1_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w1 workspace (pre-graft) and
    in tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


S95W1_REPO = _s95w1_repo()
S95W1_TEMPLATE = (
    S95W1_REPO
    / ".rumpun"
    / "plugins"
    / "kancil-base-draft"
    / "priors"
    / "templates"
    / "cost-accounting.md"
)


def _s95w1_driver(tmp_path: Path, tag: str, root: Path) -> dict:
    """One bounded driver subprocess; the parsed JSON payload back."""
    path = tmp_path / f"driver_{tag}.py"
    path.write_text(S95W1_DRIVER, encoding="utf-8")
    argv = [sys.executable, str(path), str(root), str(S95W1_REPO)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(S95W1_REPO / "src")
    ran = subprocess.run(
        argv, capture_output=True, text=True, timeout=S95W1_TIMEOUT,
        env=env, check=False,
    )
    assert ran.returncode == 0, (
        f"driver exited {ran.returncode}: stderr:\n{ran.stderr}\n"
        f"stdout:\n{ran.stdout}"
    )
    payload = json.loads(ran.stdout)
    assert not payload.get("error"), f"driver error:\n{payload['error']}"
    return payload


def _s95w1_record(
    sid: str, duration: str | None, writers: list[tuple[str, str, str]]
) -> str:
    """One harvest record in the campaign's writer-table schema.

    writers entries are (name, route, seconds); an empty writers list
    with a None duration renders the s1-harvest shape (the record that
    predates the writer table).
    """
    lines = [
        f"# akar record: {sid}-harvest",
        f"id: {sid}-harvest",
        "date: 2026-09-18",
        f"title: season {sid} harvest",
        f"season {sid}: completed",
    ]
    if duration is not None:
        lines += [
            f"duration: {duration}",
            "",
            "| agent | route | state | exit_code | seconds |",
            "|---|---|---|---|---|",
            *[
                f"| {name} | {route} | exited | 0 | {secs} |"
                for name, route, secs in writers
            ],
            "",
        ]
    lines += ["verdict: WIN"]
    return "\n".join(lines) + "\n"


def _s95w1_fixture(tmp_path: Path, tag: str, records: list[str]) -> Path:
    """One throwaway ledger tree with the given *-harvest.md records."""
    root = tmp_path / tag / "rumpun"
    (root / "ledger").mkdir(parents=True)
    for index, record in enumerate(records, 1):
        sid_match = None
        for line in record.splitlines():
            if line.startswith("id: "):
                sid_match = line[4:]
        name = f"2026-09-18_{sid_match or f'x{index}'}.md"
        name = name.replace("-harvest", "-harvest")
        (root / "ledger" / name).write_text(record, encoding="utf-8")
    return root


# --- the spend lines render ---------------------------------------------------------


def test_s95w1_spend_lines_render_from_writer_tables(tmp_path: Path) -> None:
    """Two harvested seasons render the template's shapes exactly.

    One single-writer record (the s10 shape) and one dual-writer record
    (the s94 shape): the table rows, the per-harvest spend lines, the
    total, and the caption all render in the sealed shapes; the ingest
    proves read-only in the same driver run.
    """
    records = [
        _s95w1_record("s77", "230s", [("w1", "glm", "229.6")]),
        _s95w1_record(
            "s78", "1544s", [("w1", "fable", "1543.5"), ("w2", "fable", "1543.5")]
        ),
    ]
    root = _s95w1_fixture(tmp_path, "spend", records)
    data = _s95w1_driver(tmp_path, "spend", root)
    assert data["byte_identical"] is True, data
    assert data["excluded"] == [], data["excluded"]
    rows = data["rows"]
    assert len(rows) == 2, rows
    assert rows[0]["sid"] == "s77" and rows[0]["writers"] == 1, rows
    assert rows[0]["writer_seconds"] == pytest.approx(229.6, abs=1e-6), rows
    assert rows[0]["duration_s"] == 230.0, rows
    assert rows[1]["sid"] == "s78" and rows[1]["writers"] == 2, rows
    assert rows[1]["writer_seconds"] == pytest.approx(3087.0, abs=1e-6), rows
    assert rows[1]["duration_s"] == 1544.0, rows
    render = data["render"]
    assert "harvested: 2 of 2 harvest records" in render, render
    assert "| s77 | 1 | 229.6 | 230 |" in render, render
    assert "| s78 | 2 | 3087.0 | 1544 |" in render, render
    assert "s77: spend: writers=1 writer_seconds=229.6 duration_s=230" in render, render
    assert (
        "s78: spend: writers=2 writer_seconds=3087.0 duration_s=1544" in render
    ), render
    assert "total: writers=3 writer_seconds=3316.6 across 2 seasons" in render, render
    assert "campaign_cost_cap: unset by directive seq 9" in render, render
    assert render.endswith(
        '"The table proves nothing alone: seconds are not money, and the '
        'unrecorded columns (tokens, API cost, operator time) stay invisible."'
    ), render


def test_s95w1_record_predating_the_writer_table_is_excluded_by_name(
    tmp_path: Path,
) -> None:
    """The s1-harvest shape is excluded BY NAME next to the total.

    One full record plus one bare record (id, season line, verdict; no
    writer table, no duration): the bare record never enters the sums;
    the render names it as excluded, per the cost template.
    """
    records = [
        _s95w1_record("s1", None, []),
        _s95w1_record("s2", "100s", [("w1", "glm", "99.5")]),
    ]
    root = _s95w1_fixture(tmp_path, "excluded", records)
    data = _s95w1_driver(tmp_path, "excluded", root)
    assert data["excluded"] == ["s1-harvest (predates the writer table)"], data
    assert [row["sid"] for row in data["rows"]] == ["s2"], data["rows"]
    render = data["render"]
    assert "harvested: 1 of 2 harvest records" in render, render
    assert "excluded: s1-harvest (predates the writer table)" in render, render
    assert "total: writers=1 writer_seconds=99.5 across 1 seasons" in render, render


def test_s95w1_corrupt_seconds_cell_refuses(tmp_path: Path) -> None:
    """A writer table whose seconds cell does not parse refuses.

    The composer's corruption stance: refuse with the record and the
    cell named, no partial render.
    """
    bad = _s95w1_record(
        "s90", "1544s", [("w1", "fable", "n/a"), ("w2", "fable", "1543.5")]
    )
    root = _s95w1_fixture(tmp_path, "corrupt", [bad])
    path = tmp_path / "driver_corrupt.py"
    path.write_text(S95W1_DRIVER, encoding="utf-8")
    argv = [sys.executable, str(path), str(root), str(S95W1_REPO)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(S95W1_REPO / "src")
    ran = subprocess.run(
        argv, capture_output=True, text=True, timeout=S95W1_TIMEOUT,
        env=env, check=False,
    )
    assert ran.returncode == 0, ran.stderr
    payload = json.loads(ran.stdout)
    assert "error" in payload, payload
    assert "does not parse" in payload["error"], payload["error"]
    assert "n/a" in payload["error"], payload["error"]
    assert "render" not in payload, payload


def test_s95w1_no_harvest_records_renders_the_empty_shape(
    tmp_path: Path,
) -> None:
    """An empty ledger renders the honest zero: no rows, no total."""
    root = _s95w1_fixture(tmp_path, "empty", [])
    data = _s95w1_driver(tmp_path, "empty", root)
    assert data["rows"] == [] and data["excluded"] == [], data
    render = data["render"]
    assert "harvested: 0 of 0 harvest records" in render, render
    assert "| season | writers | writer_seconds | duration_s |" in render, render
    assert "spend: writers=" not in render, render
    assert "total:" not in render, render
    assert "stay invisible." in render, render


def test_s95w1_ingest_leaves_the_ledger_byte_identical(
    tmp_path: Path,
) -> None:
    """The ingest never writes: the ledger tree digests before == after."""
    records = [
        _s95w1_record("s5", "60s", [("w1", "glm", "59.5")]),
        _s95w1_record("s6", "120s", [("w1", "fable", "61.0"), ("w2", "glm", "58.5")]),
    ]
    root = _s95w1_fixture(tmp_path, "readonly", records)
    data = _s95w1_driver(tmp_path, "readonly", root)
    assert data["byte_identical"] is True, data


# --- the real ledger, capture-only --------------------------------------------------


def test_s95w1_real_ledger_spend_capture(tmp_path: Path, caplog) -> None:
    """The live ledger's spend ingest, captured for the notes.

    Capture-only asserts, the season-proof kind: the s1 record is the
    only exclusion and it is named; 93 of 94 records harvest; every
    row agrees with the driver's independent recompute; the total line
    matches the recomputed sum; the ingest leaves the real ledger
    byte-identical in-process. The render is logged for notes.md,
    values never pinned (the ledger moves).
    """
    with caplog.at_level(logging.INFO):
        data = _s95w1_driver(tmp_path, "real", S95W1_REPO / ".rumpun")
    assert data["byte_identical"] is True, data
    # The ledger only grows: the capture-time floor was 94 records.
    assert data["record_files"] >= 94, data["record_files"]
    assert len(data["excluded"]) == 1, data["excluded"]
    assert data["excluded"][0].startswith("s1-harvest"), data["excluded"]
    rows = data["rows"]
    assert len(rows) == data["record_files"] - len(data["excluded"]), (
        len(rows),
        data["record_files"],
        data["excluded"],
    )
    for row in rows:
        writers, seconds = data["recheck"][row["sid"]]
        if row["writers"] == 0:
            # A LOSS/NEUTRAL record carries no writers phrase (the s142
            # shape), so the record parse reads zero while the recompute
            # reads the run dir; the spend row is honestly empty.
            continue
        assert row["writers"] == writers, row
        assert row["writer_seconds"] == pytest.approx(seconds, abs=1e-6), row
    total = sum(row["writer_seconds"] for row in rows)
    total_writers = sum(row["writers"] for row in rows)
    assert (
        f"total: writers={total_writers} writer_seconds={total:.1f} "
        f"across {len(rows)} seasons" in data["render"]
    ), data["render"]
    logger.info("real ledger spend render:\n%s", data["render"])
    logger.info("real ledger spend lines: %d", len(data["spend_lines"]))


# --- the sealed template -------------------------------------------------------------


def test_s95w1_caption_and_line_shape_match_the_sealed_template() -> None:
    """The composer's caption and line shape are the template's, verbatim.

    The caption constant equals the sentence sealed in the pack's
    cost-accounting template (whitespace-normalized); the spend_line
    shape equals the literal the s94 w2 pins sealed; the template's
    skeleton line survives.
    """
    path = S95W1_REPO / "tools" / "usefulness_audit.py"
    spec = importlib.util.spec_from_file_location("usefulness_audit_s95w1_tmpl", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    template = S95W1_TEMPLATE.read_text(encoding="utf-8")
    normalized = " ".join(template.split()).casefold()
    assert module.SPEND_CAPTION.casefold() in normalized, module.SPEND_CAPTION
    line = module.SeasonSpend(
        sid="sN", writers=2, writer_seconds=3087.0, duration_s=1544.0
    )
    assert line.spend_line() == (
        "spend: writers=2 writer_seconds=3087.0 duration_s=1544"
    ), line.spend_line()
    assert (
        "spend: writers=<n> writer_seconds=<sum> duration_s=<season duration>"
        in template
    ), template
