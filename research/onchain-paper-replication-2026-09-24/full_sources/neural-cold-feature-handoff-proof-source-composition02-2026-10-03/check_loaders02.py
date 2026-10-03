"""Finite path-argument audit; no imports or execution of any loader."""
import ast,json
from pathlib import Path
from discover_source01 import HERE,ROOT
from source_symbols01 import Symbols
x=json.loads((HERE/'source_inventory02.json').read_bytes());rows={r['target']:r for r in x['source_inventory']};w=Symbols(rows);calls=[]
for target,row in rows.items():
 if not target.endswith('.py'):continue
 m=w.module(target);m.cache['root']=ROOT
 for n in ast.walk(m.tree):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('load','_load','module') and len(n.args)>=2:
   if n.func.id in ('load','_load'):
    declared=next((f for f in m.tree.body if isinstance(f,ast.FunctionDef) and f.name==n.func.id),None)
    if declared is None or not any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='spec_from_file_location' for c in ast.walk(declared)):continue
   try:path=m.evaluate(n.args[1]);name=str(Path(path).relative_to(ROOT))
   except (ValueError,KeyError,AttributeError,TypeError) as e:raise ValueError('unresolved selected path caller: '+target+':'+str(n.lineno)) from e
   if name not in rows:raise ValueError('loader target outside inventory: '+name)
   calls.append({'source':target,'line':n.lineno,'target':name})
# Remaining nonliteral spec sites have precise disjoint meanings, not fallback.
mcm=w.module('tradingagents/research/onchain_replication/compact_mcm.py').KERNEL
imported=w.module('tradingagents/research/onchain_replication/imported_mcm_identity.py').KERNEL
assert mcm in rows and imported in rows
reuse=rows['tradingagents/research/onchain_replication/native_reuse.py'];tree=ast.parse((ROOT/reuse['snapshot']).read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='selected')
assert any(isinstance(n,ast.If) and ast.unparse(n.test)=="route.get('native_backend') != BACKEND" and any(isinstance(a,ast.Return) and isinstance(a.value,ast.Constant) and a.value.value is False for a in n.body) for n in fn.body)
result={'schema_version':1,'source_only':True,'finite_path_callers':calls,'generic_load_functions_all_callers_resolved':True,'MCM_path_dispatch':{'scientific':mcm,'imported':imported,'scientific_proof_selects':'scientific'},'legacy_native_reuse':{'selected':False,'reason':'different explicit native_backend returns False before api; schema2 compatibility is not broadened','legacy_api_not_admitted_by_this_closure':True}}
print(json.dumps(result,indent=2))
