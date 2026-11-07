"""MCP contract and GUI import tests, requiring no external MCP SDK or display."""
from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile

from rej.integrations import launcher_path, claude_config, codex_config, claude_command, codex_command
from rej.mcp_server import TOOLS, handle_message, serve, call_tool, MAX_OUTPUT_CLASSES


class MCPTests(unittest.TestCase):
    def test_initialize_and_notification(self):
        result = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
        self.assertEqual(result["result"]["serverInfo"]["name"], "rej")
        self.assertEqual(result["result"]["protocolVersion"], "2025-06-18")
        self.assertIsNone(handle_message({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_tool_list(self):
        result = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertEqual(len(result["result"]["tools"]), 4)
        self.assertEqual({t["name"] for t in TOOLS}, {"rej_inspect_jar", "rej_list_classes", "rej_inspect_class", "rej_compare_jars"})

    def test_invalid_tool_arguments(self):
        response = handle_message({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "rej_inspect_jar", "arguments": {"jar_path": 123}}})
        self.assertTrue(response["result"]["isError"])
        with self.assertRaisesRegex(ValueError, "limit must"):
            call_tool("rej_list_classes", {"jar_path": "unknown.jar", "limit": MAX_OUTPUT_CLASSES + 1})
        with self.assertRaisesRegex(ValueError, "Unexpected arguments"):
            call_tool("rej_inspect_jar", {"jar_path": "unknown.jar", "shell": "whoami"})

    def test_stdio_frames(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "ping"},
        ]
        inp = io.StringIO("\n".join(json.dumps(x) for x in requests) + "\n")
        out = io.StringIO()
        serve(inp, out)
        frames = [json.loads(s) for s in out.getvalue().splitlines()]
        self.assertEqual([f["id"] for f in frames], [1, 2, 3])
        self.assertEqual(frames[2]["result"], {})

    def test_jar_inspection_via_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar = Path(tmp) / "demo.jar"
            with zipfile.ZipFile(jar, "w") as out:
                out.writestr("plugin.yml", "name: Test\nversion: 1\n")
            inspect = call_tool("rej_inspect_jar", {"jar_path": str(jar)})
            self.assertEqual(inspect["metadata"]["plugin"]["name"], "Test")
            self.assertEqual(call_tool("rej_list_classes", {"jar_path": str(jar)})["total_matches"], 0)
            diff = call_tool("rej_compare_jars", {"old_path": str(jar), "new_path": str(jar)})
            self.assertEqual(diff["added"], [])

    def test_launcher_real_process(self):
        command = [sys.executable, str(launcher_path())]
        payload = json.dumps({"jsonrpc": "2.0", "id": 10, "method": "tools/list"}) + "\n"
        result = subprocess.run(command, input=payload, text=True, capture_output=True, timeout=10,
                                cwd=tempfile.gettempdir())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["id"], 10)

    def test_configs(self):
        parsed = json.loads(claude_config())
        self.assertTrue(Path(parsed["mcpServers"]["rej"]["args"][0]).is_file())
        data = tomllib.loads(codex_config())
        self.assertEqual(data["mcp_servers"]["rej"]["command"], sys.executable)
        self.assertIn("mcp add", codex_command())
        self.assertIn("mcp add", claude_command())

    def test_gui_import_does_not_open_window(self):
        try:
            from rej.gui import REJDesktop
        except ImportError as exc:
            self.skipTest(f"Tkinter unavailable: {exc}")
        self.assertTrue(callable(REJDesktop))


if __name__ == "__main__":
    unittest.main()
