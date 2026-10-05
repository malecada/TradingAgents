"""Exact correction and clock refusals only; never calls inventory()."""
import ast,hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
P=BASE/'real-eligible-population-inventory02-2026-10-05';OLD=BASE/'real-eligible-population-inventory01-2026-10-05'
def sha(b):return hashlib.sha256(b).hexdigest()
raw=(P/'MANIFEST02.json').read_bytes();assert sha(raw)=='989cd54aae59dd136f4ece741f280bc2dcf6fa5aead2afc10926025a3b2b6141'
for r in json.loads(raw)['files']:
 b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
before=(OLD/'inventory01.py').read_text();after=(P/'inventory02.py').read_text();delta=json.loads((P/'CHANGE01.json').read_text())
assert sha(before.encode())==delta['baseline']['sha256'] and sha(after.encode())==delta['candidate_sha256']=='931e9f6b605bcba9dda21ea2568dfd0ea1c7e943a1735456357435d9b4e35c70'
work=before;operations=[]
for e in delta['literal_edits']:
 assert work.count(e['old'])==1;i=work.index(e['old']);operations.append((i,e['old'],e['new']));work=work[:i]+e['new']+work[i+len(e['old']):]
assert len(operations)==5 and work==after
for i,old,new in reversed(operations):assert work[i:i+len(new)]==new;work=work[:i]+old+work[i+len(new):]
assert work==before
spec=importlib.util.spec_from_file_location('corrected_inventory',P/'inventory02.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert m.utc is m.F['utc']
for name,h in m.SOURCE_PINS.items():assert sha((ROOT/'tradingagents/research/onchain_replication'/name).read_bytes())==h
assert 'provenance.py' in m.SOURCE_PINS
# Verify extracted UTC's original definition without importing numerical dependencies.
source=ROOT/'tradingagents/research/onchain_replication/provenance.py'
node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='utc')
ns={'datetime':m.datetime,'timedelta':m.timedelta};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_provenance_utc','exec'),ns)
assert m.utc.__code__.co_code==ns['utc'].__code__.co_code and m.utc.__code__.co_consts==ns['utc'].__code__.co_consts
for v in ('2024-01-01T01:00:00+01:00','2024-01-01T00:00:00',None):
 try:m.utc(v)
 except ValueError:pass
 else:raise AssertionError('UTC contract weakened')
fold={'id':'mechanical','train_start':'2024-02-01T00:00:00Z','train_end':'2024-02-03T00:00:00Z','test_start':'2024-02-03T00:00:00Z','test_end':'2024-02-06T00:00:00Z'}
weeks=m.F['required_weeks'](SimpleNamespace(**fold),28)
graphs=[dict(start_utc=w,available_at=m.F['stamp'](m.utc(w)+m.timedelta(days=8)),graph_hash=str(i).zfill(64),manifest_path=str(i)) for i,w in enumerate(weeks)]
expected=m.graph_support(fold,graphs)
aliases=[dict(g,start_utc=g['start_utc'].replace('Z','+00:00')) for g in graphs]
assert m.graph_support(fold,aliases)==expected
try:m.graph_support(fold,graphs+[aliases[0]])
except ValueError:pass
else:raise AssertionError('equal UTC week duplicate accepted')
assert sha((OLD/'INVENTORY01.json').read_bytes())=='df36f171066934b5464ea104fd25ab80c75205f3af06cd4b52bf071b562c6161'
assert not {'numpy','torch','scipy','pandas'}&set(sys.modules)
print(json.dumps({'schema_version':1,'decision':'ACCEPTED_EXACT_CORRECTED_REPORTING_SOURCE_ONLY','candidate_sha256':sha(after.encode()),'manifest_sha256':sha(raw),'literal_edits':5,'exact_forward_and_inverse':True,'source_pins':m.SOURCE_PINS,'original_utc_code_equal':True,'strict_clock_refusals':3,'all_UTC_aliases_preserve_support':True,'ambiguous_UTC_alias_refused':True,'saved_inventory_unchanged':True,'inventory_function_called':False,'artifact_scope_rescanned':False,'numerical_imports':False},sort_keys=True,indent=2))
