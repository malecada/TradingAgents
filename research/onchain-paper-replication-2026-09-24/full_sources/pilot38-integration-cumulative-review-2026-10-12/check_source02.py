"""Final exact installed-source join; no project imports or empirical work."""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
D=F/'pilot-efficiency-integration-2026-10-12'
sha=lambda b:hashlib.sha256(b).hexdigest()
original=json.loads((P/'SOURCE_CHECK01.json').read_text())
root=json.loads((D/'SOURCE02.json').read_text())
assert len(root['changes'])==len(original['entries'])==6
rows=[]
for item in root['changes']:
 previous=next(x for x in original['entries'] if x['path']==item['path'])
 current=(R/item['path']).read_bytes(); candidate=(R/item['candidate']).read_bytes()
 assert current==candidate and sha(current)==item['after_sha256']==previous['candidate_sha256']
 assert len(current)==item['bytes'] and item['before_sha256']==previous['original36_sha256']
 rows.append({'path':item['path'],'sha256':sha(current),'bytes':len(current)})
old_path=F/'pilot38-entry-policy-correction-2026-10-12/ORIGINAL_compact_mcm.py'
def function(path,name):
 return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
before=function(old_path,'_produce_locked');after=function(R/'tradingagents/research/onchain_replication/compact_mcm.py','_produce_locked')
assert ast.dump(before)==ast.dump(after)
assert any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr=='poisoned' for t in n.targets) and isinstance(n.value,ast.Constant) and n.value.value is True for n in ast.walk(before))
test=R/'tests/research/onchain_replication/test_compact_mcm.py'
now=test.read_bytes();new=b"assert list(owner.stages) == ['dictionary'] and owner.poisoned"
old=b"assert list(owner.stages) == ['dictionary'] and not owner.poisoned"
assert now.count(new)==1 and now.count(old)==0
rows.append({'path':str(test.relative_to(R)),'sha256':sha(now),'bytes':len(now),'inverse_single_assertion_sha256':sha(now.replace(new,old,1))})
evidence={}
for p in [D/'SOURCE02.json',D/'COMPACT_PREFLIGHT_TEST_CORRECTION01.diff',D/'FAILURE_ISOLATION01.json',D/'FAILURE_ISOLATION02.json']:
 b=p.read_bytes();evidence[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)}
out={'status':'PASS_EXACT_SIX_INSTALLED_BODIES_AND_UNCHANGED_FATAL_POISON_SOURCE','sources':rows,'evidence':evidence,'operational_deviation':root['operational_deviation'],'whole_suite_pass':False,'remaining_validation':'Original broad suite timed out with failures; obsolete preflight assertion corrected, second-pair isolation/final focused checks remain Root-owned.'}
(P/'SOURCE_SNAPSHOT02.json').write_text(json.dumps(out,indent=2)+'\n')
print(out['status'])
