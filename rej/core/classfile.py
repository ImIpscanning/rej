"""Bounded JVM .class metadata parser. Never loads or executes Java bytecode."""
from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Any


class ClassFormatError(ValueError):
    """Invalid or unsupported JVM classfile."""


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read(self, size: int) -> bytes:
        if size < 0 or size > len(self.data) - self.pos:
            raise ClassFormatError(f"Unexpected end of classfile at offset {self.pos}")
        value = self.data[self.pos : self.pos + size]
        self.pos += size
        return value

    def u1(self) -> int:
        return self.read(1)[0]

    def u2(self) -> int:
        return struct.unpack(">H", self.read(2))[0]

    def u4(self) -> int:
        return struct.unpack(">I", self.read(4))[0]


CLASS_FLAGS = {
    0x0001: "public", 0x0010: "final", 0x0020: "super", 0x0200: "interface",
    0x0400: "abstract", 0x1000: "synthetic", 0x2000: "annotation", 0x4000: "enum", 0x8000: "module",
}
FIELD_FLAGS = {
    0x0001: "public", 0x0002: "private", 0x0004: "protected", 0x0008: "static",
    0x0010: "final", 0x0040: "volatile", 0x0080: "transient", 0x1000: "synthetic", 0x4000: "enum",
}
METHOD_FLAGS = {
    0x0001: "public", 0x0002: "private", 0x0004: "protected", 0x0008: "static",
    0x0010: "final", 0x0020: "synchronized", 0x0040: "bridge", 0x0080: "varargs",
    0x0100: "native", 0x0400: "abstract", 0x0800: "strict", 0x1000: "synthetic",
}


def flag_names(bits: int, lookup: dict[int, str]) -> list[str]:
    return [name for bit, name in lookup.items() if bits & bit]


def java_version(major: int) -> str:
    if major == 45:
        return "Java 1.1"
    if 46 <= major <= 48:
        return f"Java 1.{major - 44}"
    if major >= 49:
        return f"Java {major - 44}"
    return "Unknown"


def parse_classfile(data: bytes, *, include_members: bool = True) -> dict[str, Any]:
    r = Reader(data)
    if r.u4() != 0xCAFEBABE:
        raise ClassFormatError("Missing CAFEBABE magic")
    minor = r.u2()
    major = r.u2()
    count = r.u2()
    if count < 1:
        raise ClassFormatError("Invalid constant pool count")
    pool: list[Any] = [None] * count
    index = 1
    while index < count:
        tag = r.u1()
        if tag == 1:  # CONSTANT_Utf8
            raw = r.read(r.u2())
            pool[index] = (tag, raw.decode("utf-8", errors="replace"))
        elif tag in (3, 4):
            r.read(4)
            pool[index] = (tag,)
        elif tag in (5, 6):
            r.read(8)
            pool[index] = (tag,)
            index += 1
        elif tag in (7, 8, 16, 19, 20):
            pool[index] = (tag, r.u2())
        elif tag in (9, 10, 11, 12, 17, 18):
            pool[index] = (tag, r.u2(), r.u2())
        elif tag == 15:
            pool[index] = (tag, r.u1(), r.u2())
        else:
            raise ClassFormatError(f"Unknown constant pool tag {tag} at index {index}")
        index += 1

    def utf8(idx: int) -> str:
        if not (0 < idx < count) or pool[idx] is None or pool[idx][0] != 1:
            raise ClassFormatError(f"Invalid UTF8 constant pool reference: {idx}")
        return pool[idx][1]

    def class_name(idx: int) -> str | None:
        if idx == 0:
            return None
        if not (0 < idx < count) or pool[idx] is None or pool[idx][0] != 7:
            raise ClassFormatError(f"Invalid class reference: {idx}")
        return utf8(pool[idx][1]).replace("/", ".")

    flags = r.u2()
    this_name = class_name(r.u2())
    parent_name = class_name(r.u2())
    interfaces = [class_name(r.u2()) for _ in range(r.u2())]

    def attributes() -> dict[str, Any]:
        result: dict[str, Any] = {}
        for _ in range(r.u2()):
            name = utf8(r.u2())
            length = r.u4()
            if name == "SourceFile" and length == 2:
                result["source_file"] = utf8(r.u2())
            else:
                r.read(length)
        return result

    def members(lookup: dict[int, str]) -> list[dict[str, Any]]:
        out = []
        for _ in range(r.u2()):
            access = r.u2()
            name = utf8(r.u2())
            descriptor = utf8(r.u2())
            attributes()
            if include_members:
                out.append({"name": name, "descriptor": descriptor, "flags": flag_names(access, lookup)})
        return out

    fields = members(FIELD_FLAGS)
    methods = members(METHOD_FLAGS)
    class_attrs = attributes()
    if r.pos != len(data):
        raise ClassFormatError(f"Unexpected {len(data) - r.pos} trailing classfile bytes")
    return {
        "name": this_name,
        "superclass": parent_name,
        "interfaces": interfaces,
        "major_version": major,
        "minor_version": minor,
        "java_version": java_version(major),
        "flags": flag_names(flags, CLASS_FLAGS),
        "field_count": len(fields) if include_members else None,
        "method_count": len(methods) if include_members else None,
        "fields": fields if include_members else [],
        "methods": methods if include_members else [],
        **class_attrs,
    }
