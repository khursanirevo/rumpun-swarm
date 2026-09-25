"""s117 w2 pins - the replay matrix classifies its skips.

Spec source: the s117 w2 brief; the decade-6 review residual, verbatim:
"replay-matrix.md runs five scripts and skips 140, including unclassified
replacements. Historical replay coverage remains incomplete." Ground truth
measured 2026-09-20: the s25-era matrix and the verb's tables stop at the
s25-era corpus; everything newer (landed tool copies, season pins scripts,
one-off probes) emitted as a blanket-UNCLASSIFIED SKIP row.

The contract these pins hold, over the REAL verb (tools/replay_corpus.py)
and the REAL committed matrix (replay-matrix.md at the repo root), no
fixtures:
1. the verb's tables classify every script today's discover() yields --
   an adapter (run), a replacement target, or a skip reason; nothing
   falls through (the verb exits nonzero naming the gap instead of
   emitting an UNCLASSIFIED row);
2. the s48 re-seal repro is a run adapter and its matrix row reads PASS
   (measured 2026-09-20: GREEN: 23/23 checks passed, 0.8s solo);
3. the matrix document classifies every row: run / skip (named reason) /
   replacement-of (note names the covering script, and that script exists
   on disk); the row set equals discover()'s set;
4. the header counts and the class summary match the parsed rows.

Color history (the s92 evidence-trail convention):
- RED captured 2026-09-20 on the pre-classification tree (the verb's
  tables leave the post-s25 scripts unclassified; the committed matrix
  carries UNCLASSIFIED rows and no class summary);
  /tmp/s117-w2-pins-red.txt.
- GREEN captured 2026-09-20 post-classification;
  /tmp/s117-w2-pins-green.txt.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

_MATRIX_HEADER = "| script | verdict | first failing line | note |"


def _s117w2_repo() -> Path:
    """First ancestor holding src/rumpun + tools/replay_corpus.py."""
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "src" / "rumpun").is_dir() and (
            candidate / "tools" / "replay_corpus.py"
        ).is_file():
            return candidate
    msg = "no ancestor of the pins file holds src/rumpun + tools/replay_corpus.py"
    raise AssertionError(msg)


REPO = _s117w2_repo()
EVIDENCE = REPO / ".rumpun" / "ledger" / "evidence"
MATRIX = REPO / "replay-matrix.md"


def _s117w2_verb():
    """The real corpus verb, imported from tools/ by path."""
    spec = importlib.util.spec_from_file_location(
        "s117_replay_corpus", REPO / "tools" / "replay_corpus.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass resolution needs the registration
    spec.loader.exec_module(module)
    return module


def _s117w2_rows(path: Path) -> dict[str, tuple[str, str]]:
    """script -> (verdict, note), mirroring the audit's committed parse."""
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        head = lines.index(_MATRIX_HEADER)
    except ValueError:
        return {}
    rows: dict[str, tuple[str, str]] = {}
    for line in lines[head + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 5 or cells[0] or cells[-1]:
            continue
        script, verdict, _first_fail, note = (
            cell.replace("\\|", "|") for cell in cells[1:5]
        )
        if script and verdict:
            rows[script] = (verdict, note)
    return rows


def _s117w2_class_of(verdict: str, note: str) -> str:
    """The class a matrix row carries, per the verb's emission rules."""
    if verdict in {"PASS", "FAIL", "DRIFT"}:
        return "run"
    if note.startswith("replacement-of: "):
        return "replacement-of"
    return "skip"


def _s117w2_target_exists(repo: Path, target: str) -> bool:
    """A replacement target on disk: evidence/... under the ledger, else repo."""
    if target.startswith("evidence/"):
        return (repo / ".rumpun" / "ledger" / target).is_file()
    return (repo / target).is_file()


def test_s117w2_verb_tables_classify_real_discovery():
    """Pin 1: the verb's tables classify every script discover() yields.

    Red pre-fix: the post-s25 evidence scripts (landed tool copies, season
    pins scripts, one-off probes) match no table. The verb's own rule is
    the discovery walk; the pin reuses it verbatim.
    """
    verb = _s117w2_verb()
    rels = [
        path.relative_to(EVIDENCE).as_posix() for path in verb.discover(EVIDENCE)
    ]
    assert rels, "empty corpus discovery"
    unclassified = [
        rel
        for rel in rels
        if rel not in verb.ADAPTER_MAP
        and rel not in verb.REPLACEMENTS
        and not any(re.search(pat, rel.rsplit("/", 1)[-1]) for pat, _ in verb.SKIP_REASONS)
    ]
    assert not unclassified, (
        "corpus scripts no verb table classifies (the verb would exit "
        f"nonzero): {sorted(unclassified)}"
    )


def test_s117w2_reseal_repro_is_a_run_class_pass():
    """Pin 2: the s48 re-seal repro runs in the corpus and passes on main.

    Red pre-fix: no s48 adapter (the row was an UNCLASSIFIED SKIP).
    """
    verb = _s117w2_verb()
    assert "s48/w1-repro.py" in verb.ADAPTER_MAP, sorted(verb.ADAPTER_MAP)
    rows = _s117w2_rows(MATRIX)
    assert rows, f"no parsable matrix table at {MATRIX}"
    verdict, note = rows["s48/w1-repro.py"]
    assert verdict == "PASS", (verdict, note)


def test_s117w2_real_matrix_classifies_every_row():
    """Pin 3: the matrix document classifies every row it carries.

    Row set equals discover()'s set (a stale matrix reds), no UNCLASSIFIED
    token survives, every SKIP note names its reason, and every
    replacement-of note names a script that exists on disk.
    """
    verb = _s117w2_verb()
    text = MATRIX.read_text(encoding="utf-8")
    assert "UNCLASSIFIED" not in text, "the matrix still carries UNCLASSIFIED rows"
    rows = _s117w2_rows(MATRIX)
    assert rows, f"no parsable matrix table at {MATRIX}"
    discovered = {
        path.relative_to(EVIDENCE).as_posix() for path in verb.discover(EVIDENCE)
    }
    assert set(rows) == discovered, (
        "matrix rows diverge from discovery: "
        f"missing from matrix: {sorted(discovered - set(rows))}; "
        f"stale rows: {sorted(set(rows) - discovered)}"
    )
    bad_reasons: list[str] = []
    bad_targets: list[str] = []
    for script, (verdict, note) in sorted(rows.items()):
        if _s117w2_class_of(verdict, note) != "skip":
            continue
        if note.startswith("replacement-of: "):
            target = note.removeprefix("replacement-of: ").split(" ", 1)[0]
            if not _s117w2_target_exists(REPO, target):
                bad_targets.append(f"{script} -> {target}")
        elif not note or "UNCLASSIFIED" in note:
            bad_reasons.append(script)
    assert not bad_targets, f"replacement targets missing on disk: {bad_targets}"
    assert not bad_reasons, f"skip rows without a named reason: {bad_reasons}"


def test_s117w2_header_counts_match_rows():
    """Pin 4: the header's discovered count and class summary match the rows."""
    text = MATRIX.read_text(encoding="utf-8")
    rows = _s117w2_rows(MATRIX)
    assert rows, f"no parsable matrix table at {MATRIX}"
    discovered_match = re.search(r"^- Discovered (\d+) scripts:", text, re.M)
    assert discovered_match, "no Discovered line in the matrix header"
    assert int(discovered_match.group(1)) == len(rows), (
        f"header claims {discovered_match.group(1)} discovered, "
        f"table carries {len(rows)} rows"
    )
    counts = {"run": 0, "skip": 0, "replacement-of": 0}
    for verdict, note in rows.values():
        counts[_s117w2_class_of(verdict, note)] += 1
    classes_match = re.search(
        r"^- Classes: (\d+) run, (\d+) skip, (\d+) replacement-of$", text, re.M
    )
    assert classes_match, "no Classes summary line in the matrix header"
    claimed = {
        "run": int(classes_match.group(1)),
        "skip": int(classes_match.group(2)),
        "replacement-of": int(classes_match.group(3)),
    }
    assert claimed == counts, f"class summary {claimed} != parsed {counts}"
