# Changelog

## 0.2.0 — MCP / REJ Desktop

- Local JSON-RPC/stdio MCP server for Claude Code and Codex with four read-only analysis tools.
- Tkinter GUI to inspect JARs, browse classes, compare builds and export JSON.
- Copyable MCP configuration snippets and client setup commands for actual local Python paths.
- Optional REA Companion availability panel (REA does not decompile Java through REJ).
- MCP contract and launcher tests; 19 tests in local development.


## 0.1.0 — Initial release

- Read-only JAR archive inspection with SHA-256 and resource boundaries.
- Java class file metadata parsing: types, superclass, interfaces, fields, methods and classfile version.
- Minecraft plugin descriptor detection.
- Class listings and filtering, class-detail output.
- Comparison of added, removed and modified Java classes across two archives.
- Optional JSON exports.
- Optional local Vineflower decompilation integration.
- Windows launcher and interactive text menu.
- Included original compiled demo JAR and 11 unit/CLI tests.

**Known limitations:** no built-in bytecode disassembly or deobfuscation; nested YAML only partially parsed; source reconstruction requires external Vineflower.
