import struct
from binaryninja import *

tI = lambda e: InstructionTextToken(InstructionTextTokenType.InstructionToken, e)
tt = lambda e: InstructionTextToken(InstructionTextTokenType.TextToken, e)
tr = lambda e: InstructionTextToken(InstructionTextTokenType.RegisterToken, e)
ti = lambda e: InstructionTextToken(InstructionTextTokenType.IntegerToken, e, int(e, 16))
ta = lambda e: InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, e, int(e, 16))
ts = lambda e: InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, e)


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

    def __init__(self, opcode, operands, addr, opcodes) -> None:
        self.opcode = opcode
        self.operands = operands
        self.addr = addr
        self.name = opcodes[self.opcode] if self.opcode in opcodes else "invalid"
        self.size = 2 * (len(operands) + 1)


    @staticmethod
    def disassemble(data: bytes, addr: int, opcodes = opcodes, registers = registers) -> 'Instruction':
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
                value = stream.read_i16()
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

        return Instruction(opcode, operands, addr, opcodes)


    def to_tokens(self) -> List[InstructionTextToken]:
        tokens = [tI(self.name)]

        for op in self.operands:
            tokens.append(tt(" "))
            if isinstance(op, Register):
                tokens.append(tr(op.name))
            elif isinstance(op, Mem):
                tokens.append(tr(op.name))
            elif isinstance(op, Imm):
                if "rel" in self.name or self.name == "call_imm":
                    tokens.append(ta(str(hex(self.jmp_dest()))))
                else:
                    tokens.append(ti(str(op.value)))
                    tokens.append(tt(" ("))
                    tokens.append(ti(str(hex(op.raw))))
                    tokens.append(tt(")"))

        return tokens

    def info(self) -> InstructionInfo:
        info = InstructionInfo()
        info.length = self.size

        if "exit" in self.name or "stop" in self.name or self.name == "ret":
            info.add_branch(BranchType.FunctionReturn)

        return info



class Megalosaure(Architecture):
    name = "megalosaure"
    address_size = 2
    default_int_size = 4
    instr_aligment = 2
    max_instr_length = 12

    regs = {reg: RegisterInfo(reg, 4) for reg in registers}
    stack_pointer = "sp"

    def get_instruction_text(self, data, addr):
        instruction = Instruction.disassemble(data, addr)
        return instruction.to_tokens(), instruction.size

    def get_instruction_info(self, data, addr):
        instruction = Instruction.disassemble(data, addr)
        return instruction.info()

    def get_instruction_low_level_il(self, data, addr, il):
        pass


Megalosaure.register()
arch = Architecture["megalosaure"]
