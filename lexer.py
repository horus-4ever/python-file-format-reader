from token import Token, Type


class Lexer:
    def __init__(self, code):
        self.code = code
        self.position = 0

    @property
    def current(self):
        return self.code[self.position]

    def eof(self):
        return self.position >= len(self.code)

    def next(self):
        self.position += 1

    def tokenize(self):
        result = []
        while not self.eof():
            current = self.current
            if current == "\n":
                self.next()
                result.append(Token(current, Type.EOL))
            elif current.isspace():
                self.next()
                continue
            elif current.isdigit():
                result.append(Token(self.find_number(), Type.Number))
            elif current.isalnum():
                result.append(Token(self.find_identifier(), Type.Identifier))
            elif current == "\"":
                result.append(Token(self.find_string(), Type.String))
            else:
                self.next()
                result.append(Token(current, Type.Syntax))
        return result

    def find_number(self):
        result = ""
        is_hex = False
        hex_str = "abcdef"
        while not self.eof():
            if self.current.isdigit():
                result += self.current
            elif is_hex and self.current in hex_str:
                result += self.current
            elif self.current == "x" and not is_hex:
                result += self.current
                is_hex = True
            else:
                break
            self.next()
        return int(result, 16) if is_hex else int(result)

    def find_identifier(self):
        result = ""
        while not self.eof() and self.current.isalnum() or self.current == "_":
            result += self.current
            self.next()
        return result

    def find_string(self):
        result = ""
        self.next()
        while not self.eof() and self.current != "\"":
            result += self.current
            self.next()
        self.next()
        return result