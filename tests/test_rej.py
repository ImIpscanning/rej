"""Unit tests using synthetic classfiles, no JDK or external fixtures required."""
from __future__ import annotations

import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

from rej.archive import JarInspectionError, compare_jars, inspect_class, inspect_jar
from rej.classfile import ClassFormatError, parse_classfile
from rej.metadata import parse_manifest, parse_simple_yaml


def u2(n):
    return struct.pack(">H", n)


def u4(n):
    return struct.pack(">I", n)


def utf8(s):
    encoded = s.encode("utf-8")
    return b"\x01" + u2(len(encoded)) + encoded


def synthetic_class(name="example/Main", *, major=61, with_method=True):
    # Constant pool: 1=this class name, 2=this class, 3=java/lang/Object,
    # 4=superclass, 5=method name, 6=descriptor, 7=SourceFile,
    # 8=Main.java. Method has no Code attribute (abstract class/method).
    pool = (
        utf8(name) + b"\x07" + u2(1)
        + utf8("java/lang/Object") + b"\x07" + u2(3)
        + utf8("run") + utf8("()V") + utf8("SourceFile") + utf8("Main.java")
    )
    method = u2(1) + u2(0x0401) + u2(5) + u2(6) + u2(0) if with_method else u2(0)
    return (
        bytes.fromhex("CAFEBABE") + u2(0) + u2(major) + u2(9) + pool
        + u2(0x0421) + u2(2) + u2(4) + u2(0)
        + u2(0) + method + u2(1) + u2(7) + u4(2) + u2(8)
    )


class ClassfileTests(unittest.TestCase):
    def test_parse_class(self):
        data = parse_classfile(synthetic_class())
        self.assertEqual(data["name"], "example.Main")
        self.assertEqual(data["superclass"], "java.lang.Object")
        self.assertEqual(data["java_version"], "Java 17")
        self.assertEqual(data["method_count"], 1)
        self.assertEqual(data["methods"][0]["name"], "run")
        self.assertEqual(data["source_file"], "Main.java")

    def test_classfile_malformed(self):
        with self.assertRaises(ClassFormatError):
            parse_classfile(b"not-a-class")
        with self.assertRaises(ClassFormatError):
            parse_classfile(synthetic_class()[:-1])
        with self.assertRaises(ClassFormatError):
            parse_classfile(synthetic_class() + b"\x00")

    def test_classfile_unsupported_constant(self):
        data = bytearray(synthetic_class())
        data[10] = 99
        with self.assertRaisesRegex(ClassFormatError, "Unknown constant pool tag"):
            parse_classfile(bytes(data))


class MetadataTests(unittest.TestCase):
    def test_manifest_continuation(self):
        data = parse_manifest(b"Manifest-Version: 1.0\r\nMain-Class: example.\r\n Main\r\n")
        self.assertEqual(data["Main-Class"], "example.Main")

    def test_plugin_descriptor(self):
        parsed = parse_simple_yaml(b"name: MyPlugin\nversion: 1.0\nmain: example.Main\ndepend:\n - Vault\n - LuckPerms\n")
        self.assertEqual(parsed["name"], "MyPlugin")
        self.assertEqual(parsed["depend"], ["Vault", "LuckPerms"])


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.jar1 = self.root / "plugin1.jar"
        self.jar2 = self.root / "plugin2.jar"
        with zipfile.ZipFile(self.jar1, "w") as zf:
            zf.writestr("plugin.yml", "name: Example\nversion: 1.0\nmain: example.Main\n")
            zf.writestr("example/Main.class", synthetic_class())
            zf.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
        with zipfile.ZipFile(self.jar2, "w") as zf:
            zf.writestr("plugin.yml", "name: Example\nversion: 2.0\n")
            zf.writestr("example/Main.class", synthetic_class(major=65))
            zf.writestr("example/Other.class", synthetic_class("example/Other"))

    def test_inspect(self):
        result = inspect_jar(self.jar1)
        self.assertEqual(result["summary"]["class_count"], 1)
        self.assertEqual(result["summary"]["error_count"], 0)
        self.assertEqual(result["metadata"]["platform"], "Bukkit/Spigot/Paper")
        self.assertEqual(result["metadata"]["plugin"]["name"], "Example")
        self.assertEqual(len(result["sha256"]), 64)

    def test_class_details(self):
        result = inspect_class(self.jar1, "example.Main")
        self.assertEqual(result["methods"][0]["descriptor"], "()V")
        with self.assertRaisesRegex(JarInspectionError, "Class not found"):
            inspect_class(self.jar1, "no.SuchClass")

    def test_diff(self):
        result = compare_jars(self.jar1, self.jar2)
        self.assertEqual(result["added"], ["example/Other.class"])
        self.assertEqual(result["modified"], ["example/Main.class"])
        self.assertEqual(result["removed"], [])

    def test_invalid_zip(self):
        fake = self.root / "fake.jar"
        fake.write_text("hello")
        with self.assertRaisesRegex(JarInspectionError, "Not a valid"):
            inspect_jar(fake)

    def test_malformed_class_reported(self):
        jar = self.root / "bad.jar"
        with zipfile.ZipFile(jar, "w") as zf:
            zf.writestr("broken.class", b"oops")
        result = inspect_jar(jar)
        self.assertEqual(result["summary"]["error_count"], 1)
        self.assertEqual(result["summary"]["class_count"], 0)

    def test_cli_json(self):
        dest = self.root / "report.json"
        result = subprocess.run(
            [sys.executable, "-m", "rej", "inspect", str(self.jar1), "--json", str(dest)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Platform: Bukkit/Spigot/Paper", result.stdout)
        self.assertEqual(json.loads(dest.read_text(encoding="utf-8"))["summary"]["class_count"], 1)


if __name__ == "__main__":
    unittest.main()
