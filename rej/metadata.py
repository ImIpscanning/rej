"""Read human-readable JAR metadata without executing plugins or importing YAML libraries."""
from __future__ import annotations

import json
import re
from typing import Any


def parse_manifest(raw: bytes) -> dict[str, str]:
    text = raw.decode("utf-8-sig", errors="replace")
    result: dict[str, str] = {}
    last_key = None
    for line in text.splitlines():
        if line.startswith(" ") and last_key:
            result[last_key] += line[1:]
        elif ": " in line:
            key, value = line.split(": ", 1)
            result[key] = value
            last_key = key
        else:
            last_key = None
    return result


def parse_simple_yaml(raw: bytes) -> dict[str, Any]:
    """Extract common top-level plugin.yml scalars and flat lists only.

    This is intentionally not a general YAML parser. Complex nested structures
    remain unparsed; no unsafe YAML tags or object construction is supported.
    """
    text = raw.decode("utf-8-sig", errors="replace")
    result: dict[str, Any] = {}
    active_list = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([\w.-]+)\s*:\s*(.*?)\s*$", line)
        if top:
            key, value = top.groups()
            active_list = key if not value else None
            if not value:
                result[key] = []
            elif value.startswith("[") and value.endswith("]"):
                result[key] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            else:
                result[key] = value.strip("'\"")
        elif active_list and re.match(r"^\s+-\s+", line):
            result[active_list].append(re.sub(r"^\s+-\s+", "", line).strip().strip("'\""))
        else:
            active_list = None
    return result


def identify_plugin(files: dict[str, bytes]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if "META-INF/MANIFEST.MF" in files:
        result["manifest"] = parse_manifest(files["META-INF/MANIFEST.MF"])
    for name, kind in (
        ("plugin.yml", "Bukkit/Spigot/Paper"),
        ("paper-plugin.yml", "Paper"),
        ("bungee.yml", "BungeeCord"),
    ):
        if name in files:
            result["platform"] = kind
            result["descriptor"] = name
            result["plugin"] = parse_simple_yaml(files[name])
            break
    for name, kind in (("velocity-plugin.json", "Velocity"), ("fabric.mod.json", "Fabric")):
        if name in files:
            result["platform"] = kind
            result["descriptor"] = name
            try:
                result["plugin"] = json.loads(files[name].decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                result["plugin_parse_error"] = str(exc)
            break
    return result
