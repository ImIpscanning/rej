# REJ MCP Integration — Claude Code & Codex

REJ v0.3.0 runs a local, **read-only MCP server over stdio**. It exposes Java JAR inspection to agents using the Model Context Protocol without uploading archive bytes to a REJ service or executing the Java plugin. As with any local agent, the agent may include excerpts of returned metadata in its conversation: review the client/provider's data handling before connecting private plugins.

## Requirements

- Windows, Linux or macOS with Python **3.11+**.
- This REJ repository downloaded and extracted, or installed locally via `python -m pip install .`.
- Claude Code and/or Codex CLI for the respective client (install the client separately).
- **No extra Python MCP package is required.** REJ implements the seven read-only MCP tools directly over stdio.

## Verify MCP server locally

From the REJ directory:

```powershell
py -3 -m rej mcp
```

The command should remain silent: MCP clients send JSON-RPC requests through stdin and read protocol messages through stdout. Press Ctrl+C to stop it. **Do not expect a terminal menu when running `mcp`.**

The file `rej_mcp.py` is a launcher that works from any working directory because its path automatically places the REJ source directory on Python's module path.

## Claude Code

From Windows CMD or PowerShell, replace the two absolute paths with your actual `python.exe` and REJ directory:

```powershell
claude mcp add --scope user rej -- "C:\Users\IK\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\IK\rej\rej_mcp.py"
claude mcp list
```

Alternatively, add this to a Claude Code project `.mcp.json` (replace the paths):

```json
{
  "mcpServers": {
    "rej": {
      "command": "C:\\Path\\To\\python.exe",
      "args": ["C:\\Path\\To\\rej\\rej_mcp.py"]
    }
  }
}
```

Restart Claude Code and use `/mcp` to verify the connection. In **REJ Desktop → MCP / AI Agents**, you can copy the configuration and installation command for *your actual Python and REJ paths*.

## Codex CLI / IDE extension

From CMD or PowerShell (replace with your real paths):

```powershell
codex mcp add rej -- "C:\Path\To\python.exe" "C:\Path\To\rej\rej_mcp.py"
codex mcp list
```

Or add to your Codex `~/.codex/config.toml` (on Windows: `%USERPROFILE%\.codex\config.toml`):

```toml
[mcp_servers.rej]
command = 'C:\Path\To\python.exe'
args = ['C:\Path\To\rej\rej_mcp.py']
```

Codex's desktop app / CLI / IDE extension share the same MCP configuration on supported installations.

## Available tools

| Tool | Arguments | Result |
| --- | --- | --- |
| `rej_inspect_jar` | `jar_path`, optional `offset`, `limit` | Archive hash, summary, plugin metadata and a paged class preview |
| `rej_list_classes` | `jar_path`, optional `filter`, `offset`, `limit` | Filtered classes (up to 200 per request, `offset` pagination) |
| `rej_inspect_class` | `jar_path`, `class_name` | Class metadata and first 200 methods / fields |
| `rej_compare_jars` | `old_path`, `new_path`, optional `offset`, `limit` | Paged class-path/hash difference report |
| `rej_search_methods` | `jar_path`, `query`, optional `offset`, `limit` | Filtered method signatures |
| `rej_disassemble_method` | `jar_path`, `class_name`, `method_name`, optional `descriptor`, `offset`, `limit` | JVM instruction mnemonics and symbolic constant pool references |
| `rej_rea_status` | No arguments | Whether the separate REA executable is found on PATH |

The tools accept **local paths**, not a URL or uploaded archive. Reports are bounded for MCP responses. For full inspection outputs use REJ CLI's `--json` or the GUI's **Export JSON** action.

## Example prompts

> Inspect `C:\MyPlugins\Example.jar` using REJ, summarize the plugin metadata and Java version, and list the main classes.

> Compare `C:\MyPlugins\Example-1.jar` and `C:\MyPlugins\Example-2.jar` using REJ. Which class files were added, removed, or modified?

> Inspect class `com.example.Main` inside `C:\MyPlugins\Example.jar`, listing its fields and method signatures.

## Security notes

- REJ MCP **does not** provide shell execution, JAR execution, remote access, filesystem search, or automated decompilation.
- Run only locally through stdio. The supplied tool names support read-only inspection.
- Users must grant permission before analyzing files. Treat bytecode, filenames and plugin metadata as untrusted input.
- Successful analysis is not a guarantee that a plugin is safe.
- REA (Reverse Engineer Anything) is a separate project. REJ's GUI can detect whether `rea` is installed, but this version does **not** connect REA's engines to the Java JAR parser.

## Troubleshooting

- **MCP server not found:** Use the full path to `rej_mcp.py`, not just its filename.
- **Python not found:** Run `py -3 -c "import sys; print(sys.executable)"` to find the executable.
- **No tools visible:** Restart Claude/Codex after registering the server and inspect `/mcp` or `codex mcp list`.
- **No MCP output in terminal:** Expected. The command communicates only with MCP clients.
- **Permissions / file not found:** Pass an absolute local path to an accessible `.jar` file.

Official client documentation:
- [Claude Code MCP documentation](https://code.claude.com/docs/en/mcp)
- [Codex MCP documentation](https://developers.openai.com/codex/mcp)
