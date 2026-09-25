#!/usr/bin/env python3
"""Cross-season repro corpus runner (s25 w1).

Closes the cross-season verification gap (akar audit-13: zero candidates,
backlog empty): every archived Python script under
.rumpun/akar/evidence/<season>/ is discovered, the six repro scripts among
them run once against the CURRENT repo src, and a markdown matrix
(replay-matrix.md) lands in the workspace for the harness to commit under
evidence.

Verdicts
    PASS    script exited 0 and printed its all-pass signature
    FAIL    script ran and reported a failing check. On main every
            reproduced defect has a landed fix (s18 warn gate, s18 H6,
            s19 H2+H3, s20 H5+H9, s22 M1+M5), so a red repro here is a
            REGRESSION candidate; the note column says so.
    DRIFT   the script's hardcoded assumptions no longer hold on main:
            imports of moved module internals, missing fixture paths, or
            the s22 scripts' exit-2 script-error convention.
    SKIP    discovered but not run, always with the reason.

Adapter table (how each corpus script is normalized to the current repo
src; the runner adapts, the scripts keep their meaning):

    s18/w1-h6-loop.py
        no args. The script itself inserts the repo src by absolute path
        (accepted drift risk: an absolute path hardcode). PASS signature:
        "both-appends-succeeded in 0 of 20" (akar H6: both succeeding is
        the silent-replacement signature; any other count is a REGRESSION
        candidate, timing-dependent).
    s18/w1-warn-repro.py
        needs PYTHONPATH=<repo>/src: it imports rumpun with no path setup
        of its own. PASS signature: a bare "PASS" stdout line
        (transition-gated WARNING + exactly one lane event, the s17 fix).
    s19/w1-repro-h2-h3.py
        expects a src/ directory NEXT TO ITSELF (scratch-tree layout:
        sys.path.insert(0, <script dir>/src)). The runner stages a copy of
        the script in a per-run temp dir with src/ symlinked to the repo
        src: the script's contract (import the tree under ./src) is
        preserved while that tree IS the current main checkout.
        PASS signature: "RESULT: H2=PASS H3=PASS".
    s20/w1-repro.py
        takes <src-dir> as argv[1]. The script ALWAYS exits 0 (its
        docstring: red FAIL lines are the evidence), so the verdict reads
        its verdict lines instead: PASS = a "verdicts:" summary printed
        and zero FAIL lines. Harvest/docstring alias: repro_h5_h9.py
        (H5 startup cleanup, H9 per-agent budgets).
    s22/w1-repro-m1.py
        takes <repo-root> as argv[1] and appends /src itself.
        Conventions: exit 0 green, 1 red, 2 script error (script error =
        DRIFT). PASS signature: "GREEN:".
    s22/w1-repro-m5.py
        same conventions as m1. PASS signature: "GREEN:".

Skip taxonomy (every other discovered .py; full coverage is enforced --
an unmatched script still emits a row marked UNCLASSIFIED):

    w[0-9]+-(scratch-)?engine.py   archived engine module copy
    w[0-9]+-cli.py                 archived cli module copy
    w[0-9]+-akar.py                archived akar module copy
    w[0-9]+-audit.py               archived audit module copy
    w[0-9]+-evolve.py              archived evolve module copy
    w[0-9]+-report.py              archived report module copy
    w[0-9]+-lint.py                archived lint module copy
    collab.py                      archived collab module copy
    (w[0-9]+-)?test_rumpun.py      archived pytest suite copy (binds to its
                                   scratch-tree src; not runnable as archived)
    calibrate_toolless.py          one-off harness calibration over the
                                   rimba/ agent.log snapshot; label set
                                   pinned at s14, not a repo-src repro
    w2-make_tests.py               test-file generator (writes a built test
                                   file into its own tree), not a repro
    w1-replay.py                   s16 scratch replay harness: loads engine
                                   copies from its workspace scratch/ and
                                   hardcoded .rumpun/rimba/s15 streams (now
                                   .gz) and writes replay-results.json next
                                   to itself; fixtures moved and a run would
                                   write outside this workspace

Runner rules honored here: stdlib only; logging (no print); subprocess
isolation per script (own process group, per-script timeout, cleanup in
finally); raw stdout/stderr go to log files, and the matrix/console surface
only verdict lines plus error-class tokens -- never script stderr content.

Usage:
    .venv/bin/python tools/replay_corpus.py [--only SUBSTR] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger("replay_corpus")

NOTE_MAX_CHARS = 200


@dataclass(frozen=True)
class Adapter:
    """How to run one archived repro script against the current repo src."""

    rel: str  # path relative to the evidence root
    alias: str  # name the script goes by in its season's notes/harvest
    arg_mode: str  # none | src_dir | repo_root
    pythonpath: str  # none | repo_src
    staging: str  # asis | copy_with_src_link
    pass_re: str  # all-pass signature, searched in stdout+stderr
    timeout_s: int = 120
    pass_summary_re: str = ""  # optional evidence line quoted in the note
    fail_hint_re: str = ""  # extra evidence when the pass signature misses
    fail_hint: str = ""  # template; {0} is the first regex group
    exit2_is_drift: bool = False  # s22 convention: exit 2 = script error


ADAPTERS: tuple[Adapter, ...] = (
    Adapter(
        rel="s18/w1-h6-loop.py",
        alias="h6_oldcode_loop",
        arg_mode="none",
        pythonpath="none",
        staging="asis",
        pass_re=r"both-appends-succeeded in 0 of 20",
        timeout_s=240,
        pass_summary_re=r"^unpatched akar: both-appends-succeeded.*$",
        fail_hint_re=r"both-appends-succeeded in (\d+) of 20",
        fail_hint=(
            "REGRESSION candidate (akar H6): race window observed in {0}/20"
            " barrier runs; timing-dependent, rerun before escalating"
        ),
    ),
    Adapter(
        rel="s18/w1-warn-repro.py",
        alias="warn_repro",
        arg_mode="none",
        pythonpath="repo_src",
        staging="asis",
        pass_re=r"(?m)^PASS\r?$",
        timeout_s=60,
    ),
    Adapter(
        rel="s19/w1-repro-h2-h3.py",
        alias="s19 scratch repro H2+H3",
        arg_mode="none",
        pythonpath="none",
        staging="copy_with_src_link",
        pass_re=r"RESULT: H2=PASS H3=PASS",
        timeout_s=120,
    ),
    Adapter(
        rel="s20/w1-repro.py",
        alias="repro_h5_h9",
        arg_mode="src_dir",
        pythonpath="none",
        staging="asis",
        pass_re=r"(?m)^.*\bverdicts: \S+=PASS.*$",
        timeout_s=300,
        pass_summary_re=r"(?m)^.*\bverdicts: .*$",
    ),
    Adapter(
        rel="s22/w1-repro-m1.py",
        alias="repro_m1_deterministic",
        arg_mode="repo_root",
        pythonpath="none",
        staging="asis",
        pass_re=r"GREEN:",
        timeout_s=120,
        exit2_is_drift=True,
    ),
    Adapter(
        rel="s22/w1-repro-m5.py",
        alias="repro_m5_failed_exit",
        arg_mode="repo_root",
        pythonpath="none",
        staging="asis",
        pass_re=r"GREEN:",
        timeout_s=300,
        exit2_is_drift=True,
    ),
)

ADAPTER_MAP = {a.rel: a for a in ADAPTERS}

SKIP_REASONS: tuple[tuple[str, str], ...] = (
    (r"^w[0-9]+-(scratch-)?engine\.py$",
     "archived engine module copy (its season's patched src), not a repro"),
    (r"^w[0-9]+-cli\.py$", "archived cli module copy, not a repro"),
    (r"^w[0-9]+-akar\.py$", "archived akar module copy, not a repro"),
    (r"^w[0-9]+-audit\.py$", "archived audit module copy, not a repro"),
    (r"^w[0-9]+-evolve\.py$", "archived evolve module copy, not a repro"),
    (r"^w[0-9]+-report\.py$", "archived report module copy, not a repro"),
    (r"^w[0-9]+-lint\.py$", "archived lint module copy, not a repro"),
    (r"^(w[0-9]+-)?collab\.py$", "archived collab module copy, not a repro"),
    (r"^(w[0-9]+-)?test_rumpun\.py$",
     "archived pytest suite copy; binds to its scratch-tree src"),
    (r"^calibrate_toolless\.py$",
     "one-off harness calibration over the rimba/ agent.log snapshot; label"
     " set pinned at s14, not a repo-src repro"),
    (r"^w2-make_tests\.py$",
     "test-file generator (writes a built test file), not a repro"),
    (r"^w1-replay\.py$",
     "s16 scratch replay harness: loads engine copies from its workspace"
     " scratch/ and hardcoded .rumpun/rimba/s15 streams (now .gz) and writes"
     " replay-results.json next to itself; fixtures moved and a run would"
     " write outside this workspace"),
)

UNCLASSIFIED_REASON = (
    "UNCLASSIFIED by runner adapter/skip tables; review before trusting"
    " this matrix"
)

DRIFT_RE = re.compile(
    r"^(Traceback|usage: )|"
    r"^\w*(?:ModuleNotFoundError|ImportError|AttributeError|TypeError|"
    r"NameError|KeyError|IndexError|ValueError)",
    re.M,
)

FAIL_LINE_RE = re.compile(r"\bFAIL\b|\bRED\b")

EXIT_TOKEN_RE = re.compile(r"(\w+(?:Error|Exception))\b")


@dataclass
class Row:
    """One matrix row."""

    rel: str
    verdict: str  # PASS | FAIL | DRIFT | SKIP
    first_fail: str
    note: str


def find_repo_root(start: Path) -> Path:
    """First ancestor of start holding src/rumpun (the repo root)."""
    for candidate in (start, *start.parents):
        if (candidate / "src" / "rumpun").is_dir():
            return candidate
    msg = f"no ancestor of {start} contains src/rumpun"
    raise SystemExit(msg)


def discover(evidence: Path) -> list[Path]:
    """Every .py directly under evidence/<season>/, sorted."""
    found: list[Path] = []
    for season_dir in sorted(evidence.iterdir()):
        if not season_dir.is_dir() or not re.fullmatch(r"s\d+", season_dir.name):
            continue
        found.extend(sorted(season_dir.glob("*.py")))
    return found


def git_state(repo: Path) -> str:
    """Short head sha and dirty flag, or an honest unknown."""
    try:
        sha = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=15,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True, text=True, check=True, timeout=15,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown (git unavailable)"
    return f"{sha[:12]} ({'dirty' if dirty else 'clean'} worktree)"


def _cell(text: str) -> str:
    """One markdown table cell: no raw pipes or newlines, bounded length."""
    flat = " ".join(text.split())
    if len(flat) > NOTE_MAX_CHARS:
        flat = flat[: NOTE_MAX_CHARS - 3] + "..."
    return flat.replace("|", "\\|")


def _first_line(output: str, pattern: str) -> str:
    match = re.search(pattern, output, re.M)
    return match.group(0).strip() if match else ""


def _drift_token(err: str) -> str:
    """Exception class from the last stderr line; a token, never content."""
    for line in reversed(err.strip().splitlines()):
        token = EXIT_TOKEN_RE.match(line.strip())
        if token:
            return token.group(1)
    return "unknown cause (see logs)"


def decide(
    adapter: Adapter, rc: int, out: str, err: str, timed_out: bool,
) -> tuple[str, str, str]:
    """(verdict, first failing line, note) from the captured streams."""
    combined = out + "\n" + err
    fail_lines = [line for line in combined.splitlines() if FAIL_LINE_RE.search(line)]
    first_fail = fail_lines[0].strip() if fail_lines else ""
    pass_hit = re.search(adapter.pass_re, combined)
    drift_hit = DRIFT_RE.search(err) or (
        DRIFT_RE.search(out) if pass_hit is None else None
    )

    if timed_out:
        return (
            "FAIL",
            first_fail,
            f"timeout after {adapter.timeout_s}s, process group killed;"
            " see logs",
        )
    if rc == 0 and pass_hit and not fail_lines:
        return "PASS", "", ""
    if adapter.exit2_is_drift and rc == 2:
        token = _drift_token(err) if drift_hit else "script-error convention"
        return "DRIFT", first_fail, f"exit 2 ({token}); assumption moved"
    if drift_hit and pass_hit is None and not fail_lines:
        return (
            "DRIFT",
            first_fail,
            f"assumption moved: {_drift_token(err)}; see logs",
        )
    if fail_lines:
        hint = ""
        if adapter.fail_hint_re:
            match = re.search(adapter.fail_hint_re, combined)
            if match:
                hint = " " + adapter.fail_hint.format(*match.groups())
        return (
            "FAIL",
            first_fail,
            f"REGRESSION candidate (fix landed on main); exit {rc};{hint} see logs",
        )
    if rc != 0:
        return (
            "FAIL",
            first_fail,
            f"nonzero exit {rc} without a verdict line; see logs",
        )
    hint = ""
    if adapter.fail_hint_re:
        match = re.search(adapter.fail_hint_re, combined)
        if match:
            hint = " " + adapter.fail_hint.format(*match.groups())
    return (
        "FAIL",
        first_fail,
        f"exited 0 without its all-pass signature;{hint} see logs",
    )


def run_one(adapter: Adapter, evidence: Path, repo: Path, logs_dir: Path) -> Row:
    """Run one corpus script in an isolated process group; classify it."""
    script = evidence / adapter.rel
    slug = adapter.rel.replace("/", "__")
    started = time.monotonic()
    staging = Path(tempfile.mkdtemp(prefix="replay-s25w1-"))
    timed_out = False
    try:
        env = dict(os.environ)
        if adapter.pythonpath == "repo_src":
            env["PYTHONPATH"] = str(repo / "src")
        target = script
        if adapter.staging == "copy_with_src_link":
            target = staging / script.name
            shutil.copyfile(script, target)
            os.symlink(repo / "src", staging / "src", target_is_directory=True)
        argv = [sys.executable, str(target)]
        if adapter.arg_mode == "src_dir":
            argv.append(str(repo / "src"))
        elif adapter.arg_mode == "repo_root":
            argv.append(str(repo))
        logger.info("running %s", adapter.rel)
        proc = subprocess.Popen(
            argv,
            cwd=str(staging),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            out, err = proc.communicate(timeout=adapter.timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGKILL)
            out, err = proc.communicate()
        rc = proc.returncode
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    duration = time.monotonic() - started

    (logs_dir / f"{slug}.out").write_text(out, encoding="utf-8")
    (logs_dir / f"{slug}.err").write_text(err, encoding="utf-8")

    verdict, first_fail, note = decide(adapter, rc, out, err, timed_out)
    summary_re_hit = ""
    if adapter.pass_summary_re:
        summary_re_hit = _first_line(out + "\n" + err, adapter.pass_summary_re)
    pass_summary = f"; measured: {_cell(summary_re_hit)}" if summary_re_hit else ""
    parts = [f"exit {rc} in {duration:.1f}s"]
    if adapter.staging == "copy_with_src_link":
        parts.append(
            "runner adaptation: staged copy with src/ symlinked to current"
            " repo src (script expects src/ next to itself)"
        )
    if adapter.alias:
        parts.append(f"aka {adapter.alias}")
    if verdict == "PASS":
        parts.append("all-pass signature matched" + pass_summary)
    parts.append(note)
    note = "; ".join(part for part in parts if part)

    logger.info("%s -> %s (%.1fs)", adapter.rel, verdict, duration)
    return Row(rel=adapter.rel, verdict=verdict, first_fail=first_fail, note=note)


def skip_row(rel: str, reason: str) -> Row:
    logger.info("skipping %s: %s", rel, reason)
    return Row(rel=rel, verdict="SKIP", first_fail="", note=reason)


def build_matrix(
    rows: list[Row], repo: Path, evidence: Path, run_started: str, elapsed: float,
) -> str:
    """The markdown matrix document."""
    counts = {
        verdict: sum(1 for row in rows if row.verdict == verdict)
        for verdict in ("PASS", "FAIL", "DRIFT", "SKIP")
    }
    lines = [
        "# s25 w1 -- cross-season replay matrix",
        "",
        f"- Ran at: {run_started} (UTC), wall {elapsed:.1f}s",
        f"- Repo: {repo} @ git {git_state(repo)}",
        f"- Discovery: {evidence}/<s*>/*.py, direct children",
        f"- Discovered {len(rows)} scripts:"
        f" {counts['PASS']} PASS, {counts['FAIL']} FAIL,"
        f" {counts['DRIFT']} DRIFT, {counts['SKIP']} SKIP",
        "- Raw streams per run: rimba/s25/w1/logs/<season>__<script>.out/.err",
        "- Verdicts: PASS = exit 0 + all-pass signature; FAIL = failing"
        " check (on main, every reproduced defect has a landed fix, so a"
        " red repro is a REGRESSION candidate); DRIFT = hardcoded"
        " assumption moved; SKIP = not run, reason in the note.",
        "",
        "| script | verdict | first failing line | note |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {_cell(row.rel)} | {row.verdict} | {_cell(row.first_fail) or '--'}"
            f" | {_cell(row.note)} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the archived repro corpus against the current repo src.",
    )
    parser.add_argument("--repo", type=Path, default=None, help="repo root")
    parser.add_argument("--evidence", type=Path, default=None, help="evidence root")
    parser.add_argument(
        "--out-dir", type=Path, default=None,
        help="workspace for replay-matrix.md and logs/ (default: tools/..)",
    )
    parser.add_argument("--only", default=None, help="substring filter on relpath")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    repo = args.repo or find_repo_root(Path(__file__).resolve())
    evidence = args.evidence or repo / ".rumpun" / "akar" / "evidence"
    out_dir = args.out_dir or Path(__file__).resolve().parent.parent
    logs_dir = out_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    run_started = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    clock = time.monotonic()
    rows: list[Row] = []
    for path in discover(evidence):
        rel = path.relative_to(evidence).as_posix()
        if args.only and args.only not in rel:
            continue
        adapter = ADAPTER_MAP.get(rel)
        if adapter is not None:
            rows.append(run_one(adapter, evidence, repo, logs_dir))
            continue
        rows.append(skip_row(rel, next(
            (reason for pattern, reason in SKIP_REASONS if re.search(pattern, path.name)),
            UNCLASSIFIED_REASON,
        )))
    if not rows:
        logger.warning("no scripts discovered under %s", evidence)
    elapsed = time.monotonic() - clock

    matrix = build_matrix(rows, repo, evidence, run_started, elapsed)
    matrix_path = out_dir / "replay-matrix.md"
    tmp = matrix_path.with_suffix(".md.tmp")
    tmp.write_text(matrix, encoding="utf-8")
    tmp.replace(matrix_path)
    logger.info("matrix written: %s", matrix_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
