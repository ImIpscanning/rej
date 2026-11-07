"""Executable selection for local MCP clients."""
from pathlib import Path
import json
import sys


def launcher_path() -> Path:
    """Legacy source launcher; present in git checkouts, absent in pip installs."""
    return Path(__file__).resolve().parents[2] / 'rej_mcp.py'


def mcp_command() -> tuple[str, list[str]]:
    launcher = launcher_path()
    if launcher.is_file():
        return sys.executable, [str(launcher)]
    return sys.executable, ['-m', 'rej', 'mcp']


def quote_arg(argument: str) -> str:
    # subprocess.list2cmdline safely quotes Windows path arguments.
    import subprocess
    return subprocess.list2cmdline([argument]) if sys.platform == 'win32' else __import__('shlex').quote(argument)
