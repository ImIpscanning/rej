"""MCP configuration formatting independent of presentation framework."""
from ..integrations import claude_config, codex_config, claude_command, codex_command


def config_for(client:str)->str:
    return claude_config() if client=='Claude Code' else codex_config()


def install_command_for(client:str)->str:
    return claude_command() if client=='Claude Code' else codex_command()
