import gzip,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;rows=[];checks=0
sha=lambda x:hashlib.sha256(x).hexdigest()
for dirname,expected in [('financial-batch-output-genuine-storage-lease-preparation01-2026-10-04','4666b0d4745709a43326b8b2298be5cb8a8754800aceb9343b552a260ef8b250'),('financial-batch-output-genuine-storage-lease-source-review01-2026-10-04','050bb158a3c6d1c3e38976afe3e115609237f6a1ac1007967c619e571ea3cae8')]:
 r=B/dirname;raw=(r/'MANIFEST01.json').read_bytes();assert sha(raw)==expected;checks+=1;m=json.loads(raw);items=m.get('entries',m['members']);assert {p.relative_to(r).as_posix() for p in r.rglob('*') if p!=r/'MANIFEST01.json'}=={x['path'] for x in items};checks+=1
 for row in items:
  p=r/row['path'];s=p.lstat();mode=int(row['mode'],8) if type(row['mode']) is str else row['mode'];assert stat.S_IMODE(s.st_mode)==mode;checks+=1
  if row['kind']=='file':assert s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'] and s.st_nlink==row['nlink'];checks+=3
  elif row['kind']=='symlink':assert os.readlink(p)==row['target'];checks+=1
  else:assert stat.S_ISDIR(s.st_mode);checks+=1
 rows.append({'directory':str(r),'manifest_sha256':expected,'members':len(items),'file_bytes':sum(x.get('bytes',0) for x in items)})
old=B/'financial-batch-output-genuine-storage-lease-preparation01-2026-10-04';negative=json.loads((old/'OFFLINE_OVERSIZE01.json').read_text());p=old/negative['path'];raw=p.read_bytes();assert sha(raw)==negative['sha256'] and len(raw)==4194305 and gzip.decompress((old/'OFFLINE_OVERSIZE_RAW01.gz').read_bytes())==raw;checks+=3
review=B/'financial-batch-output-genuine-storage-lease-source-review01-2026-10-04';machine=json.loads((review/'MACHINE01.json').read_text());assert machine['decision']=='WITHHELD_SL1_SL2' and machine['failed_replay']=='check02 accepted partial';checks+=2
# Exact raw failed stderr retained in original review; store bounded literal copy
# without altering original body/namespace. Original full tree is above authenticated.
failed=[]
for p in review.glob('*.err'):
 if p.stat().st_size:
  raw=p.read_bytes();name='PREDECESSOR_'+p.name;(H/name).write_bytes(raw);failed.append({'path':str(p),'bytes':len(raw),'sha256':sha(raw),'literal_copy':name})
assert failed;checks+=1
(H/'AUTHENTICATION01.json').write_text(json.dumps({'checks':checks,'scopes':rows,'negative':negative,'failed_prior_replays':failed,'prior364_claim':'155 repeated twice +49+5 author assertions; original independent rapid-rewrite replay did not pass155','original_byte_mutation_or_deletion':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':checks,'status':'PASS'}))
