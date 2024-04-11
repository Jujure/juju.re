#!/usr/bin/env python3

import struct
from typing import Optional
import copy

regs = {
    0x42048: "DT_RELA",
    0x42068: "DT_RELASZ",
    0x42088: "r0",
    0x420a0: "r1",
    0x420b8: "r2",
    0x420d0: "r3",
    0x420e8: "r4",
    0x42100: "r5",
    0x42118: "r6",
    0x42130: "r7",
    0x42148: "r8",
    0x42160: "r9",
    0x42178: "r10",
    0x42190: "r11",
    0x421a8: "r12",
    0x421c0: "r13",
    0x421d8: "r14",
    0x421f0: "r15",

    0x42090: "r0.size",
    0x420a8: "r1.size",
    0x420c0: "r2.size",
    0x420d8: "r3.size",
    0x420f0: "r4.size",
    0x42108: "r5.size",
    0x42120: "r6.size",
    0x42138: "r7.size",
    0x42150: "r8.size",
    0x42168: "r9.size",
    0x42180: "r10.size",
    0x42198: "r11.size",
    0x421b0: "r12.size",
    0x421c8: "r13.size",
    0x421e0: "r14.size",
    0x421f8: "r15.size"
}

class Stream:
    i: int
    buf: bytes

    def __init__(self, buf) -> None:
        self.pos = 0
        self.buf = buf

    def read_u8(self) -> Optional[int]:
        try:
            val = struct.unpack("<B", self.buf[self.pos:self.pos + 1])
            self.pos += 1
            return val[0]
        except:
            return None

    def read_u16(self) -> Optional[int]:
        try:
            val = struct.unpack("<H", self.buf[self.pos:self.pos + 2])
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

    def read_u64(self) -> Optional[int]:
        try:
            val = struct.unpack("<Q", self.buf[self.pos:self.pos + 8])
            self.pos += 8
            return val[0]
        except:
            return None

    def is_done(self):
        return self.pos >= len(self.buf)


class RelaEnt:
    def __init__(self, stream):
        self.addr = stream.read_u64()
        self.type = stream.read_u32()
        self.symbol = stream.read_u32()
        self.addend = stream.read_u64()

class Rela:
    def __init__(self, rela_addr, rela_size, elf):
        self.rela_addr = rela_addr
        self.rela_size = rela_size
        self.elf = elf

    def pop(self):
        if self.rela_size <= 0:
            return None
        stream = Stream(self.elf.get_data(self.rela_addr, 0x18))
        entry = RelaEnt(stream)
        entry.offset = self.rela_addr
        self.rela_addr += 0x18
        self.rela_size -= 0x18
        return entry

    def peek(self):
        if self.rela_size <= 0:
            return None
        stream = Stream(self.elf.get_data(self.rela_addr, 0x18))
        entry = RelaEnt(stream)
        entry.offset = self.rela_addr
        return entry

class Symbol:
    def __init__(self, data):
        stream = Stream(data)
        self.name = stream.read_u16()
        self.info = stream.read_u8()
        self.other = stream.read_u8()
        self.shndx = stream.read_u32()
        self.value = stream.read_u64()
        self.size = stream.read_u64()

class Elf:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self._data = bytearray(f.read())

        self.dynt_rela = 0x42048
        self.dynt_relasz = 0x42068
        self.symtab = 0x42080
        self.breakpoints = {}

    def dump(self, path):
        with open(path, 'wb') as f:
            f.write(self._data)

    def get_data(self, addr, size):
        addr -= 0x40000
        return self._data[addr:addr + size]

    def set_data(self, addr, data):
        addr -= 0x40000
        self._data[addr:addr + len(data)] = data

    def set_flag(self, flag):
        addr = 0x5a100
        addr -= 0x40000
        self._data[addr:addr + len(flag)] = flag

    def get_rela(self):
        rela_addr = Stream(self.get_data(self.dynt_rela, 8)).read_u64()
        rela_size = Stream(self.get_data(self.dynt_relasz, 8)).read_u64()
        return Rela(rela_addr, rela_size, self)

    def get_symbol(self, i):
        sym_data = self.get_data(self.symtab + 0x18 * i, 0x18)
        return Symbol(sym_data)

    def set_breakpoint(self, addr, func, res):
        self.breakpoints[addr] = (func, res)

    def apply_relocs(self):
        rela = self.get_rela()
        patched_code = False
        asm = ""
        while True:
            entry = rela.pop()
            if not entry:
                break
            symbol = self.get_symbol(entry.symbol)
            dst_name = regs[entry.addr] if entry.addr in regs else f'[{hex(entry.addr)}]'
            line = f'{hex(entry.offset)}: '
            if entry.type == 1:
                data_int = (symbol.value + entry.addend) % 2**64
                data = struct.pack('<Q', data_int)
                line += f'add {dst_name}, r{entry.symbol}, ${hex(entry.addend)}'

            elif entry.type == 5:
                data = self.get_data(symbol.value + entry.addend, symbol.size)
                line += f'mov {dst_name}, [r{entry.symbol}].{symbol.size}'
                if entry.addend != 0:
                    raise

            elif entry.type == 8:
                data_int = entry.addend
                data = struct.pack('<Q', data_int)
                src_name = f'&{regs[entry.addend]}' if entry.addend in regs else f'${hex(entry.addend)}'
                line += f'mov {dst_name}, {src_name}'

            else:
                print(hex(entry.type))
                raise

            line += ' ' * (50 - len(line)) + f'# {bytes(data).hex()}'
            if entry.addr > entry.offset and entry.addr < 0x49000:
                next_instr = rela.peek()
                if not (entry.addr >= next_instr.offset and entry.addr < next_instr.offset + 0x18):
                    line += "  PATCHING FAR"
                else:
                    line += '  PATCHING CODE'
            asm += line + '\n'

            if entry.offset in self.breakpoints:
                stop = not self.breakpoints[entry.offset][0](self, entry, line, data, self.breakpoints[entry.offset][1])
                if stop:
                    return asm, stop

            self.set_data(entry.addr, data)
            if entry.addr >= 0x41000 and entry.addr < 0x41083:
                patched_code = True

        asm += '#End of block\n'
        return asm, patched_code


def fetch_r4(elf, entry, asm, data, res):
    if data != b'\x00':
        res.append(True)
        return True
    else:
        return False

def check(elf, entry, asm, data):
    if data == b'\x00':
        print(asm)


def main():
    elf = Elf('./svartalfheim')
    asm = ""
    n = 0
    while n <= 3:
        #print('---')
        step_asm, patched_code = elf.apply_relocs()
        if patched_code:
            asm += '# NATIVE CODE LOADING:\n'
            n += 1
            elf.dump(f'./dumps/pydumped{n}')
        asm += step_asm
    flag = bytearray(0x46)
    for i in range(0x46):
        for b in range(0x30, 127):
            n = 4
            flag[i] = b
            before_read = copy.deepcopy(elf)
            res = []
            before_read.set_breakpoint(0x47000, fetch_r4, res)
            before_read.set_breakpoint(0x47270, fetch_r4, res)
            before_read.set_flag(flag)
            while n < 7:
                step_asm, patched_code = before_read.apply_relocs()
                if patched_code:
                    asm += '# NATIVE CODE LOADING:\n'
                    n += 1
                    elf.dump(f'./dumps/pydumped{n}')
                    break
                asm += step_asm
            if len(res) == 2 * (i + 1):
                print(flag)
                break


        #print(asm)

if __name__ == "__main__":
    main()
