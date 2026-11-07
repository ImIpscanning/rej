"""Read-only MCP dispatch for the REJ analysis service."""
from __future__ import annotations

from typing import Any
from ..core.analysis import cached_inspect, cached_class, search_methods, method_bytecode
from ..core.archive import compare_jars
from ..integrations.rea import rea_status
from .schemas import TOOLS, MAX_OUTPUT_CLASSES, MAX_OUTPUT_ERRORS


def _validate_arguments(name: str, arguments: Any) -> dict[str,Any]:
    if not isinstance(arguments,dict):
        raise ValueError('arguments must be a JSON object')
    spec=next((t['inputSchema'] for t in TOOLS if t['name']==name),None)
    if spec is None:
        raise ValueError(f'Unknown tool: {name}')
    if any(key not in spec['properties'] for key in arguments):
        raise ValueError('Unexpected arguments supplied')
    for key in spec['required']:
        if not isinstance(arguments.get(key),str) or not arguments[key].strip():
            raise ValueError(f'{key} must be a nonempty string')
    for key,value in arguments.items():
        typ=spec['properties'][key]['type']
        if typ=='string' and not isinstance(value,str):
            raise ValueError(f'{key} must be a string')
        if typ=='integer' and (type(value) is not int or
            not spec['properties'][key]['minimum']<=value<=spec['properties'][key]['maximum']):
            if key=='limit':
                raise ValueError(f'limit must be an integer between 1 and {MAX_OUTPUT_CLASSES}')
            raise ValueError(f'{key} is out of bounds')
    return arguments


def _page(items:list,offset:int,limit:int)->dict:
    return {'items':items[offset:offset+limit], 'total':len(items),
            'next_offset':offset+limit if offset+limit<len(items) else None}


def call_tool(name:str, arguments:Any)->dict[str,Any]:
    args=_validate_arguments(name,arguments)
    offset=args.get('offset',0); limit=args.get('limit',100)
    if name=='rej_rea_status':
        return rea_status()
    if name=='rej_inspect_jar':
        report=cached_inspect(args['jar_path'])
        page=_page(report['classes'],offset,limit)
        report['classes']=page['items']
        report['total_classes']=page['total']
        report['next_offset']=page['next_offset']
        report['errors_truncated']=max(0,len(report['errors'])-MAX_OUTPUT_ERRORS)
        report['errors']=report['errors'][:MAX_OUTPUT_ERRORS]
        return report
    if name=='rej_list_classes':
        classes=cached_inspect(args['jar_path'])['classes']
        matching=[x for x in classes if args.get('filter','').casefold() in x['name'].casefold()]
        page=_page(matching,offset,limit)
        return {'classes':page['items'],'total_matches':page['total'],
                'next_offset':page['next_offset'], 'truncated':max(0,page['total']-offset-len(page['items']))}
    if name=='rej_inspect_class':
        report=cached_class(args['jar_path'],args['class_name'])
        for key in ('methods','fields'):
            items=report[key]; report[key]=items[:MAX_OUTPUT_CLASSES]
            report[f'{key}_truncated']=max(0,len(items)-MAX_OUTPUT_CLASSES)
        return report
    if name=='rej_compare_jars':
        report=compare_jars(args['old_path'],args['new_path'])
        for key in ('added','removed','modified'):
            page=_page(report[key],offset,limit)
            report[f'{key}_total']=page['total']; report[key]=page['items']
            report[f'{key}_next_offset']=page['next_offset']
        return report
    if name=='rej_search_methods':
        return search_methods(args['jar_path'],args['query'],offset=offset,limit=limit)
    if name=='rej_disassemble_method':
        return method_bytecode(args['jar_path'],args['class_name'],args['method_name'],
                               args.get('descriptor'), offset=offset,limit=limit)
    raise ValueError(f'Unknown tool: {name}')
