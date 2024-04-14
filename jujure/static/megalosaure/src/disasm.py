#!/usr/bin/env python3

import struct
from pwn import *
from typing import Optional, List
from Crypto.Util.number import inverse
from z3 import *


opcodes = {
        0x0: "pushread_i_f",
        0x1: "push_m",
        0x2: "push32_i_i",
        0x3: "popwrite_i_f",
        0x4: "pop_m",
        0x5: "dup",
        0x6: "add",
        0x7: "sub",
        0x8: "mul",
        0x9: "mod",
        0xa: "xor",
        0xb: "and",
        0xc: "or",
        0xd: "shr",
        0xe: "shl",
        0xf: "not",
        0x10: "neg",
        0x11: "nop",
        0x12: "exit",
}

registers = [
        "ip",
        "sp"
]

N = 2**32


class Stream:
    i: int
    buf: bytes

    def __init__(self, buf) -> None:
        self.pos = 0
        self.buf = buf

    def read_u16(self) -> Optional[int]:
        try:
            val = struct.unpack("<H", self.buf[self.pos:self.pos + 2])
            self.pos += 2
            return val[0]
        except:
            return None

    def read_i16(self) -> Optional[int]:
        try:
            val = struct.unpack("<h", self.buf[self.pos:self.pos + 2])
            self.pos += 2
            return val[0]
        except:
            return None

    def read_u32(self) -> Optional[int]:
        try:
            val = struct.unpack("<I", self.buf[self.pos:self.pos + 4])
            self.pos += 4
            return val[0]
        except:
            return None

    def read_i32(self) -> Optional[int]:
        try:
            val = struct.unpack("<i", self.buf[self.pos:self.pos + 4])
            self.pos += 4
            return val[0]
        except:
            return None

class Operand:
    pass


class Register(Operand):
    index: int
    name: str

    def __init__(self, index: int) -> None:
        self.index = index
        self.name = f"r{hex(index)}"

class Mem(Operand):
    index: int
    name: str

    def __init__(self, index: int) -> None:
        self.index = index
        self.name = f"m[{hex(index)}]"

class Imm(Operand):
    value: int
    unsigned: int

    def __init__(self, value: int) -> None:
        self.value = value
        self.raw = struct.unpack("<I", struct.pack("<i", self.value))[0]


class Instruction:
    opcode: int
    operands: List[Operand]
    addr: int
    name: str
    size: int

    def __init__(self, opcode, operands, opcodes) -> None:
        self.opcode = opcode
        self.operands = operands
        self.name = opcodes[self.opcode] if self.opcode in opcodes else "invalid"
        self.size = 2 * (len(operands) + 1)


    @staticmethod
    def disassemble(data: bytes) -> 'Instruction':
        stream = Stream(data)
        opcode = stream.read_u16()
        operands = []

        if opcode not in opcodes:
            return Instruction(opcode, [], addr, opcodes)

        mnemonic = opcodes[opcode]
        mnemonic_decomp = mnemonic.split('_')
        mnemonic_decomp.pop(0)

        for element in mnemonic_decomp:
            if element == 'i':
                value = stream.read_u16()
                operand = Imm(value)
                operands.append(operand)
            elif element == 'm':
                value = stream.read_u16()
                operand = Mem(value)
                operands.append(operand)
            elif element == 'f':
                n_regs = operands[-1].value
                for i in range(n_regs):
                    index = stream.read_u16()
                    operand = Register(index)
                    operands.append(operand)

        return Instruction(opcode, operands, opcodes)

    def to_string(self):
        asm = self.name

        for op in self.operands:
            asm += ' '
            if isinstance(op, Register):
                asm += op.name
            elif isinstance(op, Mem):
                asm += op.name
            elif isinstance(op, Imm):
                asm += f"{hex(op.value)}"

        return asm

    def transpile(self):
        if self.name == "pop_m":
            return ''
        elif self.name == "push32_i_i":
            val = (self.operands[1].value << 0x10) | self.operands[0].value
            return f'{val}'
        elif self.name == "push_m":
            return f'm{self.operands[0].index}'
        elif self.name == "add":
            return '+'
        elif self.name == "sub":
            return '-'
        elif self.name == "mul":
            return '*'
        elif self.name == "mod":
            return '%'
        elif self.name == "xor":
            return '^'
        elif self.name == "and":
            return '&'
        elif self.name == "or":
            return '|'
        elif self.name == "not":
            return '~'
        elif self.name == "neg":
            return '-'
        elif self.name == "shr":
            return '>>'
        elif self.name == "shl":
            return '<<'
        else:
            raise



class Child:
    def __init__(self, pod, index):
        self.pod = pod
        self.index = index
        self.offset = (pod.offset + index) * self.pod.code_size
        self.code = self.pod.megalosaure.elf.read(self.pod.code_base + self.offset * 2, self.pod.code_size * 2)
        self.instructions = []
        self.depends = []
        self.unlocks = []
        self.inputs = []
        self.forced = False, 0
        self.main_instr = None
        while True:
            instr = Instruction.disassemble(self.code)
            self.code = self.code[instr.size:]
            self.instructions.append(instr)
            if instr.name == 'exit':
                break

            elif instr.name == 'pushread_i_f':
                for reg in instr.operands[1:]:
                    self.depends.append(reg.index)

            elif instr.name == 'popwrite_i_f':
                for reg in instr.operands[1:]:
                    self.unlocks.append(reg.index)

            else:
                if self.main_instr != None:
                    raise
                self.main_instr = instr


    def to_string(self):
        asm = ""
        for instr in self.instructions:
            asm += instr.to_string() + '\n'
        return asm

    def consume_locks(self, locks):
        while self.depends != []:
            dependency = self.depends[0]
            if locks[dependency][0]:
                return
            self.inputs.append(locks[dependency][1])
            locks[dependency] = (True, None)
            self.depends.pop(0)

    def is_schedulable(self, locks):
        return len(self.depends) == 0

    def mark_unlocks(self, locks):
        for unlock in self.unlocks:
            locks[unlock] = (False, self)


    def invert(self, desired):
        instr = self.main_instr
        op = instr.name
        inputs = self.inputs

        if len(inputs) == 0:
            if op == 'push_m':
                return desired
            elif op == 'push32_i_i':
                print(self.forced)
                raise
            else:
                print(op)

        elif len(inputs) == 1:
            inp = inputs[0]
            if op == "pop_m":
                return inp.invert(desired)
            if op == "not":
                return inp.invert((~desired) % N)
            else:
                print(op)
        else:
            forced0 = inputs[0].forced
            forced1 = inputs[1].forced

            if not forced0 and not forced1:
                return

            forced_child = inputs[0] if forced0[0] else inputs[1]
            unk_child = inputs[1] if forced0[0] else inputs[0]

            if op == 'xor':
                return unk_child.invert(desired ^ forced_child.forced[1])
            elif op == 'sub':
                if forced0:
                    return unk_child.invert((desired + forced_child.forced[1]) % N)
                else:
                    return unk_child.invert((-desired + forced_child.forced[1]) % N)
            elif op == 'add':
                return unk_child.invert((desired - forced_child.forced[1]) % N)
            elif op == 'and':
                return unk_child.invert(desired & forced_child.forced[1])
            elif op == 'or':
                return unk_child.invert(desired | forced_child.forced[1])
            elif op == 'mul':
                return unk_child.invert(((desired) * inverse(forced_child.forced[1], N)) % N)
            elif op == 'shl':
                return unk_child.invert(((desired) * inverse(forced_child.forced[1], N)) % N)
            else:
                print(op)

    def transpile(self, indent=0):
        code = "(\n"
        indent += 4
        code += ' ' * indent
        instr = self.main_instr
        op = instr.name
        inputs = self.inputs

        if len(inputs) == 0:
            code += instr.transpile()

        elif len(inputs) == 1:
            inp = inputs[0]
            code += instr.transpile() + inp.transpile(indent)
        else:
            code += inputs[1].transpile(indent)
            code += instr.transpile()
            code += inputs[0].transpile(indent)
        code += '\n'
        indent -= 4
        code += ' ' * indent
        code += ")"
        return code

    def z3(self, solver, memory):
        instr = self.main_instr
        op = instr.name
        inputs = self.inputs
        output = BitVec(f'{self.pod.index}_{self.index}', 32)

        if len(inputs) == 0:
            if op == 'push_m':
                addr = instr.operands[0].index
                mem = memory[addr]
                solver.add(mem == output)
            elif op == 'push32_i_i':
                val = (instr.operands[1].value << 0x10) | instr.operands[0].value
                output = BitVecVal(val, 32)
            else:
                print(op)

        elif len(inputs) == 1:
            inp = inputs[0]
            value = inp.z3(solver, memory)
            if op == "pop_m":
                addr = instr.operands[0].index
                mem = memory[addr]
                solver.add(mem == value)
                solver.add(mem == output)
            elif op == "not":
                solver.add(output == ~value)
            else:
                print(op)
        else:
            value0 = inputs[0].z3(solver, memory)
            value1 = inputs[1].z3(solver, memory)
            if op == "xor":
                solver.add(output == (value0 ^ value1))
            elif op == "or":
                solver.add(output == (value0 | value1))
            elif op == "and":
                solver.add(output == (value0 & value1))
            elif op == "add":
                solver.add(output == (value0 + value1))
            elif op == "sub":
                solver.add(output == (value1 - value0))
            elif op == "mul":
                solver.add(output == (value1 * value0))
            elif op == "shl":
                solver.add(output == (value1 << value0))
            elif op == "shr":
                solver.add(output == (value1 >> value0))
            else:
                print(op)
        return output


class Pod:
    def __init__(self, n_childs, offset, megalosaure, i):
        self.megalosaure = megalosaure
        self.n_childs = n_childs
        self.offset = offset
        self.childs = []
        self.code_size = 9
        self.code_base = 0x50c0
        self.stages = []
        self.index = i
        for i in range(n_childs):
            self.childs.append(Child(self, i))

    def build_ast(self):
        locks = [(True, None) for _ in range(0x26c9)]
        to_schedule = [child for child in self.childs]
        next_stage_schedule = [1]
        while next_stage_schedule != []:
            current_stage = []
            next_stage_schedule = []
            while to_schedule != []:
                child = to_schedule.pop(0)
                child.consume_locks(locks)
                if child.is_schedulable(locks):
                    current_stage.append(child)
                    child.mark_unlocks(locks)
                else:
                    next_stage_schedule.append(child)
            to_schedule = next_stage_schedule
            self.stages.append(current_stage)
        return self.stages


    def transpile(self):
        code = f"uint32_t m{self.index + 2} = {self.stages[-1][0].transpile()};\n"
        return code

    def z3(self, solver, memory):
        self.stages[-1][0].z3(solver, memory)


class Megalosaure:
    name = "megalosaure"
    address_size = 2
    default_int_size = 4
    instr_aligment = 2
    max_instr_length = 12

    def __init__(self, path):
        self.elf = ELF(path)
        print('[+] Loading virtual machines')
        self.podinfo_addresses = 0x444220
        self.pods = []
        for i in range(0x2c):
            podinfo_b = self.elf.read(self.podinfo_addresses + i * 8, 8)
            n_childs = struct.unpack('<L', podinfo_b[:4])[0]
            offset = struct.unpack('<L', podinfo_b[4:])[0]
            pod = Pod(n_childs, offset, self, i)
            self.pods.append(pod)

    def build_ast(self):
        print('[+] Lifting AST')
        for pod in self.pods:
            pod.build_ast()

    def transpile(self, path, depth):
        print('[+] Transpiling to C')
        code = "#include <stdint.h>\nuint64_t megalosaure(uint32_t m0, uint32_t m1) {\n"
        for i in range(depth):
            code += self.pods[i].transpile()
        code += f"return (((uint64_t)m{depth + 1}) << 32) | m{depth};\n"
        code += "}\n"

        print(f'[+] Transpiled to {path}')
        with open(path, 'w') as f:
            f.write(code)
        return code

    def z3(self, depth, desired):
        print('[+] Building z3 solver')

        memory = [BitVec(f'm{i}', 32) for i in range(0x2e)]
        memory[0] = BitVecVal(0x43534346, 32)
        solver = Solver()
        for i in range(depth):
            self.pods[i].z3(solver, memory)

        m44 = desired % (2**32)
        m45 = desired >> 32

        solver.add(memory[44] == m44)
        solver.add(memory[45] == m45)

        print('[+] Running solver')
        print(solver.check())
        m = solver.model()
        print(m)
        return code


meg = Megalosaure('./megalosaure')
meg.build_ast()
#meg.z3(0x2c,  0x9b07e7ce91a8a7b5)
meg.transpile('./megalosaure.c', 0x2c)
