"""s54 w2 pins — the rename finishes: writers key, English strings, drafts.

Spec-first pins (red against current code) for the s54 contract: the
season goal (seasons/s54.yaml) and the operator's rename confirmation
(ledger/directives.jsonl seq 3): the writer-table key is `writers` with
`benih` as a read alias, user-facing strings carry no benih/tuai/musim/
akar, and draft_next emits the new key. Spec, merge anchors, and the
measured red set: .rumpun/runs/s54/w2/notes.md.

Grafting: land this file in tests/ as-is (additions-only; existing suite
files stay untouched). Helpers carry the _s54w2_ prefix, so nothing
collides with existing defs.

Alias rule under test: the new names work AND the historical names keep
working. Three pins are green guards (marked in their docstrings); the
other five are red against current code (measured in notes.md).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from rumpun import akar, cli, engine, evolve, lint, paths, yamlio

# --- shared fixtures ---------------------------------------------------------

S54W2_BANNED = ("akar", "benih", "musim", "tuai")

S54W2_RUMPUN_YAML = """\
autonomy:
  stage: manual
  invariants: [goal_immutable, budget_cap, falsify_required]
routes:
  glm: "cat {prompt} | true"
"""

# One variable: the writer-table key spelling. The execute node's
# `agents: {table}` tracks the key so each fixture is internally
# consistent; the table (roster, routes, budgets) is byte-identical
# between the two spellings.
S54W2_SEASON = """\
id: {sid}
goal: "fixture"
metric: m
mode: fight
methodology:
  approach: "x"
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
  - name: alpha
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 2}}
  - name: beta
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 3}}
stop:
  "on": [all_exited]
"""

S54W2_DRAFT = """\
id: {sid}
goal: "draft fixture"
metric: m
mode: fight
methodology:
  approach: "x"
  pipeline:
    - phase: execute
      primitive: execute
      agents: {table}
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
{table}:
  - name: alpha
    route: glm
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 2}}
stop:
  "on": [all_exited]
"""


def _s54w2_proj(tmp_path: Any) -> Path:
    """A minimal rumpun project: .rumpun root, canonical seasons/ dir, dummy
    prompt, rumpun.yaml with the autonomy block and one instant-exit route."""
    root = tmp_path / "proj" / ".rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "prompts" / "dev").mkdir(parents=True)
    (root / "rumpun.yaml").write_text(S54W2_RUMPUN_YAML, encoding="utf-8")
    (root / "prompts" / "dev" / "dummy.md").write_text("prompt body\n", encoding="utf-8")
    return root


def _s54w2_season(root: Path, sid: str, table: str) -> Path:
    """Write seasons/<sid>.yaml with the writer table under `table`."""
    season = root / "seasons" / f"{sid}.yaml"
    season.write_text(S54W2_SEASON.format(sid=sid, table=table), encoding="utf-8")
    return season


def _s54w2_errors(findings: list[Any]) -> list[str]:
    """Error messages only (house lint.Finding shape: severity/message)."""
    return [
        finding.message
        for finding in findings
        if getattr(finding, "severity", None) == "error"
    ]


def _s54w2_banned(text: str) -> list[str]:
    """The legacy tokens present in `text`, sorted for stable messages."""
    return sorted(token for token in S54W2_BANNED if token in text)


def _s54w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and
    grafted into tests/ (post-graft): both sit under the repo root.
    """
    for ancestor in Path(__file__).resolve().parents:
        if (ancestor / "pyproject.toml").is_file():
            return ancestor
    raise AssertionError("no pyproject.toml above the pins file")


def _s54w2_env() -> dict[str, str]:
    """The subprocess env: repo src/ on PYTHONPATH ahead of any inherited value."""
    env = dict(os.environ)
    src = str(_s54w2_repo() / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src, existing]) if existing else src
    return env


def _s54w2_run(cwd: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """One bounded `python -m rumpun <argv>` subprocess from cwd."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "rumpun", *argv],
            cwd=str(cwd),
            env=_s54w2_env(),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"rumpun {' '.join(argv)} exceeded 120s") from exc


def _s54w2_help_texts() -> dict[str, str]:
    """Every parser's help text keyed by verb path (top parser included).

    Walks argparse's subparser choices recursively, so nested groups
    (season, evolve, plugin) are covered and no help string is missed.
    """
    collected: dict[str, str] = {}
    stack: list[tuple[str, argparse.ArgumentParser]] = [("", cli.build_parser())]
    while stack:
        prefix, node = stack.pop()
        collected[prefix or "rumpun"] = node.format_help()
        for action in node._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    stack.append((f"{prefix} {name}".strip(), sub))
    return collected


# --- pin 1: both spellings lint clean and start identically ------------------


def test_s54w2_writers_and_benih_lint_clean(tmp_path: Any) -> None:
    """s54 pin 1a (GREEN GUARD): writers-keyed and benih-keyed seasons lint
    with zero errors; the key is the only delta between the two fixtures."""
    root = _s54w2_proj(tmp_path)
    for table in ("writers", "benih"):
        season = _s54w2_season(root, "s91" if table == "writers" else "s92", table)
        errors = _s54w2_errors(lint.lint(season))
        assert errors == [], f"{table}-keyed season errored: {errors}"


def test_s54w2_writers_and_benih_start_identically(tmp_path: Any) -> None:
    """s54 pin 1b (GREEN GUARD): both spellings start identically — same
    roster, same budgets, all agents exited 0, both seasons completed."""
    root = _s54w2_proj(tmp_path)
    writers = _s54w2_season(root, "s91", "writers")
    benih = _s54w2_season(root, "s92", "benih")
    states = {
        table: engine.start_season(path, root)
        for table, path in (("writers", writers), ("benih", benih))
    }
    started: dict[str, dict[str, Any]] = {}
    for table, state in states.items():
        assert state["status"] == "completed", (
            f"{table}-keyed season ended {state['status']}: {state.get('error', '')}"
        )
        started[table] = state
    for field in ("budget_s",):
        assert started["writers"][field] == started["benih"][field], (
            f"budget differs between spellings: {started['writers'][field]} vs "
            f"{started['benih'][field]}"
        )
    for table, state in started.items():
        roster = {
            name: (snap["route"], snap["exit_code"], snap["state"])
            for name, snap in state["agents"].items()
        }
        started[table] = {"roster": roster, "budget_s": state["budget_s"]}
    assert started["writers"]["roster"] == started["benih"]["roster"], (
        "roster differs between spellings: "
        f"{started['writers']['roster']} vs {started['benih']['roster']}"
    )
    assert set(started["writers"]["roster"]) == {"alpha", "beta"}


# --- pin 2: the user-facing strings are English -------------------------------


def test_s54w2_help_has_no_legacy_tokens() -> None:
    """s54 pin 2a (red today): no benih/tuai/musim/akar survives in --help.

    Every parser's help text (top, verbs, nested groups) is swept. Red
    sources today: harvest help ("tuai: close a season into akar"), evolve
    approve help ("akar approval record"), evolve rollback help ("records
    in akar"), audit --last help ("musim seasons").
    """
    texts = _s54w2_help_texts()
    assert len(texts) >= 15, f"parser walk found only {len(texts)} parsers"
    offenders = {
        verb: found for verb, text in texts.items() if (found := _s54w2_banned(text))
    }
    assert offenders == {}, f"legacy tokens survive in --help: {offenders}"


def test_s54w2_harvest_help_names_the_ledger() -> None:
    """s54 pin 2b (red today): the harvest verb's help one-liner names the
    real record location (ledger/, where records land since the rename).
    The one-liner renders in the top-level --help verb list, which is
    where `rumpun --help` shows it."""
    line = next(
        line
        for line in _s54w2_help_texts()["rumpun"].splitlines()
        if line.strip().startswith("harvest")
    )
    assert "ledger" in line, f"harvest help line does not name ledger/: {line!r}"


def test_s54w2_evolve_reject_message_names_real_paths(tmp_path: Any) -> None:
    """s54 pin 2c (red today): `evolve reject` stderr names the real paths.

    The draft's real destination (seasons/rejected/<name>) and the real
    ledger record path must both appear, and the message must carry no
    legacy token. Red today: the message says "musim/rejected/" and
    "akar record" while the draft really moves to seasons/rejected/ and
    the record really lands in ledger/.
    """
    root = _s54w2_proj(tmp_path)
    draft = root / "seasons" / "s10.yaml"
    draft.write_text(S54W2_DRAFT.format(sid="s10", table="benih"), encoding="utf-8")
    result = _s54w2_run(tmp_path / "proj", ["evolve", "reject", str(draft)])
    err = result.stderr
    assert result.returncode == 0, f"evolve reject exited {result.returncode}: {err}"
    target = paths.seasons_dir(root) / "rejected" / draft.name
    assert target.is_file(), f"draft never reached the real destination: {target}"
    record = akar.declared_ids(root)["reject-s10"]
    assert str(target) in err, f"reject message misses the real target: {err}"
    assert str(record) in err, f"reject message misses the real record: {err}"
    assert _s54w2_banned(err) == [], f"reject stderr carries legacy tokens: {err}"


def test_s54w2_evolve_rollback_message_names_real_paths(tmp_path: Any) -> None:
    """s54 pin 2d (red today): `evolve rollback` stderr names the real paths.

    Same contract as the reject pin for an applied season: the real
    seasons/rejected/ destination and the real ledger record path appear,
    with no legacy token. Red today: "musim/rejected/; akar record".
    """
    root = _s54w2_proj(tmp_path)
    _s54w2_season(root, "s9", "benih")
    result = _s54w2_run(tmp_path / "proj", ["evolve", "rollback", "s9"])
    err = result.stderr
    assert result.returncode == 0, f"evolve rollback exited {result.returncode}: {err}"
    target = paths.seasons_dir(root) / "rejected" / "s9.yaml"
    assert target.is_file(), f"season never reached the real destination: {target}"
    record = akar.declared_ids(root)["rollback-s9"]
    assert str(target) in err, f"rollback message misses the real target: {err}"
    assert str(record) in err, f"rollback message misses the real record: {err}"
    assert _s54w2_banned(err) == [], f"rollback stderr carries legacy tokens: {err}"


# --- pin 3: back-compat is pinned, not implied --------------------------------


def test_s54w2_draft_next_emits_writers_for_benih_parent(tmp_path: Any) -> None:
    """s54 pin 3a (red today): draft_next emits the new key from an old key.

    The old key still reads: a benih-keyed historical parent drafts
    successfully (the draft exists, id s10, parent s9). The new key is
    what draft_next writes: the draft's writer table is keyed `writers:`
    with the parent's roster and budgets byte-identical, and the draft
    text carries no old-name spelling (no `benih:` key, no
    `agents: benih`) — the renamed schema fields speak the new names
    end to end. Red today: the verbatim copy carries the benih key.
    """
    root = _s54w2_proj(tmp_path)
    parent = _s54w2_season(root, "s9", "benih")
    parent_doc = yamlio.load(parent)
    draft = evolve.draft_next(root, parent)
    assert draft.is_file(), f"draft_next wrote nothing at {draft}"
    text = draft.read_text(encoding="utf-8")
    doc = yamlio.load(draft)
    assert doc["id"] == "s10" and doc["parent"] == "s9", f"draft ids wrong: {doc['id']}"
    assert doc["writers"] == parent_doc["benih"], (
        f"roster/budgets changed in the draft: {doc['writers']} vs "
        f"{parent_doc['benih']}"
    )
    assert "writers:" in text, f"draft never names the writers key: {text!r}"
    assert "benih:" not in text, f"draft carries the old table key: {text!r}"
    assert "agents: benih" not in text, f"draft carries agents: benih: {text!r}"


def test_s54w2_draft_next_keeps_writers_for_writers_parent(tmp_path: Any) -> None:
    """s54 pin 3b (GREEN GUARD): a writers-keyed parent drafts a
    writers-keyed draft with the roster and budgets unchanged."""
    root = _s54w2_proj(tmp_path)
    parent = _s54w2_season(root, "s9", "writers")
    parent_doc = yamlio.load(parent)
    draft = evolve.draft_next(root, parent)
    text = draft.read_text(encoding="utf-8")
    doc = yamlio.load(draft)
    assert doc["writers"] == parent_doc["writers"], (
        f"roster/budgets changed in the draft: {doc['writers']} vs "
        f"{parent_doc['writers']}"
    )
    assert _s54w2_banned(text) == [], f"draft carries legacy tokens: {text}"
