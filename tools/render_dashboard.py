#!/usr/bin/env python3
"""Maintained dashboard render loop (s27 w1).

The harness refreshed the campaign dashboard every season close with a
session-local script that died with the session; this is that loop landed
as repo tooling.

Render order: the campaign index first (render_index also renders the
discoveries pages), then every season listed in seasons/ that HAS a persisted
state file. The state-check rule comes from rumpun.engine.state_path --
no season state, no render, one INFO skip line per skipped season.

Artifact logging: render_index and render_report log their own artifact
lines at INFO; this module logs the discoveries artifacts (which the report
functions write but do not log) and the skip lines, so one run yields one
INFO line per rendered artifact.

Exit codes: 0 when the index rendered. A single season-render error is
logged with traceback and does not fail the run. Nonzero (1) only on total
failure: the index itself could not be rendered.

Usage: render_dashboard.py [ROOT]
    ROOT  project root containing the .rumpun tree. Default: cwd.
    The index renders LAST so campaign-strip links see all sibling
    reports; a missing .rumpun/seasons fails loudly before any render.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

from rumpun.engine import state_path
from rumpun.report import _discovery_records, _season_ids, render_index, render_report

logger = logging.getLogger(__name__)

_DISCOVERY_SLUG_RE = re.compile(r"[^a-z0-9-]")


def _discovery_page(root: Path, rid: str) -> Path:
    """Page path mirror of the render_discoveries slug rule (logic lives in report.py)."""
    slug = _DISCOVERY_SLUG_RE.sub("-", rid.lower())
    return root / "runs" / "discoveries" / f"{slug}.html"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the rumpun dashboard: index, discoveries, season reports."
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="project root containing the .rumpun tree; default: cwd",
    )
    args = parser.parse_args(argv)
    root: Path = args.root
    rumpun_root: Path = root / ".rumpun"
    if not (rumpun_root / "seasons").is_dir():
        logger.error(
            "no campaign found at %s (missing .rumpun/seasons); refusing to render",
            rumpun_root,
        )
        return 1

    # Seasons first: the index's campaign-strip links depend on which
    # sibling report.html files exist at render time (s27 w2 probe).
    for _, sid in _season_ids(rumpun_root):
        if not state_path(rumpun_root, sid).is_file():
            logger.info("skip %s: no season state (no state, no render)", sid)
            continue
        try:
            # Logs its own artifact line at INFO.
            render_report(rumpun_root, sid)
        except Exception:
            logger.exception("season %s report render failed; continuing", sid)
    # Pass B: re-render against the complete sibling set (pass A created
    # every report.html the strip links to), so consecutive runs over
    # unchanged bytes converge to identical pages.
    for _, sid in _season_ids(rumpun_root):
        if not state_path(rumpun_root, sid).is_file():
            continue
        try:
            render_report(rumpun_root, sid)
        except Exception:
            logger.exception("season %s pass-B render failed; continuing", sid)
    try:
        # Also renders the discoveries pages; logs the index line itself.
        render_index(rumpun_root)
    except Exception:
        logger.exception("total failure: index render failed for root %s", rumpun_root)
        return 1
    logger.info("discoveries list -> %s", rumpun_root / "runs" / "discoveries" / "index.html")
    for rec in _discovery_records(rumpun_root):
        logger.info("discovery %s -> %s", rec["id"], _discovery_page(rumpun_root, rec["id"]))
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    sys.exit(main())
