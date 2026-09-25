"""s84 w2 pins — the resolution-trail contract, pinned adversarially.

Spec-first pins for issue #6 (khursanirevo/rumpun#6): audit-44 re-emitted
audit-43's three usefulness-decade-1 residual candidates verbatim the
same day s80 resolved them. w1 (the parallel lane) lands the suppression
in src/rumpun/audit.py — the reflection is the re-entry point: it reads
usefulness residuals off the ledger and turns them into `candidate: `
lines. These pins hold the landed shape to the adversarial contract so
the suppression can never be a blanket filter.

Contract these pins hold — src/rumpun/audit.py, the reflection's emit
path (run_audit with an injectable issue_trail, and the trail matcher):

1. A candidate whose resolution trail is complete NEVER re-emerges as a
   `candidate: ` line. The landed shape emits it as a `resolved: `
   marker carrying the evidence; dropping would also satisfy the slice,
   and any re-arming emission fails.
2. A candidate with no trail (fresh) always emits as `candidate: `, in
   the same reflection as the suppressed one — the suppression cannot
   eat a fresh candidate.
3. A partial trail (one of two citations resolved) follows the landed
   shape: the resolved citation suppresses with its marker; the pin
   holds the invariants either way — the matcher is order-deterministic
   and the partial candidate is never silent (it comes back as a
   non-empty marker or a live candidate, never a silent drop).
4. The reflection's output shape: `candidate: ` and `resolved: ` lines
   are machine-distinguishable (never one line, never blurred), and the
   akar record's sha256 seal (the s66 shape) recomputes over a body
   that carries both kinds.

Offline: every pin runs in a subprocess driver with a blocking gh guard
(any gh argv raises into the payload; the pins assert it stays empty).
The e2e pins drive the landed run_audit(root, last_n, corpus_matrix,
issue_trail) over a throwaway fixture campaign whose F1-F7 and corpus
sections are findings-only (bare season yamls plus one empty runs/<sid>
directory), so the three real audit-43 residual texts are the only
proposals and the cap never interferes.

Red history (measured 2026-09-17; logs /tmp/s84w2-run1..4.log): runs 1-2
pinned the composer (tools/usefulness_audit.py) per the slice's surface
attribution. Against main 374f262 (composer unmodified): 3 failed /
1 passed — the fully-resolved candidate re-emerged as an armed `- `
bullet (pins 1 and 4), and no trail surface existed to bind (pin 3);
the fresh-candidate pin passed (nothing suppressed anything yet — a
regression guard, green for the trivial reason). Run 1 also carried a
driver defect (composer loaded from the fixture repo; fixed, never a
spec reason). w1's landing then surfaced on src/rumpun/audit.py — the
reflection is the re-entry point — so the pins retargeted to the landed
shape: run 3 (w1's in-flight tree, 4 pins) and run 4 (after two
ruff-only fixes) all 4 passed, 0.86s. No red generation against the
landed surface: the landed code and these pins met already green.

Grafting: drop this file into tests/. All helpers carry the _s84w2_
prefix; nothing collides with existing defs. Fixture-shape assumptions
the harness reconciles at merge if w1's landed shapes differ:
(a) the landed suppression is reflection-side: run_audit grows the
    optional issue_trail param; None keeps the pre-s84 audit byte-stable
    (the recorded divergence: the composer tools/usefulness_audit.py
    still emits every residual as an armed `- ` bullet, and the
    reflection is where re-entry is stopped);
(b) the landed marker is a `resolved: ` line (drop was not chosen);
(c) trail rows are gh-shaped dicts (number/state/title/body); the
    citation is the emitted candidate string verbatim in the issue
    body — the landed matcher reads the body only, and the board's own
    filings put the candidate verbatim in the body (board.py
    audit_issue_argv), the title compressed to 60 chars;
(d) the landed matcher resolves on any CLOSED citation (a partial trail
    whose one resolved citation is CLOSED suppresses with that marker);
(e) the harvest leg: a harvest implies/observed line naming the citing
    issue's number ("#N" or "issues/N");
(f) the seal is akar's sha256 over the record body (lines[4:-1]), the
    s66 shape;
(g) the quiet-fixture contract: a season yaml without a declared
    pipeline plus an empty runs/<sid> dir renders F1-F7 and corpus as
    findings-only, zero noise candidates;
(h) no live gh anywhere in the pins: the driver blocks gh argvs and
    each pin asserts the guard log stays empty.
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

S84W2_TIMEOUT = 240  # bounds one driver subprocess (the task bound)

# The three real audit-43 usefulness-decade-1 residual texts (the issue #6
# evidence), verbatim as extract_residuals normalizes them.
S84W2_TEXT_A = (
    "Reported locking repairs, citation checks, regression tooling, and "
    "reduced rendering provide specific utility. Independent artifact "
    "checks remain absent here."
)
S84W2_TEXT_B = (
    "The ledger establishes 24 WIN, eight LOSS, and two missing verdicts, "
    "not 34 completed improvements."
)
S84W2_TEXT_C = (
    "Recorded verdicts establish what evaluators wrote. They do not "
    "independently establish implementation correctness or practical value."
)

S84W2_DRIVER = r'''
"""s84 w2 pin driver: the reflection offline, one JSON payload on stdout.

Modes:
  reflect  call run_audit(root, 10, None, trail) over the fixture
           campaign the test built; report the appended audit record.
  matcher  bind the landed trail matcher (_resolved_candidate) from
           src/rumpun/audit.py and call it with fixture trail data,
           logging every call attempt.

A blocking guard wraps every subprocess entry point: any argv invoking
gh raises into the payload's gh_calls list -- the pins assert it stays
empty (no live gh call, the slice bound).
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import logging
import re
import subprocess
import sys
import traceback
from pathlib import Path

logger = logging.getLogger("s84w2-driver")

GH_CALLS = []
_GUARD_RE = re.compile(r"(?:^|[\s/])gh(?:\s|$)")


def _guard(name, original):
    def wrapped(*args, **kwargs):
        argv = args[0] if args else kwargs.get("args", "")
        if isinstance(argv, (list, tuple)):
            joined = " ".join(str(part) for part in argv)
        else:
            joined = str(argv)
        if _GUARD_RE.search(joined):
            GH_CALLS.append(joined[:200])
            raise RuntimeError("s84w2 no-live-gh guard: " + joined[:120])
        return original(*args, **kwargs)

    wrapped.__name__ = name
    return wrapped


def _arm_guard():
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        setattr(subprocess, name, _guard(name, getattr(subprocess, name)))


def _load_audit(repo):
    sys.path.insert(0, str(Path(repo) / "src"))
    path = Path(repo) / "src" / "rumpun" / "audit.py"
    spec = importlib.util.spec_from_file_location("rumpun_audit_s84w2", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _mode_reflect(module, root, calls):
    trail = calls.get("trail") or []
    record_path = module.run_audit(root, 10, None, trail)
    return {
        "record_path": str(record_path),
        "record_text": Path(record_path).read_text(encoding="utf-8"),
    }


_MATCHER_CANDIDATES = (
    "_resolved_candidate",
    "resolved_candidate",
)


def _normalize(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(str(v) for v in value)
    return repr(value)


def _attempt(surface, params, spec, root):
    candidates = spec["candidates"]
    trail = spec.get("trail") or []
    harvest = spec.get("harvest") or []
    kwargs = {}
    if "issue_trail" in params:
        kwargs["issue_trail"] = trail
    if "harvest_lines" in params:
        kwargs["harvest_lines"] = harvest
    if "emitted" in params:
        kwargs["emitted"] = candidates[0]
    forms = []
    if kwargs:
        forms.append(kwargs)
    forms.append((trail, harvest, candidates[0]))
    last_error = "no call form attempted"
    for form in forms:
        try:
            if isinstance(form, dict):
                value = surface(**form)
            else:
                value = surface(*form)
            return _normalize(value), ""
        except Exception:
            last_error = traceback.format_exc()
    return None, last_error


def _mode_matcher(module, root, calls):
    surface = None
    name = ""
    for candidate in _MATCHER_CANDIDATES:
        found = getattr(module, candidate, None)
        if callable(found):
            surface, name = found, candidate
            break
    if surface is None:
        return {"surface": None, "results": {}, "attempts": []}
    params = list(inspect.signature(surface).parameters)
    payload = {"surface": name, "params": params, "results": {}, "attempts": []}
    for call_id, spec in calls.items():
        value, error = _attempt(surface, params, spec, root)
        if value is None and error:
            payload["results"][call_id] = {"ok": False, "error": error}
            payload["attempts"].append(call_id)
        else:
            payload["results"][call_id] = {"ok": True, "value": value}
    return payload


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    mode = sys.argv[1]
    module_repo = sys.argv[2]
    root = Path(sys.argv[3])
    calls = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    payload = {"mode": mode, "root": str(root)}
    _arm_guard()
    try:
        module = _load_audit(module_repo)
        if mode == "reflect":
            payload.update(_mode_reflect(module, root, calls))
        elif mode == "matcher":
            payload.update(_mode_matcher(module, root, calls))
        else:
            payload["error"] = "unknown mode " + mode
    except Exception:
        payload["error"] = traceback.format_exc()
    payload["gh_calls"] = GH_CALLS
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


# --- helpers -----------------------------------------------------------------------


def _s84w2_repo() -> Path:
    """The repo root: the first ancestor of this file holding pyproject.toml.

    Works identically with the file in the w2 workspace (pre-graft) and in
    tests/ (post-graft): both sit under the repo root.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


S84W2_REPO = _s84w2_repo()


def _s84w2_emitted(text: str) -> str:
    """The emitted candidate string the reflection arms for one residual."""
    return f"usefulness residual: {text} (usefulness-decade-1)"


def _s84w2_issue_row(number: int, state: str, emitted: str) -> dict:
    """One gh-shaped fixture issue citing the emitted string in its body,
    title compressed to 60 chars like the board's own filings."""
    return {
        "number": number,
        "state": state,
        "title": emitted[:60],
        "body": emitted + "\n\nFiled from audit-43 (usefulness-decade-1)",
    }


def _s84w2_akar_record(record_id: str, title: str, body: str) -> str:
    """The akar record file text: header, body, sha256 seal over the body."""
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return (
        f"# akar record: {record_id}\n"
        f"id: {record_id}\n"
        "date: 2026-09-17\n"
        f"title: {title}\n"
        f"{body}"
        f"sha256: {digest}\n"
    )


def _s84w2_campaign(tmp_path: Path, tag: str) -> Path:
    """One throwaway fixture campaign root.

    10 bare season yamls (no declared pipeline: F1-F7 and corpus render
    findings-only) with runs/s10 present (the reflection's engine-season
    requirement), and the ledger's usefulness-decade-1 record carrying
    the three residual texts as `- ` bullets (the composer's real
    emitted shape). Returns the root; the repo dir is not needed.
    """
    base = tmp_path / tag
    root = base / "rumpun"
    (root / "seasons").mkdir(parents=True)
    (root / "ledger").mkdir(parents=True)
    (root / "runs" / "s10").mkdir(parents=True)
    for number in range(1, 11):
        (root / "seasons" / f"s{number}.yaml").write_text(
            f"id: s{number}\n", encoding="utf-8"
        )
    body = (
        "verdict: USEFUL (different-model decade audit, route stub)\n"
        "decade: 1\n"
        "seasons: 10 season yamls at audit time\n"
        "residuals:\n"
        f"- {S84W2_TEXT_A}\n"
        f"- {S84W2_TEXT_B}\n"
        f"- {S84W2_TEXT_C}\n"
        "evidence: ledger/evidence/usefulness-decade-1/output.txt\n"
        "evidence sha256: "
        + hashlib.sha256(
            (
                "VERDICT: USEFUL\n"
                f"residual: {S84W2_TEXT_A}\n"
                f"residual: {S84W2_TEXT_B}\n"
                f"residual: {S84W2_TEXT_C}\n"
            ).encode()
        ).hexdigest()
        + "\n"
    )
    (root / "ledger" / "2026-09-17_usefulness-decade-1.md").write_text(
        _s84w2_akar_record(
            "usefulness-decade-1", "USEFUL (decade 1 different-model review)", body
        ),
        encoding="utf-8",
    )
    return root


def _s84w2_drive(mode: str, root: Path, calls: dict | None = None) -> dict:
    """Run the driver once against the real repo's audit module; return its
    JSON payload plus rc/stderr tail."""
    workdir = root.parent
    driver_path = workdir / "s84w2_driver.py"
    driver_path.write_text(S84W2_DRIVER, encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(driver_path),
            mode,
            str(S84W2_REPO),
            str(root),
            json.dumps(calls or {}),
        ],
        capture_output=True,
        text=True,
        timeout=S84W2_TIMEOUT,
        cwd=str(workdir),
    )
    payload: dict = {}
    stdout_lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if stdout_lines:
        try:
            payload = json.loads(stdout_lines[-1])
        except ValueError:
            payload = {}
    if not payload:
        payload = {
            "error": (
                "driver produced no JSON payload "
                f"(rc={proc.returncode}); stderr tail: {proc.stderr[-1500:]}"
            )
        }
    payload["rc"] = proc.returncode
    payload["stderr_tail"] = proc.stderr[-1500:]
    return payload


@pytest.fixture(scope="module")
def _s84w2_reflect_payload(tmp_path_factory) -> dict:
    """One offline reflection over the fixture campaign with the fixture
    issue trail, shared by the e2e pins on a single observable."""
    tmp = tmp_path_factory.mktemp("s84w2-reflect")
    root = _s84w2_campaign(tmp, "e2e")
    trail = [
        _s84w2_issue_row(3, "CLOSED", _s84w2_emitted(S84W2_TEXT_A)),
        _s84w2_issue_row(8, "CLOSED", _s84w2_emitted(S84W2_TEXT_C)),
        _s84w2_issue_row(9, "OPEN", _s84w2_emitted(S84W2_TEXT_C)),
    ]
    return _s84w2_drive("reflect", root, {"trail": trail})


# --- pins --------------------------------------------------------------------------


def test_s84w2_resolved_candidate_never_reemerges(_s84w2_reflect_payload) -> None:
    """A complete trail (a CLOSED issue citing the candidate verbatim)
    suppresses it: the reflection never emits it as `candidate: ` and the
    resolved marker carries the evidence."""
    payload = _s84w2_reflect_payload
    assert not payload.get("error"), (
        f"the offline reflection failed: {payload.get('error')}"
    )
    assert payload.get("gh_calls") == [], (
        f"the reflection attempted a live gh call in the pin: {payload['gh_calls']}"
    )
    lines = payload["record_text"].splitlines()
    rearming = [
        line
        for line in lines
        if line.startswith("candidate: ") and S84W2_TEXT_A in line
    ]
    assert rearming == [], (
        "the fully-resolved candidate re-emerged as a candidate line: "
        + " | ".join(rearming)
    )
    markers = [
        line
        for line in lines
        if line.startswith("resolved: ") and S84W2_TEXT_A in line
    ]
    assert markers, (
        "no resolved marker for the trail-resolved candidate; the landed "
        "shape emits the evidence, silence is not an accepted shape"
    )
    assert any("issue #3" in line for line in markers), (
        f"the resolved marker does not name its evidence: {markers}"
    )


def test_s84w2_fresh_candidate_still_emits(_s84w2_reflect_payload) -> None:
    """A candidate with no trail always emits as `candidate: ` — in the
    same reflection as the suppressed one, so the suppression cannot be a
    blanket filter."""
    payload = _s84w2_reflect_payload
    assert not payload.get("error"), (
        f"the offline reflection failed: {payload.get('error')}"
    )
    lines = payload["record_text"].splitlines()
    armed_b = [
        line
        for line in lines
        if line.startswith("candidate: ") and S84W2_TEXT_B in line
    ]
    assert armed_b, (
        "the fresh candidate (no trail) was eaten by the suppression: "
        "no candidate line for it"
    )
    assert not any(
        line.startswith("resolved: ") and S84W2_TEXT_B in line for line in lines
    ), "the fresh candidate was resolved-marked with no trail"
    assert any(line.startswith("candidate: ") for line in lines), (
        "the reflection proposed nothing"
    )


def test_s84w2_partial_trail_not_silent(tmp_path) -> None:
    """A partial trail (one of two citations resolved) follows the landed
    shape; the invariants hold either way: the matcher binds, reads
    gh-shaped fixture rows with no live gh, is order-deterministic, and
    the partial candidate is never silent."""
    root = _s84w2_campaign(tmp_path, "matcher")
    emitted_a = _s84w2_emitted(S84W2_TEXT_A)
    emitted_c = _s84w2_emitted(S84W2_TEXT_C)
    emitted_b = _s84w2_emitted(S84W2_TEXT_B)
    calls = {
        "complete": {
            "candidates": [emitted_a],
            "trail": [_s84w2_issue_row(3, "CLOSED", emitted_a)],
        },
        "partial": {
            "candidates": [emitted_c],
            "trail": [
                _s84w2_issue_row(8, "CLOSED", emitted_c),
                _s84w2_issue_row(9, "OPEN", emitted_c),
            ],
        },
        "partial-rev": {
            "candidates": [emitted_c],
            "trail": [
                _s84w2_issue_row(9, "OPEN", emitted_c),
                _s84w2_issue_row(8, "CLOSED", emitted_c),
            ],
        },
        "fresh": {"candidates": [emitted_b], "trail": []},
        "harvest-leg": {
            "candidates": [emitted_c],
            "trail": [_s84w2_issue_row(9, "OPEN", emitted_c)],
            "harvest": [
                (
                    "s84f-harvest",
                    "issue #9 closed on evidence — the residual is resolved",
                )
            ],
        },
        "harvest-mismatch": {
            "candidates": [emitted_c],
            "trail": [_s84w2_issue_row(9, "OPEN", emitted_c)],
            "harvest": [("s84g-harvest", "issue #10 unrelated work")],
        },
    }
    payload = _s84w2_drive("matcher", root, calls)
    assert not payload.get("error"), (
        f"the matcher driver failed: {payload.get('error')}"
    )
    assert payload.get("gh_calls") == [], (
        f"the trail matcher attempted a live gh call: {payload['gh_calls']}"
    )
    if not payload.get("surface"):
        pytest.fail(
            "no trail matcher on src/rumpun/audit.py (_resolved_candidate) — "
            "the trail contract has no checkable seam until w1 lands "
            "(the intended spec-first red)"
        )
    results = payload.get("results") or {}
    failed_calls = sorted(
        call_id for call_id, result in results.items() if not result.get("ok")
    )
    assert failed_calls == [], (
        f"trail-matcher calls failed over fixture trail data: {results}"
    )
    complete = results["complete"]["value"]
    assert isinstance(complete, str) and complete.startswith("resolved: "), (
        f"a complete trail must resolve with a marker, got: {complete!r}"
    )
    assert "issue #3" in complete, (
        f"the marker does not name its evidence: {complete!r}"
    )
    partial = results["partial"]["value"]
    rev = results["partial-rev"]["value"]
    assert partial == rev, (
        "trail matching is order-dependent: not deterministic over one trail"
    )
    assert isinstance(partial, str) and partial.startswith("resolved: "), (
        f"the landed shape resolves a partial trail on its resolved citation, "
        f"got: {partial!r}"
    )
    assert "#8" in partial, (
        f"the partial marker does not name its evidence: {partial!r}"
    )
    assert results["fresh"]["value"] is None, (
        f"a fresh candidate must stay live (None), got: {results['fresh']['value']!r}"
    )
    leg = results["harvest-leg"]["value"]
    assert isinstance(leg, str) and leg.startswith("resolved: ") and "#9" in leg, (
        f"the harvest leg must resolve via the naming harvest line, got: {leg!r}"
    )
    mismatch = results["harvest-mismatch"]["value"]
    assert mismatch is None, (
        "a harvest line naming another issue must not resolve the candidate, "
        f"got: {mismatch!r}"
    )


def test_s84w2_output_shape_sealed_and_distinguishable(
    _s84w2_reflect_payload,
) -> None:
    """`candidate: ` and `resolved: ` lines never share a line, and the
    akar record's sha256 seal (the s66 shape) recomputes over a body that
    carries both kinds."""
    payload = _s84w2_reflect_payload
    assert not payload.get("error"), (
        f"the offline reflection failed: {payload.get('error')}"
    )
    text = payload["record_text"]
    lines = text.splitlines()
    for line in lines:
        if line.startswith(("candidate: ", "resolved: ")):
            assert not line.startswith("candidate: resolved"), (
                f"blur: one line carries both kinds: {line}"
            )
    armed_b = [
        line
        for line in lines
        if line.startswith("candidate: ") and S84W2_TEXT_B in line
    ]
    markers_a = [
        line
        for line in lines
        if line.startswith("resolved: ") and S84W2_TEXT_A in line
    ]
    assert armed_b, "no candidate line for the fresh candidate"
    assert markers_a, "no resolved marker for the resolved candidate"
    body = "\n".join(text.splitlines()[4:-1])
    sha_line = next(
        (line for line in lines if line.startswith("sha256: ")), None
    )
    assert sha_line is not None, "the audit record carries no sha256 seal line"
    recorded = sha_line.removeprefix("sha256: ").strip()
    recomputed = hashlib.sha256(body.encode("utf-8")).hexdigest()
    assert recorded == recomputed, (
        "the akar seal does not recompute over the record body"
    )
    assert f"candidate: {_s84w2_emitted(S84W2_TEXT_B)}" in body and (
        "resolved: " in body
    ), "the sealed body does not carry both kinds"
