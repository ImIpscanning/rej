"""Command-line interface for REJ."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from .archive import JarInspectionError, compare_jars, inspect_class, inspect_jar
from .classfile import ClassFormatError


def print_header() -> None:
    print("REJ  |  Reverse Engineer Java  |  v0.1.0")
    print("=" * 51)


def write_json(data: dict, destination: str | None) -> None:
    if destination:
        output = Path(destination).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\n[+] JSON report: {output}")


def run_decompiler(source: str, tool: str, output: str, timeout: int) -> int:
    """Invoke a locally supplied Vineflower jar. Never runs the target JAR."""
    if not shutil.which("java"):
        raise JarInspectionError("Java runtime not found. Install JDK 21+ and add java to PATH.")
    src = Path(source).expanduser().resolve()
    dec = Path(tool).expanduser().resolve()
    out = Path(output).expanduser().resolve()
    if not src.is_file() or not dec.is_file():
        raise JarInspectionError("Input JAR or Vineflower JAR does not exist")
    if src.suffix.lower() != ".jar":
        raise JarInspectionError("Input must be a .jar file")
    out.mkdir(parents=True, exist_ok=True)
    command = ["java", "-jar", str(dec), str(src), str(out)]
    print(f"[*] Decompiling into {out} (timeout: {timeout}s)")
    try:
        completed = subprocess.run(command, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise JarInspectionError(f"Decompiler exceeded {timeout}s timeout") from exc
    if completed.returncode:
        raise JarInspectionError(f"Decompiler exited with code {completed.returncode}")
    print("[+] Decompilation completed. Decompiled output is approximate, not original source.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rej", description="Read-only Java JAR inspection and comparison")
    parser.add_argument("--version", action="version", version="REJ 0.1.0")
    subs = parser.add_subparsers(dest="command", required=True)
    inspect = subs.add_parser("inspect", help="Inspect JAR and detect Minecraft plugin metadata")
    inspect.add_argument("jar")
    inspect.add_argument("--json", metavar="PATH", help="Save full JSON report")
    classes = subs.add_parser("classes", help="List classes in JAR")
    classes.add_argument("jar")
    classes.add_argument("--filter", default="", help="Substring of class name")
    classes.add_argument("--limit", type=int, default=100, help="Maximum displayed classes")
    classes.add_argument("--json", metavar="PATH")
    class_cmd = subs.add_parser("class", help="Show fields and methods of a class")
    class_cmd.add_argument("jar")
    class_cmd.add_argument("name", help="Fully qualified name or internal path")
    class_cmd.add_argument("--json", metavar="PATH")
    diff = subs.add_parser("diff", help="Compare class-level changes between two JARs")
    diff.add_argument("old")
    diff.add_argument("new")
    diff.add_argument("--json", metavar="PATH")
    subs.add_parser("menu", help="Interactive terminal menu (Windows-friendly)")
    dec = subs.add_parser("decompile", help="Decompile using your local Vineflower JAR")
    dec.add_argument("jar")
    dec.add_argument("--vineflower", required=True, metavar="PATH", help="Path to a local Vineflower JAR")
    dec.add_argument("--out", required=True, metavar="DIRECTORY")
    dec.add_argument("--timeout", type=int, default=300)
    return parser


def interactive_menu() -> int:
    options = {
        "1": "inspect", "2": "classes", "3": "class", "4": "diff", "5": "decompile",
    }
    while True:
        print()
        print_header()
        print("  [1] Inspect JAR / Minecraft plugin")
        print("  [2] List classes")
        print("  [3] Inspect a class and its methods")
        print("  [4] Compare two JAR versions")
        print("  [5] Decompile with Vineflower (optional)")
        print("  [0] Exit")
        try:
            choice = input("\nREJ > ").strip()
            if choice == "0":
                return 0
            if choice not in options:
                print("[!] Select 0-5")
                continue
            cmd = options[choice]
            if cmd in ("inspect", "classes", "class", "decompile"):
                jar = input("JAR path: ").strip().strip('"')
                if not jar:
                    continue
                arguments = [cmd, jar]
            else:
                arguments = ["diff", input("Old JAR: ").strip().strip('"'), input("New JAR: ").strip().strip('"')]
            if cmd == "class":
                arguments.append(input("Class name (e.g. org.example.Main): ").strip())
            if cmd == "decompile":
                arguments.extend(["--vineflower", input("Vineflower JAR path: ").strip().strip('"')])
                arguments.extend(["--out", input("Output directory: ").strip().strip('"')])
            print()
            main(arguments)
            input("\nPress Enter to return to REJ menu...")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting REJ.")
            return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "menu":
            return interactive_menu()
        if args.command == "decompile":
            if not 1 <= args.timeout <= 3600:
                raise JarInspectionError("Timeout must be between 1 and 3600 seconds")
            return run_decompiler(args.jar, args.vineflower, args.out, args.timeout)
        print_header()
        if args.command == "inspect":
            report = inspect_jar(args.jar)
            summary = report["summary"]
            print(f"File:     {report['file']}")
            print(f"SHA-256:  {report['sha256']}")
            print(f"Classes:  {summary['class_count']}")
            print(f"Resources:{summary['resource_count']:>4}")
            print(f"Errors:   {summary['error_count']}")
            print(f"Java:     {', '.join(summary['java_versions']) or 'N/A'}")
            metadata = report["metadata"]
            if metadata.get("platform"):
                print(f"Platform: {metadata['platform']}")
                plugin = metadata.get("plugin", {})
                if isinstance(plugin, dict):
                    for key in ("name", "version", "main", "api-version", "depend", "softdepend"):
                        if key in plugin:
                            print(f"{key}: {plugin[key]}")
            write_json(report, args.json)
        elif args.command == "classes":
            if args.limit < 0:
                raise JarInspectionError("Limit cannot be negative")
            report = inspect_jar(args.jar)
            selected = [c for c in report["classes"] if args.filter.lower() in c["name"].lower()]
            print(f"Matched: {len(selected)} class(es)")
            for c in selected[: args.limit]:
                print(f"  {c['name']}  [{c['java_version']}]  methods={c['method_count']}")
            if len(selected) > args.limit:
                print(f"  ... {len(selected) - args.limit} more (increase --limit)")
            write_json({"classes": selected}, args.json)
        elif args.command == "class":
            info = inspect_class(args.jar, args.name)
            print(f"Class:      {info['name']}")
            print(f"Extends:    {info['superclass']}")
            print(f"Implements: {', '.join(info['interfaces']) or '-'}")
            print(f"Java:       {info['java_version']}")
            print("Fields:")
            for item in info["fields"]:
                print(f"  {' '.join(item['flags'])} {item['name']} : {item['descriptor']}")
            print("Methods:")
            for item in info["methods"]:
                print(f"  {' '.join(item['flags'])} {item['name']}{item['descriptor']}")
            write_json(info, args.json)
        elif args.command == "diff":
            report = compare_jars(args.old, args.new)
            for category in ("added", "removed", "modified"):
                print(f"{category.capitalize()}: {len(report[category])}")
                for name in report[category][:30]:
                    print(f"  {name}")
                if len(report[category]) > 30:
                    print("  ...")
            print(f"Unchanged: {report['unchanged_count']}")
            write_json(report, args.json)
    except (JarInspectionError, ClassFormatError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1
    return 0
