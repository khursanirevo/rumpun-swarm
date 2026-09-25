"""s44 w2 seed check: leaks, yaml parse, tail lines.

Run from the repo root with the repo's python so pyyaml resolves.
Exits 1 on any leak hit, parse error, or missing tail line.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

import yaml

SEED = Path(__file__).resolve().parent.parent / "seed" / "kaggle-base"

TOKENS = (
    "rumpun",
    "kancil",
    "rimba",
    "musim",
    "akar",
    "khursani",
    "glm",
    "gpt",
    "codex",
    "fable",
    "operator-token",
    "hunter2",
)

SID = re.compile(r"\bs\d+\b")
ABS = re.compile(r"(?<![\w:])(/(?:[\w.-]+/)+[\w.-]+)")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    log = logging.getLogger(__name__)
    hits: list[str] = []
    for path in sorted(SEED.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(SEED).as_posix()
        text = path.read_text(encoding="utf-8")
        for no, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            hits += [f"{rel}:{no}: token {t!r}" for t in TOKENS if t in low]
            if SID.search(line):
                hits.append(f"{rel}:{no}: sid token")
            if ABS.search(line):
                hits.append(f"{rel}:{no}: absolute path")
        if rel.endswith(".yaml"):
            try:
                yaml.safe_load(text)
            except yaml.YAMLError as exc:
                hits.append(f"{rel}: yaml parse error: {exc}")
        kept = [ln for ln in text.splitlines() if ln.strip()]
        marks = [
            i
            for i, ln in enumerate(kept)
            if ln.lstrip("#").strip().startswith("Generalized from:")
        ]
        if not marks or (len(kept) - 1 - marks[-1]) > 3:
            hits.append(f"{rel}: missing Generalized-from tail line")
    if hits:
        for hit in hits:
            log.error("%s", hit)
        return 1
    log.info("seed check clean: %s", SEED)
    return 0


if __name__ == "__main__":
    sys.exit(main())
