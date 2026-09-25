"""s65 w2 pins — spec-first pins for the containment gate.

Spec-first pins for the s65 containment contract (w1 brief
.rumpun/runs/s65/w1/prompt.md; ledger anchors s64-harvest, check-s63,
usefulness-decade-5 — decade-5's containment residual is the gap this
season lands: "Artifact-check refusal or DELTA leaves WIN intact. The
brief does not establish mandatory containment before subsequent
work."). Spec anchors, the measured red set, and fixture-shape
assumptions: .rumpun/runs/s65/w2/notes.md.

Contract these pins hold — `rumpun season start` is the containment
gate. The start reads the newest check-<sid> ledger record for the
campaign's previous closed season; a DELTA verdict blocks the start
(refusal exit, the record named in the message); the block releases on
a later VERIFIED check record for that season or on a ledger waiver
record naming the check; a campaign with no check records at all
starts normally. Every pin runs the real CLI as a bounded subprocess
(S65W2_TIMEOUT = 240s, the task bound) over a throwaway tmp .rumpun
campaign whose one writer route is a stub that exits 0 instantly: no
real model route is ever spawned, and no pin touches the real repo,
the real ledger, or akar.

1. The block: a DELTA check record as the newest check for the previous
   closed season refuses `season start` nonzero, naming the record.
2. The releases: a later VERIFIED check record for that season releases
   the block, and a ledger waiver record naming the check releases it
   too — both starts succeed.
3. Clean campaigns start normally: a closed previous season with zero
   check records and a fresh campaign with nothing closed at all both
   start (first seasons are never gated).

Red history (measured 2026-09-16; logs /tmp/s65w2-pytest-run*.log):
w1's gate landed in the worktree during pin authoring, so run1 already
ran against it: pins 1 and 3 passed (the refusal names check-s650;
clean campaigns start), pin 2 failed on a fixture-shape mismatch — my
rerun was a re-dated same-id record, the landed gate takes the
suffixed rerun id and correctly kept the block. Fixtures reconciled
to the landed shapes; run2: 3 passed in 5.57s. The pre-landing red
(pin 1 against a gateless tree) was never measured: w1 landed first.

Grafting: drop this file into tests/ as the season's pins file.
Helpers carry the _s65w2_ prefix, so nothing collides with existing
defs. Fixture-shape assumptions the harness reconciles at merge:
(a) check records carry the real corpus shape — date-stamped filename
<date>_check-<sid>.md, four header lines with id check-<sid>, a
season line, a verdict line DELTA|VERIFIED (real corpus:
.rumpun/ledger/2026-09-16_check-s63.md); the newest check is max by
(filename date prefix, id) over check-<sid> and the suffixed reruns
check-<sid>-<rerun> (engine.newest_check_record), so the pin's later
VERIFIED check appends under the rerun id check-s650-2 — a rerun
cannot reuse the base id (the akar discipline refuses a duplicate id
and the checker refuses an existing check-<sid> file); (b) the waiver
record is id waiver-<sid> or the waiver:<sid> alias
(engine.has_waiver), appended through the landed 'rumpun waive' verb,
which the pin drives end to end; (c) the previous season is the
newest closed season below sid in sN order
(engine._prev_closed_season; the fixture drafts exactly s650 and
s651, s651 parent s650).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

S65W2_TIMEOUT = 240  # bounds one CLI subprocess (the task bound)
S65W2_PREV = "s650"  # the fixture campaign's previous (closed) season
S65W2_NEXT = "s651"  # the fixture season the pins start
S65W2_CHECK = "check-s650"  # the previous close's check record id
S65W2_COMMIT = "a1b2c3d4e5" * 4  # 40-hex fixture close commit

S65W2_PC = (
    "  primary_change:\n"
    "    type: add\n"
    "    node: execute\n"
    '    baseline: "the loop rolls past an unresolved close-check delta"\n'
    '    expected_band: "WIN if the containment gate binds"\n'
    '    rollback: "git revert the s65 commits"\n'
    '    eval_window: "w2 pins"\n'
)

S65W2_SEASON = """\
id: {sid}
{parent}goal: "fixture season for the s65 containment pins"
metric: "m"
mode: fight
methodology:
  approach: "stub close for the containment fixture"
  evidence: []
{pc}  pipeline:
    - phase: execute
      primitive: execute
      agents: benih
      prompt: prompts/dev/dummy.md
      writes: results.jsonl
      reads: results.jsonl
writers:
  - name: w1
    route: stub
    prompt: prompts/dev/dummy.md
    knowledge: none
    budget: {{minutes: 1}}
stop:
  "on": [all_exited, {{stall_minutes: 0.1}}]
"""


def _s65w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _s65w2_campaign(tmp_path: Path, tag: str) -> tuple[Path, Path, Path]:
    """One throwaway two-season campaign; (root, prev_yaml, next_yaml).

    The only route is a stub that exits 0 instantly, so a start closes
    in one watcher cycle with no model quota and no network. The two
    season yamls differ only in id/parent/primary_change (lint needs
    primary_change on the non-seed season; the falsify invariant is
    met by the self-read on results.jsonl).
    """
    root = tmp_path / tag / "proj" / ".rumpun"
    for sub in ("seasons", "ledger", "runs", "prompts/dev"):
        (root / sub).mkdir(parents=True)
    (root / "prompts" / "dev" / "dummy.md").write_text(
        "prompt body\n", encoding="utf-8",
    )
    (root / "rumpun.yaml").write_text(
        "autonomy:\n"
        "  stage: manual\n"
        "  invariants: [goal_immutable, budget_cap, falsify_required]\n"
        "routes:\n"
        "  stub: 'true'\n",
        encoding="utf-8",
    )
    prev_yaml = root / "seasons" / f"{S65W2_PREV}.yaml"
    prev_yaml.write_text(
        S65W2_SEASON.format(sid=S65W2_PREV, parent="", pc=""), encoding="utf-8",
    )
    next_yaml = root / "seasons" / f"{S65W2_NEXT}.yaml"
    next_yaml.write_text(
        S65W2_SEASON.format(sid=S65W2_NEXT, parent=f"parent: {S65W2_PREV}\n", pc=S65W2_PC),
        encoding="utf-8",
    )
    return root, prev_yaml, next_yaml


def _s65w2_akar(path: Path, record_id: str, date: str, title: str, body: list[str]) -> None:
    """One sha-sealed ledger record in the real corpus shape.

    Four header lines, the body, then a final sha256 line digesting the
    body exactly (the akar.append_record layout; lint's citation rule
    reads that layout). Nothing here writes outside the fixture tree.
    """
    header = [
        f"# akar record: {record_id}",
        f"id: {record_id}",
        f"date: {date}",
        f"title: {title}",
    ]
    digest = hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()
    path.write_text("\n".join(header + body + [f"sha256: {digest}"]) + "\n", encoding="utf-8")


def _s65w2_check(
    root: Path, verdict: str, date: str, record_id: str | None = None,
) -> Path:
    """One check record in the landed corpus shape: base id check-<prev>, or
    the check-<prev>-<rerun> suffixed id for a rerun (the landed rerun
    convention: the akar discipline refuses a duplicate id and the checker
    refuses an existing check-<sid> file, so a rerun appends suffixed)."""
    rid = record_id or S65W2_CHECK
    path = root / "ledger" / f"{date}_{rid}.md"
    _s65w2_akar(
        path, rid, date,
        f"independent artifact check {S65W2_PREV} @ {S65W2_COMMIT[:12]} ({verdict})",
        [
            f"season: {S65W2_PREV}",
            f"close-commit: {S65W2_COMMIT}",
            f"verdict: {verdict}",
        ],
    )
    return path


def _s65w2_waiver(tmp_path: Path, root: Path) -> None:
    """The operator release through the landed 'rumpun waive' verb.

    Appends the sha-sealed waiver-s650 record (append-only,
    duplicate-refusing) into the fixture ledger; --reason is recorded
    verbatim. The reason names the released check record, so the record
    names the check in its body and the season in its id.
    """
    proc = _s65w2_cli(
        tmp_path, "waive", S65W2_PREV, "--reason", f"operator releases {S65W2_CHECK}",
        cwd=root.parent,
    )
    assert proc.returncode == 0, (
        f"fixture defect: 'rumpun waive' failed; the release pin would red "
        f"for the wrong reason\nstderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )


def _s65w2_cli(
    tmp_path: Path, *argv: str, cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """One bounded rumpun CLI subprocess (240s cap); PYTHONPATH pins repo src.

    cwd points at the fixture proj dir when the verb resolves the campaign
    from cwd ('rumpun waive'); the default tmp_path keeps every other call
    outside the campaign.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_s65w2_repo() / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "rumpun", *argv], cwd=str(cwd) if cwd else str(tmp_path),
        capture_output=True, text=True, timeout=S65W2_TIMEOUT, check=False,
    )


def _s65w2_start(tmp_path: Path, season: Path) -> subprocess.CompletedProcess[str]:
    """A start that must succeed; stderr/stdout ride the error message."""
    proc = _s65w2_cli(tmp_path, "season", "start", str(season))
    assert proc.returncode == 0, (
        f"season start exit {proc.returncode}; the fixture campaign must start\n"
        f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )
    return proc


def _s65w2_completed(tmp_path: Path, root: Path, sid: str) -> None:
    """A start that must succeed AND persist status completed.

    The rc assert alone could pass on a refusal-shaped success; the
    persisted state names the real terminal status.
    """
    proc = _s65w2_start(tmp_path, root / "seasons" / f"{sid}.yaml")
    state_path = root / "runs" / sid / "_season" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state.get("status") == "completed", (
        f"season {sid} persisted {state.get('status')!r}, not completed; "
        f"stderr:\n{proc.stderr}"
    )


def _s65w2_lint_ok(tmp_path: Path, season: Path) -> None:
    """Fixture sanity: the season lints clean BEFORE any gate step.

    A lint refusal would exit nonzero without naming the record, and an
    exit-0 release pin would red for the wrong reason; this isolates
    fixture validity from gate behavior in both directions.
    """
    proc = _s65w2_cli(tmp_path, "lint", str(season))
    assert proc.returncode == 0, (
        f"fixture defect: {season.name} does not lint clean; the pin would "
        f"red for the wrong reason\nstderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    )


# --- pin 1: the block ---------------------------------------------------------------


def test_s65w2_delta_check_blocks_the_next_start(tmp_path: Path) -> None:
    """A DELTA check record as the newest check refuses the start, naming it.

    The fixture closes s650 through the real engine (the stub writer
    exits 0), writes one DELTA check-s650 record dated after the close,
    and starts s651. The gate must refuse nonzero and name the record.
    On a tree without the gate the start runs the stub and exits 0 —
    the decade-5 gap verbatim; this pin is the red the landing must
    turn green.
    """
    root, _prev, nxt = _s65w2_campaign(tmp_path, "delta-block")
    _s65w2_lint_ok(tmp_path, nxt)
    _s65w2_completed(tmp_path, root, S65W2_PREV)
    _s65w2_check(root, "DELTA", "2026-09-15")
    proc = _s65w2_cli(tmp_path, "season", "start", str(nxt))
    combined = proc.stdout + "\n" + proc.stderr
    assert proc.returncode != 0, (
        f"the containment gate must refuse: season start exited 0 over an "
        f"unresolved DELTA {S65W2_CHECK} record (no gate on this tree?). "
        f"output:\n{combined}"
    )
    assert S65W2_CHECK in combined, (
        f"the refusal must name the record {S65W2_CHECK}; output:\n{combined}"
    )
    logger.info(
        "pin 1 held: season start refused over the DELTA %s record, record named",
        S65W2_CHECK,
    )


# --- pin 2: the releases ------------------------------------------------------------


def test_s65w2_verified_and_waiver_release_the_block(tmp_path: Path) -> None:
    """A later VERIFIED check releases; a waiver naming the season releases.

    Arm a: DELTA check-s650 (2026-09-15), then a later VERIFIED rerun
    record check-s650-2 (2026-09-16) — the landed rerun convention: a
    rerun appends under a suffixed id (the akar discipline refuses a
    duplicate id), and newest = max by (date prefix, id), so a rerun
    can never be shadowed by the base record. The newest check stands
    VERIFIED, so s651 starts and completes. Arm b: fresh fixture, the
    DELTA stands and the operator appends the waiver-s650 record
    through the landed 'rumpun waive' verb (sha-sealed, append-only,
    --reason recorded verbatim) — the explicit release, so s651 starts
    and completes. These arms bind the gate the merge must not
    overblock.
    """
    root_a, _prev_a, nxt_a = _s65w2_campaign(tmp_path, "release-verified")
    _s65w2_lint_ok(tmp_path, nxt_a)
    _s65w2_completed(tmp_path, root_a, S65W2_PREV)
    _s65w2_check(root_a, "DELTA", "2026-09-15")
    _s65w2_check(root_a, "VERIFIED", "2026-09-16", f"{S65W2_CHECK}-2")
    _s65w2_completed(tmp_path, root_a, S65W2_NEXT)

    root_b, _prev_b, nxt_b = _s65w2_campaign(tmp_path, "release-waiver")
    _s65w2_lint_ok(tmp_path, nxt_b)
    _s65w2_completed(tmp_path, root_b, S65W2_PREV)
    _s65w2_check(root_b, "DELTA", "2026-09-15")
    _s65w2_waiver(tmp_path, root_b)
    _s65w2_completed(tmp_path, root_b, S65W2_NEXT)
    logger.info(
        "pin 2 held: the VERIFIED rerun and the waiver record both release the block"
    )


# --- pin 3: clean campaigns ---------------------------------------------------------


def test_s65w2_clean_campaigns_start_normally(tmp_path: Path) -> None:
    """No check records anywhere is never a block.

    Arm a: the previous season closed completed and the ledger holds
    zero check records — the common clean path starts normally. Arm b:
    a fresh campaign, nothing closed yet, the first season starts
    (first seasons are never gated). These arms bind the gate the
    merge must not overblock.
    """
    root_a, _prev_a, _nxt_a = _s65w2_campaign(tmp_path, "clean-closed")
    _s65w2_lint_ok(tmp_path, _nxt_a)
    _s65w2_completed(tmp_path, root_a, S65W2_PREV)
    _s65w2_completed(tmp_path, root_a, S65W2_NEXT)

    root_b, _prev_b, nxt_b = _s65w2_campaign(tmp_path, "clean-fresh")
    _s65w2_lint_ok(tmp_path, nxt_b)
    _s65w2_completed(tmp_path, root_b, S65W2_PREV)
    logger.info("pin 3 held: clean closed campaign and fresh campaign both start")
