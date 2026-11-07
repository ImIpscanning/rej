# REJ Security Policy

REJ is a **read-only Java archive metadata and bytecode inspection tool**, not an antivirus, Java sandbox or exploit prevention product.

Please use **Issues** for ordinary parser bugs and tests. Report potentially sensitive security issues privately through the repository's GitHub security advisory workflow when available. Do not publish private files, proprietary plugins, credentials, or malware samples.

## Analysis boundaries

- The JAR being inspected is never executed by REJ CLI, GUI or MCP.
- REJ does not automatically download or run third-party analysis engines.
- The optional Vineflower integration executes the **user-supplied decompiler JAR**, not the target JAR; run only trusted tools.
- MCP runs locally over stdio and exposes no network server. Connected clients may send text results to an AI provider, so review the provider's data practices before using private code.
- A successful report does not prove that a JAR is safe or benign.
- Archive readers enforce entry count and size limits but may still encounter malformed or unusual JVM classfiles. Consider sandboxing the analysis environment when inspecting untrusted data.

REJ's native class metadata parser and disassembler do not reconstruct original Java source or bypass protections.
