from token import Token, Type
import ast


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    @property
    def current(self):
        return self.tokens[self.position]

    def eof(self):
        return self.position >= len(self.tokens)

    def next(self):
        self.position += 1

    def next_assert(self, flag, value=None):
        current = self.current
        if current.flag == flag and value is None:
            self.next()
        elif current.flag == flag and current.value == value:
            self.next()
        else:
            raise AssertionError(f"current={self.current} ; flag={flag} ; value={value}")
        return current

    def skip_lines(self):
        while not self.eof() and self.current.flag == Type.EOL:
            self.next()

    def parse(self):
        readers = []
        tables = []
        bitflags = []
        code = None
        self.skip_lines()
        while not self.eof():
            if self.current == Token("map", Type.Identifier):
                tables.append(self.parse_map())
            elif self.current == Token("reader", Type.Identifier):
                readers.append(self.parse_reader())
            elif self.current == Token("bitflag", Type.Identifier):
                bitflags.append(self.parse_bitflag())
            elif self.current == Token("main", Type.Identifier):
                code = self.parse_code()
            else:
                raise Exception(f"Invalid token {self.current}")
            self.skip_lines()
        return ast.Root(readers, tables, bitflags, code)

    def parse_reader(self):
        self.next_assert(Type.Identifier, "reader")
        reader_name = self.next_assert(Type.Identifier).value
        self.next_assert(Type.Identifier, "where")
        self.next_assert(Type.EOL)
        rules = []
        while self.current != Token("end", Type.Identifier):
            self.next_assert(Type.Syntax, "|")
            rules.append(self.parse_rule())
            self.next_assert(Type.EOL)
        self.next_assert(Type.Identifier, "end")
        return ast.Reader(reader_name, rules)

    def parse_rule(self):
        rule_name = self.next_assert(Type.Identifier).value
        self.next_assert(Type.Syntax, ":")
        nb_to_read = self.next_assert(Type.Number).value
        if self.current == Token("as", Type.Identifier):
            instruction = self.parse_as_rule()
        else:
            instruction = None
        return ast.Rule(rule_name, nb_to_read, instruction)

    def parse_map(self):
        self.next_assert(Type.Identifier, "map")
        table_name = self.next_assert(Type.Identifier).value
        self.next_assert(Type.Identifier, "where")
        self.next_assert(Type.EOL)
        table = {}
        while self.current != Token("end", Type.Identifier):
            self.next_assert(Type.Syntax, "|")
            table.update(self.parse_table_entry())
            self.next_assert(Type.EOL)
        self.next_assert(Type.Identifier, "end")
        return ast.Map(table_name, table)

    def parse_table_entry(self):
        key = self.next_assert(Type.Number).value
        self.next_assert(Type.Syntax, ">")
        value = self.current.value
        self.next()
        return {key: value}

    def parse_bitflag(self):
        self.next_assert(Type.Identifier, "bitflag")
        table_name = self.next_assert(Type.Identifier).value
        self.next_assert(Type.Identifier, "where")
        self.next_assert(Type.EOL)
        rows = []
        while self.current != Token("end", Type.Identifier):
            self.next_assert(Type.Syntax, "|")
            rows.append(self.parse_biflag_row())
            self.next_assert(Type.EOL)
        self.next_assert(Type.Identifier, "end")
        return ast.Bitflag(table_name, rows)

    def parse_biflag_row(self):
        key = self.next_assert(Type.Number).value
        self.next_assert(Type.Syntax, ">")
        value = self.next_assert(Type.Identifier).value
        return (key, value)

    def parse_as_rule(self):
        self.next_assert(Type.Identifier, "as")
        name = self.next_assert(Type.Identifier).value
        return ast.READ_AS(name)

    def parse_code(self):
        self.next_assert(Type.Identifier, "main")
        self.next_assert(Type.Syntax, "{")
        instructions = []
        while self.current != Token("}", Type.Syntax):
            self.skip_lines()
            instructions.append(self.parse_instruction())
            self.next_assert(Type.EOL)
        self.next_assert(Type.Syntax, "}")
        return instructions

    def parse_instruction(self):
        name = self.next_assert(Type.Identifier).value
        if name == "read":
            return self._parse_READ()
        elif name == "goto":
            return self._parse_GOTO()
        else:
            raise ValueError(f"Invalid instruciton {name}.")

    def _parse_READ(self):
        reader_name = self.next_assert(Type.Identifier).value
        return ast.READ(reader_name)
    
    def _parse_GOTO(self):
        cls_name = self.next_assert(Type.Identifier).value
        self.next_assert(Type.Syntax, ".")
        attr_name = self.next_assert(Type.Identifier).value
        return ast.GOTO(cls_name, attr_name)