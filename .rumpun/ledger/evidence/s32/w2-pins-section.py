

# --- band-mask guard (w2 s32 scope, spec-first) -----------------------------------
#
# Ratified contract (musim/s32.yaml expected_band, from audit-20's recalibration
# candidate and the s5/s6/s12/s14/s17-era precedent): a season that declares
# metric modules_integrated but whose primary_change.expected_band never states
# what counts as integrated gets exactly one lint WARNING naming the sid; a band
# carrying any integration-evidence token (integration|integrated|suite|tests)
# stays silent; any other metric stays silent; and the audit's "recalibrate LOSS
# bands" candidate retires: it fires only when a band-warned season sits in the
# audited window, so compliant bands accumulate without the candidate aging in.
#
# Pin status against the pre-guard code is measured in notes.md: pins 1 and 4a
# red, pins 2, 3, and 4b green-guard.

BAND_GUARD_VAGUE_BAND = "WIN if the season score improves by 0.5 over baseline"
BAND_GUARD_COMPLIANT_BAND = "WIN if 2 integrated modules land and the suite passes"

BAND_GUARD_SEASON = """\
id: {sid}
parent: s0
goal: "fixture"
metric: {metric}
mode: fight
methodology:
  approach: "x"
  evidence:
    - akar:band-guard-fixture@{sha}
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "{band}"
    rollback: "git revert"
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
benih:
  - name: w2
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""

BAND_GUARD_AUDIT_SEASON = """\
id: {sid}
goal: "fixture"
metric: modules_integrated
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "{band}"
    rollback: "git revert"
    eval_window: "{sid}"
  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: verdicts.jsonl
benih:
  - name: w2
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""


def _write_band_guard_proj(tmp_path, metric, band, sid="s1"):
    """Lint fixture: one otherwise-clean non-seed season; evidence resolves.

    parent plus a resolving citation keep the two pre-existing warnings
    (missing evidence, stage free) out of the findings, so the warning list
    is empty before the guard lands and any warning the pins see is the
    guard's.
    """
    root, season = _write_proj(
        tmp_path,
        BAND_GUARD_SEASON.format(sid=sid, metric=metric, band=band, sha="0" * 64),
    )
    record = akar.append_record(root, "band-guard-fixture", "fixture evidence", "body")
    sha = record.read_text(encoding="utf-8").splitlines()[-1].removeprefix("sha256: ")
    season.write_text(
        BAND_GUARD_SEASON.format(sid=sid, metric=metric, band=band, sha=sha),
        encoding="utf-8",
    )
    return season


def _band_guard_warnings(tmp_path, metric, band):
    season = _write_band_guard_proj(tmp_path, metric, band)
    findings = lint.lint(season)
    errors = [f for f in findings if f.severity == "error"]
    assert errors == []  # a broken fixture must fail loudly, not pass vacuously
    return [f for f in findings if f.severity == "warning"]


def _write_band_guard_audit_proj(tmp_path, band):
    """Audit fixture: two engine seasons, old trigger met, band text decides.

    Both seasons hold the F5 evidence (season-level LOSS, results row
    integrated: true) so the only variable is the musim yaml band text; the
    pre-guard audit proposes recalibrate for both band variants, and the
    pin pair discriminates on it.
    """
    root = _write_audit_proj(tmp_path, sids=("s1", "s2"))
    for sid in ("s1", "s2"):
        _write_rimba_season(root, sid)
        _write_harvest_record(root, sid, "LOSS")
        _write_results_rows(root, sid, [{"integrated": True}])
        (root / "musim" / f"{sid}.yaml").write_text(
            BAND_GUARD_AUDIT_SEASON.format(sid=sid, band=band), encoding="utf-8"
        )
    return root


def test_band_guard_warns_once_naming_sid(tmp_path):
    warnings = _band_guard_warnings(
        tmp_path, "modules_integrated", BAND_GUARD_VAGUE_BAND
    )
    assert len(warnings) == 1
    assert "s1" in warnings[0].message


def test_band_guard_silent_on_compliant_band(tmp_path):
    warnings = _band_guard_warnings(
        tmp_path, "modules_integrated", BAND_GUARD_COMPLIANT_BAND
    )
    assert warnings == []


def test_band_guard_silent_on_other_metric(tmp_path):
    warnings = _band_guard_warnings(tmp_path, "win_rate", BAND_GUARD_VAGUE_BAND)
    assert warnings == []


def test_band_guard_audit_compliant_bands_retire_recalibrate(tmp_path):
    root = _write_band_guard_audit_proj(tmp_path, BAND_GUARD_COMPLIANT_BAND)
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert not any("recalibrate" in line for line in text.splitlines())


def test_band_guard_audit_warned_band_keeps_recalibrate(tmp_path):
    root = _write_band_guard_audit_proj(tmp_path, BAND_GUARD_VAGUE_BAND)
    text = audit.run_audit(root).read_text(encoding="utf-8")
    assert any("recalibrate" in line for line in text.splitlines())
