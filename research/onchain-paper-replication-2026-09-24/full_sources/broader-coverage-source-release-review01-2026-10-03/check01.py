import pathlib,hashlib,json,ast,sys,importlib.util,tempfile,os
from unittest.mock import patch
R=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'neural-cold-feature-handoff-broader-coverage-source-release-preparation01-2026-10-03';D=pathlib.Path(__file__).parent
H=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((P/'MANIFEST01.json').read_bytes());assert H((P/'MANIFEST01.json').read_bytes())=='a69fdb1861180e6336663524c6e44b53ba4b77c0781b3d69c05ac9cadb9a4647'
for r in m['files']:b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
class Block:
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(P));import acquisition_preparation as a
actual=a.prepare(R);frozen=json.loads((P/'drafts02.json').read_bytes());assert actual==frozen
rows=actual['asset_years'];assert len(rows)==15 and sum(len(x['cells']) for x in rows)==5480
assert sum(x['scope']['objects'] for x in rows)==5480
assert sum(x['scope']['listed_complete_object_bytes'] for x in rows)==1964328974076
for row in rows:
 assert row['scope']['selected_column_bytes'] is None and row['experiment_identity'] is None and row['range_policy'] is None
 assert len(row['required_physical_leaves'])==(16 if row['asset_year'].startswith('BTC') else 9)
source=(P/'unchanged-source/range_source.py').read_text();tree=ast.parse(source)
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='range_policy');fn2=next(x for x in ast.parse((P/'range_policy_source.py').read_text()).body if isinstance(x,ast.FunctionDef))
assert ast.dump(fn)==ast.dump(fn2)
for r in json.loads((P/'source-pins01.json').read_bytes())['files']:
 b=(R/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
 if r['path'].startswith('tradingagents/'):assert b==(P/'unchanged-source'/pathlib.Path(r['path']).name).read_bytes()
assert "'If-Match': item['etag']" in source and "'retries': 0" in source
for v in [None,{}, {'approved':True,'budget':65}]:
 try:a.require_execution_release(v)
 except a.ReleaseUnavailable:pass
 else:raise AssertionError('release allowed')
with tempfile.TemporaryDirectory(dir=D) as tmp:
 root=pathlib.Path(tmp);(root/'x').write_bytes(b'x');ref={'path':'x','bytes':1,'sha256':H(b'x')};fatal=SystemExit('first');later=MemoryError('second');close=os.close;seen=[]
 def closing(fd):seen.append(fd);close(fd);raise later
 with patch.object(a.os,'read',side_effect=fatal),patch.object(a.os,'close',side_effect=closing):
  try:a.read_pinned(root,ref)
  except BaseException as e:assert e is fatal
  else:raise AssertionError('no fatal')
 assert len(seen)==len(set(seen))==2
out={'decision':'accepted_source_only','manifest_sha256':H((P/'MANIFEST01.json').read_bytes()),'members_verified':len(m['files']),'actual_prepare_equals_frozen':True,'years':15,'dates':5480,'objects':5480,'whole_object_bytes':1964328974076,'selected_bytes':None,'acquisition_performed':False,'release_always_refused':True,'fund350_vintage_still_missing':True,'source_policy_AST_and_complete_route_bytes_unchanged':True,'fatal_identity_close_once':True}
(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
