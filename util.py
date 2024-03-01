import json
from enum import Enum

INT_MIN = -2147483648
INT_MAX = 2147483647

USER_REGISTERS = ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12", "r14", "r15"]


class Register(str, Enum):
    R0 = "r0"
    R1 = "r1"
    R2 = "r2"
    R3 = "r3"
    R4 = "r4"
    R5 = "r5"
    R6 = "r6"
    R7 = "r7"
    R8 = "r8"
    R9 = "r9"
    R10 = "r10"
    R11 = "r11"
    R12 = "r12"
    R13 = "r13"
    R14 = "r14"
    R15 = "r15"

    def __str__(self):
        return self.name


SP = Register.R15
DR = Register.R14
IP = Register.R13


def is_register(arg: str) -> bool:
    return arg in USER_REGISTERS


class RegisterEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Register):
            return "R" + str(obj.value)
        return super().default(obj)


def convert_to_register(arg):
    if arg and isinstance(arg, str) and arg.startswith("R"):
        return Register[arg]
    return arg


class InvalidSymbolsError(Exception):
    def __init__(self, got, expected):
        self.token = got
        self.expected = expected

    def __str__(self):
        return f"Got invalid symbols or tokens: {self.token}, expected: {self.expected}"
