"""rumpun statusline — one-line campaign segment for shell statusbars.

Reads only tiny state files (runs/*/_season/state.json plus the newest
harvest records), so the segment renders well inside a statusbar budget.
`rumpun statusline` prints it. `rumpun statusline --install` composes the
Claude Code statusLine setting so installing rumpun sets it up for you;
--uninstall restores the original command from the wrapper record."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MARKER = "rumpun-hud (rumpun statusline install)"


def _find_state(start: Path) -> Path | None:
    """Walk up from start to the first dir containing .rumpun/runs."""
    for cur in [start, *start.parents]:
        if (cur / ".rumpun" / "runs").is_dir():
            return cur
    return None


def _seasons(state_home: Path) -> list[dict]:
    runs = state_home / "runs"
    if not runs.is_dir():
        runs = state_home / "rimba"
    out: list[dict] = []
    for meta in sorted(runs.glob("*/_season/state.json")):
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("id"):
            out.append(data)
    out.sort(key=lambda d: d.get("started_at", 0), reverse=True)
    return out


def _verdict(ledger: Path, sid: str) -> str:
    for harvest in sorted(ledger.glob(f"*_{sid}-harvest.md")):
        try:
            m = re.search(r"^verdict:\s*(\S+)",
                          harvest.read_text(encoding="utf-8"), re.M)
        except OSError:
            return ""
        if m:
            return m.group(1)
    return ""


def segment(start: Path) -> str:
    """One status line: running season with lane states, then the last
    two closed seasons with their ledger verdicts when recorded."""
    root = _find_state(start)
    if root is None:
        return ""
    state_home = root / ".rumpun"
    seasons = _seasons(state_home)
    if not seasons:
        return ""
    parts = ["rumpun:"]
    latest = seasons[0]
    if latest.get("status") == "running":
        lanes = ",".join(
            f"{name}:{(info or {}).get('state', '?')}"
            for name, info in sorted((latest.get("agents") or {}).items())
        ) or "spawning"
        parts.append(f"{latest['id']} run ({lanes})")
    shown = 0
    for s in seasons:
        if shown >= 2:
            break
        if s.get("status") == "running":
            continue
        sid = str(s["id"])
        verdict = _verdict(state_home / "ledger", sid)
        parts.append(f"{sid} {verdict or s.get('status', '?')}")
        shown += 1
    return " ".join(parts)


def install(claude_home: Path, project: Path) -> int:
    """Compose the Claude statusLine: run the original command first, then
    append the rumpun segment pinned to the given project dir."""
    settings_path = claude_home / "settings.json"
    wrapper = claude_home / "hud" / "rumpun-hud.sh"
    settings: dict = {}
    if settings_path.is_file():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    original = (settings.get("statusLine") or {}).get("command", "")
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(
        "#!/bin/sh\n"
        f"# {MARKER}\n"
        "# original command:\n"
        f"ORIG={json.dumps(original)}\n"
        'eval "$ORIG"\n'
        'printf "\\n"\n'
        f'rumpun statusline --home "{project}"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    settings["statusLine"] = {"type": "command", "command": f"sh {wrapper}"}
    settings_path.write_text(json.dumps(settings, indent=2) + "\n",
                             encoding="utf-8")
    print(f"statusline wired -> {wrapper}")
    return 0


def uninstall(claude_home: Path) -> int:
    """Restore the original statusLine command and drop the wrapper."""
    settings_path = claude_home / "settings.json"
    wrapper = claude_home / "hud" / "rumpun-hud.sh"
    original = ""
    if wrapper.is_file():
        text = wrapper.read_text(encoding="utf-8")
        m = re.search(r"^ORIG=(.*)$", text, re.M)
        if m:
            original = json.loads(m.group(1))
        wrapper.unlink()
    if settings_path.is_file():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        command = (settings.get("statusLine") or {}).get("command", "")
        if "rumpun-hud.sh" in command:
            if original:
                settings["statusLine"] = {"type": "command",
                                          "command": original}
            else:
                settings.pop("statusLine", None)
            settings_path.write_text(json.dumps(settings, indent=2) + "\n",
                                     encoding="utf-8")
    print("statusline restored")
    return 0


def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="rumpun.statusline")
    ap.add_argument("--home", default=str(Path.cwd()),
                    help="project dir holding .rumpun (searched upward "
                    "from the given path)")
    args = ap.parse_args()
    print(segment(Path(args.home)), end="")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
