"""s45 w2 pins — the English rename: yaml keys, citation prefix, scaffold output.

Spec-first pins (red against current code) for the s45 contract: the
operator's rename confirmation (akar/directives.jsonl seq 3), musim/s45.yaml
primary_change.expected_band, and the season's w1/w2 split (w2 owns the yaml
key renames, scaffold's new-name output, the citation prefix acceptance, the
glossary, and these pins; w1 owns the path renames in the other modules).
Spec, merge anchors, and the measured red set:
.rumpun/rimba/s45/w2/notes.md.

Grafting: land this file in tests/ as-is (additions-only; existing suite
files stay untouched). Every helper carries the _s45w2_ prefix, so nothing
collides with existing defs.

Alias rule under test: the new names lint clean AND the historical names
still do. Two pins are green guards (marked in their docstrings); the other
eight are red against current code (measured in notes.md).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from rumpun import akar, lint, scaffold

# --- shared fixtures ---------------------------------------------------------

S45W2_RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

# One variable: the writer-table key. The two fixtures are byte-identical
# except for {table} (writers: the renamed key; benih: the historical
# alias). The execute node's `agents: {table}` tracks the key so each
# fixture is internally consistent; the alias pins flip only the key.
S45W2_SEASON = """\
id: s9
goal: "fixture"
metric: m
mode: fight
methodology:
  approach: "x"
  evidence: [{evidence}]
  pipeline:
    - phase: execute
      primitive: execute
      agents: {table}
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
    - phase: evaluate
      primitive: evaluate
      agent: judge
      prompt: prompts/dev/dummy.md
      reads: results.jsonl
      writes: verdicts.jsonl
{table}:
  - name: w9
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited]
"""


def _s45w2_write_proj(tmp_path: Any, table: str, evidence: str = "") -> tuple[Any, Any]:
    """Minimal lint fixture: .rumpun root, dummy prompt, one season s9 whose
    writer table uses `table` (writers or benih) and whose single evidence
    citation is `evidence` (empty string -> no citations). Returns
    (project .rumpun root, season path). The writer-table key is the only
    delta between the two table spellings."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "musim").mkdir(parents=True)
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S45W2_RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    cited = f'"{evidence}"' if evidence else ""
    season = root / "musim" / "s9.yaml"
    season.write_text(
        S45W2_SEASON.format(table=table, evidence=cited), encoding="utf-8"
    )
    return root, season


def _s45w2_errors(findings: list[Any]) -> list[str]:
    """Error messages only (house lint.Finding shape: severity/message)."""
    return [
        finding.message
        for finding in findings
        if getattr(finding, "severity", None) == "error"
    ]


# --- pins 1-3: init scaffolds the new names -----------------------------------

def test_s45w2_init_scaffolds_seasons_and_ledger_dirs(tmp_path: Any) -> None:
    """s45 pin 1 (red today): init scaffolds seasons/ and ledger/, never musim/ or akar/.

    The operator's rename (directives.jsonl seq 3) makes seasons/ and
    ledger/ the emitted directory names; the old names must not appear in
    fresh scaffolds.
    """
    target = tmp_path / "proj"
    scaffold.init_project(target)
    r = target / ".rumpun"
    assert (r / "seasons" / "s1.yaml").is_file(), "init must scaffold seasons/s1.yaml"
    assert (r / "seasons" / "_template.yaml").is_file()
    assert (r / "ledger" / ".gitkeep").is_file()
    assert not (r / "musim").exists(), "init must not scaffold musim/ any more"
    assert not (r / "akar").exists(), "init must not scaffold akar/ any more"


def test_s45w2_init_templates_speak_the_new_names(tmp_path: Any) -> None:
    """s45 pin 2 (red today): the scaffolded templates carry the new names.

    s1.yaml declares its writer table under writers with agents: writers on
    the execute node and teaches the ledger: citation prefix; the template
    carries writers: []. No old key names remain in the emitted templates.
    """
    target = tmp_path / "proj"
    scaffold.init_project(target)
    s1 = (target / ".rumpun" / "seasons" / "s1.yaml").read_text(encoding="utf-8")
    assert "writers:" in s1
    assert "benih:" not in s1
    assert "agents: writers" in s1
    assert "ledger:" in s1
    template = (target / ".rumpun" / "seasons" / "_template.yaml").read_text(
        encoding="utf-8"
    )
    assert "writers: []" in template
    assert "benih" not in template


def test_s45w2_scaffolded_s1_lints_clean(tmp_path: Any) -> None:
    """s45 pin 3 (red today): the scaffolded s1 lints clean once filled.

    This is the rename's integration pin. The scaffold intentionally emits
    goal/metric as FILL placeholders (README first-season step 2), so the
    pin fills exactly those two fields and nothing else, then demands zero
    lint errors: the emitted writers table, agents: writers node, ledger:
    citation hint, and prompt paths must stand on their own.
    """
    target = tmp_path / "proj"
    scaffold.init_project(target)
    season = target / ".rumpun" / "seasons" / "s1.yaml"
    assert season.is_file(), "init must scaffold seasons/s1.yaml before it can lint"
    text = season.read_text(encoding="utf-8")
    assert 'goal: ""' in text and 'metric: ""' in text, (
        "the emitted s1 no longer carries FILL placeholders; rewrite this pin"
    )
    season.write_text(
        text.replace('goal: ""', 'goal: "fill"').replace('metric: ""', 'metric: "fill"'),
        encoding="utf-8",
    )
    findings = lint.lint(season)
    errors = _s45w2_errors(findings)
    assert errors == [], f"filled scaffolded s1 does not lint clean: {errors}"


# --- pins 4-7: the writer-table key and the agents value ----------------------


def test_s45w2_writers_keyed_season_lints_clean(tmp_path: Any) -> None:
    """s45 pin 4 (red today): a writers-keyed season lints with zero errors.

    The renamed writer table is fully valid on its own; today lint demands
    the benih key and rejects the season outright.
    """
    _root, season = _s45w2_write_proj(tmp_path, "writers")
    findings = lint.lint(season)
    errors = _s45w2_errors(findings)
    assert errors == [], f"writers-keyed season errored: {errors}"


def test_s45w2_benih_keyed_historical_season_still_lints_clean(tmp_path: Any) -> None:
    """s45 pin 5 (GREEN GUARD): the benih alias keeps working.

    A benih-keyed historical season (the 45 existing yamls) lints with zero
    errors today; the rename must keep it that way.
    """
    _root, season = _s45w2_write_proj(tmp_path, "benih")
    findings = lint.lint(season)
    errors = _s45w2_errors(findings)
    assert errors == [], f"benih-keyed historical season errored: {errors}"


def test_s45w2_both_writer_keys_declared_is_error(tmp_path: Any) -> None:
    """s45 pin 6 (red today): benih and writers together is an ambiguity error.

    Exactly one writer table may be declared; the error names both keys.
    Today lint ignores the stray writers key, so no such error exists.
    """
    _root, season = _s45w2_write_proj(tmp_path, "writers")
    text = season.read_text(encoding="utf-8")
    text += (
        "benih:\n"
        "  - name: b9\n"
        "    route: glm\n"
        "    knowledge: none\n"
        "    budget: {minutes: 1}\n"
    )
    season.write_text(text, encoding="utf-8")
    findings = lint.lint(season)
    ambiguity = [
        message
        for message in _s45w2_errors(findings)
        if "benih" in message and "writers" in message
    ]
    assert ambiguity, (
        f"no ambiguity error names both writer keys: {_s45w2_errors(findings)}"
    )


def test_s45w2_pipeline_agents_writers_value_accepted(tmp_path: Any) -> None:
    """s45 pin 7 (red today): agents: writers satisfies the agent requirement.

    The scaffold emits `agents: writers` on pipeline nodes (the renamed
    `agents: benih`); lint must accept both spellings. The fixture keeps the
    HISTORICAL benih table so the pipeline checks are actually reached
    (a writers-keyed table would trip the missing-key early return and mask
    the agents value); the agents value is the only new-name token here.
    Today only the old value passes, so the fixture draws 'needs agent or
    agents' errors.
    """
    _root, season = _s45w2_write_proj(tmp_path, "benih")
    text = season.read_text(encoding="utf-8").replace(
        "agents: benih", "agents: writers"
    )
    season.write_text(text, encoding="utf-8")
    findings = lint.lint(season)
    stale = [
        message
        for message in _s45w2_errors(findings)
        if "needs agent or agents" in message
    ]
    assert stale == [], f"agents: writers rejected on pipeline nodes: {stale}"


# --- pins 8-9: the citation prefix ---------------------------------------------


def test_s45w2_ledger_citation_resolves(tmp_path: Any) -> None:
    """s45 pin 8 (red today): a ledger:<id>@<digest> citation resolves.

    The record is the same append-only record akar.append_record writes;
    the ledger: prefix must reach it through the same record lookup and the
    same body-digest check as akar:. Today the citation regex admits only
    akar:, so the citation errors.
    """
    root, season = _s45w2_write_proj(
        tmp_path, "benih", evidence="ledger:w2-doc@" + hashlib.sha256(
            b"ledger prefix resolves against the same append-only records\n"
        ).hexdigest()
    )
    akar.append_record(
        root, "w2-doc", "w2 fixture",
        "ledger prefix resolves against the same append-only records\n",
    )
    findings = lint.lint(season)
    errors = _s45w2_errors(findings)
    assert errors == [], f"ledger: citation did not resolve: {errors}"


def test_s45w2_akar_citation_still_resolves(tmp_path: Any) -> None:
    """s45 pin 9 (GREEN GUARD): the akar: prefix keeps resolving.

    A historical akar:<id>@<digest> citation resolves today; the rename
    must keep it that way (the 45 historical seasons' citations).
    """
    digest = hashlib.sha256(
        b"ledger prefix resolves against the same append-only records\n"
    ).hexdigest()
    root, season = _s45w2_write_proj(tmp_path, "benih", evidence=f"akar:w2-doc@{digest}")
    akar.append_record(
        root, "w2-doc", "w2 fixture",
        "ledger prefix resolves against the same append-only records\n",
    )
    findings = lint.lint(season)
    errors = _s45w2_errors(findings)
    assert errors == [], f"akar: citation stopped resolving: {errors}"


# --- pin 10: the glossary -------------------------------------------------------


def _s45w2_repo_root() -> Any:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and
    grafted into tests/ (post-graft): both sit under the repo root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    return Path(__file__).resolve().parent.parent


def test_s45w2_glossary_exists_and_maps_every_renamed_term() -> None:
    """s45 pin 10 (red today): GLOSSARY.md exists at the repo root and maps
    every renamed term (old and new tokens both present) per the operator's
    glossary requirement (directives.jsonl seq 3)."""
    glossary = _s45w2_repo_root() / "GLOSSARY.md"
    assert glossary.is_file(), f"GLOSSARY.md must exist at the repo root: {glossary}"
    text = glossary.read_text(encoding="utf-8")
    renames = [
        ("benih", "writers"),
        ("musim/", "seasons/"),
        ("akar/", "ledger/"),
        ("rimba/", "runs/"),
        ("akar:", "ledger:"),
    ]
    missing = [
        f"{old} -> {new}"
        for old, new in renames
        if old not in text or new not in text
    ]
    assert missing == [], f"glossary missing renames: {missing}"
