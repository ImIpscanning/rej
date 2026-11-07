# Changelog

## 0.3.0 — Architecture, Bytecode & Windows Packaging

- Refactored code into `rej.core`, `rej.gui`, `rej.mcp`, and `rej.integrations` packages with backward-compatible import shims.
- Added read-only JVM bytecode disassembly with symbolic method/field references, method searching, and CLI/MCP paging.
- MCP expanded from four to seven tools with paginated class and diff responses.
- GUI now includes nested package browsing, method search, opcode view, async progress, and stale-result protection.
- Added cached read-only JAR inspection, invalidated by path/size/mtime.
- Added packaging entry points `rej`, `rej-gui`, `rej-mcp` and manual GitHub Actions Windows EXE build.
- Documented architecture, standalone REA companion, security limits, and CLI usage.
- Expanded local tests to 34, plus GitHub Actions matrix for Windows and Linux.

> Windows standalone EXE is built by a separate workflow; it is **not** bundled into the Python source repository.
> REA remains an optional separate engine, not a Java decompiler inside REJ.


## 0.2.0 — MCP / REJ Desktop

- Local JSON-RPC/stdio MCP server for Claude Code and Codex, with four read-only analysis tools.
- Tkinter GUI for inspecting JARs, browsing classes, comparing versions and exporting JSON.
- MCP configuration generator and copyable client setup commands.
- Optional REA availability panel (does not pretend to decompile Java with REA).
- Cross-platform MCP protocol tests, updated CI coverage and GUI smoke test.
