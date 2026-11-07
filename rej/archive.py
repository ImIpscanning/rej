"""Read-only, resource-bounded JAR inspection."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import zipfile
from typing import Any

from .classfile import ClassFormatError, parse_classfile
from .metadata import identify_plugin
from . import __version__

MAX_ENTRIES = 50_000
MAX_TOTAL_UNCOMPRESSED = 500 * 1024 * 1024
MAX_CLASS_BYTES = 4 * 1024 * 1024
MAX_METADATA_BYTES = 512 * 1024
MAX_CLASSES = 20_000
METADATA_NAMES = {
    "META-INF/MANIFEST.MF", "plugin.yml", "paper-plugin.yml", "bungee.yml",
    "velocity-plugin.json", "fabric.mod.json",
}


class JarInspectionError(ValueError):
    """JAR violates resource limits or cannot be inspected."""


def _validate_archive(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    entries = zf.infolist()
    if len(entries) > MAX_ENTRIES:
        raise JarInspectionError(f"Too many ZIP entries ({len(entries)})")
    if sum(x.file_size for x in entries) > MAX_TOTAL_UNCOMPRESSED:
        raise JarInspectionError("Uncompressed archive exceeds 500 MiB limit")
    if any(x.flag_bits & 1 for x in entries):
        raise JarInspectionError("Encrypted ZIP entries are not supported")
    return entries


def _safe_read(zf: zipfile.ZipFile, entry: zipfile.ZipInfo, limit: int) -> bytes:
    if entry.file_size > limit:
        raise JarInspectionError(f"Entry {entry.filename} exceeds {limit} byte limit")
    with zf.open(entry) as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise JarInspectionError(f"Entry {entry.filename} exceeds {limit} byte limit")
    return data


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def inspect_jar(path: str | Path) -> dict[str, Any]:
    jar = Path(path).expanduser().resolve()
    if not jar.is_file():
        raise JarInspectionError(f"JAR not found: {jar}")
    if not zipfile.is_zipfile(jar):
        raise JarInspectionError(f"Not a valid ZIP/JAR file: {jar}")
    classes: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    resources = 0
    versions: Counter[str] = Counter()
    packages: Counter[str] = Counter()
    with zipfile.ZipFile(jar) as zf:
        entries = _validate_archive(zf)
        metadata: dict[str, bytes] = {}
        for entry in entries:
            if entry.is_dir():
                continue
            if entry.filename in METADATA_NAMES:
                try:
                    metadata[entry.filename] = _safe_read(zf, entry, MAX_METADATA_BYTES)
                except (JarInspectionError, RuntimeError, zipfile.BadZipFile) as exc:
                    errors.append({"file": entry.filename, "error": str(exc)})
            if not entry.filename.endswith(".class"):
                resources += 1
                continue
            if len(classes) >= MAX_CLASSES:
                raise JarInspectionError(f"Class limit exceeded ({MAX_CLASSES})")
            try:
                content = _safe_read(zf, entry, MAX_CLASS_BYTES)
                parsed = parse_classfile(content)
                classes.append({
                    "path": entry.filename,
                    "name": parsed["name"],
                    "java_version": parsed["java_version"],
                    "major_version": parsed["major_version"],
                    "method_count": parsed["method_count"],
                    "field_count": parsed["field_count"],
                    "sha256": hashlib.sha256(content).hexdigest(),
                })
                versions[parsed["java_version"]] += 1
                package = parsed["name"].rpartition(".")[0] or "(default)"
                packages[package] += 1
            except (ClassFormatError, JarInspectionError, RuntimeError, zipfile.BadZipFile) as exc:
                errors.append({"file": entry.filename, "error": str(exc)})
    classes.sort(key=lambda item: item["name"])
    return {
        "tool": "REJ",
        "version": __version__,
        "file": str(jar),
        "size_bytes": jar.stat().st_size,
        "sha256": _hash_file(jar),
        "metadata": identify_plugin(metadata),
        "summary": {
            "class_count": len(classes),
            "resource_count": resources,
            "error_count": len(errors),
            "java_versions": dict(sorted(versions.items())),
            "top_packages": [{"package": name, "classes": total} for name, total in packages.most_common(20)],
        },
        "classes": classes,
        "errors": errors,
    }


def inspect_class(path: str | Path, name: str) -> dict[str, Any]:
    jar = Path(path).expanduser().resolve()
    target = name.replace(".", "/")
    if not target.endswith(".class"):
        target += ".class"
    if not zipfile.is_zipfile(jar):
        raise JarInspectionError(f"Not a valid JAR: {jar}")
    with zipfile.ZipFile(jar) as zf:
        entries = _validate_archive(zf)
        for entry in entries:
            if entry.filename == target:
                return parse_classfile(_safe_read(zf, entry, MAX_CLASS_BYTES))
    raise JarInspectionError(f"Class not found: {target}")


def compare_jars(old: str | Path, new: str | Path) -> dict[str, Any]:
    a = inspect_jar(old)
    b = inspect_jar(new)
    old_classes = {c["path"]: c["sha256"] for c in a["classes"]}
    new_classes = {c["path"]: c["sha256"] for c in b["classes"]}
    return {
        "tool": "REJ",
        "old": a["file"],
        "new": b["file"],
        "added": sorted(new_classes.keys() - old_classes.keys()),
        "removed": sorted(old_classes.keys() - new_classes.keys()),
        "modified": sorted(k for k in old_classes.keys() & new_classes.keys() if old_classes[k] != new_classes[k]),
        "unchanged_count": sum(old_classes[k] == new_classes[k] for k in old_classes.keys() & new_classes.keys()),
    }
