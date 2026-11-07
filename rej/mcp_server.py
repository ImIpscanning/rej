"""Dependency-free MCP stdio server exposing REJ's read-only JAR inspector.

Model Context Protocol JSON-RPC messages are one JSON object per line on stdout.
All diagnostics go to stderr, and Java archives are never executed.
"""
from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from . import __version__
from .archive import inspect_jar, inspect_class, compare_jars

SUPPORTED_PROTOCOLS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
MAX_OUTPUT_CLASSES = 200
MAX_OUTPUT_ERRORS = 30
MAX_MESSAGE_BYTES = 1024 * 1024

TOOLS: list[dict[str, Any]] = [
    {
        "name": "rej_inspect_jar",
        "description": "Read JAR and Minecraft plugin metadata, Java versions and a bounded class preview. Never executes the JAR.",
        "inputSchema": {
            "type": "object", "properties": {"jar_path": {"type": "string", "description": "Absolute local path to a .jar archive"}},
            "required": ["jar_path"], "additionalProperties": False,
        },
    },
    {
        "name": "rej_list_classes",
        "description": "List up to 200 Java classes in a JAR, optionally filtered by name. Read-only.",
        "inputSchema": {
            "type": "object", "properties": {
                "jar_path": {"type": "string"},
                "filter": {"type": "string", "description": "Case-insensitive substring"},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_OUTPUT_CLASSES},
            }, "required": ["jar_path"], "additionalProperties": False,
        },
    },
    {
        "name": "rej_inspect_class",
        "description": "Read fields, methods, descriptors, superclass, interfaces, and Java version of one class inside a JAR.",
        "inputSchema": {
            "type": "object", "properties": {
                "jar_path": {"type": "string"}, "class_name": {"type": "string", "description": "Example: com.example.Main"},
            }, "required": ["jar_path", "class_name"], "additionalProperties": False,
        },
    },
    {
        "name": "rej_compare_jars",
        "description": "Compare two JAR versions by class path and SHA-256, without executing them.",
        "inputSchema": {
            "type": "object", "properties": {
                "old_path": {"type": "string"}, "new_path": {"type": "string"},
            }, "required": ["old_path", "new_path"], "additionalProperties": False,
        },
    },
]


def _validate_arguments(name: str, arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be a JSON object")
    spec = next((tool["inputSchema"] for tool in TOOLS if tool["name"] == name), None)
    if spec is None:
        raise ValueError(f"Unknown REJ tool: {name}")
    if any(key not in spec["properties"] for key in arguments):
        raise ValueError("Unexpected arguments supplied")
    for key in spec["required"]:
        if not isinstance(arguments.get(key), str) or not arguments[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    if "filter" in arguments and not isinstance(arguments["filter"], str):
        raise ValueError("filter must be a string")
    if "limit" in arguments:
        value = arguments["limit"]
        if type(value) is not int or not 1 <= value <= MAX_OUTPUT_CLASSES:
            raise ValueError(f"limit must be an integer between 1 and {MAX_OUTPUT_CLASSES}")
    return arguments


def call_tool(name: str, arguments: Any) -> dict[str, Any]:
    """Dispatch exactly four static, read-only tools; no arbitrary shell execution."""
    args = _validate_arguments(name, arguments)
    if name == "rej_inspect_jar":
        report = inspect_jar(args["jar_path"])
        classes = report["classes"]
        errors = report["errors"]
        report["classes"] = classes[:MAX_OUTPUT_CLASSES]
        report["errors"] = errors[:MAX_OUTPUT_ERRORS]
        report["classes_truncated"] = max(0, len(classes) - MAX_OUTPUT_CLASSES)
        report["errors_truncated"] = max(0, len(errors) - MAX_OUTPUT_ERRORS)
        return report
    if name == "rej_list_classes":
        classes = inspect_jar(args["jar_path"])["classes"]
        filtered = [c for c in classes if args.get("filter", "").casefold() in c["name"].casefold()]
        limit = args.get("limit", 100)
        return {"total_matches": len(filtered), "classes": filtered[:limit], "truncated": max(0, len(filtered) - limit)}
    if name == "rej_inspect_class":
        detail = inspect_class(args["jar_path"], args["class_name"])
        for key in ("methods", "fields"):
            members = detail[key]
            detail[key] = members[:MAX_OUTPUT_CLASSES]
            detail[f"{key}_truncated"] = max(0, len(members) - MAX_OUTPUT_CLASSES)
        return detail
    if name == "rej_compare_jars":
        return compare_jars(args["old_path"], args["new_path"])
    raise ValueError(f"Unknown REJ tool: {name}")


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
