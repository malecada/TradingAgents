import hashlib,json,tarfile
from pathlib import Path
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent/'real-data-pilot-twentyfirst-failed-increment01-2026-10-08'
cap=json.loads((D/'CAPTURE01.json').read_text());join=json.loads((D/'CAPTURE_SOURCE_JOIN01.json').read_text());src=(D/'capture01.py').read_text();base=(R/join['baseline_path']).read_text()
assert hashlib.sha256(src.encode()).hexdigest()==join['candidate_sha256'] and hashlib.sha256(base.encode()).hexdigest()==join['baseline_sha256']
for row in join['edits']:src=src.replace(row['new'],row['old'])
assert src==base
sraw=(R/cap['selection']['path']).read_bytes();assert hashlib.sha256(sraw).hexdigest()==cap['selection']['sha256']=='62164022b84311c5986c690131bc93ed3ee6762d93b50456a98b5105b03aeb4d';s=json.loads(sraw)
p=R/cap['archive']['path'];raw=p.read_bytes();assert len(raw)==cap['archive']['bytes']==1280000 and hashlib.sha256(raw).hexdigest()==cap['archive']['sha256']=='23973fce1e7ea541c7678aba018ad537e757c10fdad7a013bc0f375534870ec2'
rows={x['path']:x for x in s['rows']+s['directories']}
with tarfile.open(p,'r:') as tar:
 members=tar.getmembers();assert len(members)==118 and len({m.name for m in members})==118 and set(rows)=={m.name for m in members}
 for m in members:
  row=rows[m.name];assert m.mode==int(row['mode'],8)
  if row['type']=='directory':assert m.isdir()
  else:
   assert m.isfile();body=tar.extractfile(m).read();assert m.size==len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
x={'decision':'accepted-local-public-capture','identity':s['identity'],'capture_sha256':hashlib.sha256((D/'CAPTURE01.json').read_bytes()).hexdigest(),'archive':cap['archive'],'selection':cap['selection'],'files':87,'directories':31,'regular_bytes':1090330,'checks':['capture source exact two-edit inverse','exact selected archive typed names/no duplicates/no additional members','all archive modes and regular opaque hashes/lengths match original selection'],'qualification':'Local public capture verified, not external recovery or binary semantic/POSIX reconstruction/deletion proof. Private/runtime/scientific input stores excluded; original terminal FAILED/spent92 unchanged.'}
(H/'CAPTURE_REVIEW04.json').write_text(json.dumps(x,indent=2)+'\n');print(hashlib.sha256((H/'CAPTURE_REVIEW04.json').read_bytes()).hexdigest())
