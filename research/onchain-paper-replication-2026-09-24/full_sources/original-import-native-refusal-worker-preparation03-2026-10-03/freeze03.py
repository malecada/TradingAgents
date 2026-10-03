"""One-time frozen source manifest; no capsule/registration/execution authority."""
import hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3];OLD=D.parent/'original-import-native-refusal-worker-preparation02-2026-10-03';INVEST=D.parent/'original-import-native-refusal-resource-investigation-2026-10-03'
def ref(p):
 raw=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert not (D/'MANIFEST03.json').exists(),'immutable frozen successor'
rows=json.loads((D/'source_inventory03.json').read_text())['source_inventory']
for row in rows:
 observed=ref(ROOT/row['origin']);assert observed['sha256']==row['sha256'] and observed['bytes']==row['bytes']
for row in json.loads((OLD/'MANIFEST02.json').read_text())['files']:assert ref(ROOT/row['path'])==row
files=[ref(p) for p in sorted(D.iterdir()) if p.is_file()]
value={'schema_version':1,'status':'frozen-source-only-unreviewed-not-admitted','files':files,'file_count':len(files),'dependencies':[ref(OLD/'MANIFEST02.json'),ref(OLD/'source_inventory02.json'),ref(OLD/'REVIEW_WORKER_PREPARATION02.md'),ref(INVEST/'INVESTIGATION01.md')],'source_count':170,'package_count':144,'source_bytes':sum(r['bytes'] for r in rows),'actual_jobs':0,'actual_claims':0,'numeric_imports':False}
(D/'MANIFEST03.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
for name in ('MANIFEST03.json','source_inventory03.json','install-delta03.json','refusal_outer01.py','refusal_inventory03.py','templates01.py','REPORT03.md'):print(name,ref(D/name)['sha256'])
print('files',len(files),'source_bytes',value['source_bytes'])
