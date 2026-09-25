"""s71 w2 pins — the panel's second-opinion route (seeded issue #1, second slice).

Spec source: .rumpun/runs/s73/w2/prompt.md (the s71 w2 brief); the s70
w2 file is the fixture-pattern precedent and tools/usefulness_audit.py
(the decadal route) is the spawn-pattern precedent.

Contract these pins hold — src/rumpun/panel.py, importable as
rumpun.panel:

1. route_argv(template, prompt_path) renders the route command as
   ["/bin/sh", "-c", template.replace("{prompt}", path)] (the decadal
   run_route argv).
2. gpt6_astra_route(root, review, timeout_s) is the default route-seam
   callable: reads routes: gpt-6-astra from <root>/rumpun.yaml, writes
   the review to a prompt file, spawns the rendered command under
   /bin/sh in its own process group (stdin /dev/null, captured
   streams), bounded at timeout_s (SIGKILL to the process group on
   expiry, PANEL_ROUTE_TIMEOUT_S == 300). Returns stdout as the reply.
   Raises PanelError when the config or template is missing, the spawn
   fails, the call times out, or the route exits nonzero. Spawn
   mechanics are pinned offline with harmless commands (cat/sleep/
   false) — never a real route call.
3. request_review(root, sid, dry_run, route=...) — the pluggable seam:
   without --dry-run it appends the sha-sealed panel-<sid> pending
   record, calls the seam with the exact rendered review and the 300s
   bound, and seals the outcome as a NEW record (the pending record
   stays): panel-<sid>-verdict (status: <verdict>, reply quoted) on a
   parsable reply, panel-<sid>-error (status: pending, error quoted)
   when the route is unreachable, times out, exits nonzero, or replies
   without an actionable verdict line. Never silent, never fabricated,
   no retries. --dry-run never calls the seam and writes nothing.

Fixture discipline: the fixture campaign copies the REAL s69 season
yaml and harvest record (the stable-history anchor the s70 pins used)
plus the live DESIGN.md, and a rumpun.yaml whose routes: block names
the pin's harmless command.
"""


from __future__ import annotations

import hashlib
import logging
import shutil
import time
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


def _s71w2_repo_root() -> Path:
    """Repo root from this file's location, workspace and merged alike.

    The s70 walk-up rule: parents[] must hold pyproject.toml,
    src/rumpun/report.py and DESIGN.md together, so archived src/ copies
    in scratch trees never match.
    """
    for candidate in Path(__file__).resolve().parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "rumpun" / "report.py").is_file()
            and (candidate / "DESIGN.md").is_file()
        ):
            return candidate
    pytest.fail(f"repo root not found above {Path(__file__)}")


def _s71w2_panel_module():
    """Import rumpun.panel; fail naming the spec reason when unlanded."""
    try:
        from rumpun import panel as panel_module
    except ImportError as exc:
        pytest.fail(f"src/rumpun/panel.py missing/unimportable: {exc}")
    return panel_module


def _s71w2_fixture_campaign(tmp_path: Path, route_cmd: str = "cat {prompt}") -> Path:
    """A fixture campaign with the real s69 panel input and a harmless route.

    Layout: <tmp>/s71w2proj/DESIGN.md (live copy) beside <tmp>/s71w2proj/
    .rumpun/ with rumpun.yaml (routes: gpt-6-astra -> route_cmd), the real
    seasons/s69.yaml, and the real s69-harvest ledger record resolved
    through akar (the discipline, not a filename glob).
    """
    repo_root = _s71w2_repo_root()
    campaign = tmp_path / "s71w2proj"
    root = campaign / ".rumpun"
    for sub in ("seasons", "ledger", "runs"):
        (root / sub).mkdir(parents=True)
    (root / "rumpun.yaml").write_text(
        "autonomy:\n"
        "  stage: manual\n"
        "routes:\n"
        f"  gpt-6-astra: '{route_cmd}'\n",
        encoding="utf-8",
    )
    shutil.copyfile(repo_root / "DESIGN.md", campaign / "DESIGN.md")
    shutil.copyfile(repo_root / ".rumpun" / "seasons" / "s69.yaml", root / "seasons" / "s69.yaml")
    from rumpun import akar

    harvest_src = akar.find_record(repo_root / ".rumpun", "s69-harvest")
    shutil.copyfile(harvest_src, root / "ledger" / harvest_src.name)
    return root


def test_s71w2_route_argv_renders_sh_c() -> None:
    """The route command renders as /bin/sh -c with {prompt} substituted."""
    panel = _s71w2_panel_module()
    prompt = Path("/tmp/s71w2-prompt.md")
    argv = panel.route_argv(
        "codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-6-astra {prompt}",
        prompt,
    )
    assert argv == [
        "/bin/sh",
        "-c",
        "codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-6-astra "
        "/tmp/s71w2-prompt.md",
    ], f"unexpected route argv: {argv!r}"
    assert panel.route_argv("cat {prompt}", prompt) == [
        "/bin/sh",
        "-c",
        "cat /tmp/s71w2-prompt.md",
    ], "the simple template must render the same way"


def test_s71w2_default_route_captures_the_reply(tmp_path: Path) -> None:
    """The default seam writes the prompt file and returns the route stdout."""
    panel = _s71w2_panel_module()
    root = _s71w2_fixture_campaign(tmp_path, route_cmd="cat {prompt}")
    review = "panel review request: s69\ngoal: the band holds\n"
    reply = panel.gpt6_astra_route(root, review)
    assert reply == review, f"the reply is not the prompt the seam sent: {reply!r}"
    leftovers = list(tmp_path.rglob("panel-prompt-*"))
    assert not leftovers, f"the prompt temp file leaked: {leftovers!r}"


def test_s71w2_default_route_timeout_kills_the_call(tmp_path: Path) -> None:
    """The 300s-class bound kills the route group; PanelError quotes it."""
    panel = _s71w2_panel_module()
    root = _s71w2_fixture_campaign(tmp_path, route_cmd="sleep 30")
    started = time.monotonic()
    with pytest.raises(panel.PanelError, match="timed out"):
        panel.gpt6_astra_route(root, "review text", timeout_s=1)
    elapsed = time.monotonic() - started
    assert elapsed < 20, f"the timeout bound did not fire ({elapsed:.1f}s for a 1s call)"


def test_s71w2_default_route_nonzero_exit_quotes_stderr(tmp_path: Path) -> None:
    """A dead route is an honest PanelError carrying the exit and stderr."""
    panel = _s71w2_panel_module()
    root = _s71w2_fixture_campaign(tmp_path, route_cmd="echo route-down >&2; exit 3")
    with pytest.raises(panel.PanelError) as excinfo:
        panel.gpt6_astra_route(root, "review text")
    message = str(excinfo.value)
    assert "3" in message, f"exit code not quoted: {message!r}"
    assert "route-down" in message, f"stderr not quoted: {message!r}"


def test_s71w2_request_review_seals_the_verdict_record(tmp_path: Path) -> None:
    """Healthy path: pending stays; panel-<sid>-verdict seals the reply.

    The seam is called with the exact rendered review and the 300s
    bound; the new record opens `status: <verdict>`, names the route,
    quotes the reply verbatim, and carries the recomputed sha256 seal.
    """
    panel = _s71w2_panel_module()
    root = _s71w2_fixture_campaign(tmp_path)
    from rumpun import akar

    reply = "second opinion follows\nverdict: WIN the band holds\nend of reply\n"
    seen: list[tuple[Path, str, int]] = []

    def fake_route(root: Path, review: str, timeout_s: int) -> str:
        seen.append((root, review, timeout_s))
        return reply

    panel.request_review(root, "s69", dry_run=False, route=fake_route)
    assert panel.PANEL_ROUTE_TIMEOUT_S == 300, "the route bound must stay 300s"
    assert seen == [(root, panel.render_review(panel.claim_set(root, "s69")), 300)], (
        f"the seam did not get (root, rendered review, 300): {seen!r}"
    )
    record = akar.find_record(root, "panel-s69-verdict")
    lines = record.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# akar record: panel-s69-verdict"
    assert lines[4] == "status: WIN the band holds", f"no verdict status: {lines[4]!r}"
    assert "route: gpt-6-astra (bounded 300s)" in lines, "the route line is missing"
    body_lines = lines[4:-1]
    reply_at = body_lines.index("reply:")
    reply_lines = reply.splitlines()
    assert body_lines[reply_at + 1 : reply_at + 1 + len(reply_lines)] == reply_lines, (
        "the reply is not quoted verbatim inside the sealed body"
    )
    body = "\n".join(body_lines)
    seal = "sha256: " + hashlib.sha256(body.encode("utf-8")).hexdigest()
    assert lines[-1] == seal, (
        f"seal mismatch: claimed {lines[-1]!r} recomputed {seal!r}"
    )
    pending_lines = akar.find_record(root, "panel-s69").read_text(encoding="utf-8").splitlines()
    assert pending_lines[4] == "status: pending", "the pending record must stay pending"
    assert set(akar.declared_ids(root)) == {
        "s69-harvest",
        "panel-s69",
        "panel-s69-verdict",
    }, f"unexpected ledger ids: {sorted(akar.declared_ids(root))}"


def test_s71w2_request_review_seals_pending_on_route_error(tmp_path: Path) -> None:
    """Unreachable/timeout path: status stays pending, the error is quoted.

    The seam raising PanelError seals panel-<sid>-error (status:
    pending, error section quoting the exception); no verdict record
    may exist and nothing is fabricated.
    """
    panel = _s71w2_panel_module()
    root = _s71w2_fixture_campaign(tmp_path)
    from rumpun import akar

    def failing_route(root: Path, review: str, timeout_s: int) -> str:
        raise panel.PanelError("gpt-6-astra route timed out after 300s")

    panel.request_review(root, "s69", dry_run=False, route=failing_route)
    record = akar.find_record(root, "panel-s69-error")
    lines = record.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "# akar record: panel-s69-error"
    assert lines[4] == "status: pending", f"the error record must stay pending: {lines[4]!r}"
    assert lines[5] == "route: gpt-6-astra (bounded 300s)"
    assert lines[6] == "error:", f"no error section: {lines[6]!r}"
    body = "\n".join(lines[4:-1])
    assert "gpt-6-astra route timed out after 300s" in body, "the error is not quoted"
    assert set(akar.declared_ids(root)) == {
        "s69-harvest",
        "panel-s69",
        "panel-s69-error",
    }, f"unexpected ledger ids: {sorted(akar.declared_ids(root))}"


def test_s71w2_request_review_seals_pending_on_unparsable_reply(tmp_path: Path) -> None:
    """A reply without an actionable verdict seals pending, reply quoted.

    Both refusals land on the error record: a reply with no `verdict:`
    line at all, and a reply whose only verdict line is the request's
    own `verdict: pending` echo (an echo is not an answer).
    """
    panel = _s71w2_panel_module()
    root = _s71w2_fixture_campaign(tmp_path)
    from rumpun import akar

    def no_verdict_route(root: Path, review: str, timeout_s: int) -> str:
        return "the band holds, sounds fine\nno marker line here\n"

    panel.request_review(root, "s69", dry_run=False, route=no_verdict_route)
    lines = akar.find_record(root, "panel-s69-error").read_text(encoding="utf-8").splitlines()
    assert lines[4] == "status: pending"
    body = "\n".join(lines[4:-1])
    assert "no actionable 'verdict:' line" in body, "the parse refusal is not quoted"
    assert "the band holds, sounds fine" in body, "the reply is not quoted as evidence"
    assert "panel-s69-verdict" not in akar.declared_ids(root), "a verdict was fabricated"

    echoed_root = _s71w2_fixture_campaign(tmp_path / "echoed")
    echoed_reply = "verdict: pending (the second-opinion route answers next season)"
    panel.request_review(echoed_root, "s69", dry_run=False, route=lambda r, v, t: echoed_reply)
    echoed_lines = (
        akar.find_record(echoed_root, "panel-s69-error").read_text(encoding="utf-8").splitlines()
    )
    assert echoed_lines[4] == "status: pending"
    echoed_body = "\n".join(echoed_lines[4:-1])
    assert "no actionable 'verdict:' line" in echoed_body
    assert "panel-s69-verdict" not in akar.declared_ids(echoed_root)


def test_s71w2_dry_run_never_calls_the_route(tmp_path: Path) -> None:
    """--dry-run returns the review, never touches the seam or the ledger."""
    panel = _s71w2_panel_module()
    root = _s71w2_fixture_campaign(tmp_path)
    from rumpun import akar

    def boom(root: Path, review: str, timeout_s: int) -> str:
        raise AssertionError("the dry run must not call the route seam")

    review = panel.request_review(root, "s69", dry_run=True, route=boom)
    assert review == panel.render_review(panel.claim_set(root, "s69")), (
        "the dry run did not return the rendered review"
    )
    assert set(akar.declared_ids(root)) == {"s69-harvest"}, (
        f"the dry run wrote records: {sorted(akar.declared_ids(root))}"
    )
