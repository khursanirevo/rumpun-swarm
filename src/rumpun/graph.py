"""rumpun graph — render a season pipeline DAG as mermaid (review surface, P31 ruling)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rumpun import yamlio


def re_safe(name: str) -> str:
    return "n_" + re.sub(r"\W", "_", name)


def mermaid(season_path: Path) -> str:
    season: dict[str, Any] = yamlio.load(season_path)
    pipeline = season.get("methodology", {}).get("pipeline", [])
    lines = ["graph TD"]
    producers: dict[str, str] = {}
    for node in pipeline:
        phase = node.get("phase", "?")
        lines.append(f'  {re_safe(phase)}["{phase} ({node.get("primitive", "?")})"]')
        writes = node.get("writes")
        for artifact in [writes] if isinstance(writes, str) else (writes or []):
            producers[artifact] = phase
    for node in pipeline:
        phase = node.get("phase", "?")
        reads = node.get("reads")
        for artifact in [reads] if isinstance(reads, str) else (reads or []):
            producer = producers.get(artifact)
            if producer and producer != phase:
                lines.append(f'  {re_safe(producer)} -->|"{artifact}"| {re_safe(phase)}')
    if season.get("mode") == "collab":
        lane = season.get("collab", {}).get("lane", "")
        lines.append(f'  lane["collab lane: {lane}"]')
    return "\n".join(lines)
