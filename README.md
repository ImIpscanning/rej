# REJ — Reverse Engineer Java

**REJ (Reverse Engineer Java)** is an open-source, Windows-friendly command-line utility for **static inspection of Java JAR files**, with a focus on **Minecraft plugins** (Bukkit, Spigot, Paper, BungeeCord, Velocity and Fabric).

> **Version:** 0.1.0 · **Status:** early MVP · **Language:** Python 3.11+ · **License:** MIT  
> REJ is independent of [REA (Reverse Engineer Anything)](https://github.com/morluto/rea).

**Español:** REJ permite inspeccionar archivos `.jar` y plugins de Minecraft sin ejecutarlos: muestra clases, métodos, campos, versión de Java, manifiestos, metadatos del plugin y diferencias entre versiones. Puede generar informes JSON y utilizar Vineflower como decompilador externo opcional.

## ✨ Features / Características

- 🔍 Inspect JAR files **without executing the inspected Java code**.
- 🧩 Identify `plugin.yml`, `paper-plugin.yml`, `bungee.yml`, `velocity-plugin.json` and `fabric.mod.json`.
- 📚 List classes, packages, JVM class versions, inheritance, interfaces, fields, methods and descriptors.
- 📝 Read `META-INF/MANIFEST.MF` and plugin metadata.
- 🔄 Compare two JARs to identify added, removed and modified `.class` files.
- 📊 Export inspection and diff reports to JSON, including SHA-256 information.
- 🖥️ Windows `REJ.bat` interactive terminal menu.
- ☕ Optionally run a separately supplied **Vineflower** JAR to reconstruct approximate Java source.
- 🛡️ Static inspection includes limits for ZIP entries, class sizes and total declared uncompressed data.

## 📦 Requirements / Requisitos

**Basic inspection:** Python **3.11+**, no third-party Python packages required when running the source directly. **Java is not required** for the inspect/classes/class/diff commands.

**Optional decompilation:** Java available on PATH and a trusted, locally downloaded Vineflower JAR. REJ does **not** include or automatically download Vineflower.

## 🚀 Installation on Windows

1. Download this repository as ZIP (GitHub → **Code → Download ZIP**) or clone it.
2. Extract the files and open the folder containing `REJ.bat`.
3. Install Python 3.11+ from [python.org](https://www.python.org/downloads/windows/) and select **Add Python to PATH**.
4. Double-click `REJ.bat` for the interactive menu, or use CMD/PowerShell:

```bat
py -3 -m rej --help
py -3 -m rej menu
```

If Git is installed:

```bat
git clone https://github.com/ImIpscanning/rej.git
cd rej
py -3 -m rej menu
```

Optional install as a package (from the repository directory):

```bat
py -3 -m pip install .
rej --help
```

## 🛠️ CLI commands / Comandos

### Inspect a Minecraft plugin

```bat
py -3 -m rej inspect "C:\plugins\ExamplePlugin.jar"
py -3 -m rej inspect "C:\plugins\ExamplePlugin.jar" --json "report.json"
```

Lists archive SHA-256, classes, resources, Java versions and detected plugin metadata.

### List classes and inspect methods

```bat
py -3 -m rej classes "C:\plugins\ExamplePlugin.jar"
py -3 -m rej classes "C:\plugins\ExamplePlugin.jar" --filter com.example --limit 200
py -3 -m rej class "C:\plugins\ExamplePlugin.jar" com.example.Main
py -3 -m rej class "C:\plugins\ExamplePlugin.jar" com.example.Main --json "class.json"
```

### Compare versions

```bat
py -3 -m rej diff "C:\plugins\Plugin-v1.jar" "C:\plugins\Plugin-v2.jar"
py -3 -m rej diff "C:\plugins\Plugin-v1.jar" "C:\plugins\Plugin-v2.jar" --json "changes.json"
```

Comparison is based on class file paths and SHA-256, **not semantic equivalence**.

### Optional Java source reconstruction

```bat
py -3 -m rej decompile "C:\plugins\ExamplePlugin.jar" --vineflower "C:\tools\vineflower.jar" --out "C:\plugins\decompiled"
```

This launches **the trusted decompiler supplied by the user**, not the inspected JAR. The result is approximate Java: comments, variable names, original formatting and some structures may be irrecoverable. It is not a guaranteed deobfuscator.

### Try the included example / Probar ejemplo

```bat
py -3 -m rej inspect examples\HelloPlugin-demo.jar
py -3 -m rej class examples\HelloPlugin-demo.jar org.example.HelloPlugin
```

The demo JAR is a harmless test fixture, **not a deployable Minecraft plugin**.

## 🗂️ Project structure / Estructura

```text
rej/
├── rej/
│   ├── __init__.py        Package version
│   ├── __main__.py        python -m rej entry
│   ├── cli.py             Commands and interactive menu
│   ├── archive.py         Read-only bounded JAR scanning and comparison
│   ├── classfile.py       JVM .class constant-pool / member parser
│   └── metadata.py        Manifest and plugin metadata reader
├── tests/
│   └── test_rej.py        Automated unit / CLI tests
├── examples/
│   ├── HelloPlugin.java
│   ├── HelloPlugin-demo.jar
│   └── README.md
├── REJ.bat                Windows launcher
├── pyproject.toml
├── .gitignore
├── LICENSE
└── README.md
```

## ✅ Tests / Pruebas

From the repository root:

```bat
py -3 -m unittest discover -s tests -v
```

**v0.1.0:** 11 unit/CLI tests passed in the initial development environment. This does **not** mean all Java plugins or Windows setups have been tested.

## 🔐 Security & limitations / Seguridad y limitaciones

- Inspection does not execute target JARs.
- Archives are bounded by entry count, declared uncompressed size, number of classes, per-class size, and metadata size.
- The YAML reader supports common top-level keys and simple lists only; it is **not a full YAML parser**.
- Classfile parsing reads metadata but **does not disassemble instructions or recover source code by itself**.
- Multi-release JAR entries are listed individually; runtime class selection is not modeled.
- Malformed content can produce parse errors; a clean scan does **not** prove that a plugin is safe.
- External decompilation has a timeout and should be used only with **trusted tools** and files you own or are permitted to inspect.

## 🧭 Roadmap / Próximas versiones

- **v0.2:** JVM descriptor prettification, improved class metadata, method searching and richer Minecraft plugin reports.
- **v0.3:** Bytecode disassembly and call/reference navigation.
- **Future:** GUI, dependency graphs, structured evidence and MCP integration for Codex.

## 🤝 Contributing / Contribuir

Issues, bug reports, tests and pull requests are welcome. Please include a reproducible example, expected behavior and your Python/Java version when applicable.

## 📄 License

Released under the **MIT License**. See [LICENSE](LICENSE).

**Project:** [github.com/ImIpscanning/rej](https://github.com/ImIpscanning/rej)
