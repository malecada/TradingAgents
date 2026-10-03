"""Independent finite source review; no selected numerical module execution."""
import ast,copy,hashlib,json,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
manifest=load(HERE/'MANIFEST02.json')
for row in manifest['files']:
 b=(HERE/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'],row['path']
inv=load(HERE/'source_inventory02.json');rows={r['target']:r for r in inv['source_inventory']}
assert len(rows)==len(inv['source_inventory'])==195
assert sum(r['bytes'] for r in rows.values())==3263819
assert sum(k.startswith('tradingagents/') for k in rows)==147
assert sum(k.startswith('research/') for k in rows)==33
old=load(HERE.parent/'neural-cold-feature-handoff-proof-source-composition01-2026-10-03/source_inventory01.json')
oldrows={r['target']:r for r in old['source_inventory']}
assert set(oldrows)<=set(rows)
changed=[p for p,r in oldrows.items() if r['sha256']!=rows[p]['sha256']]
assert changed==['tradingagents/research/onchain_replication/compact_mcm.py']
assert rows[changed[0]]['sha256']=='6673fa484f37c0c3556c3d158035bb0c7f1db8f4a9f834ca50374c57c1e21b81'
git_count=0
for path,r in rows.items():
 b=(ROOT/r['snapshot']).read_bytes()
 assert sha(b)==r['sha256'] and len(b)==r['bytes']
 assert sha((ROOT/r['origin']).read_bytes())==r['sha256']
 if r.get('git_commit'):
  original=subprocess.run(['git','show',r['git_commit']+':'+r['git_path']],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
  assert sha(original)==r['sha256'];git_count+=1
 if path.endswith('.py'):ast.parse(b,filename=path)
# Declared source function interpretation does not import selected modules.
from source_symbols01 import Symbols
world=Symbols(rows)
required=world.module('tradingagents/research/onchain_replication/compact_native_producer.py').required_sources()
assert len(required)==47 and required<=rows.keys()
base='research/onchain-paper-replication-2026-09-24/full_sources/'
critical=['pair-component-reader-2026-10-01/reader.py','mcm-array-kernel-2026-10-01/kernel.py','sampler-leased-core-2026-10-01/core.py','graph-feature-boundary-2026-10-01/boundary.py','representation-denominator-2026-10-01/denominator.py','terminal-output-lifetime-2026-10-01/native_map.py','terminal-output-lifetime-2026-10-01/seal.py','terminal-output-lifetime-2026-10-01/outputs.py','representation-seal-2026-10-01/publication.py']
assert {base+p for p in critical}<=rows.keys()
# Exercise genuine selection hash loop for each independently deleted/corrupt pin.
path=HERE/'source-bodies/tradingagents/research/onchain_replication/compact_native_producer.py'
fn=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='selected')
loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.iter,ast.Call) and ast.unparse(n.iter.func)=='required_sources')
code=compile(ast.Module(body=[loop],type_ignores=[]),str(path),'exec')
def require(ok,msg):
 if not ok:raise ValueError(msg)
def selection(mapping):
 run=SimpleNamespace(admission=SimpleNamespace(root=HERE/'source-bodies',experiment={'source_files':mapping}))
 exec(code,{'run':run,'ROOT':HERE/'source-bodies','required_sources':lambda:required,'require':require,'file_hash':lambda p:sha(p.read_bytes())})
mapping={p:r['sha256'] for p,r in rows.items()};selection(mapping)
refused=0
for p in required:
 for missing in (True,False):
  corrupt=dict(mapping)
  if missing:del corrupt[p]
  else:corrupt[p]='0'*64
  try:selection(corrupt)
  except (ValueError,KeyError):refused+=1
  else:raise AssertionError(('selected source accepted corruption',p,missing))
from prepare_metadata_composed02 import source_mapping
assert source_mapping(HERE/'source-bodies',inv)==mapping
for mutation in ('removed_dynamic','changed_hash','extra_source'):
 bad=copy.deepcopy(inv)
 if mutation=='removed_dynamic':bad['source_inventory']=[r for r in bad['source_inventory'] if r['target']!=base+critical[0]]
 elif mutation=='changed_hash':bad['source_inventory'][0]['sha256']='0'*64
 else:bad['source_inventory'].append(dict(bad['source_inventory'][0],target='extra.py'))
 try:source_mapping(HERE/'source-bodies',bad)
 except ValueError:pass
 else:raise AssertionError(mutation)
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'status':'passed-source-only','manifest_bodies':len(manifest['files']),'source_bodies':len(rows),'logical_bytes':inv['logical_bytes'],'git_blobs_verified':git_count,'unchanged_old_sources':len(oldrows)-1,'added_dynamic_sources':len(rows)-len(oldrows),'actual_source_loop_refusals':refused,'inventory_mutations_refused':3,'numerical_imports':False},indent=2))
