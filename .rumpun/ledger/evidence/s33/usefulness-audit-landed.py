#!/usr/bin/env python3
"""Decadal usefulness audit (s33 w1).

Every ten musim seasons the campaign owes itself one different-model
usefulness review: an auditor from another provider reads DESIGN
sections 13-16 plus the ledger's verdict history and answers one
question -- does this loop do something useful, or is it a self-loop
doing nothing?  This tool composes that brief from the ledger, invokes
the configured different-model route (rumpun.yaml: ``usefulness.route``
names a key of ``routes:``, default ``gpt-6-astra``'s codex bypass
command), parses the final verdict line (USEFUL / PARTIALLY USEFUL /
SELF-LOOP DOING NOTHING), and appends one akar record
``usefulness-decade-<N>`` carrying the verdict, the residuals the
auditor listed, and a pointer to the captured output under
``.rumpun/akar/evidence/``.

Isolation follows the audit corpus-runner precedent
(``audit.refresh_corpus_matrix``): the route runs as a subprocess in its
own process group (``start_new_session=True``) with stdin from
/dev/null, captured streams, and the hard timeout USEFULNESS_TIMEOUT_S
(SIGKILL to the process group on expiry).  Captured streams are never
echoed into the record: the record carries the verdict line, bounded
one-line residual summaries, the musim count, and the evidence pointer
with its sha256 -- nothing else of the prompt or the output.  The tool
refuses honestly (exit 1, no record) when rumpun.yaml is missing, the
configured route is missing, the route fails or times out, no verdict
line parses, no decade is due, or the record id is already taken.

The due decade N is the first decade (10 musim seasons per decade) with
no ``usefulness-decade-N`` record among the declared akar ids -- the
same debt order the run_audit finding reports, so paying debt in order
(append usefulness-decade-1, then -2, ...) reaches the audit's fixed
point.  Refuses when every decade up to count // 10 is covered.

Usage:
    .venv/bin/python tools/usefulness_audit.py [--repo DIR]
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import logging
import os
import re
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

logger = logging.getLogger("usefulness_audit")

USEFULNESS_TIMEOUT_S = 300
SEASONS_PER_DECADE = 10
DEFAULT_ROUTE = "gpt-6-astra"
VERDICTS = ("USEFUL", "PARTIALLY USEFUL", "SELF-LOOP DOING NOTHING")
RESIDUAL_MAX_CHARS = 200

_SEASON_FILE_RE = re.compile(r"^s(\d+)\.yaml$")
_SID_RE = re.compile(r"^s(\d+)$")
_USEFULNESS_DECADE_RE = re.compile(r"^usefulness-decade-(\d+)$")
_VERDICT_RE = re.compile(r"^\s*VERDICT:\s*(.+?)\s*$", re.M)
_RESIDUAL_RE = re.compile(r"^\s*residual:\s*(.+?)\s*$", re.I | re.M)


class UsefulnessAuditError(Exception):
    """Invalid input, missing route, failed route call, or unparsable verdict."""


def find_repo_root(start: Path) -> Path:
    """First ancestor of start holding src/rumpun (the repo root)."""
    for candidate in (start, *start.parents):
        if (candidate / "src" / "rumpun").is_dir():
            return candidate
    msg = f"no ancestor of {start} contains src/rumpun"
    raise UsefulnessAuditError(msg)


def _import_rumpun(repo: Path) -> tuple[ModuleType, ModuleType]:
    """Return the project's (akar, yamlio) modules.

    An existing import (installed package or PYTHONPATH, which fixture
    repros point at a patched tree) wins; otherwise this repo's src is
    appended as the bootstrap path -- the tool file sits in <repo>/tools/.
    """
    try:
        from rumpun import akar, yamlio
    except ModuleNotFoundError:
        sys.path.append(str(repo / "src"))
        from rumpun import akar, yamlio
    return akar, yamlio  # type: ignore[return-value]


def _load_config(root: Path, yamlio: ModuleType) -> dict:
    """The campaign config parsed with the project's own YAML guards."""
    path = root / "rumpun.yaml"
    if not path.is_file():
        msg = f"no rumpun.yaml under {root}"
        raise UsefulnessAuditError(msg)
    doc = yamlio.load(path)
    if not isinstance(doc, dict):
        msg = f"{path}: campaign config must be a mapping"
        raise UsefulnessAuditError(msg)
    return doc


def resolve_route(doc: dict) -> tuple[str, str, int | None]:
    """(route name, command template) from usefulness.route -> routes.

    usefulness.route names a key of the routes: block; the default is
    gpt-6-astra's codex bypass command.  A missing name, a missing
    routes block, or a non-string template refuses honestly.
    """
    usefulness = doc.get("usefulness") or {}
    if not isinstance(usefulness, dict):
        msg = "rumpun.yaml: usefulness: must be a mapping when present"
        raise UsefulnessAuditError(msg)
    name = usefulness.get("route") or DEFAULT_ROUTE
    raw_timeout = usefulness.get("timeout_s")
    timeout_s = int(raw_timeout) if isinstance(raw_timeout, (int, float)) else None
    routes = doc.get("routes") or {}
    template = routes.get(name) if isinstance(routes, dict) else None
    if not isinstance(template, str) or not template.strip():
        msg = f"rumpun.yaml: no route {name!r} under routes: (usefulness.route)"
        raise UsefulnessAuditError(msg)
    return str(name), template, timeout_s


def season_count(root: Path) -> int:
    """Number of musim/s<N>.yaml season files; honest refusal when none."""
    musim = root / "musim"
    if not musim.is_dir():
        msg = f"no musim directory under {root}"
        raise UsefulnessAuditError(msg)
    count = sum(
        1 for p in musim.iterdir() if p.is_file() and _SEASON_FILE_RE.match(p.name)
    )
    if not count:
        msg = f"no musim/s<N>.yaml seasons under {musim}"
        raise UsefulnessAuditError(msg)
    return count


def covered_decades(root: Path, akar: ModuleType) -> set[int]:
    """Decade numbers of every usefulness-decade-<N> akar record id."""
    try:
        declared = akar.declared_ids(root)
    except akar.AkarError as exc:
        msg = f"cannot scan akar records under {root / 'akar'}: {exc}"
        raise UsefulnessAuditError(msg) from exc
    return {
        int(m.group(1))
        for rid in declared
        if (m := _USEFULNESS_DECADE_RE.match(rid))
    }


def due_decade(count: int, covered: set[int]) -> int | None:
    """First decade without a record, or None when the debt is paid.

    Decades are 10 seasons wide; floor(count/10) decades are owed, and
    the first missing one is due (the audit finding's fixed point).
    """
    due = count // SEASONS_PER_DECADE
    for decade in range(1, due + 1):
        if decade not in covered:
            return decade
    return None


def verdict_history(root: Path) -> list[tuple[str, str]]:
    """(sid, last season-level verdict) per rimba season, sorted by number.

    A season-level row is one whose ``season`` value equals the sid (the
    report verb's rule [H]); the last such row wins.  A season without
    verdicts.jsonl or without a season-level row reports "none".  A
    corrupt line refuses rather than guessing.
    """
    rimba = root / "rimba"
    if not rimba.is_dir():
        return []
    seasons = sorted(
        (int(m.group(1)), d)
        for d in rimba.iterdir()
        if d.is_dir() and (m := _SID_RE.match(d.name))
    )
    history: list[tuple[str, str]] = []
    for _num, season_dir in seasons:
        rows: list[dict] = []
        path = season_dir / "verdicts.jsonl"
        if path.is_file():
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError as exc:
                msg = f"cannot read {path}: {exc}"
                raise UsefulnessAuditError(msg) from exc
            for lineno, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    msg = f"{path}: line {lineno} is not valid JSON: {exc}"
                    raise UsefulnessAuditError(msg) from exc
                if isinstance(row, dict):
                    rows.append(row)
        verdict = ""
        for row in rows:
            sid = season_dir.name
            if row.get("season") == sid:
                verdict = str(row.get("verdict", ""))
        history.append((season_dir.name, verdict or "none"))
    return history


def design_sections(repo: Path) -> str:
    """The verbatim DESIGN.md text from section 13 through end of file."""
    path = repo / "DESIGN.md"
    if not path.is_file():
        msg = f"no DESIGN.md at {path}"
        raise UsefulnessAuditError(msg)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        msg = f"cannot read {path}: {exc}"
        raise UsefulnessAuditError(msg) from exc
    for index, line in enumerate(lines):
        if line.startswith("## 13."):
            return "\n".join(lines[index:])
    msg = f"{path}: no '## 13.' heading; sections 13-16 not extractable"
    raise UsefulnessAuditError(msg)


def compose_brief(
    decade: int, count: int, history: list[tuple[str, str]], design_text: str
) -> str:
    """The auditor brief: the question, the output contract, both inputs."""
    history_lines = "\n".join(f"{sid}: {verdict}" for sid, verdict in history)
    if not history_lines:
        history_lines = "(no rimba seasons yet)"
    return (
        f"You are the independent usefulness auditor for the rumpun campaign.\n"
        f"This is the decade-{decade} review: the ledger holds {count} musim "
        f"seasons.\n\n"
        "Question: does this loop produce something useful, or is it a "
        "self-loop doing nothing?\n\n"
        "Judge the system the two inputs below describe, skeptically and in "
        "your own words. Credited value must be real and specific. "
        "Ceremony, overstated records, unfalsifiable bands, and claims the "
        "ledger cannot support are residuals.\n\n"
        "Output contract, strict:\n"
        '1. List every residual, one per line, each starting exactly with '
        '"residual: ". Keep each residual to one bounded line.\n'
        "2. End the reply with the final line exactly one of:\n"
        "VERDICT: USEFUL\n"
        "VERDICT: PARTIALLY USEFUL\n"
        "VERDICT: SELF-LOOP DOING NOTHING\n"
        "Nothing follows the verdict line.\n"
        "\n--- DESIGN.md sections 13-16 (the campaign's own account) ---\n"
        f"{design_text}\n"
        "\n--- ledger facts (harness-observed) ---\n"
        f"musim seasons: {count}\n"
        "season verdicts (last season-level row per season, "
        "rimba/<sid>/verdicts.jsonl):\n"
        f"{history_lines}\n"
    )


def run_route(
    template: str, prompt_path: Path, repo: Path, timeout_s: int | None = None
) -> tuple[str, str, int, bool]:
    """Run the rendered route command; return (stdout, stderr, rc, timed_out).

    The engine's own rendering (engine.py): ``template.replace("{prompt}",
    ...)`` spawned as ``/bin/sh -c`` in a new session.  stdin is /dev/null,
    streams are captured (never echoed), and the timeout kills the whole
    process group.
    """
    cmd = template.replace("{prompt}", str(prompt_path))
    try:
        proc = subprocess.Popen(
            ["/bin/sh", "-c", cmd],
            cwd=str(repo),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        msg = f"usefulness route could not start: {exc}"
        raise UsefulnessAuditError(msg) from exc
    timed_out = False
    out, err = "", ""
    try:
        out, err = proc.communicate(timeout=timeout_s or USEFULNESS_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        timed_out = True
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(proc.pid, signal.SIGKILL)
        with contextlib.suppress(Exception):
            out, err = proc.communicate(timeout=10)
    return out or "", err or "", proc.returncode, timed_out


def extract_verdict(stdout: str) -> str:
    """The final VERDICT: line's token; honest refusal on anything else."""
    matches = _VERDICT_RE.findall(stdout)
    if not matches:
        msg = "no 'VERDICT:' line in the route output (refusing)"
        raise UsefulnessAuditError(msg)
    token = " ".join(matches[-1].split())
    if token not in VERDICTS:
        msg = f"verdict token {token[:60]!r} is not one of {VERDICTS}"
        raise UsefulnessAuditError(msg)
    return token


def extract_residuals(stdout: str) -> list[str]:
    """Bounded one-line summaries of every 'residual: ' line, in order."""
    residuals: list[str] = []
    for match in _RESIDUAL_RE.findall(stdout):
        text = " ".join(match.split())
        if not text:
            continue
        if len(text) > RESIDUAL_MAX_CHARS:
            text = text[: RESIDUAL_MAX_CHARS - 3] + "..."
        residuals.append(text)
    return residuals


def save_evidence(
    root: Path, decade: int, out: str, err: str
) -> tuple[Path, str]:
    """Write the captured streams under akar/evidence; return (path, sha256).

    Evidence is the audit trail for the operator; the record itself later
    carries only the pointer and this digest, never the content.
    """
    evidence_dir = root / "akar" / "evidence" / f"usefulness-decade-{decade}"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_path = evidence_dir / "output.txt"
    stderr_path = evidence_dir / "stderr.txt"
    try:
        output_path.write_text(out, encoding="utf-8")
        stderr_path.write_text(err, encoding="utf-8")
    except OSError as exc:
        msg = f"cannot write evidence under {evidence_dir}: {exc}"
        raise UsefulnessAuditError(msg) from exc
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return output_path, digest


def append_usefulness_record(
    akar: ModuleType,
    root: Path,
    decade: int,
    verdict: str,
    residuals: list[str],
    evidence_path: Path,
    evidence_sha: str,
    route_name: str,
    count: int,
) -> Path:
    """Append usefulness-decade-<decade>; the only akar mutation."""
    residual_lines = [f"- {text}" for text in residuals] or ["- none"]
    body = "\n".join(
        [
            f"verdict: {verdict} (different-model decade audit, route {route_name})",
            f"decade: {decade}",
            f"seasons: {count} musim seasons at audit time",
            "residuals:",
            *residual_lines,
            f"evidence: {evidence_path.relative_to(root).as_posix()}",
            f"evidence sha256: {evidence_sha}",
        ]
    )
    title = f"{verdict} (decade {decade} different-model review)"
    return akar.append_record(
        root, f"usefulness-decade-{decade}", title, body
    )


def run(root: Path, repo: Path, akar: ModuleType, yamlio: ModuleType) -> Path:
    """One usefulness audit against the ledger at root; returns the record."""
    doc = _load_config(root, yamlio)
    route_name, template, timeout_s = resolve_route(doc)
    count = season_count(root)
    covered = covered_decades(root, akar)
    decade = due_decade(count, covered)
    if decade is None:
        msg = (
            f"no usefulness decade due: {count} musim seasons owe "
            f"{count // SEASONS_PER_DECADE} decade review(s), "
            f"{len(covered)} covered"
        )
        raise UsefulnessAuditError(msg)
    history = verdict_history(root)
    design_text = design_sections(repo)
    brief = compose_brief(decade, count, history, design_text)

    evidence_dir = root / "akar" / "evidence" / f"usefulness-decade-{decade}"
    with tempfile.TemporaryDirectory(prefix="usefulness-brief-", dir=root) as tmp:
        prompt_path = Path(tmp) / "prompt.md"
        prompt_path.write_text(brief, encoding="utf-8")
        out, err, rc, timed_out = run_route(
            template, prompt_path, repo, timeout_s=timeout_s
        )

    _path, evidence_sha = save_evidence(root, decade, out, err)
    evidence_path = evidence_dir / "output.txt"
    if timed_out:
        msg = (
            f"usefulness route {route_name!r} timed out after "
            f"{timeout_s or USEFULNESS_TIMEOUT_S}s; captured output at {evidence_dir}"
        )
        raise UsefulnessAuditError(msg)
    if rc != 0:
        msg = (
            f"usefulness route {route_name!r} failed with exit {rc}; "
            f"captured output at {evidence_dir}"
        )
        raise UsefulnessAuditError(msg)
    verdict = extract_verdict(out)
    residuals = extract_residuals(out)
    record = append_usefulness_record(
        akar, root, decade, verdict, residuals,
        evidence_path, evidence_sha, route_name, count,
    )
    logger.info(
        "usefulness decade %s: %s (%d residuals) -> %s",
        decade, verdict, len(residuals), record,
    )
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the decadal different-model usefulness audit.",
    )
    parser.add_argument("--repo", type=Path, default=None, help="repo root")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    repo = args.repo or (
        Path.cwd()
        if (Path.cwd() / ".rumpun" / "rumpun.yaml").is_file()
        else find_repo_root(Path(__file__).resolve())
    )
    akar, yamlio = _import_rumpun(repo)
    try:
        run(repo / ".rumpun", repo, akar, yamlio)
    except (UsefulnessAuditError, akar.AkarError, yamlio.YamlError) as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
