class AST:
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, vars(self))


class Root(AST):
    def __init__(self, readers, tables, bitflags, code):
        self.readers = readers
        self.tables = tables
        self.bitflags = bitflags
        self.code = code


class Reader(AST):
    def __init__(self, name, rules):
        self.name = name
        self.rules = rules


class Rule(AST):
    def __init__(self, name, nb_to_read, as_rule=None):
        self.name = name
        self.nb_to_read = nb_to_read
        self.as_rule = as_rule


class Map(AST):
    def __init__(self, name, table):
        self.name = name
        self.table = table


class Bitflag(AST):
    def __init__(self, name, rows):
        self.name = name
        self.rows = rows


class Instruction(AST):
    pass

class GOTO(Instruction):
    def __init__(self, cls_name, attr_name):
        self.cls_name = cls_name
        self.attr_name = attr_name

class READ(Instruction):
    def __init__(self, reader_name):
        self.reader_name = reader_name

class READ_AS(Instruction):
    def __init__(self, as_name):
        self.as_name = as_name