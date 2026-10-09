import hashlib,json,stat
from pathlib import Path
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=F/'real-data-pilot-outcome23-scope01-2026-10-09/SELECTION01.json';v=json.loads(s.read_text());r=json.loads((H/'RESULT01.json').read_text());assert v['files']==len(v['rows'])==140 and v['body_bytes']==sum(x['bytes'] for x in v['rows'])==4043990 and len(v['directories'])==35
paths=[x['path'] for x in v['rows']+v['directories']];assert len(paths)==len(set(paths));body_checked=[];opaque=[]
for row in v['rows']+v['directories']:
 p=R/row['path'];st=p.lstat();assert not stat.S_ISLNK(st.st_mode) and stat.S_IMODE(st.st_mode)==int(row['mode'],8)
 if row['type']=='directory':assert stat.S_ISDIR(st.st_mode)
 else:
  assert stat.S_ISREG(st.st_mode) and st.st_size==row['bytes']
  if p.suffix=='.npy':opaque.append(row['path'])
  else:assert sha(p)==row['sha256'];body_checked.append(row['path'])
selected=set(x['path'] for x in v['rows'])
for entry in r['preservation_roots']:assert {x['path'] for x in entry['files']}<=selected
inverse={}
for name in ['capture01.py','recover01.py']:
 old=F/'real-data-pilot-twentysecond-failed-increment01-2026-10-09'/name;new=F/'real-data-pilot-twentythird-failed-increment01-2026-10-09'/name
 reverted=new.read_text().replace('outcome23-scope01','outcome22-scope01').replace('failed23','failed22').replace('20261009-23-01.git','20261008-22-01.git')
 assert reverted==old.read_text();inverse[name]={'baseline_sha256':sha(old),'candidate_sha256':sha(new),'literal_inverse':True}
result={'selection_sha256':sha(s),'files':140,'directories':35,'body_bytes':4043990,'all_six_owned_roots_covered':True,'nonarray_body_hashes_verified':len(body_checked),'opaque_array_metadata_only':opaque,'helper_inverse':inverse,'qualification':'Source/scoped local selection only. Array payloads not opened or authenticated here; selected original declared hashes retained. No capture execution/network/remote-return claim.'}
(H/'SELECTION_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
