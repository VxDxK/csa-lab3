#!/usr/bin/env python3

from __future__ import annotations

import json

import self

from isa import *
from util import *
import logging
import sys
from ctypes import c_int32


class ALU:
    negative: bool = False
    zero: bool = False
    overflow: bool = False

    OPCODES_IMPLS = {
        Opcode.ADD: lambda a, b: a + b,
        Opcode.INC: lambda a, b: a + 1,
        Opcode.DEC: lambda a, b: a - 1,
        Opcode.DIV: lambda a, b: a // b,
        Opcode.MOD: lambda a, b: a % b,
    }

    def process(self, op: Opcode, left: int, right: int) -> int:
        ans: int = 0
        if op == Opcode.CMP:
            calc = left - right
            if calc > INT_MAX or calc < INT_MIN:
                calc = c_int32(ans).value
                self.overflow = True
            else:
                self.overflow = False
            self.negative = calc < 0
            self.zero = calc == 0
            ans = left
        elif op in self.OPCODES_IMPLS:
            ans = self.OPCODES_IMPLS[op](left, right)
            if ans > INT_MAX or ans < INT_MIN:
                ans = c_int32(ans).value
                self.overflow = True
            else:
                self.overflow = False

            self.negative = ans < 0
            self.zero = ans == 0
        else:
            raise ValueError(f"Invalid opcode: {op}")
        return ans


class IO:
    def __init__(self, charset: list[int]):
        self.charset: list[int] = charset
        self.output: str = ""

    def read_byte(self) -> int:
        if len(self.charset) == 0:
            raise EOFError("No charset")

        value = self.charset[0]
        self.charset = self.charset[1:]

        return value

    def write_byte(self, value: int):
        self.output += chr(value)


MEM_SIZE = 2 ** 9


class DataPath:
    alu: ALU = ALU()
    data_mem: list[int] = [0 for _ in range(MEM_SIZE)]
    code_mem: list[Instruction] = [Instruction(Opcode.NOP) for _ in range(MEM_SIZE)]

    def __init__(self, start: int, code: dict[int, Instruction], data: dict[int, int]):
        self.regs: dict[Register, int] = dict()
        for reg in range(0, 15):
            self.regs[Register(f"r{reg}")] = 0

        for k, v in data.items():
            self.data_mem[int(k)] = v
        for k, v in code.items():
            self.code_mem[int(k)] = v
        self.regs[IP] = start
        self.regs[SP] = MEM_SIZE - 1

    def latch_reg(self, reg: Register, value: int):
        if reg == Register.R0:
            raise ValueError("Cannot latch register R0")
        self.regs[reg] = value

    def getR0(self):
        return self.load_reg(Register.R0)

    def load_reg(self, reg: Register) -> int:
        return self.regs[reg]

    def get_zero_flag(self) -> bool:
        return self.alu.zero

    def negative(self) -> bool:
        return self.alu.negative

    def calc(self, opcode: Opcode, arg1: int, arg2: int) -> int:
        return self.alu.process(opcode, arg1, arg2)


class ControlUnit:
    tick_counter = 0

    def __init__(self, dp: DataPath, ports: [int, IO]):
        self.dataPath = dp
        self.ports = ports

    def tick(self):
        self.tick_counter += 1

    def get_ticks(self):
        return self.tick_counter

    def instruction_fetch(self) -> Instruction:
        addr: int = self.dataPath.regs[IP]
        instr: Instruction = self.dataPath.code_mem[addr]
        self.tick()
        return instr

    def decode_and_execute_control_flow_instruction(self, instr: Instruction) -> bool:
        opcode = instr.opcode
        if opcode is Opcode.HLT:
            raise StopIteration()

        if opcode is Opcode.JUMP:
            addr = int(instr.args[0])
            self.dataPath.latch_reg(IP, addr)
            self.tick()
            return True
        elif opcode is Opcode.JE:
            jmp_flag = self.dataPath.get_zero_flag() == 1
        elif opcode is Opcode.JG:
            jmp_flag = self.dataPath.negative() == 0
        else:
            return False

        if jmp_flag:
            addr = int(instr.args[0])
            self.dataPath.latch_reg(IP, addr)
        else:
            self.dataPath.latch_reg(IP, self.dataPath.regs[IP] + 1)
        self.tick()
        return True

    def bin_arithmetic(self, instr: Instruction):
        res: int = self.dataPath.calc(
            instr.opcode, self.dataPath.load_reg(Register(instr.args[0])),
            self.dataPath.load_reg(Register(instr.args[1])))
        self.dataPath.latch_reg(Register(instr.args[0]), res)
        self.tick()

    def un_arithmetic(self, instr: Instruction):
        res: int = self.dataPath.calc(instr.opcode, self.dataPath.load_reg(Register(instr.args[0])),
                                      self.dataPath.getR0())
        self.dataPath.latch_reg(Register(instr.args[0]), res)
        self.tick()

    def mov(self, instr: Instruction):
        if instr.args[1].isdigit():
            reg_from_data: int = int(instr.args[1])
        else:
            reg_from: Register = Register(instr.args[1])
            reg_from_data: int = self.dataPath.calc(Opcode.ADD, self.dataPath.regs[reg_from],
                                                    self.dataPath.getR0())
        self.tick()
        reg_to: Register = Register(instr.args[0])
        self.dataPath.latch_reg(reg_to, reg_from_data)
        self.tick()

    def ld(self, instr: Instruction):
        reg_to: Register = Register(instr.args[0])
        addr_reg: Register = Register(instr.args[1])
        addr_to_read: int = self.dataPath.calc(Opcode.ADD, self.dataPath.regs[addr_reg], self.dataPath.getR0())
        self.tick()
        data: int = self.dataPath.data_mem[addr_to_read]
        self.tick()
        self.dataPath.latch_reg(reg_to, data)
        self.tick()

    def st(self, instr: Instruction):
        data_reg: Register = Register(instr.args[1])
        data: int = self.dataPath.calc(Opcode.ADD, self.dataPath.regs[data_reg], self.dataPath.getR0())
        self.tick()
        addr_reg: Register = Register(instr.args[0])
        addr: int = self.dataPath.calc(Opcode.ADD, 0, self.dataPath.regs[addr_reg])
        self.tick()
        self.dataPath.data_mem[addr] = data
        self.tick()

    def out(self, instr: Instruction):
        io = self.ports[int(instr.args[0])]
        self.tick()
        reg_from = Register(instr.args[1])
        value: int = self.dataPath.calc(Opcode.ADD, self.dataPath.regs[reg_from], self.dataPath.getR0())
        self.tick()
        io.write_byte(value)
        self.tick()
        pass

    def inb(self, instr: Instruction):
        io = self.ports[int(instr.args[1])]
        reg_to = Register(instr.args[0])
        self.tick()
        self.tick()
        value = io.read_byte()
        self.tick()
        self.dataPath.latch_reg(reg_to, value)
        pass

    def decode_and_execute_instruction(self):
        instr: Instruction = self.instruction_fetch()

        if self.decode_and_execute_control_flow_instruction(instr):
            return

        if instr.opcode == Opcode.MOV:
            self.mov(instr)
        elif instr.opcode == Opcode.LD:
            self.ld(instr)
        elif instr.opcode == Opcode.ST:
            self.st(instr)
        elif instr.opcode in [Opcode.ADD, Opcode.DIV, Opcode.CMP, Opcode.MOD]:
            self.bin_arithmetic(instr)
        elif instr.opcode in [Opcode.INC, Opcode.DEC]:
            self.un_arithmetic(instr)
        elif instr.opcode == Opcode.OUT:
            self.out(instr)
        elif instr.opcode == Opcode.IN:
            self.inb(instr)
        elif instr.opcode == Opcode.NOP:
            pass
        else:
            raise Exception(f"NOT IMPLEMENTED: {instr.opcode}")

        self.dataPath.latch_reg(IP, self.dataPath.regs[IP] + 1)
        self.tick()

    def __repr__(self):
        regs_str = ""
        for reg, value in self.dataPath.regs.items():
            regs_str += f"({reg} = {value}) "
        state_repr = f"TICK {self.tick_counter} REGS: {regs_str.strip()}"
        instr = self.dataPath.code_mem[self.dataPath.regs[IP]]
        opcode = instr.opcode
        instr_repr = str(opcode)
        instr_repr += f" {instr.args}"
        return f"{state_repr} \t{instr_repr}"


def simulation(start: int, code: dict[int, Instruction], data: dict[int, int], input_tokens: list[int], limit: int):
    ports = {
        0: IO(input_tokens),
        1: IO([]),
        2: IO([])
    }
    dp = DataPath(start, code, data)
    cu = ControlUnit(dp, ports)

    logging.debug("%s", cu)
    instr_counter = 0
    try:
        while instr_counter < limit:
            cu.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", cu)
    except EOFError:
        logging.error("Input buffer is empty!")
    except StopIteration:
        pass

    for port, io in ports.items():
        if len(io.output) != 0:
            print(f"Port {port}: '{io.output}'")


def main(code_file, input_file=None):
    code_dict = json.load(open(code_file, "r", encoding="utf-8"))

    data_mem: dict[int, int] = code_dict["data_mem"]
    start: int = code_dict["start"]
    tmp_code_mem: dict[str, str] = code_dict["code_mem"]
    code_mem: dict[int, Instruction] = {}
    for k, v in tmp_code_mem.items():
        code_mem[int(k)] = Instruction(Opcode(v['opcode']), v['args'])

    if input_file is None:
        input_token = [0]
    else:
        with open(input_file, "r", encoding="utf-8") as file:
            input_token = [ord(i) for i in file.read()]
            input_token.append(0)

    simulation(
        start,
        code_mem,
        data_mem,
        input_token,
        100000,
    )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        raise Exception("Wrong arguments: machine.py <code_file> <optional_input_file>")
