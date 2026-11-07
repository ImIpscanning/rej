"""Bounded static JVM bytecode disassembler; never executes target instructions.

This is a linear instruction decoder, NOT a Java source decompiler or a
control-flow verifier. It exposes symbolic constant-pool references where known.
"""
from __future__ import annotations

import struct
from typing import Any
from .classfile import ClassFormatError, Reader

# JVM opcode mnemonics (0..201). Undefined opcode values are rejected.
_NAMES = '''nop aconst_null iconst_m1 iconst_0 iconst_1 iconst_2 iconst_3 iconst_4 iconst_5
lconst_0 lconst_1 fconst_0 fconst_1 fconst_2 dconst_0 dconst_1 bipush sipush ldc ldc_w ldc2_w
iload lload fload dload aload iload_0 iload_1 iload_2 iload_3 lload_0 lload_1 lload_2 lload_3
fload_0 fload_1 fload_2 fload_3 dload_0 dload_1 dload_2 dload_3 aload_0 aload_1 aload_2 aload_3
iaload laload faload daload aaload baload caload saload istore lstore fstore dstore astore
istore_0 istore_1 istore_2 istore_3 lstore_0 lstore_1 lstore_2 lstore_3
fstore_0 fstore_1 fstore_2 fstore_3 dstore_0 dstore_1 dstore_2 dstore_3
astore_0 astore_1 astore_2 astore_3 iastore lastore fastore dastore aastore bastore castore sastore
pop pop2 dup dup_x1 dup_x2 dup2 dup2_x1 dup2_x2 swap
iadd ladd fadd dadd isub lsub fsub dsub imul lmul fmul dmul idiv ldiv fdiv ddiv
irem lrem frem drem ineg lneg fneg dneg ishl lshl ishr lshr iushr lushr iand land ior lor ixor lxor
iinc i2l i2f i2d l2i l2f l2d f2i f2l f2d d2i d2l d2f i2b i2c i2s
lcmp fcmpl fcmpg dcmpl dcmpg ifeq ifne iflt ifge ifgt ifle if_icmpeq if_icmpne if_icmplt
if_icmpge if_icmpgt if_icmple if_acmpeq if_acmpne goto jsr ret tableswitch lookupswitch
ireturn lreturn freturn dreturn areturn return getstatic putstatic getfield putfield invokevirtual
invokespecial invokestatic invokeinterface invokedynamic new newarray anewarray arraylength
athrow checkcast instanceof monitorenter monitorexit wide multianewarray ifnull ifnonnull goto_w jsr_w'''.split()
assert len(_NAMES) == 202, len(_NAMES)
# Operand lengths, in bytes; unlisted opcodes take zero operands.
_OPERANDS = {**{i: 1 for i in [16,18,21,22,23,24,25,54,55,56,57,58,169,188]},
             **{i: 2 for i in [17,19,20,132,178,179,180,181,182,183,184,187,189,192,193,198,199]},
             **{i: 2 for i in range(153,167)},
             167:2,168:2,185:4,186:4,197:3,200:4,201:4}
_POOL_REFS = set([18,19,20,178,179,180,181,182,183,184,185,186,187,189,192,193,197])


def _pool(data: bytes, reader: Reader) -> list[tuple | None]:
    count = reader.u2()
    if count < 1:
        raise ClassFormatError('Invalid constant pool count')
    pool: list[tuple | None] = [None] * count
    i = 1
    while i < count:
        tag = reader.u1()
        if tag == 1:
            pool[i] = (tag, reader.read(reader.u2()).decode('utf-8', errors='replace'))
        elif tag in (3,4):
            pool[i] = (tag, reader.read(4).hex())
        elif tag in (5,6):
            pool[i] = (tag, reader.read(8).hex()); i += 1
        elif tag in (7,8,16,19,20):
            pool[i] = (tag, reader.u2())
        elif tag in (9,10,11,12,17,18):
            pool[i] = (tag, reader.u2(), reader.u2())
        elif tag == 15:
            pool[i] = (tag, reader.u1(), reader.u2())
        else:
            raise ClassFormatError(f'Unsupported constant pool tag {tag}')
        i += 1
    return pool


def _reference(pool: list[tuple | None], index: int) -> str:
    def item(i):
        if not isinstance(i, int) or not 0 < i < len(pool) or pool[i] is None:
            raise ClassFormatError(f'Invalid constant pool reference #{i}')
        return pool[i]
    def utf(i):
        v=item(i)
        if v[0] != 1:
            raise ClassFormatError(f'Expected UTF8 at #{i}')
        return v[1]
    value = item(index)
    if value[0] in (7,8,16,19,20):
        return utf(value[1]).replace('/', '.')
    if value[0] == 1:
        return value[1]
    if value[0] in (9,10,11):
        owner = _reference(pool, value[1])
        name_type = item(value[2])
        if name_type[0] == 12:
            return f'{owner}.{utf(name_type[1])}{utf(name_type[2])}'
    if value[0] in (17,18):
        name_type = item(value[2])
        if name_type[0] == 12:
            return f'{utf(name_type[1])}{utf(name_type[2])} [bootstrap #{value[1]}]'
    return f'constant_pool#{index}'


def decode_instructions(code: bytes, pool: list[tuple | None], *, offset: int = 0, limit: int = 200) -> dict[str, Any]:
    if not (0 <= offset <= len(code) and 1 <= limit <= 1000):
        raise ValueError('offset or limit out of bounds')
    pos = 0
    result: list[dict[str, Any]] = []
    total = 0
    has_more = False
    def read_n(size: int) -> bytes:
        nonlocal pos
        if size < 0 or size > len(code) - pos:
            raise ClassFormatError(f'Truncated instruction at offset {pos}')
        block = code[pos:pos+size]; pos += size
        return block

    while pos < len(code):
        start = pos
        op = read_n(1)[0]
        if op >= len(_NAMES):
            raise ClassFormatError(f'Invalid JVM opcode 0x{op:02x} at {start}')
        mnemonic = _NAMES[op]
        if op in (170, 171):
            padding = (4 - (pos % 4)) % 4
            read_n(padding)
            default = struct.unpack('>i', read_n(4))[0]
            if op == 170:
                lo, hi = struct.unpack('>ii', read_n(8))
                n = hi - lo + 1
                if not 0 <= n <= len(code) // 4:
                    raise ClassFormatError('Invalid tableswitch bounds')
                read_n(n * 4)
                operand = {'default_target': start+default, 'low': lo, 'high': hi, 'entries': n}
            else:
                n = struct.unpack('>i', read_n(4))[0]
                if not 0 <= n <= len(code) // 8:
                    raise ClassFormatError('Invalid lookupswitch count')
                read_n(n * 8)
                operand = {'default_target': start+default, 'entries': n}
        elif op == 196:  # wide
            nxt = read_n(1)[0]
            if nxt not in (21,22,23,24,25,54,55,56,57,58,132,169):
                raise ClassFormatError('Invalid wide opcode')
            data = read_n(4 if nxt == 132 else 2)
            operand = {'wide_opcode': _NAMES[nxt], 'hex': data.hex()}
        else:
            operand = {'hex': read_n(_OPERANDS.get(op,0)).hex()}
        if op in _POOL_REFS:
            raw = bytes.fromhex(operand['hex'])
            idx = raw[0] if op == 18 else struct.unpack('>H', raw[:2])[0]
            operand['reference'] = _reference(pool, idx)
        total += 1
        if start >= offset:
            if len(result) < limit:
                result.append({'offset':start, 'opcode':op, 'mnemonic':mnemonic, 'operand': operand})
            else:
                has_more = True
    next_offset = result[-1]['offset'] + 1 if has_more and result else None
    return {'instructions': result, 'total_instructions': total, 'code_length': len(code), 'next_offset': next_offset}


def inspect_method_bytecode(class_bytes: bytes, method_name: str, descriptor: str | None = None,
                            *, offset: int = 0, limit: int = 200) -> dict[str, Any]:
    r = Reader(class_bytes)
    if r.u4() != 0xCAFEBABE:
        raise ClassFormatError('Missing CAFEBABE magic')
    minor, major = r.u2(), r.u2()
    pool = _pool(class_bytes, r)
    def utf(idx: int) -> str:
        if not 0 < idx < len(pool) or pool[idx] is None or pool[idx][0] != 1:
            raise ClassFormatError('Invalid constant pool UTF8')
        return pool[idx][1]
    r.read(6)  # access flags, this_class, super_class
    r.read(r.u2()*2)  # interfaces
    def read_attributes(want_code=False):
        code = None
        for _ in range(r.u2()):
            name = utf(r.u2()); size = r.u4()
            content = r.read(size)
            if want_code and name == 'Code':
                ar = Reader(content)
                ar.u2(); ar.u2(); length = ar.u4()
                if length > 65535:
                    raise ClassFormatError('JVM Code attribute exceeds 65535 bytes')
                code = ar.read(length)
        return code
    for _ in range(r.u2()):
        r.read(6); read_attributes()
    found = []
    for _ in range(r.u2()):
        flags = r.u2(); name = utf(r.u2()); desc = utf(r.u2())
        code = read_attributes(name == method_name and (descriptor is None or descriptor == desc))
        if name == method_name and (descriptor is None or descriptor == desc):
            found.append((name, desc, code))
    if not found:
        raise ClassFormatError(f'Method not found: {method_name} {descriptor or ""}')
    if len(found) > 1:
        raise ClassFormatError('Method overloaded: supply a JVM descriptor to disambiguate')
    name, desc, code = found[0]
    if code is None:
        return {'method':name, 'descriptor':desc, 'has_code':False, 'instructions':[]}
    return {'method':name,'descriptor':desc,'has_code':True,
            **decode_instructions(code, pool, offset=offset, limit=limit)}
