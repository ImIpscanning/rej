"""Copyable local MCP configuration examples for Claude Code and Codex."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys


def launcher_path() -> Path:
    return Path(__file__).resolve().parent.parent / "rej_mcp.py"


def connection_status() -> dict[str, bool]:
    return {"python": bool(sys.executable), "claude": shutil.which("claude") is not None,
            "codex": shutil.which("codex") is not None, "rea": shutil.which("rea") is not None}


def claude_config() -> str:
    return json.dumps({"mcpServers": {"rej": {"command": sys.executable,
        "args": [str(launcher_path())]}}}, indent=2)


def codex_config() -> str:
    # Windows paths in TOML basic quoted strings need escaping.
    return ("[mcp_servers.rej]\n"
            f"command = {json.dumps(sys.executable)}\n"
            f"args = [{json.dumps(str(launcher_path()))}]\n")


def claude_command() -> str:
    return f'claude mcp add --scope user rej -- "{sys.executable}" "{launcher_path()}"'


def codex_command() -> str:
    return f'codex mcp add rej -- "{sys.executable}" "{launcher_path()}"'
