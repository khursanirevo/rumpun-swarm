"""s79 w1 pins — issue #2: append_record citations lint cannot resolve.

Spec source: .rumpun/runs/s79/w1/prompt.md + the issue #2 text (the spec):
append_record must land each record where _citation_resolves scans, so a
freshly appended record's ledger:<id>@<sha256> citation resolves
immediately. Measured divergence (repro_issue2.py in the season workspace,
transcript in repro_out.txt): a project-dir root wrote <proj>/ledger/
while lint scanned .rumpun/ledger/ (the issue shape), and in a legacy
akar/-only state dir the first append stranded the legacy records'
citations (the legacy shape).

Fix contract these pins hold -- src/rumpun/paths.py only:

1. state_dir(root): root/.rumpun when root/.rumpun is a directory (the
   scaffold shape; the s79 w2 contract pin holds the post-init form
   without rumpun.yaml), else root; idempotent.
2. ledger_dir resolves over state_dir(root): a project-dir root and the
   state-dir root scan one tree; the legacy akar/ alias keeps resolving.
3. ledger_new writes into the tree the project actually has, over the
   anchored root: ledger/ wins, a legacy akar/-only tree keeps receiving
   the writes, a root with neither tree falls back to the new name.
4. End to end: append_record(project dir) lands in .rumpun/ledger/ and
   its citation resolves in a full rumpun lint over a probe season;
   append_record(state dir) in a legacy akar/ tree lands in akar/ and
   BOTH records' citations resolve; the well-formed state-dir path
   (record path, resolution, duplicate refusal, immutability) is
   unchanged.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Any

import pytest

from rumpun import akar, lint, paths, scaffold

logger = logging.getLogger(__name__)


def _s79w1_citation(record: Path) -> str:
    """The ledger:<id>@<sha256> citation a record backs (P11 shape)."""
    rid: str | None = None
    digest: str | None = None
    for line in record.read_text(encoding="utf-8").splitlines():
        if rid is None and line.startswith("id: "):
            rid = line[4:].strip()
        if line.startswith("sha256: "):
            digest = line[len("sha256: "):].strip()
    assert rid is not None and digest is not None, f"record {record} lacks id/sha256"
    return f"ledger:{rid}@{digest}"


def _s79w1_probe_season(project: Path, citation: str) -> Path:
    """The scaffolded s1 seed with goal/metric filled and one evidence cite."""
    s1 = (project / ".rumpun" / "seasons" / "s1.yaml").read_text(encoding="utf-8")
    assert s1.count('goal: ""') == 1 and s1.count('metric: ""') == 1
    assert s1.count("evidence: []") == 1
    text = s1.replace('goal: ""', 'goal: "s79 w1 issue #2 pin"')
    text = text.replace('metric: ""', "metric: probe_metric")
    text = text.replace("evidence: []", f"evidence:\n  - {citation}")
    probe = project / ".rumpun" / "seasons" / "probe.yaml"
    probe.write_text(text, encoding="utf-8")
    return probe


def test_s79w1_state_dir_descends_on_config_marker(tmp_path: Any) -> None:
    project = tmp_path / "proj"
    scaffold.init_project(project)
    state = project / ".rumpun"
    assert paths.state_dir(project) == state
    assert paths.state_dir(state) == state, "already-anchored root is unchanged"
    partial = tmp_path / "partial"
    (partial / ".rumpun" / "ledger").mkdir(parents=True)  # post-init, no rumpun.yaml
    assert paths.state_dir(partial) == partial / ".rumpun", "scaffold shape descends"
    bare = tmp_path / "bare"
    bare.mkdir()
    assert paths.state_dir(bare) == bare, "no .rumpun/rumpun.yaml: root as-is"


def test_s79w1_ledger_dir_scans_one_tree_from_both_roots(tmp_path: Any) -> None:
    project = tmp_path / "proj"
    scaffold.init_project(project)
    state = project / ".rumpun"
    assert paths.ledger_dir(project) == state / "ledger"
    assert paths.ledger_dir(state) == state / "ledger"
    legacy_root = tmp_path / "legacy"
    legacy_state = legacy_root / ".rumpun"
    legacy_state.mkdir(parents=True)
    (legacy_state / "rumpun.yaml").write_text("campaign:\n  goal: g\n", encoding="utf-8")
    (legacy_state / "akar").mkdir()
    assert paths.ledger_dir(legacy_root) == legacy_state / "akar"
    assert paths.ledger_dir(legacy_state) == legacy_state / "akar"


def test_s79w1_ledger_new_writes_into_scanned_tree(tmp_path: Any) -> None:
    project = tmp_path / "proj"
    scaffold.init_project(project)
    state = project / ".rumpun"
    assert paths.ledger_new(project) == state / "ledger"
    assert paths.ledger_new(state) == state / "ledger"
    legacy_root = tmp_path / "legacy"
    legacy_state = legacy_root / ".rumpun"
    legacy_state.mkdir(parents=True)
    (legacy_state / "rumpun.yaml").write_text("campaign:\n  goal: g\n", encoding="utf-8")
    (legacy_state / "akar").mkdir()
    assert paths.ledger_new(legacy_root) == legacy_state / "akar"
    assert paths.ledger_new(legacy_state) == legacy_state / "akar"
    bare = tmp_path / "bare"
    bare.mkdir()
    assert paths.ledger_new(bare) == bare / "ledger", "no tree: new-name fallback"


def test_s79w1_issue_repro_project_root_citation_resolves(tmp_path: Any) -> None:
    """The issue's literal repro, end to end through rumpun lint."""
    project = tmp_path / "proj"
    scaffold.init_project(project)
    state = project / ".rumpun"
    record = akar.append_record(project, "issue-rec", "issue repro", "body\n")
    assert record.parent == state / "ledger", "record must land where lint scans"
    citation = _s79w1_citation(record)
    assert lint._citation_resolves(citation, state)
    probe = _s79w1_probe_season(project, citation)
    findings = lint.lint(probe)
    errors = [f for f in findings if f.severity == "error"]
    assert errors == [], f"lint errors: {[f.message for f in errors]}"


def test_s79w1_legacy_append_keeps_legacy_citations(tmp_path: Any) -> None:
    project = tmp_path / "proj"
    scaffold.init_project(project)
    state = project / ".rumpun"
    shutil.rmtree(state / "ledger")
    akar_tree = state / "akar"
    akar_tree.mkdir()
    body = "legacy body\n"
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    (akar_tree / "2026-01-01_old-rec.md").write_text(
        "\n".join(
            [
                "# akar record: old-rec",
                "id: old-rec",
                "date: 2026-01-01",
                "title: legacy record",
                body,
                f"sha256: {digest}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    record = akar.append_record(state, "new-rec", "legacy control", "new body\n")
    assert record.parent == akar_tree, "writes stay in the tree the scans read"
    assert (akar_tree / "append.lock").exists()
    assert akar.find_record(state, "new-rec") == record
    assert akar.find_record(state, "old-rec") == akar_tree / "2026-01-01_old-rec.md"
    assert lint._citation_resolves(_s79w1_citation(record), state)
    assert lint._citation_resolves(f"ledger:old-rec@{digest}", state), (
        "the append must not strand the legacy citation"
    )


def test_s79w1_well_formed_state_root_unchanged(tmp_path: Any) -> None:
    project = tmp_path / "proj"
    scaffold.init_project(project)
    state = project / ".rumpun"
    record = akar.append_record(state, "ctl-rec", "state root", "body\n")
    assert record.parent == state / "ledger"
    citation = _s79w1_citation(record)
    assert lint._citation_resolves(citation, state)
    assert lint._citation_resolves(citation, project), "anchored scan agrees"
    before = record.read_text(encoding="utf-8")
    with pytest.raises(akar.AkarError):
        akar.append_record(state, "ctl-rec", "dup", "other body\n")
    assert record.read_text(encoding="utf-8") == before, "append-only holds"


def test_s79w1_append_record_bare_root_writes_match_scans(tmp_path: Any) -> None:
    bare = tmp_path / "bare"
    bare.mkdir()
    record = akar.append_record(bare, "bare-rec", "bare root", "body\n")
    assert record.parent == bare / "ledger", "no-tree fallback unchanged"
    assert akar.find_record(bare, "bare-rec") == record, "scans follow the write"
