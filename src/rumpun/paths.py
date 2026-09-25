"""rumpun paths — directory-name resolution for the s45 rename.

Each renamed directory has exactly one resolver here. The new name wins
when its directory exists; otherwise the legacy name resolves, so the
historical seasons keep their records. Writes land inside whichever tree
the project actually has (ledger_new), and the ledger resolvers anchor
root at the state dir (state_dir) so writes and citation scans share one
tree (issue #2).
"""

from __future__ import annotations

from pathlib import Path


def _resolve(root: Path, new: str, old: str) -> Path:
    """root/new when it is a directory, else root/old (the alias)."""
    new_dir = root / new
    if new_dir.is_dir():
        return new_dir
    return root / old


def seasons_dir(root: Path) -> Path:
    """The seasons directory: seasons/ when present, else legacy musim/."""
    return _resolve(root, "seasons", "musim")


STATE_DIR = ".rumpun"  # the project state dir; scaffold.RUMPUN_DIR scaffolds it


def state_dir(root: Path) -> Path:
    """The state dir: root/.rumpun when root is the project dir, else root.

    Citations resolve against .rumpun/ (DESIGN.md): the lint CLI derives
    its scan root from a season path under .rumpun/. A caller that hands
    a resolver the PROJECT dir instead (issue #2: append_record with the
    project dir) must still land where lint scans, so descend when the
    scaffolded state dir is present (the s79 w2 contract pin models the
    post-init shape: .rumpun/ exists, rumpun.yaml may not yet). A root
    that already is the state dir has no nested .rumpun/, so the
    resolution is idempotent.
    """
    if (root / STATE_DIR).is_dir():
        return root / STATE_DIR
    return root


def ledger_dir(root: Path) -> Path:
    """The evidence ledger: ledger/ when present, else legacy akar/.

    Resolved over state_dir(root), so a project-dir root and the state-dir
    root scan the same tree the write resolver (ledger_new) fills.
    """
    return _resolve(state_dir(root), "ledger", "akar")


def runs_dir(root: Path) -> Path:
    """The run tree: runs/ when present, else legacy rimba/."""
    return _resolve(root, "runs", "rimba")


def ledger_new(root: Path) -> Path:
    """The ledger directory for writes: the tree the project actually has.

    Writes must land where _citation_resolves scans (issue #2), so the
    existing ledger/ wins, a legacy akar/-only tree keeps receiving the
    writes (its records must not lose their citations), and a root with
    neither tree falls back to the new name.
    """
    resolved = state_dir(root)
    if (resolved / "ledger").is_dir():
        return resolved / "ledger"
    if (resolved / "akar").is_dir():
        return resolved / "akar"
    return resolved / "ledger"


def runs_new(root: Path) -> Path:
    """The run tree for writes: always the new name."""
    return root / "runs"


def events_dir(root: Path) -> Path:
    """The event bus (#30): events/ under the state dir, created on demand."""
    return state_dir(root) / "events"
