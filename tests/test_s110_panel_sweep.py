"""s110 w2 pins - the panel pending-outcome sweep.

s70..s84 sealed panel requests against the gpt-6-astra route and the
outcome half waits on the operator's route credits: the s71 convention
keeps every request record `status: pending` forever (the pending
record stays, a new record carries the outcome), so the ledger cannot
say which requests still await an outcome and nothing could seal a
route outcome after the calling season closed. s110 w2 resolves it:
`audit --panel-sweep` lists the pending panel records (id, date,
status), refuses with exit 2 without an explicit --outcome-file, and
with one seals each named outcome as <id>-verdict or <id>-error beside
the pending request - never invented (the request must be a declared
ledger record, the verdict must parse from the named reply) and never
rewriting (a sealed outcome refuses; the append-only ledger backs the
refusal; validation completes before the first seal).

Fixture: the s70/s108 pattern - the real s69 season yaml, the real
s69-harvest ledger record, the live DESIGN.md, panel records
hand-sealed with akar.append_record (the sweep reads the ledger, it
never calls the route). No network, no route calls, no real campaign
writes.
"""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest
import yaml


def _repo_root() -> Path:
    """Repo root by the s70 walk-up (pyproject + src/rumpun + DESIGN)."""
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _panel_module():
    """Import rumpun.panel; fail naming the spec reason when unlanded."""
    try:
        from rumpun import panel as panel_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/panel.py missing/unimportable: {exc}")
    return panel_module


def _fixture_campaign(tmp_path: Path) -> Path:
    """The s108 fixture: real s69 panel-input files, records hand-sealed."""
    repo_root = _repo_root()
    campaign = tmp_path / "s110w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text("autonomy:\n  stage: manual\n", encoding="utf-8")
    shutil.copyfile(repo_root / "DESIGN.md", campaign / "DESIGN.md")
    shutil.copyfile(
        repo_root / ".rumpun" / "seasons" / "s69.yaml", root / "seasons" / "s69.yaml"
    )
    from rumpun import akar

    harvest_src = akar.find_record(repo_root / ".rumpun", "s69-harvest")
    shutil.copyfile(harvest_src, root / "ledger" / harvest_src.name)
    return root


def _seal_request(root: Path, rid: str) -> Path:
    """Hand-seal a pending panel request record (the s71 request shape)."""
    from rumpun import akar

    return akar.append_record(
        root,
        rid,
        f"panel review request {rid.removeprefix('panel-')} (pending)",
        "\n".join(
            [
                "status: pending",
                "route: gpt-6-astra (bounded 300s); the outcome seals as "
                f"{rid}-verdict or {rid}-error",
                "review request:",
                "panel review request: s69",
            ]
        ),
    )


def _seal_outcome(root: Path, rid: str, status: str, body: str) -> Path:
    """Hand-seal an outcome record (verdict or error) beside a request."""
    from rumpun import akar

    return akar.append_record(
        root, rid, f"panel outcome {rid}", f"status: {status}\n{body}"
    )


def _write_outcome_file(path: Path, outcomes: dict) -> Path:
    """Write the sweep's outcome file (YAML, one entry per pending id)."""
    path.write_text(
        yaml.safe_dump({"outcomes": outcomes}, sort_keys=False), encoding="utf-8"
    )
    return path


def test_s110w2_audit_parser_wires_sweep_flags() -> None:
    """`rumpun audit --panel-sweep [--outcome-file PATH]` parses to cmd_audit."""
    from rumpun import cli

    args = cli.build_parser().parse_args(["audit", "--panel-sweep"])
    assert args.panel_sweep is True
    assert args.outcome_file is None
    assert args.func is cli.cmd_audit
    args_file = cli.build_parser().parse_args(
        ["audit", "--panel-sweep", "--outcome-file", "out.yaml"]
    )
    assert args_file.panel_sweep is True
    assert args_file.outcome_file == "out.yaml"


def test_s110w2_pending_records_list_requests_skip_sealed_verdicts(
    tmp_path: Path,
) -> None:
    """The listing is the literal pending set: both requests, no verdict."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    _seal_request(root, "panel-s69")
    _seal_request(root, "panel-s69-2")
    _seal_outcome(root, "panel-s70-verdict", "WIN", "route: gpt-6-astra\nreply:\nbody")
    rows = panel.pending_panel_records(root)
    assert rows == [
        ("panel-s69-2", date.today().isoformat(), "pending"),
        ("panel-s69", date.today().isoformat(), "pending"),
    ], "the listing is not the pending set (id, date, status) in file order"


def test_s110w2_bare_sweep_lists_refuses_exit2_zero_pending_exit0(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """Bare: the listing plus the refusal exit 2; nothing pending: exit 0."""
    from rumpun import cli

    root = _fixture_campaign(tmp_path)
    _seal_request(root, "panel-s69")
    monkeypatch.chdir(root.parent)
    rc = cli.cmd_audit(cli.build_parser().parse_args(["audit", "--panel-sweep"]))
    out = capsys.readouterr().out
    assert rc == 2, f"the bare sweep did not refuse with exit 2 (rc={rc})"
    assert "panel-s69\t" in out, f"the listing did not name the pending id: {out!r}"
    assert "nothing sealed" in out, f"no bare refusal line: {out!r}"
    empty_root = _fixture_campaign(tmp_path / "empty")
    monkeypatch.chdir(empty_root.parent)
    rc = cli.cmd_audit(cli.build_parser().parse_args(["audit", "--panel-sweep"]))
    out = capsys.readouterr().out
    assert rc == 0, f"an empty ledger must not refuse (rc={rc})"
    assert "no pending panel records" in out


def test_s110w2_sweep_seals_named_verdict_and_error_from_file(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """The CLI seal path: two entries seal beside their requests; rc 0."""
    from rumpun import akar, cli

    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    request_path = _seal_request(root, "panel-s69")
    _seal_request(root, "panel-s69-2")
    request_bytes = request_path.read_bytes()
    outcome_file = _write_outcome_file(
        tmp_path / "outcomes.yaml",
        {
            "panel-s69": {"reply": "verdict: WIN\nthe reply body.\n"},
            "panel-s69-2": {"error": "route exited 127: command not found"},
        },
    )
    monkeypatch.chdir(root.parent)
    rc = cli.cmd_audit(
        cli.build_parser().parse_args(
            ["audit", "--panel-sweep", "--outcome-file", str(outcome_file)]
        )
    )
    out = capsys.readouterr().out
    assert rc == 0, f"the seal run did not exit 0 (rc={rc}): {out!r}"
    assert "sealed panel-s69-verdict -> " in out, f"no verdict receipt: {out!r}"
    verdict = akar.find_record(root, "panel-s69-verdict").read_text(encoding="utf-8")
    assert "status: WIN" in verdict.splitlines(), f"verdict record malformed: {verdict}"
    assert "the reply body." in verdict, "the verdict record does not quote the reply"
    error = akar.find_record(root, "panel-s69-2-error").read_text(encoding="utf-8")
    assert "status: pending" in error.splitlines(), f"error record malformed: {error}"
    assert "route exited 127" in error, "the error record does not quote the error"
    assert request_path.read_bytes() == request_bytes, "the request record was rewritten"
    assert panel.pending_panel_records(root), "the requests must still list as pending"


def test_s110w2_sweep_never_invents_missing_request(tmp_path: Path) -> None:
    """An outcome for an undeclared id refuses; the ledger gains nothing."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    _seal_request(root, "panel-s69")

    before = sorted(p.name for p in (root / "ledger").iterdir())
    outcome_file = _write_outcome_file(
        tmp_path / "outcomes.yaml",
        {"panel-s99": {"reply": "verdict: WIN\n"}},
    )
    with pytest.raises(panel.PanelError, match="panel-s99"):
        panel.seal_panel_outcomes(root, outcome_file)
    assert sorted(p.name for p in (root / "ledger").iterdir()) == before, (
        "a refused sweep still wrote records"
    )


def test_s110w2_sweep_never_rewrites_sealed_outcome(tmp_path: Path) -> None:
    """A request with a sealed outcome refuses; the sealed record stands."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    _seal_request(root, "panel-s69")
    _seal_outcome(
        root, "panel-s69-error", "pending", "route: gpt-6-astra\nerror:\nroutedown"
    )
    from rumpun import akar

    sealed = akar.find_record(root, "panel-s69-error").read_bytes()
    outcome_file = _write_outcome_file(
        tmp_path / "outcomes.yaml",
        {"panel-s69": {"reply": "verdict: WIN\n"}},
    )
    with pytest.raises(panel.PanelError, match="panel-s69-error"):
        panel.seal_panel_outcomes(root, outcome_file)
    assert akar.find_record(root, "panel-s69-error").read_bytes() == sealed, (
        "the sealed outcome record changed"
    )


def test_s110w2_sweep_refuses_outcome_record_as_target(tmp_path: Path) -> None:
    """An outcome record is never a sweep target: outcomes seal beside requests."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    _seal_request(root, "panel-s69-2")
    _seal_outcome(
        root, "panel-s69-2-error", "pending", "route: gpt-6-astra\nerror:\nroutedown"
    )
    outcome_file = _write_outcome_file(
        tmp_path / "outcomes.yaml",
        {"panel-s69-2-error": {"reply": "verdict: WIN\n"}},
    )
    with pytest.raises(panel.PanelError, match="outcome record"):
        panel.seal_panel_outcomes(root, outcome_file)


def test_s110w2_sweep_reply_without_actionable_verdict_refuses(
    tmp_path: Path,
) -> None:
    """A reply with no actionable verdict line seals nothing (never invented)."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    _seal_request(root, "panel-s69")
    outcome_file = _write_outcome_file(
        tmp_path / "outcomes.yaml",
        {"panel-s69": {"reply": "verdict: pending\n"},
         "panel-s69-2": {"error": "route exited 1: down"}},
    )
    with pytest.raises(panel.PanelError, match="no actionable"):
        panel.seal_panel_outcomes(root, outcome_file)
    from rumpun import akar

    with pytest.raises(akar.AkarError):
        akar.find_record(root, "panel-s69-verdict")
    with pytest.raises(akar.AkarError):
        akar.find_record(root, "panel-s69-2-error")


def test_s110w2_sweep_empty_or_ambiguous_entries_refuse(tmp_path: Path) -> None:
    """An empty outcomes mapping, and a both-keys entry, refuse."""
    panel = _panel_module()
    root = _fixture_campaign(tmp_path)
    _seal_request(root, "panel-s69")
    empty_file = _write_outcome_file(tmp_path / "empty.yaml", {})
    with pytest.raises(panel.PanelError, match="no outcomes"):
        panel.seal_panel_outcomes(root, empty_file)
    both_file = _write_outcome_file(
        tmp_path / "both.yaml",
        {"panel-s69": {"reply": "verdict: WIN\n", "error": "also down"}},
    )
    with pytest.raises(panel.PanelError, match="exactly one"):
        panel.seal_panel_outcomes(root, both_file)
