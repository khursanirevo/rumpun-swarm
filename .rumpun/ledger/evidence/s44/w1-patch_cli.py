#!/usr/bin/env python3
"""Patch the workspace cli.py copy with the `rumpun plugin lint` wiring.

Workspace-only: the repo cli.py is never touched here; the harness merges
this copy. Anchored insertions, each asserted to match exactly once; the
result is compiled before promotion (atomic replace) and re-read to confirm
every marker landed. Exits nonzero on any failure.
"""

from __future__ import annotations

import logging
import os
import py_compile
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("s44-w1-patch")

CLI = Path(__file__).resolve().parent / "src" / "rumpun" / "cli.py"

DOC_ANCHOR = "evolve plan/approve/apply/reject/rollback.\n"
DOC_INSERT = (
    "\n"
    "plugin lint <packdir> — publish guardrails for packs (operator directive seq 2): manifest\n"
    "schema, sids (s\\d+ tokens), absolute paths, private-vocabulary matches.\n"
)
IMPORT_ANCHOR = "from rumpun import lint as lint_mod\n"
IMPORT_INSERT = "from rumpun import plugin as plugin_mod\n"
CMD_ANCHOR = "def cmd_direct(args: argparse.Namespace) -> int:"
CMD_INSERT = '''def cmd_plugin_lint(args: argparse.Namespace) -> int:
    """Publish gate for a pack (operator directive, direct ledger seq 2).

    Loads manifest.yaml (missing or invalid raises PluginError, exit 1),
    runs the pack lint, logs every finding, and exits 1 on any error.
    """
    pack_dir = Path(args.packdir).resolve()
    manifest = plugin_mod.load_manifest(pack_dir)
    findings = plugin_mod.plugin_lint(pack_dir, manifest)
    errors = [f for f in findings if f.severity == "error"]
    for f in findings:
        (logger.error if f.severity == "error" else logger.warning)(f.message)
    if errors:
        logger.error("plugin lint FAILED: %d error(s)", len(errors))
        return 1
    logger.info("plugin lint OK (%d finding(s))", len(findings))
    return 0


'''
PARSER_ANCHOR = "    return parser\n"
PARSER_INSERT = '''    p_plugin = sub.add_parser(
        "plugin", help="pack tools (priors-only packs, operator directive seq 2)"
    )
    plugin_sub = p_plugin.add_subparsers(dest="plugin_command", required=True)
    p_plugin_lint = plugin_sub.add_parser(
        "lint",
        help="publish guardrails: manifest schema, sids, absolute paths, private vocabulary",
    )
    p_plugin_lint.add_argument("packdir", help="pack directory: manifest.yaml plus priors/")
    p_plugin_lint.set_defaults(func=cmd_plugin_lint)

'''
EXCEPT_ANCHOR = "audit_mod.AuditError) as exc:"
EXCEPT_REPLACE = "audit_mod.AuditError,\n            plugin_mod.PluginError) as exc:"

MARKERS = (
    "cmd_plugin_lint",
    "from rumpun import plugin as plugin_mod",
    'add_parser(\n        "plugin"',
    "plugin lint <packdir>",
    "plugin_mod.PluginError",
)


def fail(message: str) -> None:
    logger.error("%s", message)
    sys.exit(1)


def main() -> int:
    if "cmd_plugin_lint" in CLI.read_text(encoding="utf-8"):
        logger.info("already patched: %s", CLI)
        return 0
    text = CLI.read_text(encoding="utf-8")
    patches: list[tuple[str, str]] = [
        (DOC_ANCHOR, DOC_ANCHOR + DOC_INSERT),
        (IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_INSERT),
        (CMD_ANCHOR, CMD_INSERT + CMD_ANCHOR),
        (PARSER_ANCHOR, PARSER_INSERT + PARSER_ANCHOR),
        (EXCEPT_ANCHOR, EXCEPT_REPLACE),
    ]
    patched = text
    for anchor, replacement in patches:
        count = patched.count(anchor)
        if count != 1:
            fail(f"anchor matched {count} times (need 1): {anchor[:60]!r}")
        patched = patched.replace(anchor, replacement, 1)
    tmp = CLI.with_suffix(".py.tmp")
    tmp.write_text(patched, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except py_compile.PyCompileError as exc:
        tmp.unlink(missing_ok=True)
        fail(f"patched cli.py does not compile: {exc}")
    result = tmp.read_text(encoding="utf-8")
    for marker in MARKERS:
        if marker not in result:
            fail(f"marker missing after patch: {marker!r}")
    os.replace(tmp, CLI)
    logger.info("patched %s (5 hunks, all markers present, compiles)", CLI)
    return 0


if __name__ == "__main__":
    sys.exit(main())
