"""rumpun panel — the audit panel's input contract and second-opinion route.

Directive seq 0: seasons stay manual until panel tooling lands. s70
landed what the panel reviews: claim_set(root, sid) reads the
deterministic input a second-opinion route reviews for one season --
the season yaml's goal/expected_band, the harvest record's
implies/observed lines, the suite count from the DESIGN.md ships row --
and render_review(claims) renders the exact text that route receives.
s71 lands the route behind it: request_review(root, sid, dry_run,
route=gpt6_astra_route) without --dry-run appends the sha-sealed
panel-<sid> pending record, sends the rendered review to the
gpt-6-astra route (subprocess, bounded 300s, the decadal
tools/usefulness_audit.py spawn pattern), and seals the outcome as a
new sha-sealed record — the pending record stays, a new record carries
it: panel-<sid>-verdict (status: <verdict>, reply quoted) on a
parsable reply, panel-<sid>-error (status: pending, error quoted) when
the route is unreachable, times out, exits nonzero, or replies without
an actionable verdict line. Never silent, never fabricated, no
retries. --dry-run returns the rendered review writing nothing and
never calls the route.
s75 w2 lands the read side: latest_panel_record and latest_panel
surface the newest panel-<sid>* record's status to consumers like
the kanban board. Pure ledger reading; these lookups never call the
route.
s110 w2 lands the sweep: pending_panel_records lists every record
under the panel- prefix whose own status line reads `pending` (id,
date, status). Request and error records stay pending forever by
convention, so the literal read is the operator's wait, legible.
audit --panel-sweep refuses exit 2 without an explicit outcome file;
with one, seal_panel_outcomes seals each named outcome as
<id>-verdict or <id>-error beside the pending request - never
invented (the request must be a declared record, the verdict must
parse from the named reply) and never rewriting (a sealed outcome
refuses; every entry validates before the first seal). The pending
request record is never rewritten.
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
import signal
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rumpun import akar, paths, yamlio

logger = logging.getLogger(__name__)


class PanelError(Exception):
    """The panel request could not be composed from the campaign's files."""


# render_review bounds: one screen, deterministic. Same claims render to
# the same bytes; at most MAX_REVIEW_LINES lines, none wider than
# MAX_LINE_CHARS. Evidence lines past the budget are elided with a
# counting marker, never dropped silently.
MAX_REVIEW_LINES = 24
MAX_LINE_CHARS = 100
_CLIP = "..."

_SUITE_RE = re.compile(r"suite (\d+/\d+)")

# The second-opinion route (s71 w2): the rendered review goes to the
# gpt-6-astra route as a bounded subprocess, the decadal
# tools/usefulness_audit.py spawn pattern (/bin/sh -c, own process
# group, captured streams, SIGKILL to the process group on expiry).
PANEL_ROUTE_TIMEOUT_S = 300
_ROUTE_NAME = "gpt-6-astra"
_ROUTE_LINE = f"route: {_ROUTE_NAME} (bounded {PANEL_ROUTE_TIMEOUT_S}s)"
_VERDICT_RE = re.compile(r"^\s*verdict:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


@dataclass(frozen=True)
class ClaimSet:
    """The claims a panel reviews for one season (the s70 w2 contract;
    s80 w2's repro-backed closure adds the repro field)."""

    sid: str
    goal: str
    expected_band: str
    implies: tuple[str, ...]
    observed: tuple[str, ...]
    suite: str
    # s80 w2 repro-backed closure: None = the season declares no filed
    # defect (no `resolves:`); else "absent" or "present <file>::<test>".
    repro: str | None = None


def claim_set(root: Path, sid: str) -> ClaimSet:
    """Read the deterministic panel input for season <sid>. Pure file reading.

    Sources, all required (missing is a PanelError naming the path):
    - <root>/<seasons>/<sid>.yaml via yamlio: goal,
      methodology.primary_change.expected_band (yamlio.YamlError for a
      bad file propagates unwrapped, the audit.py convention).
    - the ledger record <sid>-harvest via akar.find_record: every
      implies:/observed: line, file order.
    - DESIGN.md beside the campaign root (root.parent/DESIGN.md): the
      last `| <sid> | ... | ... |` ships row; the `suite N/N` search
      spans the whole row, every cell (the artifact-check row rule:
      last row wins, several rows warn).

    The repro-backed closure (s80 w2): an optional top-level `resolves:`
    names the filed defect this season resolves (an int, or a string
    ending in the issue number). When present, the pins tree
    <root>/../tests/test_*.py is scanned for a test named for the
    issue's repro, and the claim set carries `repro: present
    <file>::<test>` or `repro: absent`; a present-but-unparseable
    resolves is a PanelError naming the yaml. A season with no
    `resolves:` sets repro to None and renders exactly the s70 shape.
    """
    root = Path(root)
    yaml_path = paths.seasons_dir(root) / f"{sid}.yaml"
    try:
        data = yamlio.load(yaml_path)
    except OSError as exc:
        raise PanelError(f"{yaml_path}: unreadable season yaml: {exc}") from exc
    goal = data.get("goal")
    methodology = data.get("methodology")
    primary = methodology.get("primary_change") if isinstance(methodology, dict) else None
    band = primary.get("expected_band") if isinstance(primary, dict) else None
    if not isinstance(goal, str) or not goal:
        raise PanelError(f"{yaml_path}: no goal line to review")
    if not isinstance(band, str) or not band:
        raise PanelError(f"{yaml_path}: no expected_band under methodology.primary_change")
    resolves = data.get("resolves")
    repro: str | None = None
    if resolves is not None:
        repro = _repro_status(root, _resolves_issue_num(yaml_path, resolves))
    try:
        record_path = akar.find_record(root, f"{sid}-harvest")
        record_text = record_path.read_text(encoding="utf-8")
    except (akar.AkarError, OSError) as exc:
        raise PanelError(f"no harvest record for {sid}: {exc}") from exc
    implies = tuple(ln for ln in record_text.splitlines() if ln.startswith("implies:"))
    observed = tuple(ln for ln in record_text.splitlines() if ln.startswith("observed:"))
    design_path = root.parent / "DESIGN.md"
    try:
        design_text = design_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PanelError(f"{design_path}: unreadable DESIGN.md: {exc}") from exc
    row_pattern = re.compile(rf"\| {re.escape(sid)} \|.*\|.*\|")
    rows = [ln for ln in design_text.splitlines() if row_pattern.fullmatch(ln.strip())]
    if not rows:
        raise PanelError(f"no ships row for {sid} in {design_path} (unknown season id?)")
    if len(rows) > 1:
        logger.warning("%d ships rows for %s in %s; using the last", len(rows), sid, design_path)
    suite_match = _SUITE_RE.search(rows[-1])
    if suite_match is None:
        raise PanelError(f"no `suite N/N` in {sid}'s ships row in {design_path}")
    return ClaimSet(
        sid=sid,
        goal=goal,
        expected_band=band,
        implies=implies,
        observed=observed,
        suite=suite_match.group(1),
        repro=repro,
    )


_RESOLVES_NUM_RE = re.compile(r"(\d+)\s*$")


def _resolves_issue_num(yaml_path: Path, resolves: object) -> str:
    """The issue number a season's `resolves:` names; PanelError when unreadable.

    The repro-backed-closure contract (priors/templates/
    repro-backed-closure.md): a season resolving a filed defect declares
    `resolves: <issue number>` -- an int, or a string ending in the
    number (`5`, `#5`, `org/repo#5`). A present-but-unparseable
    resolves is a PanelError naming the yaml: a declaration the panel
    cannot read is worse than no declaration.
    """
    if isinstance(resolves, bool):
        raise PanelError(
            f"{yaml_path}: resolves: must end in an issue number, got {resolves!r}"
        )
    if isinstance(resolves, int):
        return str(resolves)
    if isinstance(resolves, str):
        match = _RESOLVES_NUM_RE.search(resolves.strip())
        if match:
            return match.group(1)
    raise PanelError(
        f"{yaml_path}: resolves: must end in an issue number, got {resolves!r}"
    )


def _repro_status(root: Path, issue_num: str) -> str:
    """`present <file>::<test>` or `absent`: the repro-backed closure scan.

    Scans <root>/../tests/test_*.py for a test-function name carrying
    both `repro` and the issue (`issue` + separators + the number,
    case-insensitive; `issue_5` and `issue05` match 5, `issue50` does
    not). Pure file reading in sorted path order; the first match wins.
    A missing tests dir or no match is `absent`, never an error: absent
    is a finding the panel weighs, not a composition defect.
    """
    tests_dir = root.parent / "tests"
    repro_re = re.compile(r"repro", re.IGNORECASE)
    issue_re = re.compile(rf"issue\D*0*{issue_num}(?!\d)", re.IGNORECASE)
    def_re = re.compile(r"(?m)^\s*def (test\w*)\(")
    if tests_dir.is_dir():
        for path in sorted(tests_dir.glob("test_*.py")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                raise PanelError(f"{path}: unreadable pins file: {exc}") from exc
            for name in def_re.findall(text):
                if repro_re.search(name) and issue_re.search(name):
                    loc = f"{path.relative_to(root.parent).as_posix()}::{name}"
                    return f"present {loc}"
    return "absent"


def latest_panel_record(root: Path, sid: str) -> tuple[str, str] | None:
    """The newest panel-<sid>* record as (record id, status); None when none.

    Pure ledger reading over akar.declared_ids. The family spans the
    derived rerun generations (s108 w1): panel-<sid> is generation 1
    and each panel-<sid>-<N> rerun is generation N; within a generation
    the precedence verdict, error, pending request matches append order
    in every reachable state. The newest generation with any record
    answers. The trailing dash keeps neighbor ids apart (s7 never reads
    s70's records). A panel-family record without a status line is a
    PanelError naming the file, never a silent skip.
    """
    root = Path(root)
    ids = akar.declared_ids(root)
    base = f"panel-{sid}"
    hits = [rid for rid in ids if rid == base or rid.startswith(f"{base}-")]

    def _gen(rid: str) -> int:
        token = rid[len(base):].strip("-").split("-", 1)[0]
        return int(token) if token.isdigit() else 1

    for gen in sorted({_gen(rid) for rid in hits}, reverse=True):
        stem = base if gen == 1 else f"{base}-{gen}"
        for rid in (f"{stem}-verdict", f"{stem}-error", stem):
            if rid not in ids:
                continue
            try:
                text = ids[rid].read_text(encoding="utf-8")
            except OSError as exc:
                msg = f"{ids[rid]}: unreadable panel records: {exc}"
                raise PanelError(msg) from exc
            for line in text.splitlines():
                if line.startswith("status: "):
                    return rid, line.removeprefix("status: ").strip()
            raise PanelError(f"{ids[rid]}: panel record {rid} has no status line")
    return None


def latest_panel(root: Path, sid: str) -> str | None:
    """The newest panel-<sid>* record's status line; None when none exists.

    Pure ledger reading (latest_panel_record): a WIN/LOSS/NEUTRAL/
    INVALID verdict -- possibly with trailing reasoning -- or the
    pending status of the request or error record.
    """
    hit = latest_panel_record(root, sid)
    return None if hit is None else hit[1]


def _clip(label: str, value: str) -> str:
    """`<label>: <value>` on one bounded line; long values clip to the cap."""
    text = " ".join(value.split())
    prefix = f"{label}: "
    avail = MAX_LINE_CHARS - len(prefix)
    if len(text) <= avail:
        return prefix + text
    return prefix + text[: avail - len(_CLIP)] + _CLIP


def render_review(claims: ClaimSet) -> str:
    """Render the exact bounded text a second-opinion route would receive.

    Deterministic in claims: the same claims render to the same bytes.
    Bounded to one screen: at most MAX_REVIEW_LINES lines, none wider
    than MAX_LINE_CHARS (whitespace collapses, long values clip with an
    ellipsis). The evidence lines (implies then observed, file order)
    share one budget; lines past it are elided behind a counting marker
    inside the same bound. A claim set whose season declares
    `resolves:` carries its repro line in the fixed block (s80 w2).
    """
    evidence = [
        *(f"implies[{i}]: {ln.split(':', 1)[1].strip()}" for i, ln in enumerate(claims.implies, 1)),
        *(
            f"observed[{j}]: {ln.split(':', 1)[1].strip()}"
            for j, ln in enumerate(claims.observed, 1)
        ),
    ]
    lines = [
        f"panel review request: {claims.sid}",
        _clip("goal", claims.goal),
        _clip("expected_band", claims.expected_band),
        _clip("suite", claims.suite),
    ]
    if claims.repro is not None:
        lines.append(_clip("repro", claims.repro))
    evidence_budget = MAX_REVIEW_LINES - len(lines) - 2  # verdict + elision slot
    elided = len(evidence) - evidence_budget
    lines.extend(
        _clip(label, value)
        for label, value in (ln.split(": ", 1) for ln in evidence[:evidence_budget])
    )
    if elided > 0:
        lines.append(f"(+{elided} evidence lines elided)")
    lines.append("verdict: pending (the second-opinion route answers next season)")
    return "\n".join(lines)


def route_argv(template: str, prompt_path: Path) -> list[str]:
    """The decadal run_route argv: /bin/sh -c with {prompt} rendered."""
    return ["/bin/sh", "-c", template.replace("{prompt}", str(prompt_path))]


def gpt6_astra_route(root: Path, review: str, timeout_s: int = PANEL_ROUTE_TIMEOUT_S) -> str:
    """The default route seam: send the review to gpt-6-astra, return the reply.

    Reads routes: gpt-6-astra from <root>/rumpun.yaml, writes the review
    to a prompt temp file, spawns the rendered command under the /bin/sh
    in its own process group (stdin /dev/null, captured streams),
    bounded at timeout_s (SIGKILL to the process group on expiry).
    Returns stdout as the reply. Raises PanelError when the config or
    template is missing, the spawn fails, the call times out, or the
    route exits nonzero — never a silent empty reply.
    """
    config_path = root / "rumpun.yaml"
    try:
        doc = yamlio.load(config_path)
    except (OSError, yamlio.YamlError) as exc:
        msg = f"{config_path}: unreadable campaign config: {exc}"
        raise PanelError(msg) from exc
    routes = doc.get("routes") if isinstance(doc, dict) else None
    template = routes.get(_ROUTE_NAME) if isinstance(routes, dict) else None
    if not isinstance(template, str) or not template.strip():
        msg = f"{config_path}: no routes: gpt-6-astra template for the panel route"
        raise PanelError(msg)
    with tempfile.NamedTemporaryFile(
        "w", prefix="panel-prompt-", suffix=".md", delete=False
    ) as prompt_file:
        prompt_file.write(review)
        prompt_path = Path(prompt_file.name)
    try:
        argv = route_argv(template, prompt_path)
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(root.parent),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
        except OSError as exc:
            msg = f"gpt-6-astra route could not start: {exc}"
            raise PanelError(msg) from exc
        timed_out = False
        out, err = "", ""
        try:
            out, err = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGKILL)
            with contextlib.suppress(Exception):
                out, err = proc.communicate(timeout=10)
        if timed_out:
            msg = f"gpt-6-astra route timed out after {timeout_s}s (the call was killed)"
            raise PanelError(msg)
        if proc.returncode != 0:
            err_text = " ".join((err or "").split()) or "(no stderr)"
            msg = f"gpt-6-astra route exited {proc.returncode}: {err_text}"
            raise PanelError(msg)
        return out or ""
    finally:
        prompt_path.unlink(missing_ok=True)


def _extract_verdict(reply: str) -> str:
    """The last actionable `verdict:` line, collapsed; PanelError without one.

    A `verdict: pending` line is the request's own trailing line echoed
    back, not an answer; refusing beats fabricating. The verdict is
    clipped to keep the status line within the one-line bound.
    """
    candidates = [
        collapsed
        for match in _VERDICT_RE.findall(reply)
        for collapsed in [" ".join(match.split())]
        if not collapsed.lower().startswith("pending")
    ]
    if not candidates:
        msg = "gpt-6-astra reply has no actionable 'verdict:' line (refusing to fabricate one)"
        raise PanelError(msg)
    return candidates[-1][: MAX_LINE_CHARS - len("status: ")]


def _next_panel_request_id(root: Path, sid: str) -> str:
    """The next free request id in the panel-<sid> family (s108 w1).

    panel-<sid> when free; else the smallest N >= 2 with panel-<sid>-<N>
    free, read off akar.declared_ids. The ledger never rewrites: a rerun
    lands beside the first request, never over it. The append itself
    still holds the akar guard, so concurrent callers of one id
    serialize into one success and one AkarError.
    """
    ids = akar.declared_ids(root)
    base = f"panel-{sid}"
    if base not in ids:
        return base
    n = 2
    while f"{base}-{n}" in ids:
        n += 1
    return f"{base}-{n}"


def request_review(
    root: Path,
    sid: str,
    dry_run: bool,
    route: Callable[[Path, str, int], str] = gpt6_astra_route,
) -> str:
    """Compose the panel request for <sid>; returns the pending record path.

    --dry-run: the rendered review, writing nothing; the route seam is
    never invoked. Real run: derives the request id (panel-<sid> when
    free, else the next free panel-<sid>-<N>, s108 w1), appends the
    sha-sealed request record marked pending, then calls the route seam
    with the exact rendered review and the 300s bound. The outcome
    seals as a NEW record under the derived request id (the pending
    record stays): `<rid>-verdict` carries `status: <verdict>` and the
    verbatim reply on a parsable reply; `<rid>-error` stays
    `status: pending` and quotes the error (plus the reply as received)
    when the route is unreachable, times out, exits nonzero, or has no
    actionable verdict line. The ledger never rewrites: a rerun lands
    beside the first request, never over it.
    """
    claims = claim_set(root, sid)
    review = render_review(claims)
    if dry_run:
        return review
    rid = _next_panel_request_id(root, sid)
    body = "\n".join(
        [
            "status: pending",
            _ROUTE_LINE + f"; the outcome seals as {rid}-verdict or {rid}-error",
            "review request:",
            *review.splitlines(),
        ]
    )
    path = akar.append_record(
        root,
        rid,
        f"panel review request {sid} (pending)",
        body,
    )
    logger.info("panel request sealed -> %s", path)
    reply: str | None = None
    try:
        reply = route(root, review, PANEL_ROUTE_TIMEOUT_S)
        verdict = _extract_verdict(reply)
    except PanelError as exc:
        error_lines = ["status: pending", _ROUTE_LINE, "error:", str(exc)]
        if reply is not None:
            error_lines += ["reply as received:", reply]
        upgrade = akar.append_record(
            root,
            f"{rid}-error",
            f"panel route error {sid} (pending)",
            "\n".join(error_lines),
        )
        logger.error("panel route error for %s; sealed pending -> %s", sid, upgrade)
        return str(path)
    upgrade_record = akar.append_record(
        root,
        f"{rid}-verdict",
        f"panel verdict {sid} ({verdict})",
        "\n".join(["status: " + verdict, _ROUTE_LINE, "reply:", reply]),
    )
    logger.info("panel verdict for %s: %s -> %s", sid, verdict, upgrade_record)
    return str(path)


def pending_panel_records(root: Path) -> list[tuple[str, str, str]]:
    """The pending panel records as (id, date, status) rows, file order.

    Pure ledger reading over akar.declared_ids: every record id under
    the panel- prefix whose own status line reads `pending`. The s71
    convention keeps every request record pending forever (the pending
    record stays; a new record carries the outcome) and an outcome
    error record stays pending too, so the literal read is exactly the
    wait the sweep reports. A panel record without a status line or a
    date line is a PanelError naming the file, never a silent skip
    (the latest_panel_record rule).
    """
    root = Path(root)
    rows: list[tuple[str, str, str]] = []
    for rid, path in akar.declared_ids(root).items():
        if not rid.startswith("panel-"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            msg = f"{path}: unreadable panel record {rid}: {exc}"
            raise PanelError(msg) from exc
        status: str | None = None
        record_date: str | None = None
        for line in text.splitlines():
            if status is None and line.startswith("status: "):
                status = line.removeprefix("status: ").strip()
            elif record_date is None and line.startswith("date: "):
                record_date = line.removeprefix("date: ").strip()
            if status is not None and record_date is not None:
                break
        if status is None or record_date is None:
            missing = "status" if status is None else "date"
            msg = f"{path}: panel record {rid} has no {missing} line"
            raise PanelError(msg)
        if status == "pending":
            rows.append((rid, record_date, status))
    return rows


def _sweep_sid(rid: str) -> str:
    """The season id inside a request record id: panel-s69-2 -> s69."""
    stem = rid.removeprefix("panel-")
    if stem.rsplit("-", 1)[-1].isdigit():
        stem = stem.rsplit("-", 1)[0]
    return stem


def seal_panel_outcomes(root: Path, outcome_file: Path) -> list[str]:
    """Seal route outcomes from an explicit outcome file; the receipt lines.

    The file is YAML: {outcomes: {<request id>: {reply: <str>} |
    {error: <str>}}}. Every entry validates before the first seal: the
    id must declare a panel record (an undeclared id is a refusal, never
    an invented record), the id must be a pending request (an outcome id
    ending in -verdict or -error refuses; an outcome never seals beside
    an outcome), neither <id>-verdict nor <id>-error may already exist
    (the ledger never rewrites), and exactly one of reply:/error: must
    name a non-empty string. A verdict seals from the verbatim reply
    via _extract_verdict (no actionable verdict line -> PanelError,
    never invented), in the request_review verdict shape; an error
    seals status pending quoting the error, the request_review error
    shape. The pending request record is never rewritten.
    """
    root = Path(root)
    try:
        doc = yamlio.load(Path(outcome_file))
    except OSError as exc:
        msg = f"{outcome_file}: unreadable outcome file: {exc}"
        raise PanelError(msg) from exc
    entries = doc.get("outcomes") if isinstance(doc, dict) else None
    if not isinstance(entries, dict) or not entries:
        msg = f"{outcome_file}: no outcomes: mapping naming pending requests"
        raise PanelError(msg)
    ids = akar.declared_ids(root)
    planned: list[tuple[str, str, str]] = []
    for rid, raw in entries.items():
        if rid not in ids:
            msg = f"{outcome_file}: {rid} declares no ledger record; refusing to invent one"
            raise PanelError(msg)
        if rid.endswith("-verdict") or rid.endswith("-error"):
            msg = f"{outcome_file}: {rid} is an outcome record, not a pending request"
            raise PanelError(msg)
        sealed = next(
            (f"{rid}{suffix}" for suffix in ("-verdict", "-error") if f"{rid}{suffix}" in ids),
            None,
        )
        if sealed is not None:
            msg = f"{outcome_file}: {rid} already sealed in {sealed}; the ledger never rewrites"
            raise PanelError(msg)
        if not isinstance(raw, dict):
            msg = f"{outcome_file}: {rid}: outcome must be a reply:/error: mapping"
            raise PanelError(msg)
        reply = raw.get("reply")
        error = raw.get("error")
        if (reply is None) == (error is None):
            msg = f"{outcome_file}: {rid}: exactly one of reply:/error: names the outcome"
            raise PanelError(msg)
        sid = _sweep_sid(rid)
        if error is not None:
            if not isinstance(error, str) or not error.strip():
                msg = f"{outcome_file}: {rid}: error: must be a non-empty string"
                raise PanelError(msg)
            planned.append(
                (
                    f"{rid}-error",
                    f"panel route error {sid} (pending)",
                    "\n".join(["status: pending", _ROUTE_LINE, "error:", error]),
                )
            )
        else:
            if not isinstance(reply, str) or not reply.strip():
                msg = f"{outcome_file}: {rid}: reply: must be a non-empty string"
                raise PanelError(msg)
            verdict = _extract_verdict(reply)
            planned.append(
                (
                    f"{rid}-verdict",
                    f"panel verdict {sid} ({verdict})",
                    "\n".join(["status: " + verdict, _ROUTE_LINE, "reply:", reply]),
                )
            )
    receipt: list[str] = []
    for record_id, title, body in planned:
        path = akar.append_record(root, record_id, title, body)
        receipt.append(f"sealed {record_id} -> {path}")
        logger.info("panel sweep sealed %s -> %s", record_id, path)
    return receipt
