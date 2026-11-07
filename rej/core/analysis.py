"""Shared cached read-only analysis service for GUI, CLI and MCP."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import zipfile
from typing import Any

from .archive import _safe_read, _validate_archive, MAX_CLASS_BYTES, JarInspectionError, inspect_jar
from .classfile import ClassFormatError, parse_classfile
from .bytecode import inspect_method_bytecode


def _signature(path: str | Path) -> tuple[str,int,int]:
    resolved=Path(path).expanduser().resolve()
    stat=resolved.stat()
    if not resolved.is_file():
        raise JarInspectionError('Not a file')
    return str(resolved), stat.st_mtime_ns, stat.st_size


@lru_cache(maxsize=6)
def _index(path: str, mtime: int, size: int) -> dict[str,Any]:
    return inspect_jar(path)


def cached_inspect(path: str | Path) -> dict[str,Any]:
    """Always return a copy: MCP truncation must not mutate cached data."""
    from copy import deepcopy
    return deepcopy(_index(*_signature(path)))


@lru_cache(maxsize=128)
def _class(path: str, mtime: int, size: int, class_path: str) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        entries=_validate_archive(archive)
        for entry in entries:
            if entry.filename == class_path:
                return parse_classfile(_safe_read(archive, entry, MAX_CLASS_BYTES))
    raise JarInspectionError(f'Class not found: {class_path}')


def class_path(name: str) -> str:
    name=name.strip().replace('\\','/')
    if not name.endswith('.class'):
        name=name.replace('.', '/') + '.class'
    if name.startswith('/') or name.startswith('../') or '/..' in name:
        raise JarInspectionError('Invalid class path')
    return name


def cached_class(jar: str | Path, name: str) -> dict[str, Any]:
    from copy import deepcopy
    return deepcopy(_class(*_signature(jar), class_path(name)))


def method_bytecode(jar: str | Path, name: str, method: str, descriptor: str | None = None,
                    *, offset: int = 0, limit: int = 100) -> dict[str, Any]:
    path=class_path(name)
    with zipfile.ZipFile(jar) as archive:
        entries = _validate_archive(archive)
        target = next((entry for entry in entries if entry.filename == path), None)
        if target is None:
            raise JarInspectionError(f'Class not found: {path}')
        data=_safe_read(archive, target, MAX_CLASS_BYTES)
    report=inspect_method_bytecode(data, method, descriptor, offset=offset, limit=limit)
    report.update({'jar':str(Path(jar).resolve()), 'class':name})
    return report


def search_methods(jar: str | Path, query: str, *, offset: int = 0, limit: int = 100) -> dict[str,Any]:
    if not query.strip() or not (0<=offset<=500_000 and 1<=limit<=200):
        raise ValueError('Query, offset or limit invalid')
    needle=query.casefold()
    total=0
    results=[]
    with zipfile.ZipFile(jar) as archive:
        entries=_validate_archive(archive)
        if sum(entry.filename.endswith('.class') for entry in entries) > 20_000:
            raise JarInspectionError('Too many classes')
        for entry in entries:
            if not entry.filename.endswith('.class') or entry.is_dir():
                continue
            try:
                data=parse_classfile(_safe_read(archive,entry,MAX_CLASS_BYTES))
                for item in data['methods']:
                    if needle in item['name'].casefold() or needle in data['name'].casefold():
                        if offset<=total<offset+limit:
                            results.append({'class':data['name'],'method':item['name'],
                                            'descriptor':item['descriptor'],'flags':item['flags']})
                        total+=1
            except (ClassFormatError,JarInspectionError,RuntimeError,zipfile.BadZipFile):
                continue
    return {'total_matches':total, 'methods':results,
            'next_offset':offset+len(results) if offset+len(results)<total else None}
