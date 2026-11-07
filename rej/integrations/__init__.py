"""Local integrations with Claude Code, Codex and optional REA detection."""
import shutil
import sys
from .base import launcher_path, mcp_command
from .claude import claude_command, claude_config
from .codex import codex_command, codex_config
from .rea import rea_status


def connection_status() -> dict[str, bool]:
    return {'python': bool(sys.executable), 'claude': shutil.which('claude') is not None,
            'codex': shutil.which('codex') is not None, 'rea': rea_status()['installed']}
