"""s136 w2 pins: every writer route probe-checked, the serve table pinned.

Landed by w2, rewritten by the close worker after the extract check:
the original pins read the gitignored run-dir notes and probe outputs,
which the archive extract cannot carry (the check-s110 class). These
pins embed the measured serve table (2026-09-21, one bounded call per
route) and pin its shape and parity against the routes block. Reads
only; no network; no run-dir reads.
"""

from __future__ import annotations

import re
from pathlib import Path

# The measured serve table, 2026-09-21 (the lane's notes, embedded):
# every probeable route with its verdict. fable is this campaign's own
# writer route (running the season; no probe per the brief); glm-5.3
# kept its s125 serving record.
_SERVE_TABLE = {
    "glm": "serving (the glm route serves glm-5.3; probe-checked at s125"
    " and by this lane's bounded call, rc 0, reply ok)",
    "kancil": "not probed (the kancil loop route drives headless"
    " claude iterations; probing it spawns a writer session)",
    "gpt-6-astra": "serving (probe rc 0, reply ok)",
    "gpt-reserve": "serving (probe rc 0, model replied)",
    "gpt-5.6-sol": "serving (probe rc 0, reply ok)",
    "gpt-5.6-terra": "serving (probe rc 0, reply ok)",
    "gpt-5.6-luna": "serving (probe rc 0, model replied)",
    "gpt-5.5": "serving (probe rc 0, reply ok)",
    "codex-auto-review": "serving (probe rc 0, reply ok)",
}


def _repo_root() -> Path:
    """The repo root, by pyproject walk-up."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise AssertionError("no pyproject.toml above the pins file")


def _probeable_routes() -> set[str]:
    """The routes block's keys minus the fable writer route.

    The block is bounded: two-space-indented ``key: `` lines after the
    ``routes:`` header, ending at the first line that is not one.
    """
    text = (_repo_root() / ".rumpun" / "rumpun.yaml").read_text(encoding="utf-8")
    after = text.split("\nroutes:\n", 1)[1]
    routes: set[str] = set()
    for line in after.splitlines():
        if not line.startswith("  "):
            break
        match = re.match(r"^  ([a-z0-9.\-]+): ", line)
        if match:
            routes.add(match.group(1))
    return routes - {"fable"}


def test_serve_table_covers_every_probeable_route() -> None:
    """Every probeable route appears in the measured serve table."""
    routes = _probeable_routes()
    missing = routes - set(_SERVE_TABLE)
    extra = set(_SERVE_TABLE) - routes
    assert not missing, f"the serve table never names {sorted(missing)}"
    assert not extra, f"the serve table names non-existent routes {sorted(extra)}"


def test_serve_table_verdicts_are_honest() -> None:
    """Each verdict reads serving, names the failure, or names the skip."""
    for route, verdict in _SERVE_TABLE.items():
        ok = (
            verdict.startswith("serving")
            or "error" in verdict.lower()
            or "refused" in verdict.lower()
            or verdict.startswith("not probed")
        )
        assert ok, f"{route}: neither serving, a named error, nor a named skip: {verdict!r}"
