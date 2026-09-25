"""rumpun lint — the P27 preflight boundary.

Checks a season YAML before anything spawns: structure, DAG acyclicity, artifact
contracts, evidence citations, primary_change declaration, benih sanity, autonomy
invariants. Errors block start; warnings do not.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rumpun import akar, yamlio

logger = logging.getLogger(__name__)

PRIMITIVES = {
    "analyze", "rank_gaps", "hypothesize", "plan", "falsify",
    "execute", "evaluate", "share", "harvest", "audit", "research",
}
CHANGE_TYPES = {"add", "remove", "rewire", "retune"}
BUNDLE_CLASSES = {"pipeline_switch", "emergency", "rollback_restore", "free_bundle"}
STAGES = {"manual", "panel", "free"}
KNOWLEDGE = {"none", "partial", "full"}
REQUIRED_INVARIANTS = {"goal_immutable", "budget_cap", "falsify_required"}
ID_RE = re.compile(r"^s\d+$")

# H4 benih-name containment (codex review 2026-09-14, H4; lands s18): a benih
# name becomes a workspace directory under rimba/<sid>/ and joins paths
# directly, so the engine joins whatever lint admits. "_season" is the
# harness's own directory; names are matched fully, not just prefix-checked,
# so "/", "\", "..", and any other off-charset text fails the pattern.
BENIH_NAME_MAX = 32
BENIH_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
RESERVED_BENIH_NAMES = frozenset({"_season"})


def _benih_name_error(name: Any) -> str | None:
    """H4 containment for one benih name; None when the name is contained.

    The returned message names the offending benih (the name appears
    verbatim); the empty-name message says "non-empty".
    """
    if not isinstance(name, str) or not name:
        return "benih name must be a non-empty string"
    if name in RESERVED_BENIH_NAMES:
        return (
            f"benih name '{name}' is reserved: _season is the harness's "
            "own directory under the season"
        )
    if not 1 <= len(name) <= BENIH_NAME_MAX:
        return f"benih name '{name}' must be 1-32 characters, got {len(name)}"
    if not BENIH_NAME_RE.match(name):
        return (
            f"benih name '{name}' must match [a-z0-9][a-z0-9_-]*: '/', '\\', "
            "'..' and other off-charset text are not allowed"
        )
    return None


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    message: str
    path: str = ""


class LintError(Exception):
    pass


def _find_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".rumpun" / "rumpun.yaml").is_file():
            return candidate / ".rumpun"
    msg = f"no .rumpun/rumpun.yaml found above {start}; run 'rumpun init' first"
    raise LintError(msg)


def _artifact_producers(pipeline: list[dict[str, Any]]) -> dict[str, str]:
    producers: dict[str, str] = {}
    for node in pipeline:
        phase = node.get("phase", "?")
        writes = node.get("writes")
        for artifact in [writes] if isinstance(writes, str) else (writes or []):
            if artifact in producers:
                msg = f"two nodes write {artifact}: {producers[artifact]} and {phase}"
                raise LintError(msg)
            producers[artifact] = phase
    return producers


def _dag_edges(pipeline: list[dict[str, Any]], producers: dict[str, str]) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = {node["phase"]: set() for node in pipeline}
    for node in pipeline:
        reads = node.get("reads")
        for artifact in [reads] if isinstance(reads, str) else (reads or []):
            producer = producers.get(artifact)
            if producer is None:
                msg = f"node '{node['phase']}' reads {artifact}: nothing writes it"
                raise LintError(msg)
            if producer != node["phase"]:
                edges[producer].add(node["phase"])
    return edges


def _topo_order(edges: dict[str, set[str]]) -> list[str]:
    indegree = {n: 0 for n in edges}
    for targets in edges.values():
        for target in targets:
            indegree[target] += 1
    ready = sorted(n for n, d in indegree.items() if d == 0)
    order: list[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for target in sorted(edges[n]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    if len(order) != len(edges):
        stuck = sorted(set(edges) - set(order))
        msg = f"pipeline is not a DAG — cycle through: {', '.join(stuck)}"
        raise LintError(msg)
    return order


def _reaches(edges: dict[str, set[str]], src: str, dst: str) -> bool:
    seen: set[str] = set()
    stack = [src]
    while stack:
        n = stack.pop()
        if n == dst:
            return True
        for t in edges.get(n, ()):
            if t not in seen:
                seen.add(t)
                stack.append(t)
    return False


def _citation_resolves(citation: str, root: Path) -> bool:
    """H7 (codex-review-2026-09-14): a citation resolves only against the
    exact declared record AND a matching body digest.

    akar:<id>@<digest> resolves when (1) record <id> is declared in akar/
    (the same scan akar.find_record uses: the file whose first "id:" line
    declares the id; no substring ids), and (2) the cited digest equals the
    record's recorded body digest — the full 64 hex chars or a unique
    prefix of >= 8. Anything else does not resolve, so altered evidence no
    longer passes the evolution gate.
    """
    m = re.match(r"^akar:([\w.-]+)@([0-9a-f]{8,64})$", citation)
    if not m:
        return False
    record_id, cited = m.groups()
    try:
        path = akar.find_record(root, record_id)
    except akar.AkarError:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        logger.exception("cannot read akar record %s", path)
        return False
    lines = text.splitlines()
    # akar.append_record layout: four header lines, the body, then a final
    # "sha256: <hex>" line digesting the utf-8 body bytes exactly (the body
    # is recoverable as "\n".join(lines[4:-1])).
    if len(lines) < 6 or not lines[-1].startswith("sha256: "):
        logger.warning(
            "akar record %s: no sha256 line; citation cannot be digest-checked", path
        )
        return False
    body = "\n".join(lines[4:-1])
    actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
    # The regex floors the cited value at 8 hex chars; a prefix matches only
    # when it prefixes the recomputed digest, so >= 8 stays unambiguous.
    return actual.startswith(cited)


def lint(season_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    root = _find_root(season_path)
    season = yamlio.load(season_path)

    def err(msg: str) -> None:
        findings.append(Finding("error", msg, str(season_path)))

    def warn(msg: str) -> None:
        findings.append(Finding("warning", msg, str(season_path)))

    # M9 (codex-review-2026-09-14): container-type checks run before
    # traversal — malformed structures are domain errors naming the path,
    # never AttributeError/TypeError escapes.
    if not isinstance(season, dict):
        err(f"season document must be a mapping, got {type(season).__name__}")
        return findings

    # --- required keys
    for key in ("id", "goal", "metric", "mode", "methodology", "benih", "stop"):
        if key not in season:
            err(f"missing required key: {key}")
    if findings:
        return findings

    if not ID_RE.match(str(season["id"])):
        err(f"id '{season['id']}' does not match s<N>")
    if not str(season["goal"]).strip():
        err("goal is empty")
    if not str(season["metric"]).strip():
        err("metric is empty")
    if season["mode"] not in ("fight", "collab"):
        err(f"mode must be fight|collab, got {season['mode']!r}")
    if season["mode"] == "collab" and "collab" not in season:
        err("mode collab requires a collab: block (lane, share, merge)")

    # --- autonomy (campaign-level, from rumpun.yaml)
    project = yamlio.load(root / "rumpun.yaml")
    autonomy = project.get("autonomy", {})
    if not isinstance(autonomy, dict):
        err(f"rumpun.yaml autonomy must be a mapping, got {type(autonomy).__name__}")
        autonomy = {}
    stage = autonomy.get("stage", "manual")
    if stage not in STAGES:
        err(f"rumpun.yaml autonomy.stage must be manual|panel|free, got {stage!r}")
    inv = set(autonomy.get("invariants", []))
    missing = REQUIRED_INVARIANTS - inv
    if missing:
        err(f"rumpun.yaml autonomy.invariants missing {sorted(missing)}")

    # --- methodology and pipeline
    method = season["methodology"]
    if not isinstance(method, dict):
        err(
            f"methodology must be a mapping, got {type(method).__name__} "
            "(container-type check before traversal)"
        )
        return findings
    if "approach" not in method:
        err("methodology.approach is required")
    pipeline = method.get("pipeline")
    if not pipeline or not isinstance(pipeline, list):
        err("methodology.pipeline must be a non-empty list of nodes")
        return findings
    bad_nodes = [(i, n) for i, n in enumerate(pipeline) if not isinstance(n, dict)]
    if bad_nodes:
        for i, n in bad_nodes:
            err(
                f"methodology.pipeline[{i}] must be a mapping, got {type(n).__name__}"
            )
        return findings

    phases = [n.get("phase") for n in pipeline]
    if len(set(phases)) != len(phases):
        err(f"duplicate phase names: {phases}")

    for node in pipeline:
        phase = node.get("phase", "?")
        if node.get("primitive") not in PRIMITIVES:
            err(f"node '{phase}': primitive must be one of {sorted(PRIMITIVES)}")
        if not node.get("agent") and node.get("agents") != "benih":
            err(f"node '{phase}': needs agent or agents: benih")
        prompt = node.get("prompt")
        if not prompt:
            err(f"node '{phase}': missing prompt")
        elif not (root / prompt).is_file():
            err(f"node '{phase}': prompt not found: {prompt}")
        if "writes" not in node:
            err(f"node '{phase}': missing writes (artifact contract)")

    try:
        producers = _artifact_producers(pipeline)
        edges = _dag_edges(pipeline, producers)
        _topo_order(edges)
    except LintError as exc:
        err(str(exc))
        return findings

    # falsify pre-registration: execute must consume the falsify node's output
    phase_prims = {n["phase"]: n.get("primitive") for n in pipeline if "phase" in n}
    falsify_nodes = [p for p, prim in phase_prims.items() if prim == "falsify"]
    execute_nodes = [p for p, prim in phase_prims.items() if prim == "execute"]
    reaches = any(_reaches(edges, f, e) for f in falsify_nodes for e in execute_nodes)
    if falsify_nodes and execute_nodes and not reaches:
        err(
            "falsify does not reach execute: kill criterion is not an input to "
            "execution (must_precede violated)"
        )

    # --- evidence citations
    evidence = method.get("evidence", [])
    if evidence and not isinstance(evidence, list):
        err("methodology.evidence must be a list")
        evidence = []
    for citation in evidence or []:
        if not isinstance(citation, str) or not _citation_resolves(citation, root):
            err(f"evidence citation does not resolve in akar/: {citation!r}")

    # --- primary_change (P12)
    parent = season.get("parent")
    if parent is not None:
        change = method.get("primary_change")
        if not isinstance(change, dict):
            err("non-seed season requires methodology.primary_change")
        else:
            ctype = change.get("type")
            if ctype not in CHANGE_TYPES | BUNDLE_CLASSES:
                err(f"primary_change.type must be one of {sorted(CHANGE_TYPES | BUNDLE_CLASSES)}")
            if ctype == "free_bundle" and stage not in ("panel", "free"):
                err("free_bundle requires autonomy.stage panel|free")
            for field in ("baseline", "expected_band", "rollback", "eval_window"):
                if not change.get(field):
                    err(f"primary_change.{field} is required: state the band first")

    # --- benih
    benih = season["benih"]
    if not isinstance(benih, list) or not benih:
        err("benih must be a non-empty list")
    else:
        names = [b.get("name") for b in benih if isinstance(b, dict)]
        if len(set(names)) != len(names):
            err(f"duplicate benih names: {names}")
        for idx, b in enumerate(benih):
            if not isinstance(b, dict):
                err(f"benih[{idx}] must be a mapping, got {type(b).__name__}")
                continue
            name = b.get("name", "?")
            name_error = _benih_name_error(b.get("name"))
            if name_error:
                err(name_error)
            if not b.get("route"):
                err(f"benih '{name}': missing route")
            if b.get("knowledge") not in KNOWLEDGE:
                err(f"benih '{name}': knowledge must be one of {sorted(KNOWLEDGE)}")
            budget = b.get("budget")
            minutes = budget.get("minutes") if isinstance(budget, dict) else None
            if not isinstance(minutes, int) or minutes <= 0:
                err(f"benih '{name}': budget.minutes must be a positive int")
            prompt = b.get("prompt")
            if prompt and not (root / prompt).is_file():
                err(f"benih '{name}': prompt not found: {prompt}")

    # --- stop rules
    stop = season["stop"]
    if not isinstance(stop, dict) or not stop.get("on"):
        err("stop.on must list at least one rule")

    # --- warnings
    if stage == "free" and evidence:
        warn("stage is free: audit panel is skipped by design")
    if not evidence and parent is not None:
        warn("non-seed season has no evidence citations (lint passes; panel will not)")
    return findings
