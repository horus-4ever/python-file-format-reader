from ast import *


BASE_CODE = """
import sys

FILE = sys.argv[1]
reader = open(FILE, "rb")


def _runtime_lookup(name):
    try:
        return _func_wrapper(getattr(MAPS, name).__getitem__)
    except AttributeError:
        pass
    try:
        return _func_wrapper(getattr(BITFLAGS, name).get)
    except AttributeError:
        print(f"No such map or bitflag {name}")
        sys.exit(0)


def _func_wrapper(func):
    def inner_wrapper(self, *args, **kwargs):
        return func(*args, **kwargs)
    return inner_wrapper

_int = _func_wrapper(int)
_hex = _func_wrapper(hex)
_bin = _func_wrapper(bin)


def _to_bytes(rule, value):
    return int.to_bytes(value, rule.to_read, "little")

def _str(rule, value):
    return _to_bytes(rule, value).decode("ascii")


class Symbol:
    __symbols__ = {}
    def __new__(cls, value):
        if value in cls.__symbols__:
            return cls.__symbols__[value]
        obj = object.__new__(cls)
        cls.__symbols__[value] = obj
        return obj
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value
    def __eq__(self, other):
        return self is other


class Flag:
    def __init__(self, number, *symbols):
        self.number = number
        self.symbols = symbols
    def __or__(self, other):
        return Flag(self.number | other.number, *self.symbols, *other.symbols)
    def __int__(self):
        return self.number
    def __repr__(self):
        return " | ".join(str(symbol) for symbol in self.symbols)


class Bitflag:
    def __init_subclass__(cls):
        cls.__members__ = [item[0] for item in vars(cls).items() if isinstance(item[1], Flag)]
    @classmethod
    def get(cls, value):
        result = None
        for member in cls.__members__:
            flag = getattr(cls, member)
            if int(flag) & value != 0:
                result = flag if result is None else result | flag
        return result


class Attribute:
    def __init__(self, value, changed_value):
        self.value = value
        self.changed_value = changed_value

    def __int__(self):
        return self.value

    def __repr__(self):
        return str(self.changed_value)


class ReaderRule:
    def __init__(self, to_read, as_rule):
        self.to_read = to_read
        self.as_rule = as_rule
        self.name = None

    def __get__(self, instance, owner):
        if instance is not None:
            value = getattr(instance, self.name)
            return Attribute(value, self.as_rule(self, value))
        else:
            return self

    def __set_name__(self, cls, name):
        self.name = f"_{name}"


class Reader:
    def __init_subclass__(cls):
        cls.__members__ = [item[0] for item in vars(cls).items() if isinstance(item[1], ReaderRule)]

    @classmethod
    def read(cls, stream):
        reader = cls()
        for name in cls.__members__:
            new_name = f"_{name}"
            to_read = getattr(cls, name).to_read
            value = int.from_bytes(stream.read(to_read), "little")
            setattr(reader, new_name, value)
        return reader
"""


BASE_TABLES_CODE = "\n\nclass MAPS:"
TABLE_ENTRY_CODE = """
    {name} = {table}"""

BASE_BITFLAGS_CODE = "\n\nclass BITFLAGS:"
BITFLAG_CODE = """
    class {name}(Bitflag):"""
BITFLAG_ENTRY_CODE = """
      {name} = Flag({number}, "{name}")"""

BASE_READER_CODE = "\n\nclass READERS:"
READER_CODE = """
    class {name}(Reader):"""
READER_ENTRY_CODE = """
        {name} = ReaderRule({to_read}, {as_rule})"""

READ_INSTRUCTION = """
{reader_name} = getattr(READERS, '{reader_name}').read(reader)"""
GOTO_INSTRUCTION = """
reader.seek(int({reader_name}.{attr_name}), 0)"""

def generate_code(ast):
    code = BASE_CODE
    if ast.tables:
        table_code = BASE_TABLES_CODE
        for table in ast.tables:
            table_code += TABLE_ENTRY_CODE.format(name=table.name, table=table.table)
        code += table_code
    if ast.bitflags:
        bitflags_code = BASE_BITFLAGS_CODE
        for bitflag in ast.bitflags:
            bitflags_code += BITFLAG_CODE.format(name=bitflag.name)
            for number, name in bitflag.rows:
                bitflags_code += BITFLAG_ENTRY_CODE.format(name=name, number=number)
        code += bitflags_code
    if ast.readers:
        readers_code = BASE_READER_CODE
        for reader in ast.readers:
            readers_code += READER_CODE.format(name=reader.name)
            for rule in reader.rules:
                name = rule.name
                to_read = rule.nb_to_read
                as_rule = generate_as_rule(rule.as_rule)
                readers_code += READER_ENTRY_CODE.format(name=name, to_read=to_read, as_rule=as_rule)
        code += readers_code
    code += "\n\n"
    if ast.code is not None:
        code += generate_read_instructions(ast.code)
    return code

def generate_as_rule(as_rule):
    if as_rule is None:
        return "_hex"
    name = as_rule.as_name
    if name in ("int", "hex", "bin", "str"):
        return f"_{name}"
    elif name == "bytes":
        return "_to_bytes"
    else:
        return f"_runtime_lookup('{name}')"

def generate_read_instructions(instructions):
    code = ""
    for instruction in instructions:
        if isinstance(instruction, READ):
            code += generate_READ(instruction)
        elif isinstance(instruction, GOTO):
            code += generate_GOTO(instruction)
    return code

def generate_READ(instruction):
    reader_name = instruction.reader_name
    return READ_INSTRUCTION.format(reader_name=reader_name)

def generate_GOTO(instruction):
    reader_name = instruction.cls_name
    attr_name = instruction.attr_name
    return GOTO_INSTRUCTION.format(reader_name=reader_name, attr_name=attr_name)