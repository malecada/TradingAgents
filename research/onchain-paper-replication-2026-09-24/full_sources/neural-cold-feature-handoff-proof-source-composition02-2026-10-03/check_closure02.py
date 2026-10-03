"""Finite static import and actual declared-source closure readback."""
import ast,json,sys
from pathlib import Path
from discover_source01 import HERE,ROOT,sha
from source_symbols01 import Symbols
import prepare_metadata_composed02 as metadata
inv=json.loads((HERE/'source_inventory02.json').read_bytes());rows={r['target']:r for r in inv['source_inventory']};sources=metadata.source_mapping(HERE/'source-bodies',inv)
assert len(rows)==195 and len(sources)==195
missing=[];edges=0
for target,row in rows.items():
 raw=(ROOT/row['snapshot']).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'] and raw==(ROOT/row['origin']).read_bytes()
 if not target.endswith('.py'):continue
 tree=ast.parse(raw);compile(tree,target,'exec')
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.ImportFrom) and n.level:
   base=Path(target).parent
   for _ in range(n.level-1):base=base.parent
   names=[str(base.joinpath(*s.split('.'))) for s in ([n.module] if n.module else [a.name for a in n.names])]
  elif isinstance(n,ast.ImportFrom) and n.module and n.module.startswith('tradingagents'):
   base=n.module.replace('.','/');names=[base]
   if base+'/__init__.py' in rows:names += [base+'/'+a.name for a in n.names if base+'/'+a.name+'.py' in rows]
  elif isinstance(n,ast.Import):names=[a.name.replace('.','/') for a in n.names if a.name.startswith('tradingagents')]
  for name in names:
   edges+=1
   if not any(k in rows for k in (name+'.py',name+'/__init__.py')):missing.append((target,n.lineno,name))
assert not missing,repr(missing)
w=Symbols(rows);required=w.module('tradingagents/research/onchain_replication/compact_native_producer.py').required_sources();assert len(required)==47 and required<=set(rows)
# Each source proxy used to interpret actual SOURCES is itself an inventoried,
# hash-read body. Native map/SOURCES is NOT imported or replaced by a handlist.
assert set(w.modules)<=set(rows)
selected=(HERE/'source-bodies/tradingagents/research/onchain_replication/compact_mcm.py').read_text();assert 'resource_refusal' not in selected
assert not any(k.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for k in sys.modules)
print(json.dumps({'sources':195,'package':147,'external':33,'local_import_edges':edges,'missing_local_imports':missing,'actual_required_sources':len(required),'SOURCES_declaration_modules':sorted(w.modules),'numeric_imports':False,'capsule':False,'authority':False},indent=2))
