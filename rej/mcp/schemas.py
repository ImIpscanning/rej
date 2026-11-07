"""Schema definitions for REJ's MCP read-only tools."""
from __future__ import annotations

MAX_OUTPUT_CLASSES = 200
MAX_OUTPUT_ERRORS = 30


def _schema(properties, required=()):
    return {"type":"object","properties":properties,"required":list(required),"additionalProperties":False}

P_PATH={"type":"string","description":"Absolute path to a local JAR"}
P_LIMIT={"type":"integer","minimum":1,"maximum":200}
P_OFFSET={"type":"integer","minimum":0,"maximum":500000}
TOOLS = [
    {"name":"rej_inspect_jar","description":"Inspect local Java JAR and Minecraft metadata without running the JAR. Paged class preview.",
     "inputSchema":_schema({"jar_path":P_PATH,"offset":P_OFFSET,"limit":P_LIMIT},["jar_path"])},
    {"name":"rej_list_classes","description":"List Java class names with filtering and pagination.",
     "inputSchema":_schema({"jar_path":P_PATH,"filter":{"type":"string"},"offset":P_OFFSET,"limit":P_LIMIT},["jar_path"])},
    {"name":"rej_inspect_class","description":"Inspect one class, declared fields, methods and descriptors.",
     "inputSchema":_schema({"jar_path":P_PATH,"class_name":{"type":"string"}},["jar_path","class_name"])},
    {"name":"rej_compare_jars","description":"Compare class-file hashes of two JAR builds with paged results.",
     "inputSchema":_schema({"old_path":P_PATH,"new_path":P_PATH,"offset":P_OFFSET,"limit":P_LIMIT},["old_path","new_path"])},
    {"name":"rej_search_methods","description":"Search method names or class names inside a local JAR.",
     "inputSchema":_schema({"jar_path":P_PATH,"query":{"type":"string"},"offset":P_OFFSET,"limit":P_LIMIT},["jar_path","query"])},
    {"name":"rej_disassemble_method","description":"Read JVM bytecode mnemonics and constant-pool references. Does not execute or decompile Java.",
     "inputSchema":_schema({"jar_path":P_PATH,"class_name":{"type":"string"},"method_name":{"type":"string"},
          "descriptor":{"type":"string"},"offset":P_OFFSET,"limit":P_LIMIT},["jar_path","class_name","method_name"])},
    {"name":"rej_rea_status","description":"Check whether the separate REA CLI is on PATH; does not execute REA.",
     "inputSchema":_schema({})},
]
