# REA + REJ Companion

[REA (Reverse Engineer Anything)](https://github.com/morluto/rea) and [REJ](https://github.com/ImIpscanning/rej) are independent projects. They may be installed side by side on the same Windows PC.

REJ can detect whether the `rea` executable is available:

```powershell
py -3 -m rej rea-status
```

The **REA Companion** tab in REJ Desktop displays the same availability status and provides a link to the official REA documentation. REJ's MCP adds a `rej_rea_status` tool for detection.

To set up REA with your AI agent, use **REA's official installation guide** and setup command from its own repository:

```powershell
npx rea-agents setup
```

REJ can be added independently using [MCP.md](MCP.md), so an agent can see both sets of tools. REA's own capabilities are separate. **REA does not become a Java JAR decompiler through REJ**; no REA native analysis engine is invoked by REJ v0.3.0.
