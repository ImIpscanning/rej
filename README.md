<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0B1020,45:172554,100:4F46E5&height=230&section=header&text=REJ&fontSize=78&fontColor=FFFFFF&animation=fadeIn&fontAlignY=37&desc=Reverse%20Engineer%20Java&descAlignY=60&descSize=23" alt="REJ — Reverse Engineer Java" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=18&duration=2800&pause=950&color=A5B4FC&center=true&vCenter=true&width=780&height=44&lines=Inspect+Java+JARs+without+executing+them.;Explore+classes%2C+fields+and+methods.;Analyze+Minecraft+plugin+metadata.;Compare+builds.+Export+evidence." alt="REJ terminal animation" />

<p>
  <a href="https://github.com/ImIpscanning/rej/actions/workflows/tests.yml"><img src="https://img.shields.io/github/actions/workflow/status/ImIpscanning/rej/tests.yml?branch=main&style=for-the-badge&label=Tests" alt="Tests" /></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Version-0.2.0-4F46E5?style=for-the-badge" alt="Version 0.2.0" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-111827?style=for-the-badge" alt="MIT License" /></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Java-JAR%20Inspector-ED8B00?style=flat-square&logo=openjdk&logoColor=white" alt="Java JAR Inspector" />
  <img src="https://img.shields.io/badge/Minecraft-Plugin%20Analysis-62B47A?style=flat-square" alt="Minecraft Plugin Analysis" />
  <img src="https://img.shields.io/badge/Windows-CLI%20Ready-0078D4?style=flat-square&logo=windows&logoColor=white" alt="Windows CLI" />
  <img src="https://img.shields.io/badge/Mode-Static%20%7C%20Read%20Only-374151?style=flat-square" alt="Static Read-only Analysis" />
</p>

**Inspect. Understand. Compare.**

[Overview](#overview) · [Features](#what-it-does) · [Installation](#installation) · [Commands](#commands) · [Roadmap](#roadmap)

</div>

---

## Overview

**REJ (Reverse Engineer Java)** is an open-source toolkit for understanding Java `.jar` files through **static inspection**. It is especially useful for inspecting the structure of **Minecraft server plugins** without starting a Minecraft server or running the target JAR.

REJ identifies archive metadata, Java classes, superclass and interface relationships, methods, fields, plugin descriptors, and file hashes. It can compare two builds and export machine-readable JSON reports for documentation or further analysis. **v0.2.0 adds the REJ Desktop GUI and a local MCP server for Claude Code and Codex.**

> [!IMPORTANT]
> **REJ v0.2.0 is an early-stage project**, not a complete Java decompiler, deobfuscator, malware scanner, or sandbox. Decompiled Java source requires a separately installed **Vineflower** JAR. REJ does not claim that an inspected file is trustworthy or safe.

---

## What It Does

```txt
Read-only JAR / ZIP inspection
JVM .class metadata parsing
Java version detection
Class, package, method and field inventory
Superclass and interface identification
Minecraft plugin descriptor discovery
Manifest and plugin metadata extraction
SHA-256 archive and class hashing
Two-version JAR comparison
JSON evidence reports
Interactive Windows terminal menu
Optional Vineflower decompilation bridge
Tkinter desktop GUI with class explorer, build comparison and JSON export
Local MCP tools for Claude Code and Codex (stdio, read-only)
```

### Supported Inputs

| Input | REJ v0.2.0 capability |
|:--|:--|
| Java `.jar` | Inspect archive, class inventory and SHA-256 |
| JVM `.class` inside a JAR | Read class, interface, field and method metadata |
| Bukkit / Spigot / Paper | Read `plugin.yml` metadata |
| Modern Paper | Read `paper-plugin.yml` metadata |
| BungeeCord | Read `bungee.yml` metadata |
| Velocity | Read `velocity-plugin.json` metadata |
| Fabric | Read `fabric.mod.json` metadata |
| Different JAR versions | Compare added, removed and byte-changed classes |

**Important distinction:** Minecraft platform names above describe **metadata formats REJ recognizes**. REJ itself is **not a Minecraft server plugin** and should not be installed into a server's `plugins/` folder.

---

## What REJ Is

```diff
+ An offline Java archive inspector
+ A class and method metadata explorer
+ A Minecraft plugin structure reader
+ A read-only tool for investigating JAR builds
+ A version-diff and reporting utility
+ An optional frontend for a trusted Java decompiler
```

## What REJ Is Not

```diff
- A full Java source recovery engine
- A guarantee of deobfuscation or original variable names
- A malware detection or antivirus product
- A runtime sandbox for unknown plugins
- A tool that runs untrusted Java code to inspect it
- A replacement for source review and legitimate authorization
```

---

## How It Works

```txt
           Java / Minecraft Plugin JAR
                       |
                       v
             +------------------+
             |  REJ JAR Reader  |
             |   Read-only ZIP  |
             +------------------+
                       |
            +----------+-----------+
            |          |           |
            v          v           v
       Class files  Plugin YAML  Manifest /
       & metadata   and JSON     resources
            |          |           |
            +----------+-----------+
                       |
                       v
              Structured Report
              classes / versions
              fields / methods
              SHA-256 / metadata
                       |
            +----------+-----------+
            |                      |
            v                      v
        CLI Output             JSON Export
            |
            v
     Optional Vineflower
    (external Java decompiler)
```

REJ scans ZIP entries with size and count limits. Its basic inspection commands do **not** execute the target JAR.

---

## Installation

### Requirements

| Component | Required? | Purpose |
|:--|:--:|:--|
| **Python 3.11+** | Yes | REJ CLI and JAR inspection |
| **Git** | No | Optional repository cloning |
| **Java runtime** | No | Only for optional decompilation
| **Tkinter** | For GUI | Bundled with the standard Windows Python installer |
| **Vineflower JAR** | No | Optional approximate Java reconstruction |

### Windows — Quick Start

**Method 1: Download ZIP (no Git required).**

1. Open [the REJ repository](https://github.com/ImIpscanning/rej).
2. Select **Code → Download ZIP** and extract the project.
3. Install [Python 3.11 or later](https://www.python.org/downloads/windows/) and enable **Add Python to PATH**.
4. Double-click **REJ.bat** to open the interactive menu.

**Method 2: Clone from CMD / PowerShell.**

```bat
git clone https://github.com/ImIpscanning/rej.git
cd rej
py -3 -m rej menu
```

**Method 3: Run the CLI directly (no package installation).**

```bat
py -3 -m rej --help
py -3 -m rej inspect examples\HelloPlugin-demo.jar
```

Optional local installation of the `rej` command:

```bat
py -3 -m pip install .
rej --help
```

> The source-based CLI uses Python's standard library. Git and Java are not required for normal static inspection.

---

## REJ Desktop — Graphical Interface

**Windows:** Double-click `REJ-GUI.bat` from the extracted repository directory.

**Any desktop environment with Python 3.11+ and Tkinter:**

```bat
py -3 -m rej gui
```

The desktop UI provides a dark purple-themed class explorer, JAR summary, fields and methods, binary comparison between plugin builds, JSON export, and an **MCP / AI Agents** tab that generates ready-to-copy client configuration for your installed Python location.

The **REA Companion** tab checks whether the separate [Reverse Engineer Anything (REA)](https://github.com/morluto/rea) CLI is installed and links to its documentation. It is a companion panel, **not** a Java decompilation engine powered by REA.

## MCP — Claude Code & Codex

REJ provides four read-only tools over local JSON-RPC stdio, without extra Python dependencies:

```txt
rej_inspect_jar
rej_list_classes
rej_inspect_class
rej_compare_jars
```

**Server command:**

```bat
py -3 -m rej mcp
```

The MCP server does **not** display a normal terminal menu and must be started by a compatible MCP client to exchange messages.

**Claude Code setup**, using your real paths to Python and the REJ launcher:

```bat
claude mcp add --scope user rej -- "C:\Path\To\python.exe" "C:\Path\To\rej\rej_mcp.py"
claude mcp list
```

**Codex setup:**

```bat
codex mcp add rej -- "C:\Path\To\python.exe" "C:\Path\To\rej\rej_mcp.py"
codex mcp list
```

For a tailored config on your own machine, open the GUI's **MCP / AI Agents** tab. Detailed setup, JSON/TOML examples, troubleshooting and security notes are in **[docs/MCP.md](docs/MCP.md)**.

---

## Terminal Interface

```txt
REJ  |  Reverse Engineer Java  |  v0.2.0
===================================================
  [1] Inspect JAR / Minecraft plugin
  [2] List classes
  [3] Inspect a class and its methods
  [4] Compare two JAR versions
  [5] Decompile with Vineflower (optional)
  [0] Exit

REJ > _
```

Launch with `REJ.bat` on Windows or `python -m rej menu` on any supported Python environment.

---

## Commands

### Inspect a JAR

```bat
py -3 -m rej inspect "C:\plugins\MyPlugin.jar"
py -3 -m rej inspect "C:\plugins\MyPlugin.jar" --json "report.json"
```

The report includes file size, archive SHA-256, class/resource counts, Java version information, detected platform metadata and any recoverable parse errors.

### List All Classes

```bat
py -3 -m rej classes "C:\plugins\MyPlugin.jar"
py -3 -m rej classes "C:\plugins\MyPlugin.jar" --filter com.example --limit 200
```

### Explore Fields and Methods

```bat
py -3 -m rej class "C:\plugins\MyPlugin.jar" com.example.Main
py -3 -m rej class "C:\plugins\MyPlugin.jar" com.example.Main --json "class.json"
```

This displays declared fields, methods and JVM descriptors. **It does not show executable method bodies or reconstructed Java statements.**

### Compare Two JARs

```bat
py -3 -m rej diff "C:\plugins\Plugin-v1.jar" "C:\plugins\Plugin-v2.jar"
py -3 -m rej diff "C:\plugins\Plugin-v1.jar" "C:\plugins\Plugin-v2.jar" --json "changes.json"
```

REJ compares the paths and SHA-256 hashes of parsed `.class` files. A reported modification is a **binary difference**, not necessarily a behavioral change.

### Decompile with Vineflower (Optional)

```bat
py -3 -m rej decompile "C:\plugins\MyPlugin.jar" --vineflower "C:\tools\vineflower.jar" --out "C:\plugins\decompiled"
```

You must provide a **trusted Vineflower JAR** and a Java runtime. REJ launches the decompiler, not the inspected target JAR, and places generated output in the chosen directory. Recovered code is approximate and may not retain original names, comments or formatting.

### Quick Demo

The repository includes a small example JAR for learning the commands:

```bat
py -3 -m rej inspect examples\HelloPlugin-demo.jar
py -3 -m rej class examples\HelloPlugin-demo.jar org.example.HelloPlugin
```

The included demo is a test fixture, **not a deployable Minecraft plugin**.

---

## JSON Reports

Export inspection results to JSON:

```bat
py -3 -m rej inspect "C:\plugins\MyPlugin.jar" --json "reports\inspection.json"
```

Reports can include a structure like:

```json
{
  "tool": "REJ",
  "version": "0.2.0",
  "summary": {
    "class_count": 12,
    "resource_count": 4,
    "error_count": 0,
    "java_versions": {
      "Java 17": 12
    }
  },
  "classes": [
    {
      "name": "com.example.Main",
      "java_version": "Java 17",
      "method_count": 5,
      "field_count": 2
    }
  ]
}
```

*Illustrative excerpt only; real output also contains file paths, hashes and additional metadata.*

---

## Project Structure

```txt
rej/
├── .github/
│   └── workflows/
│       └── tests.yml
├── rej/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── archive.py
│   ├── classfile.py
│   └── metadata.py
├── examples/
│   ├── HelloPlugin.java
│   ├── HelloPlugin-demo.jar
│   └── README.md
├── tests/
│   └── test_rej.py
├── REJ.bat
├── pyproject.toml
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
└── README.md
```

---

## Testing

The test suite now covers MCP handshakes, tool registration, stdio launcher behavior, config examples, read-only inspection and a GUI import smoke test, in addition to the existing JAR parser tests.


Run the project tests locally:

```bat
py -3 -m unittest discover -s tests -v
```

GitHub Actions also runs tests on **Windows and Linux** with **Python 3.11 and 3.13**.

[![REJ Tests](https://img.shields.io/github/actions/workflow/status/ImIpscanning/rej/tests.yml?branch=main&label=CI%20Tests&style=flat-square)](https://github.com/ImIpscanning/rej/actions/workflows/tests.yml)

Automated tests do not guarantee compatibility with every JAR or every plugin.

---

## Security & Limitations

- Read-only inspection never intentionally runs the **target JAR**.
- The inspector applies bounds to ZIP entry counts, declared uncompressed sizes, class sizes and metadata reads.
- YAML support intentionally handles **common simple plugin fields**, not arbitrary nested YAML.
- Parsing records metadata and method signatures, but has **no built-in bytecode disassembler or Java source decompiler**.
- Multi-release JARs may contain alternate classes; REJ does not implement JVM runtime selection rules.
- Malformed files can cause parsing errors, and successful inspection **does not prove a plugin is safe**.
- The optional Vineflower integration runs **an external tool**. Only use a trusted installation and inspect files you own or are authorized to analyze.

---

## Roadmap

| Version | Focus | Status |
|:--|:--|:--|
| **v0.2.0** | JAR inventory, Minecraft metadata, class explorer, diff and JSON | **Current MVP** |
| **v0.2.0** | Desktop GUI, Claude/Codex MCP server, basic REA companion panel | **Current** |
| **v0.3.0** | Better JVM descriptors, method search, deeper plugin reporting | Planned |
| **v0.4.0** | Bytecode disassembly and reference navigation | Planned |
| **Future** | GUI, dependency visualization, agent/MCP integration | Exploring |

A feature listed as planned is **not available in the current release**.

---

## Technologies

<p align="center">
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="48" height="48" alt="Python" />
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/java/java-original.svg" width="48" height="48" alt="Java" />
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/windows11/windows11-original.svg" width="48" height="48" alt="Windows" />
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/git/git-original.svg" width="48" height="48" alt="Git" />
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg" width="48" height="48" alt="GitHub" />
</p>

---

## Contributing

Contributions, bug reports and reproducible JAR fixtures are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and [CHANGELOG.md](CHANGELOG.md).

When reporting a problem, include the command used, expected and actual results, your Python version, and a minimal example you have permission to share.

## License

REJ is distributed under the **MIT License**. See [LICENSE](LICENSE).

## Author

Developed by **[ipscanning](https://github.com/ImIpscanning)**.

```txt
Inspect.
Understand.
Compare.
Document.
```

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=17&duration=2700&pause=1100&color=A5B4FC&center=true&vCenter=true&width=780&height=45&lines=Thank+you+for+checking+out+REJ.;Built+for+Java+and+Minecraft+plugin+inspection.;Inspect.+Understand.+Compare.+Document." alt="REJ footer animation" />

**REJ — Reverse Engineer Java**

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:4F46E5,45:172554,100:0B1020&height=110&section=footer" alt="REJ footer" />

</div>
