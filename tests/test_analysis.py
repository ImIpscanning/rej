"""Bytecode, pagination, cache, comparisons and GUI helper regression tests."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from rej.core.analysis import cached_inspect, cached_class, search_methods, method_bytecode
from rej.core.bytecode import decode_instructions
from rej.core.classfile import ClassFormatError
from rej.core.archive import JarInspectionError
from rej.gui.explorer import class_details, populate_tree
from rej.gui.comparison import format_comparison
from rej.mcp.tools import call_tool
from rej.integrations import claude_config, codex_config

DEMO = Path(__file__).resolve().parent.parent / 'examples' / 'HelloPlugin-demo.jar'


class AnalysisTests(unittest.TestCase):
    def test_demo_method_bytecode(self):
        report = method_bytecode(DEMO, 'org.example.HelloPlugin', 'run')
        self.assertTrue(report['has_code'])
        names = [x['mnemonic'] for x in report['instructions']]
        self.assertIn('invokestatic', names)
        self.assertIn('return', names)
        self.assertTrue(any('java.util.List.of' in x['operand'].get('reference','') for x in report['instructions']))

    def test_method_search(self):
        report = search_methods(DEMO, 'greet')
        self.assertEqual(report['total_matches'], 1)
        self.assertEqual(report['methods'][0]['method'], 'greet')
        self.assertIsNone(report['next_offset'])

    def test_search_page(self):
        one = search_methods(DEMO, 'org.example', limit=1)
        self.assertEqual(len(one['methods']), 1)
        self.assertIsNotNone(one['next_offset'])
        two = search_methods(DEMO, 'org.example', offset=one['next_offset'], limit=1)
        self.assertNotEqual(one['methods'][0],two['methods'][0])

    def test_cached_jar_not_mutated_by_mcp(self):
        original = cached_inspect(DEMO)
        page = call_tool('rej_inspect_jar', {'jar_path':str(DEMO),'limit':1})
        page['classes'].clear()
        self.assertEqual(cached_inspect(DEMO)['summary'], original['summary'])
        self.assertEqual(len(cached_inspect(DEMO)['classes']), len(original['classes']))

    def test_cache_invalidates_when_file_changes(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'x.jar'
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr('plugin.yml','name: A\n')
            self.assertEqual(cached_inspect(path)['metadata']['plugin']['name'],'A')
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr('plugin.yml','name: B_modified\n')
            self.assertEqual(cached_inspect(path)['metadata']['plugin']['name'],'B_modified')

    def test_mcp_paginate_and_limits(self):
        page=call_tool('rej_list_classes', {'jar_path':str(DEMO),'limit':1,'offset':0})
        self.assertEqual(len(page['classes']),1)
        self.assertIsNone(page['next_offset'])
        with self.assertRaises(ValueError):
            call_tool('rej_list_classes',{'jar_path':str(DEMO),'offset':-1})
        with self.assertRaises(ValueError):
            call_tool('rej_disassemble_method',{'jar_path':str(DEMO),'class_name':'x','method_name':'run','limit':201})

    def test_mcp_disassemble(self):
        result=call_tool('rej_disassemble_method', {'jar_path':str(DEMO),'class_name':'org.example.HelloPlugin','method_name':'greet'})
        self.assertTrue(result['has_code'])
        self.assertIn('invokedynamic', [x['mnemonic'] for x in result['instructions']])

    def test_cli_entrypoint(self):
        process=subprocess.run([sys.executable,'-m','rej','bytecode',str(DEMO),'org.example.HelloPlugin','greet'],
                               capture_output=True,text=True,timeout=10)
        self.assertEqual(process.returncode,0,process.stderr)
        self.assertIn('invokedynamic',process.stdout)

    def test_simple_jvm_instruction_decoder(self):
        result=decode_instructions(bytes([0x03,0x3b,0xb1]),[None],limit=2)
        self.assertEqual([x['mnemonic'] for x in result['instructions']],['iconst_0','istore_0'])
        self.assertEqual(result['next_offset'],2)
        result2=decode_instructions(bytes([0x03,0x3b,0xb1]),[None],offset=2,limit=2)
        self.assertEqual([x['mnemonic'] for x in result2['instructions']],['return'])

    def test_bad_switch_rejected(self):
        with self.assertRaises(ClassFormatError):
            decode_instructions(bytes([170,0,0,0,0]),[None])
        with self.assertRaises(ClassFormatError):
            decode_instructions(bytes([196,255,0,0]),[None])
        with self.assertRaises(ClassFormatError):
            decode_instructions(bytes([255]),[None])

    def test_bad_class_disassembler(self):
        with self.assertRaises(ClassFormatError):
            from rej.core.bytecode import inspect_method_bytecode
            inspect_method_bytecode(b'bad', 'run')

    def test_duplicate_zip_entry_in_inspector(self):
        with tempfile.TemporaryDirectory() as d:
            jar=Path(d)/'test.jar'
            with zipfile.ZipFile(jar,'w') as z:
                z.writestr('plugin.yml','name: demo\n')
                z.writestr('plugin.yml','name: demo\n')
            report=cached_inspect(jar)
            self.assertIn('plugin',report['metadata'])

    def test_mcp_config(self):
        self.assertIn('mcpServers',json.loads(claude_config()))
        self.assertIn('mcp_servers.rej',codex_config())


class _Tree:
    """Pure fake Treeview for testing hierarchy construction without X server."""
    def __init__(self):
        self.items={}
    def get_children(self,parent=''):
        return [k for k,v in self.items.items() if v[0]==parent]
    def delete(self,key):
        for child in self.get_children(key):
            self.delete(child)
        self.items.pop(key)
    def insert(self,parent,where,**kw):
        self.items[kw['iid']] = (parent,kw)

class GuiHelpersTests(unittest.TestCase):
    def test_hierarchical_packages(self):
        tree=_Tree()
        entries=[{'name':'org.example.Main','path':'org/example/Main.class','java_version':'Java 21','method_count':5},
                 {'name':'org.example.Other','path':'org/example/Other.class','java_version':'Java 21','method_count':1}]
        mapping=populate_tree(tree,entries,'')
        self.assertIn('p:org.example',tree.items)
        self.assertEqual(len(mapping),2)
        self.assertEqual(len(populate_tree(tree,entries,'Main')),1)

    def test_compare_render(self):
        s=format_comparison({'old':'old.jar','new':'new.jar','added':['A.class'], 'removed':[],
                             'modified':[], 'unchanged_count':3})
        self.assertIn('A.class',s)
        self.assertIn('Unchanged classes: 3',s)


if __name__ == '__main__':
    unittest.main()
