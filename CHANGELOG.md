# Changelog

## 0.1.0 — Initial release

- Read-only JAR archive inspection with SHA-256 and resource boundaries.
- Java class file metadata parsing: types, superclass, interfaces, fields, methods and classfile version.
- Minecraft plugin descriptor detection.
- Class listings and filtering, class-detail output.
- Comparison of added, removed and modified Java classes across two archives.
- Optional JSON exports.
- Optional local Vineflower decompilation integration.
- Windows launcher and interactive text menu.
- Included original compiled demo JAR and 11 unit/CLI tests.

**Known limitations:** no built-in bytecode disassembly or deobfuscation; nested YAML only partially parsed; source reconstruction requires external Vineflower.
