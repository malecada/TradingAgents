"""Independent actual-source scalar allowance calculation; no array imports."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
CAP=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/original-import-native-successor-preparation03-2026-10-03/capsule02'
source=CAP/'tradingagents/research/onchain_replication/array_neighborhoods.py'
tree=ast.parse(source.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ArrayNeighborhoodIndex')
init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
statement=next(n for n in init.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='buffer_allowance' for t in n.targets))
for n in (2,3):
 value=eval(compile(ast.Expression(statement.value),str(source),'eval'),{},dict(n=n,e=n,node_width=32,edge_width=16,edge_chunk=65536))
 assert value>1048576
 print(n,'nodes/edges:',value,'B > registered 1048576 B; deterministic constructor refusal')
