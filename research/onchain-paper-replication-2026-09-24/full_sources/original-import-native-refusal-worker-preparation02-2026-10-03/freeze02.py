"""One-time source-only local manifest; no admission or recovery claim."""
import hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3];OLD=D.parent/'original-import-native-refusal-worker-preparation01-2026-10-03'
def ref(p):
 raw=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert not (D/'MANIFEST02.json').exists(),'frozen preparation cannot be overwritten'
rows=json.loads((D/'source_inventory02.json').read_text())['source_inventory']
for row in rows:
 observed=ref(ROOT/row['origin']);assert observed['sha256']==row['sha256'] and observed['bytes']==row['bytes']
for entry in json.loads((OLD/'MANIFEST01.json').read_text())['files']:assert ref(ROOT/entry['path'])==entry
files=[ref(p) for p in sorted(D.iterdir()) if p.is_file()]
value={'status':'frozen-source-only-R1-correction-unreviewed-not-admitted','files':files,'file_count':len(files),'dependencies':[ref(OLD/n) for n in ('MANIFEST01.json','source_inventory01.json','REVIEW_WORKER_PREPARATION01.md')],'source_count':169,'package_count':144,'changed_source_targets':['fixture_tools/refusal_outer01.py'],'actual_jobs':0,'actual_claims':0,'numeric_imports':False}
(D/'MANIFEST02.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
for name in ('MANIFEST02.json','source_inventory02.json','install-delta02.json','refusal_outer01.py','REPORT02.md'):print(name,ref(D/name)['sha256'])
print('frozen files',len(files),'source bytes',sum(r['bytes'] for r in rows))
