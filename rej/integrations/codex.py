"""Codex MCP registration helpers, using Windows-safe TOML strings."""
import json
from .base import mcp_command, quote_arg


def codex_config() -> str:
    exe, args = mcp_command()
    return '[mcp_servers.rej]\ncommand = ' + json.dumps(exe) + '\nargs = [' + ', '.join(json.dumps(arg) for arg in args) + ']\n'


def codex_command() -> str:
    exe, args = mcp_command()
    return 'codex mcp add rej -- ' + ' '.join(quote_arg(x) for x in [exe,*args])
