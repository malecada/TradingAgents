import ast, hashlib, json, os, stat, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CAND=HERE.parent/'mcm-batched-owner-integration01-2026-10-09'
SRC=ROOT/'tradingagents/research/onchain_replication'
def extract(path,names,ns):
    tree=ast.parse(path.read_text())
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
ns={'json':json,'hashlib':hashlib,'META_LIMIT':8192}
extract(SRC/'score_batches.py',{'_signature','_json','_require'},ns)
io=types.SimpleNamespace(**{k:ns[k] for k in ('_signature','_json','_require')})
cs={'os':os,'stat':stat,'hashlib':hashlib,'io':io,'require':io._require}
extract(CAND/'compact_mcm_batched.py',{'_checkpoint_inventory'},cs)
root=HERE/'fixture';root.mkdir();(root/'retained.bin').write_bytes(b'checkpoint fixture only\n')
before=cs['_checkpoint_inventory'](root)
(root/'unexpected-directory').mkdir()
after=cs['_checkpoint_inventory'](root)
assert before==after,'defect no longer reproduced'
assert 'numpy' not in __import__('sys').modules
manifest=json.loads((CAND/'MANIFEST.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for name, pins in manifest['baseline_pins'].items():
    checks[name]={'baseline_matches_main':sha(SRC/name)==pins['baseline_sha256'],'inverse_matches_main':(CAND/('inverse-'+name)).read_bytes()==(SRC/name).read_bytes(),'candidate_pin_matches':sha(CAND/name)==pins['candidate_sha256']}
assert all(all(v.values()) for v in checks.values())
result={'status':'DEFECT_REPRODUCED','defect':'Unexpected checkpoint directory leaves recorded inventory unchanged','before':before,'after':after,'actual_entries':sorted(p.name for p in root.iterdir()),'source_sha256':sha(CAND/'compact_mcm_batched.py'),'candidate_manifest_sha256':sha(CAND/'MANIFEST.json'),'inverse_checks':checks,'affinity':sorted(os.sched_getaffinity(0)),'numerical_imports':False,'genuine_owner_executed':False}
(HERE/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
