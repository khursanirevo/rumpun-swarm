"""s135 w2 pins — evaluate emits the LOSS it meets.

Spec source: issue #47 on khursanirevo/rumpun and the s135 w2 brief
(.rumpun/runs/s135/w2/prompt.md). The khursani campaign's s85 closed WIN
while its own verdicts.jsonl observed field admits the verifier lane never
ran: 'a2 verify lane never ran (armed wake timer then exited; all_exited
closed season)'. Audit-86 and audit-87 sealed the histogram F3: WIN 10,
LOSS 0 over s77-s86. Grading bias, not ten perfect runs.

The contract these pins hold: the verdict emitter (harvest.harvest_season)
can no longer read WIN-only. A WIN downgrades to LOSS when the close
inputs carry a deterministic met-LOSS signal:
- the observed text admits a declared lane never ran (the s85 shape);
- the observed text admits a met LOSS condition outright;
- a prior judge row in the season's verdicts.jsonl already reads LOSS.
An explicit `justification:` line in the observed text retains the WIN
(the grading is recorded either way; silence is the #47 shape). A WIN
that met its band still reads WIN (no inversion); non-WIN verdicts pass
through untouched; an unreadable season yaml never blocks a close.

Fixture discipline: tmp campaigns only. The band text and the observed
text below quote the khursani s85 shapes verbatim; no real campaign tree
is written by these pins.

Red-first honesty: RED captured 2026-09-21 pre-implementation at
/tmp/s135-w2-pins-red.txt -- 5 failed, 4 passed (the s85 flip, the record
note, the justified retention, the judge-row flip, the prompt contract;
the no-inversion, pass-through, tolerant-yaml, untouched-NEUTRAL controls
green on arrival by design). GREEN captured 2026-09-21
post-implementation at /tmp/s135-w2-pins-green.txt -- 9 passed.
"""

from __future__ import annotations

import json
from pathlib import Path

from rumpun import harvest, scaffold

BAND_S85 = (
    "WIN: live vault.sani.workers.dev 200 with working entry -> status -> "
    "export flow, Turnstile on the form, rule text sourced from official "
    "pages fetched in-run, vitest green on vault/, tsc clean, free tier "
    "only, products.json entry committed, edgeKey store listing live. "
    "LOSS: site missing, flow broken, rule text unsourced or contradicting "
    "official text, tests/tsc fail, registry or store listing missing, "
    "any paid binding."
)

OBSERVED_S85 = (
    "a2 verify lane never ran (armed wake timer then exited; "
    "all_exited closed season)"
)

OBSERVED_CLEAN = (
    "site 200; entry -> status -> export flow curl-verified; "
    "vitest green on vault/; tsc clean; products.json entry committed; "
    "store listing live"
)

OBSERVED_JUSTIFIED = (
    "a2 verify lane never ran (armed wake timer then exited); "
    "justification: the harvester's own live checks graded the WIN "
    "clauses a2 existed to grade (site 200, flow curl, vitest, tsc)"
)

IMPLIES = "the vault ships with the verify gap named"


def _s135el_campaign(tmp_path: Path) -> Path:
    """Tmp campaign root (.rumpun) with the seasons and ledger trees."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir()
    return root


def _s135el_yaml(root: Path, sid: str) -> None:
    """Season yaml with the s85 shape: two writers, a2 the verifier."""
    writers = (
        "writers:\n"
        "  - name: a1\n"
        "    route: glm\n"
        "    lane: vault-implement\n"
        "  - name: a2\n"
        "    route: claude\n"
        "    lane: vault-verify\n"
    )
    text = (
        f"id: {sid}\n"
        "metric: product_live\n"
        "mode: fight\n"
        "methodology:\n"
        "  primary_change:\n"
        f"    expected_band: {json.dumps(BAND_S85)}\n"
        + writers
    )
    (root / "seasons" / f"{sid}.yaml").write_text(text, encoding="utf-8")


def _s135el_state(root: Path, sid: str) -> None:
    """Terminal engine state: both lanes exited clean."""
    run = root / "runs" / sid / "_season"
    run.mkdir(parents=True)
    state = {
        "id": sid,
        "status": "completed",
        "started_at": 1000.0,
        "ended_at": 2000.0,
        "agents": {
            "a1": {
                "name": "a1", "route": "glm",
                "state": "exited", "exit_code": 0, "seconds": 971.2,
            },
            "a2": {
                "name": "a2", "route": "claude",
                "state": "exited", "exit_code": 0, "seconds": 971.2,
            },
        },
    }
    (run / "state.json").write_text(json.dumps(state), encoding="utf-8")


def _s135el_seed_judge_loss(root: Path, sid: str) -> None:
    """A prior evaluate-phase judge row already reading LOSS."""
    run = root / "runs" / sid
    run.mkdir(parents=True, exist_ok=True)
    row = {
        "experiment_id": "exp-vault-flow",
        "criterion_verbatim": "working entry -> status -> export flow",
        "result": "the export step returned 500 twice",
        "verdict": "LOSS",
        "implies": "the flow clause failed under the judge's own re-run",
    }
    with (run / "verdicts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def _s135el_close(
    root: Path, sid: str, verdict: str, observed: str,
) -> tuple[Path, dict]:
    """One harvest close; returns (record path, verdicts.jsonl row)."""
    record = harvest.harvest_season(
        root, sid, verdict, IMPLIES, band=BAND_S85, observed=observed,
    )
    lines = (
        (root / "runs" / sid / "verdicts.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    season_rows = [ln for ln in lines if json.loads(ln).get("season") == sid]
    return record, json.loads(season_rows[0])


def test_s135_pin01_s85_shape_reads_loss(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_yaml(root, "s85fx")
    _s135el_state(root, "s85fx")
    _, row = _s135el_close(root, "s85fx", "WIN", OBSERVED_S85)
    assert row["verdict"] == "LOSS"


def test_s135_pin02_record_names_the_downgrade(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_yaml(root, "s85fx")
    _s135el_state(root, "s85fx")
    record, row = _s135el_close(root, "s85fx", "WIN", OBSERVED_S85)
    assert row["verdict"] == "LOSS"
    text = record.read_text(encoding="utf-8")
    assert "loss-grade: WIN downgraded to LOSS" in text
    assert "declared lane a2 never ran" in text


def test_s135_pin03_no_inversion_clean_win(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_yaml(root, "s85fx")
    _s135el_state(root, "s85fx")
    _, row = _s135el_close(root, "s85fx", "WIN", OBSERVED_CLEAN)
    assert row["verdict"] == "WIN"


def test_s135_pin04_justified_win_retained(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_yaml(root, "s85fx")
    _s135el_state(root, "s85fx")
    record, row = _s135el_close(root, "s85fx", "WIN", OBSERVED_JUSTIFIED)
    assert row["verdict"] == "WIN"
    text = record.read_text(encoding="utf-8")
    assert "loss-grade: WIN retained with justification" in text
    assert "declared lane a2 never ran" in text


def test_s135_pin05_judge_loss_row_flips_win(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_yaml(root, "s85fx")
    _s135el_state(root, "s85fx")
    _s135el_seed_judge_loss(root, "s85fx")
    _, row = _s135el_close(root, "s85fx", "WIN", OBSERVED_CLEAN)
    assert row["verdict"] == "LOSS"


def test_s135_pin06_loss_caller_passes_through(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_yaml(root, "s85fx")
    _s135el_state(root, "s85fx")
    record, row = _s135el_close(root, "s85fx", "LOSS", OBSERVED_S85)
    assert row["verdict"] == "LOSS"
    text = record.read_text(encoding="utf-8")
    assert "verdict: LOSS" in text
    assert "loss-grade:" not in text


def test_s135_pin07_missing_yaml_tolerates_win(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_state(root, "s85fx")
    _, row = _s135el_close(root, "s85fx", "WIN", OBSERVED_CLEAN)
    assert row["verdict"] == "WIN"


def test_s135_pin08_neutral_untouched_with_signal(tmp_path: Path) -> None:
    root = _s135el_campaign(tmp_path)
    _s135el_yaml(root, "s85fx")
    _s135el_state(root, "s85fx")
    _, row = _s135el_close(root, "s85fx", "NEUTRAL", OBSERVED_S85)
    assert row["verdict"] == "NEUTRAL"


def test_s135_pin09_prompt_carries_the_grading_contract() -> None:
    prompt = scaffold.PROMPTS["evaluate"]
    assert "Grade each LOSS clause of the season metric pass/fail." in prompt
    assert "A met LOSS condition reads LOSS, verbatim in the verdict row." in prompt
    assert "A WIN that met its band still reads WIN (no inversion)." in prompt
