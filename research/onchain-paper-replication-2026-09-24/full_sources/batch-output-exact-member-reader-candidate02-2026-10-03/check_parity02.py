import ast
from pathlib import Path
p=Path(__file__).resolve().parent
old=ast.parse((p/'baseline01.py').read_bytes());new=ast.parse((p/'exact_members02.py').read_bytes())
cls=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='LocalContent')
assert sum(isinstance(n,ast.FunctionDef) and n.name=='__delattr__' for n in cls.body)==1
cls.body=[n for n in cls.body if not(isinstance(n,ast.FunctionDef) and n.name=='__delattr__')]
assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
print('PASS complete module AST identical except new LocalContent.__delattr__; all reader formats, FD operations, cleanup and context behavior unchanged')
