from enum import Enum


class Type(Enum):
    Identifier = "identifier"
    Number = "number"
    Syntax = "syntax"
    String = "string"
    EOL = "eol"


class Token:
    def __init__(self, value, flag):
        self.value = value
        self.flag = flag

    def __eq__(self, other):
        return self.value == other.value and self.flag == other.flag

    def __repr__(self):
        return f"Token({self.value}, {self.flag})"