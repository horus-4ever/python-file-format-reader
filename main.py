from lexer import Lexer
from parser import Parser
from codegen import generate_code
import sys, os


FORMAT = sys.argv[1]
filename = os.path.basename(FORMAT)
with open(FORMAT) as doc:
    CODE = doc.read()

lexer = Lexer(CODE)
tokens = lexer.tokenize()
# print(tokens)

parser = Parser(tokens)
ast = parser.parse()
# print(ast)

with open(f"out/{filename}.py", "w") as doc:
    doc.write(generate_code(ast))