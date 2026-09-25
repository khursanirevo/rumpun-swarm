"""s50 w1 verification: digest re-check plus plugin_lint on an emitted pack.

Independent readback: loads the draft pack from disk, re-computes the
priors/ digest, compares it to the manifest digest, and runs the full
plugin_lint guardrails. Exits nonzero on any error finding or digest
mismatch. Also logs the resolved module path so the interpreter
resolution is proven, not assumed.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from rumpun import plugin as plugin_mod

logger = logging.getLogger("verify_distill")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(sys.argv) != 2:
        logger.error("usage: verify_distill.py <pack-dir>")
        return 2
    pack_dir = Path(sys.argv[1]).resolve()
    logger.info("module under test: %s", Path(plugin_mod.__file__))
    try:
        manifest = plugin_mod.load_manifest(pack_dir)
    except plugin_mod.PluginError as exc:
        logger.error("manifest load refused: %s", exc)
        return 1
    digest = plugin_mod.priors_digest(pack_dir)
    findings = plugin_mod.plugin_lint(pack_dir, manifest)
    errors = [f for f in findings if f.severity == "error"]
    for finding in findings:
        logger.info("finding: %s", finding.message)
    if manifest.get("digest") != digest:
        logger.error(
            "digest mismatch: manifest %r vs computed %s",
            manifest.get("digest"),
            digest,
        )
        return 1
    if errors:
        logger.error("%d lint error(s) on %s", len(errors), pack_dir)
        return 1
    logger.info(
        "verify: digest matches (%s); plugin_lint: %d finding(s), 0 errors",
        digest,
        len(findings),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
