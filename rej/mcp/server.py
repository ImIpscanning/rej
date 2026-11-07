"""Dependency-free MCP stdio server exposing REJ's read-only JAR inspector.

Model Context Protocol JSON-RPC messages are one JSON object per line on stdout.
All diagnostics go to stderr, and Java archives are never executed.
"""
from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from .. import __version__
from .schemas import TOOLS, MAX_OUTPUT_CLASSES, MAX_OUTPUT_ERRORS
from .tools import call_tool

SUPPORTED_PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
MAX_MESSAGE_BYTES = 1024 * 1024

def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    """Return a JSON-RPC response or None for client notifications."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": message.get("id") if isinstance(message, dict) else None,
                "error": {"code": -32600, "message": "Invalid JSON-RPC request"}}
    if "id" not in message:  # Notifications, including notifications/initialized
        return None
    request_id = message["id"]
    method = message.get("method")
    params = message.get("params", {})
    if method == "initialize":
        requested = params.get("protocolVersion", "2025-06-18") if isinstance(params, dict) else None
        protocol = requested if requested in SUPPORTED_PROTOCOLS else "2025-06-18"
        result = {
            "protocolVersion": protocol,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "rej", "version": __version__},
            "instructions": "REJ only performs read-only, static analysis on local JARs supplied by the user. "
                            "Do not treat JAR metadata as proof of safety or recoverable original source. "
                            "Java decompilation is not available via REJ MCP.",
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        if not isinstance(params, dict) or not isinstance(params.get("name"), str):
            return {"jsonrpc": "2.0", "id": request_id,
                    "error": {"code": -32602, "message": "Expected tool name"}}
        try:
            value = call_tool(params["name"], params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "isError": False}
        except Exception as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def serve(stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
    """Run MCP over stdio. Each request and response is a single JSON line."""
    instream = stdin if stdin is not None else sys.stdin
    outstream = stdout if stdout is not None else sys.stdout
    for line in instream:
        try:
            if len(line.encode("utf-8")) > MAX_MESSAGE_BYTES:
                raise ValueError("MCP message exceeds 1 MiB limit")
            message = json.loads(line)
            response = handle_message(message)
            if response is not None:
                outstream.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
                outstream.flush()
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            outstream.write(json.dumps({"jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": str(exc)}}) + "\n")
            outstream.flush()


if __name__ == "__main__":
    serve()
