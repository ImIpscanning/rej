"""Tree construction and class/method detail presentation, independent of the GUI app."""
from __future__ import annotations


def populate_tree(tree, entries: list[dict], query: str) -> dict[str, dict]:
    """Populate hierarchical packages without requiring a Java runtime.

    The returned mapping holds the original bytecode archive path, including
    multi-release names; package nodes are intentionally not selectable classes.
    """
    for node in tree.get_children(''):
        tree.delete(node)
    nodes = {}
    mapping = {}
    needle=query.casefold().strip()
    for i, item in enumerate(entries):
        if needle and needle not in item['name'].casefold():
            continue
        full_name=item['name']
        parts=full_name.split('.')
        parent=''
        for depth in range(len(parts)-1):
            package='.'.join(parts[:depth+1])
            node='p:'+package
            if node not in nodes:
                tree.insert(parent,'end',iid=node,text=parts[depth],open=bool(needle),values=('', ''))
                nodes[node]=True
            parent=node
        key=f"c:{item['path']}#{i}"
        tree.insert(parent,'end',iid=key,text=parts[-1],values=(item['java_version'].replace('Java ',''),item['method_count']))
        mapping[key]=item
    return mapping


def class_details(data:dict) -> str:
    result=[f"CLASS {data['name']}", '='*50, f"Java: {data['java_version']}",
            f"Superclass: {data['superclass']}",f"Interfaces: {', '.join(data['interfaces']) or '-'}",
            '', 'FIELDS','-'*45]
    result += [f"  {' '.join(x['flags'])} {x['name']} : {x['descriptor']}" for x in data['fields']]
    result += ['', 'METHODS','-'*45]
    result += [f"  {' '.join(x['flags'])} {x['name']}{x['descriptor']}" for x in data['methods']]
    return '\n'.join(result)


def bytecode_details(data:dict) -> str:
    result=[f"BYTECODE {data['class']}.{data['method']}{data['descriptor']}", '='*52,
            f"Code present: {data['has_code']}", f"Instructions: {data.get('total_instructions',0)}",
            'NOTE: JVM instructions, not reconstructed Java source.', '']
    for op in data.get('instructions',[]):
        operand=op['operand']
        ref=operand.get('reference','')
        result.append(f"{op['offset']:05d}  {op['mnemonic']:<20} {ref or operand.get('hex','')}")
    if data.get('next_offset') is not None:
        result.append('\nOnly first 200 instructions shown; use CLI for pagination.')
    return '\n'.join(result)
