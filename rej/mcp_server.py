"""Compatibility import: use rej.mcp.server."""
from .mcp.server import *  # noqa: F401,F403

if __name__ == "__main__":
    serve()
