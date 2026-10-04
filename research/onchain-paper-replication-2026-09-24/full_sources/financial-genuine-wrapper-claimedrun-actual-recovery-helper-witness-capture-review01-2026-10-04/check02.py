import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;root=B/'financial-genuine-wrapper-root-claimedrun-recovery-helper-witness-capture01-2026-10-04';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v):
 global checks
 assert v
 checks+=1
u=json.loads((root/'union-manifest.json').read_bytes());logical=sum(r.get('bytes',0) for r in u['members']);ok(logical==11725363 and logical<=64*1024**2);ok(max(r.get('bytes',0) for r in u['members'])<=4*1024**2)
preserved=[]
for r in u['members']:
 if r['kind']=='file' and any(x in r['path'].lower() for x in ['partial','failed','failure','.err','late-extra']):
  b=(root/'union-bytes01'/r['path']).read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256']);preserved.append(r)
for directory in ['financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-review01-2026-10-04','financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-preparation01-2026-10-04']:
 p=B/directory;m=json.loads((p/'MANIFEST01.json').read_bytes())
 for n in ['READBACK01.json','capture_helpers01.py','FEASIBILITY01.json']:
  if (p/n).exists():
   r=next(r for r in m['members'] if r['path']==n);b=(p/n).read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256'])
result={'checks':checks,'whole_original_plus_mapping_logical_bytes':logical,'archive_total_bytes':sum((root/(scope+'.tar.gz')).stat().st_size for scope in ['flat-preparation','flat-review','pax-preparation','pax-review','tooling-preparation','tooling-review']),'preserved_failure_named_bodies':preserved,'qualification':'This named subset is an index only. Complete originals, including all other rows, were authenticated in check01. No historical failure is reclassified; no partial body is treated as a valid successful archive.'}
with (H/'PRESERVED_HISTORY02.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'failure_named_rows':len(preserved),'logical':logical}))
