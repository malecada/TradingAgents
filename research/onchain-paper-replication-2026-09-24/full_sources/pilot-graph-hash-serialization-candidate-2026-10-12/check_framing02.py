import ast,dataclasses,hashlib,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parent;ns=runpy.run_path(str(P/'check_serialization01.py'))
for n,width in ((0,4),(1,1025),(1025,4)):
 g=ns['graph'](n,width);record={f.name:(v.tolist() if isinstance(v:=getattr(g,f.name),ns['np'].ndarray) else v) for f in dataclasses.fields(g)}
 expected=hashlib.sha256(ns['canonical'](record)).hexdigest()
 assert ns['base']['graph_hash'](g)==ns['candidate']['graph_hash'](g)==expected
base=ast.parse((P/'BASELINE_neighborhoods.py').read_text());candidate=ast.parse((P/'neighborhoods.py').read_text())
a={x.name:ast.dump(x) for x in base.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};b={x.name:ast.dump(x) for x in candidate.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
assert all(a[k]==b[k] for k in a if k!='graph_hash')
assert b['graph_hash'].count("id='validate_graph'")==1
print(json.dumps({'status':'PASS','canonical_graph_framing':3,'all_other_functions_unchanged':True,'validate_graph_call_retained':True}))
