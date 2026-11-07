"""Claude Code local MCP registration helpers."""
import json
from .base import mcp_command, quote_arg


def claude_config() -> str:
    executable, args = mcp_command()
    return json.dumps({'mcpServers': {'rej': {'command': executable, 'args': args}}}, indent=2)


def claude_command() -> str:
    exe, args = mcp_command()
    return 'claude mcp add --scope user rej -- ' + ' '.join(quote_arg(x) for x in [exe,*args])
