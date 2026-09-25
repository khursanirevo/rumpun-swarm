"""s43 w2 pins — corpus coverage finding + DRIFT mismatch arming + falsify reachability.

Spec-first pins (red against current code) for the s43 contract:
musim/s43.yaml, akar audit-32 + usefulness-decade-4 residuals 7, 8, 10.
Spec and measured red set: .rumpun/rimba/s43/w2/notes.md.

Grafting: append this block to tests/test_rumpun.py and drop this scratch
import header (the repo file already imports audit and lint); every helper
carries the _s43w2_ prefix, so nothing collides with the existing defs.
"""
import json

from rumpun import audit, lint

S43W2_RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

# Lean falsify shape: execute writes results.jsonl; evaluate (the only
# reader) reads results.jsonl — an artifact another phase produces, so the
# reachable-reader gate is satisfied. The unreachable-reader pin swaps
# only the reads line, so the fixtures differ in exactly one variable.
S43W2_FALSIFY_SEASON = """\
id: s9
goal: "fixture"
metric: m
mode: fight
methodology:
  approach: "x"
  evidence: []
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
      reads: results.jsonl
      writes: verdicts.jsonl
benih:
  - name: w9
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {minutes: 1}
stop:
  "on": [all_exited]
"""

# Audit-fixture season template ({sid}): execute + evaluate, no reads.
# Audit fixtures never lint these yamls, so reads are irrelevant here.
S43W2_AUDIT_SEASON = """\
id: {sid}
goal: "fixture"
metric: "m"
mode: fight
methodology:
  approach: "x"
  evidence: []
  primary_change:
    type: add
    node: execute
    baseline: "b"
    expected_band: "WIN if x"
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
  - name: w1
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""

def _s43w2_audit_proj(tmp_path):
    """Audit fixture root: two musim seasons, s1 completed, rimba/s2 empty."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "akar").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S43W2_RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    for sid in ("s1", "s2"):
        (root / "musim" / f"{sid}.yaml").write_text(
            S43W2_AUDIT_SEASON.format(sid=sid), encoding="utf-8"
        )
    season = root / "rimba" / "s1"
    season.mkdir(parents=True)
    (season / "results.jsonl").write_text('{"n": 1}\n', encoding="utf-8")
    (season / "verdicts.jsonl").write_text('{"v": "WIN"}\n', encoding="utf-8")
    state = season / "_season"
    state.mkdir()
    (state / "state.json").write_text(
        json.dumps({"id": "s1", "status": "completed", "started_at": 1.0, "ended_at": 2.0}),
        encoding="utf-8",
    )
    (root / "rimba" / "s2").mkdir(parents=True)
    return root


def _s43w2_fresh_matrix(base, rows):
    """A fresh corpus matrix file under base from (script, verdict, line, note) tuples.

    Header matches audit._MATRIX_HEADER, which audit._parse_matrix requires.
    """
    base.mkdir(parents=True, exist_ok=True)
    lines = [
        "# s43 w2 fresh fixture matrix",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path = base / "replay-matrix.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _s43w2_write_proj(tmp_path, season_text):
    """Minimal lint fixture: .rumpun root, dummy prompt, one season s9."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S43W2_RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    season = root / "musim" / "s9.yaml"
    season.write_text(season_text, encoding="utf-8")
    return root, season


def _s43w2_coverage_rows(pass_n, skip_n, drift_n=0, fail_n=0):
    """Matrix rows: pass_n PASS + drift_n DRIFT + fail_n FAIL + skip_n SKIP.

    FAIL rows carry a REGRESSION note (house style for the FAIL/REGRESSION
    class); SKIP rows carry an explicit skip reason so the finding's SKIP
    count rests on honest rows.
    """
    rows = [
        (f"repro/pass_{i}.py", "PASS", "--", "exit 0; all-pass signature matched")
        for i in range(pass_n)
    ]
    rows += [
        (f"repro/drift_{i}.py", "DRIFT", "--", "assumption aged: provider renamed the endpoint")
        for i in range(drift_n)
    ]
    rows += [
        (f"repro/fail_{i}.py", "FAIL", "assert race (line 9)", "REGRESSION candidate")
        for i in range(fail_n)
    ]
    rows += [
        (f"repro/skip_{i}.py", "SKIP", "--", "no matching fixture on main")
        for i in range(skip_n)
    ]
    return rows

# --- s43 w2 pins: corpus coverage finding (fresh matrices) --------------------

def test_fresh_matrix_coverage_finding_counts_all_rows(tmp_path):
    """s43 pin 1 (red today): the standing coverage finding with both numbers.

    A fresh matrix (6 PASS, 47 SKIP = 53 discovered) must yield exactly one
    coverage finding line whose numbers cover every discovered script, not
    only the passing minority. Spec line shape:
    "corpus coverage: N repro scripts PASS of M discovered (K SKIP)".
    """
    root = _s43w2_audit_proj(tmp_path)
    fresh = _s43w2_fresh_matrix(tmp_path / "fresh", _s43w2_coverage_rows(6, 47))
    text = audit.run_audit(root, corpus_matrix=fresh).read_text(encoding="utf-8")
    coverage = [line for line in text.splitlines() if "coverage" in line]
    assert len(coverage) == 1, f"expected one coverage finding, got: {coverage}"
    assert coverage[0].startswith(
        "corpus coverage: 6 repro scripts PASS of 53 discovered (47 SKIP)"
    ), coverage[0]

def test_coverage_gap_is_finding_never_candidate(tmp_path):
    """s43 pin 2 (red today): the gap is a finding, never a candidate; recorded, not hidden.

    The 6/47 gap arms zero candidates (the candidates: none line stays), the
    finding is present, and the record never claims "all green on main"
    while 47 of 53 discovered scripts skip.
    """
    root = _s43w2_audit_proj(tmp_path)
    fresh = _s43w2_fresh_matrix(tmp_path / "fresh", _s43w2_coverage_rows(6, 47))
    text = audit.run_audit(root, corpus_matrix=fresh).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert candidates == []
    assert "candidates: none" in text
    coverage = [line for line in text.splitlines() if "coverage" in line]
    assert coverage, f"no coverage finding in:\n{text}"
    assert "all green on main" not in text, (
        "the record claims all green on main while 47 of 53 scripts skip"
    )
def test_coverage_zero_pass_is_honest(tmp_path):
    """s43 pin 3 (red today): the number is honest however low.

    0 PASS of 53 (53 SKIP) still yields the coverage finding reporting 0 —
    a zero-pass corpus is the honest floor, never suppressed.
    """
    root = _s43w2_audit_proj(tmp_path)
    fresh = _s43w2_fresh_matrix(tmp_path / "fresh", _s43w2_coverage_rows(0, 53))
    text = audit.run_audit(root, corpus_matrix=fresh).read_text(encoding="utf-8")
    coverage = [line for line in text.splitlines() if "coverage" in line]
    assert coverage, f"no coverage finding in:\n{text}"
    assert coverage[0].startswith(
        "corpus coverage: 0 repro scripts PASS of 53 discovered (53 SKIP)"
    ), coverage[0]

# --- s43 w2 pins: DRIFT mismatch arming ---------------------------------------
def test_drift_row_arms_mismatch_candidate_citing_script(tmp_path):
    """s43 pin 4 (red today): a DRIFT row arms one mismatch candidate.

    The drifted script and its note appear in the candidate line; DRIFT
    escapes the mismatch arming today (audit-32: 1 DRIFT, no candidate).
    """
    root = _s43w2_audit_proj(tmp_path)
    fresh = _s43w2_fresh_matrix(
        tmp_path / "fresh",
        _s43w2_coverage_rows(0, 0, drift_n=1),
    )
    text = audit.run_audit(root, corpus_matrix=fresh).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert len(candidates) == 1, candidates
    assert "repro/drift_0.py" in candidates[0]
    assert "provider renamed the endpoint" in candidates[0]
    assert "drift" in candidates[0].lower()
def test_drift_candidate_follows_regression_priority(tmp_path):
    """s43 pin 5 (red today): FAIL/REGRESSION keeps slot 1, the drift candidate follows.

    With one FAIL (REGRESSION note) and one DRIFT row, the corpus regression
    candidate is first and the drift candidate follows it, both ahead of the
    improvement triggers.
    """
    root = _s43w2_audit_proj(tmp_path)
    fresh = _s43w2_fresh_matrix(
        tmp_path / "fresh",
        _s43w2_coverage_rows(1, 0, drift_n=1, fail_n=1),
    )
    text = audit.run_audit(root, corpus_matrix=fresh).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert len(candidates) == 2, candidates
    assert "corpus regression" in candidates[0]
    assert "repro/fail_0.py" in candidates[0]
    assert "repro/drift_0.py" in candidates[1]
    assert "drift" in candidates[1].lower()
def test_drift_one_candidate_per_drifted_script(tmp_path):
    """s43 pin 6 (red today): one candidate per drifted script, before the cap.

    Two DRIFT rows arm two candidates, each citing its own script; the PASS
    row arms nothing.
    """
    root = _s43w2_audit_proj(tmp_path)
    fresh = _s43w2_fresh_matrix(
        tmp_path / "fresh",
        _s43w2_coverage_rows(1, 0, drift_n=2),
    )
    text = audit.run_audit(root, corpus_matrix=fresh).read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines() if line.startswith("candidate:")]
    assert len(candidates) == 2, candidates
    assert "repro/drift_0.py" in candidates[0]
    assert "repro/drift_1.py" in candidates[1]
    assert "drift" in candidates[1].lower()
def test_falsify_unreachable_reader_errors_naming_season_and_artifact(tmp_path):
    """s43 pin 7 (red today): the unreachable reader errors naming season and artifact.

    Under falsify_required, a season whose only reader reads an artifact
    nothing writes must error NAMING THE SEASON and the unreachable
    artifact. Today the DAG error ("node 'evaluate' reads ...: nothing
    writes it") names the artifact but never the season id, and the falsify
    gate check is never reached: the DAG error returns early.
    """
    season = S43W2_FALSIFY_SEASON.replace(
        "reads: results.jsonl", "reads: external_report.md"
    )
    _root, path = _s43w2_write_proj(tmp_path, season)
    findings = lint.lint(path)
    hits = [
        f
        for f in findings
        if f.severity == "error"
        and "s9" in f.message
        and "external_report.md" in f.message
    ]
    assert hits, (
        "no error names both the season s9 and external_report.md: "
        f"{[f.message for f in findings]}"
    )

def test_falsify_reachable_reader_passes(tmp_path):
    """s43 pin 8 (green-guard): the reachable reader passes; it must stay green.

    The lean shape (evaluate reads results.jsonl, which execute writes)
    carries zero errors today; the reachable-artifact rule must keep it
    that way.
    """
    _root, path = _s43w2_write_proj(tmp_path, S43W2_FALSIFY_SEASON)
    findings = lint.lint(path)
    errors = [f for f in findings if f.severity == "error"]
    assert errors == [], f"reachable reader errored: {[f.message for f in findings]}"
