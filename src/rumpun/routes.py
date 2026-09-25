"""Agent-route detection: which models can this machine spawn?

Build order step 2. Port of kancil ``routes.py`` (verified in kancil source,
2026-09-14). Spawn routing hides in three places: which CLI binaries exist,
which env vars point a binary at a proxy (``ANTHROPIC_BASE_URL`` + token ->
z.ai-style GLM proxy vs claude.ai login), and per-model flags. ``rumpun
models`` prints the route table; ``--write`` fills the ``routes:`` block of
rumpun.yaml. No function here ever prints or returns a token VALUE — only
var names and endpoints.

The env-strip prefix (STRIP_ENV) is the known list of vars the claude binary
reads for routing/overrides; extend it when a new override var ships (drift
is visible in the detector output, which prints exactly which vars it saw).
Rumpun adds ANTHROPIC_DEFAULT_FABLE_MODEL to kancil's six (tier-default var
observed live in this environment, 2026-09-14).
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

STRIP_ENV = (
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
)

KNOWN_CLIS = ("claude", "codex", "gemini", "opencode", "aider")

# M11 (codex-review-2026-09-14): generated commands carry a concrete default
# model, never a `<model>` placeholder. Documented default is the operator's
# current fable id; ANTHROPIC_DEFAULT_FABLE_MODEL overrides it when set
# (claude_routes).
DEFAULT_CLAUDE_MODEL = "claude-fable-5-1"

# Well-known proxy hosts -> family label. Unknown hosts fall back to hostname.
_PROXY_HOST_LABELS = {
    "api.z.ai": "glm",
    "api.bigmodel.cn": "glm",
}


class RoutesError(Exception):
    pass


def _strip_prefix() -> str:
    """The literal ``env -u VAR ...`` prefix for login-route spawns."""
    return "env " + " ".join(f"-u {v}" for v in STRIP_ENV)


def proxy_family(base_url: str) -> str:
    """Family label for a proxied claude route (host-derived)."""
    host = (urlparse(base_url).hostname or "").lower()
    for known, label in _PROXY_HOST_LABELS.items():
        if host == known or host.endswith("." + known):
            return label
    return host.split(".")[0] or "proxy"


def family_label(cmd: str, env: dict[str, str] | None = None) -> str:
    """Model-TRUE family label for an agent command.

    Precedence:
    1. ``--model X`` present -> X (explicit wins: fable, glm-5.2...).
    2. claude in cmd, ANTHROPIC_BASE_URL in the EFFECTIVE env, and the
       strip prefix absent -> proxy label (glm for z.ai).
    3. Non-claude known binary anywhere in the cmd -> its name.
    4. First token basename (custom scripts keep their label).
    """
    env = dict(os.environ if env is None else env)
    lowered = cmd.lower()
    m = re.search(r"(?:--model|-m)[ =]([A-Za-z0-9._-]+)", cmd)
    if m:
        return m.group(1).lower()
    has_claude = re.search(r"\bclaude\b", lowered) is not None
    stripped = " -u anthropic_base_url" in lowered
    if has_claude and env.get("ANTHROPIC_BASE_URL") and not stripped:
        return proxy_family(env["ANTHROPIC_BASE_URL"])
    for name in KNOWN_CLIS:
        if re.search(rf"\b{name}\b", lowered):
            return name
    token = cmd.strip().split()[0] if cmd.strip() else ""
    return token.rsplit("/", 1)[-1].lower()


def detect_clis(timeout: float = 5.0) -> list[dict[str, str]]:
    """Which agent CLIs are on PATH, with versions when cheap."""
    rows = []
    for name in KNOWN_CLIS:
        path = shutil.which(name)
        if not path:
            rows.append({"name": name, "present": "no", "version": ""})
            continue
        version = ""
        try:
            out = subprocess.run(
                [path, "--version"], capture_output=True, text=True,
                timeout=timeout, check=False,
            )
            version = (out.stdout or out.stderr or "").strip().splitlines()[
                0][:40]
        except (OSError, subprocess.TimeoutExpired):
            version = ""
        rows.append({
            "name": name, "present": "yes",
            "version": version or "present (version n/a)",
        })
    return rows


def codex_model_routes() -> list[dict[str, str]]:
    """Spawn-ready routes for every model the codex login exposes.

    Reads ``~/.codex/models_cache.json`` (refreshed by the codex CLI at
    login/use) and emits one ``codex exec -m <model>`` template per slug
    (gpt-6-astra, gpt-5.6-sol, ...). Falls back to the default codex route
    when no cache exists.
    """
    base = "codex exec --dangerously-bypass-approvals-and-sandbox"
    cache = Path.home() / ".codex" / "models_cache.json"
    slugs: list[str] = []
    with contextlib.suppress(OSError, json.JSONDecodeError, ValueError):
        data = json.loads(cache.read_text(encoding="utf-8"))
        raw = data.get("models") if isinstance(data, dict) else None
        for item in raw or []:
            slug = item.get("slug") or item.get("id")
            if slug:
                slugs.append(str(slug))
    if not slugs:
        return [{
            "family": "codex",
            "desc": "default codex model",
            "command": f"{base} {{prompt}}",
        }]
    return [
        {
            "family": slug.lower(),
            "desc": f"codex model {slug}",
            "command": f"{base} -m {slug} {{prompt}}",
        }
        for slug in slugs
    ]


def claude_routes(env: dict[str, str] | None = None) -> list[dict[str, str]]:
    """Every claude-binary route on this machine.

    Returns spawn-ready dicts: family label, one-line description, and the
    exact spawn command template. The env-strip route is ALWAYS listed when
    a claude binary exists — it is how the claude.ai login is reached from
    a proxied shell. The env-strip route carries a CONCRETE default model
    (ANTHROPIC_DEFAULT_FABLE_MODEL when set, else DEFAULT_CLAUDE_MODEL) —
    M11 (codex-review-2026-09-14).
    """
    env = dict(os.environ if env is None else env)
    routes: list[dict[str, str]] = []
    base = env.get("ANTHROPIC_BASE_URL", "")
    tiers = {
        tier: env[f"ANTHROPIC_DEFAULT_{tier.upper()}_MODEL"]
        for tier in ("sonnet", "opus", "haiku", "fable")
        if env.get(f"ANTHROPIC_DEFAULT_{tier.upper()}_MODEL")
    }
    if base:
        fam = proxy_family(base)
        desc = f"proxy {base}"
        if tiers:
            desc += " — tiers: " + ", ".join(f"{t}={m}" for t, m in tiers.items())
        routes.append({
            "family": fam,
            "desc": desc,
            "command": "cat {prompt} | claude -p --dangerously-skip-permissions",
            "env_note": f"inherited env (base_url + {len(tiers)} tier default var(s) set)",
        })
    login_desc = "claude.ai login (subscription) via env-strip"
    tier_note = ""
    if tiers:
        tier_note = " + --model <name> (tier defaults are ALSO env-pinned and must be stripped)"
    model = tiers.get("fable") or DEFAULT_CLAUDE_MODEL
    routes.append({
        "family": "claude",
        "desc": login_desc + (tier_note if tiers else ""),
        "command": (
            f"{_strip_prefix()} sh -c 'cat {{prompt}} | claude -p "
            f"--dangerously-skip-permissions --model {model}'"
        ),
        "env_note": f"strip prefix removes {len(STRIP_ENV)} routing vars",
    })
    return routes


def route_table() -> list[dict[str, str]]:
    """Combined spawn-ready route list (claude-binary routes, then codex)."""
    table = list(claude_routes())
    table.extend(codex_model_routes())
    return table


def _sh_check(cmd: str) -> None:
    """Syntax-check one route command with /bin/sh -n; raise on non-zero.

    M11: a command that cannot parse as sh is never written to the config.
    ``{prompt}`` is a plain sh word (no brace expansion in /bin/sh), so
    command templates are checked exactly as written.
    """
    proc = subprocess.run(
        ["/bin/sh", "-n"],
        input=cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        msg = (
            f"route command fails /bin/sh -n (rc={proc.returncode}):"
            f" {proc.stderr.strip()}\n  cmd: {cmd}"
        )
        raise RoutesError(msg)


def write_routes(cfg_path: Path) -> int:
    """Fill the ``routes: {}`` placeholder line of rumpun.yaml.

    Text-level single-line patch so scaffold comments survive. Raises
    RoutesError when the placeholder is missing (already filled, or not a
    scaffolded config), or when any generated command fails /bin/sh -n
    (M11) — checked before any byte of the config is written.
    """
    text = cfg_path.read_text(encoding="utf-8")
    table = route_table()
    for route in table:
        _sh_check(route["command"])
    out: list[str] = []
    patched = False
    for line in text.splitlines():
        if re.match(r"^routes:\s*\{\}\s*(#.*)?$", line):
            out.append("routes:")
            for route in table:
                cmd = route["command"].replace("'", "''")
                out.append(f"  {route['family']}: '{cmd}'")
            patched = True
        else:
            out.append(line)
    if not patched:
        msg = "rumpun.yaml has no empty `routes: {}` line to fill (already written?)"
        raise RoutesError(msg)
    cfg_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(table)


def redetect_routes(cfg_path: Path) -> list[str]:
    """Re-read detection against an existing rumpun.yaml and write.

    ``routes: {}`` placeholder -> full fill (write_routes path); every
    detected key returned. Filled block -> the detected table diffs
    against the block's keys; only new keys append after the last
    existing entry (existing lines byte-untouched: a filled block
    carries hand-tuned templates — the s125 finding; a redetect never
    clobbers). A second run adds nothing and writes no bytes. No
    ``routes:`` key at all -> RoutesError. Every generated command
    passes /bin/sh -n before any byte is written (the M11 rule).
    """
    lines = cfg_path.read_text(encoding="utf-8").splitlines()
    table = route_table()
    for route in table:
        _sh_check(route["command"])
    if any(re.match(r"^routes:\s*\{\}\s*(#.*)?$", line) for line in lines):
        write_routes(cfg_path)
        return [route["family"] for route in table]
    start = None
    for idx, line in enumerate(lines):
        if re.match(r"^routes:\s*(#.*)?$", line):
            start = idx
            break
    if start is None:
        msg = (
            "rumpun.yaml has no `routes:` block (scaffold placeholder or"
            " filled); a redetect needs one"
        )
        raise RoutesError(msg)
    existing: dict[str, int] = {}
    for idx in range(start + 1, len(lines)):
        line = lines[idx]
        if line and not line[0].isspace() and not line.startswith("#"):
            break  # next top-level key: the block ended
        m = re.match(r"^  ([^\s#][^:]*):\s", line)
        if m:
            existing[m.group(1)] = idx
    missing = [
        fam
        for fam in dict.fromkeys(r["family"] for r in table)
        if fam not in existing
    ]
    if not missing:
        return []
    insert_at = max(existing.values()) + 1 if existing else start + 1
    additions: list[str] = []
    for fam in missing:
        cmd = next(r["command"] for r in table if r["family"] == fam)
        escaped = cmd.replace("'", "''")
        additions.append(f"  {fam}: '{escaped}'")
    out = lines[:insert_at] + additions + lines[insert_at:]
    cfg_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return missing
