# REJ architecture (v0.3.0)

REJ deliberately keeps core archive and bytecode inspection independent of user interface or MCP transport.

```text
CLI ──────────┐
REJ Desktop ──┼──> rej.core.analysis ───> archive / classfile / bytecode
MCP tools ────┘                  └─────> metadata

Claude Code ─┐
Codex ───────┼──> MCP stdio server (rej.mcp.server)
             └──> Local file paths provided by user

REA is optional and remains a separate analysis engine.
```

## Packages

- `rej/core/archive.py`: bounded ZIP access, hashing, plugin metadata, binary class diff.
- `rej/core/classfile.py`: Java classfile constant-pool/member metadata parser.
- `rej/core/bytecode.py`: linear JVM opcode decoder with selected symbolic constant pool references.
- `rej/core/analysis.py`: cached inspection keyed by path, size and mtime; class lookup and method search.
- `rej/mcp/{schemas,tools,server}.py`: JSON schemas, read-only request dispatch, JSON-RPC stdio transport.
- `rej/gui/{app,theme,explorer,comparison,settings}.py`: native Tkinter GUI and testable format helpers.
- `rej/integrations/{base,claude,codex,rea}.py`: local MCP registration strings and REA capability detection.
- Root `rej/archive.py`, `rej/classfile.py`, `rej/metadata.py`, `rej/mcp_server.py` remain compatibility import shims.

## Limits

- JVM bytecode output is a **linear disassembly**, not a verified CFG or Java source recovery.
- REA companion detection is intentionally not a Java parser bridge.
- The cache detects file changes using path, `st_mtime_ns` and file size; replacing an archive with exactly the same timestamp and size is not reliably detectable until cache expiry.
- Java classfiles can be malformed or intentionally misleading. Outputs are evidence for human review, not security certification.
