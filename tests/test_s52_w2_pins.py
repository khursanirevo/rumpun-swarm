"""s52 w2 pins — mixed-matrix coverage arithmetic (additions-only vs the s43 contract).

s43 pins 1-3 (tests/test_s43_w2_pins.py — ratified, byte-identical contract)
demand the emission "corpus coverage: N repro scripts PASS of M discovered
(K SKIP)" for a fresh corpus matrix. audit-38 shows the gap on the real
ledger: 5 PASS, 97 SKIP reported as "all green on main, no candidates".
This file adds the mixed-matrix pin: the discovered denominator is the sum
of EVERY matrix row — PASS, FAIL, DRIFT, and SKIP alike — where the s43
fixtures were uniform (PASS + SKIP only). Red against current main (the
emission is absent); green at merge via w1's audit.py emission.

Grafting: drop this file into tests/ as-is. Helpers carry the _s52w2_
prefix, so nothing collides with existing defs. The pin calls run_audit
in-process — no subprocess, so no timeout to bound.
"""
import json

from rumpun import audit

S52W2_RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

# Audit-fixture season template ({sid}): execute + evaluate pipeline, the
# same shape the s43 audit fixtures use (audit never lints these yamls).
S52W2_AUDIT_SEASON = """\
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

S52W2_PASS_N = 3
S52W2_FAIL_N = 1
S52W2_DRIFT_N = 2
S52W2_SKIP_N = 40
S52W2_DISCOVERED = S52W2_PASS_N + S52W2_FAIL_N + S52W2_DRIFT_N + S52W2_SKIP_N


def _s52w2_audit_proj(tmp_path):
    """Audit fixture root: two musim seasons, s1 completed, rimba/s2 empty."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "akar").mkdir()
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S52W2_RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    for sid in ("s1", "s2"):
        (root / "musim" / f"{sid}.yaml").write_text(
            S52W2_AUDIT_SEASON.format(sid=sid), encoding="utf-8"
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


def _s52w2_fresh_matrix(base, rows):
    """A fresh corpus matrix file under base from (script, verdict, line, note) tuples.

    Header matches audit._MATRIX_HEADER, which audit._parse_matrix requires.
    """
    base.mkdir(parents=True, exist_ok=True)
    lines = [
        "# s52 w2 mixed fixture matrix",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    path = base / "replay-matrix.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _s52w2_mixed_rows():
    """3 PASS + 1 FAIL + 2 DRIFT + 40 SKIP; the FAIL row carries a REGRESSION note.

    House style per the s43 helpers: FAIL rows carry the REGRESSION note (the
    FAIL/REGRESSION class), SKIP rows carry an explicit skip reason, DRIFT
    notes carry no REGRESSION token.
    """
    rows = [
        (f"repro/pass_{i}.py", "PASS", "--", "exit 0; all-pass signature matched")
        for i in range(S52W2_PASS_N)
    ]
    rows += [
        ("repro/fail_0.py", "FAIL", "assert race (line 9)", "REGRESSION candidate")
        for _i in range(S52W2_FAIL_N)
    ]
    rows += [
        (f"repro/drift_{i}.py", "DRIFT", "--", "assumption aged: provider renamed the endpoint")
        for i in range(S52W2_DRIFT_N)
    ]
    rows += [
        (f"repro/skip_{i}.py", "SKIP", "--", "no matching fixture on main")
        for i in range(S52W2_SKIP_N)
    ]
    return rows


def test_mixed_matrix_coverage_finding_sums_all_verdicts(tmp_path):
    """s52 pin (red today): the discovered denominator sums EVERY verdict class.

    A fresh matrix mixing 3 PASS, 1 FAIL, 2 DRIFT, 40 SKIP (46 discovered)
    yields exactly one coverage finding counting all of them:
    "corpus coverage: 3 repro scripts PASS of 46 discovered (40 SKIP)".
    The finding coexists with the candidates the FAIL and DRIFT rows arm,
    and the record never claims "all green on main" while 43 of 46
    discovered scripts do not pass.
    """
    root = _s52w2_audit_proj(tmp_path)
    fresh = _s52w2_fresh_matrix(tmp_path / "fresh", _s52w2_mixed_rows())
    text = audit.run_audit(root, corpus_matrix=fresh).read_text(encoding="utf-8")
    coverage = [line for line in text.splitlines() if "coverage" in line]
    assert len(coverage) == 1, f"expected one coverage finding, got: {coverage}"
    assert coverage[0].startswith(
        "corpus coverage: 3 repro scripts PASS of 46 discovered (40 SKIP)"
    ), coverage[0]
    assert "all green on main" not in text, (
        f"record claims all green while {S52W2_DISCOVERED - S52W2_PASS_N} of "
        f"{S52W2_DISCOVERED} discovered scripts do not pass"
    )
    regression = [
        line
        for line in text.splitlines()
        if line.startswith("candidate:") and "corpus regression" in line
    ]
    assert len(regression) == 1, text
    assert "repro/fail_0.py" in regression[0], text
