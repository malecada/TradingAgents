"""Restore only pinned opaque archive bytes into this new reviewer-owned tree."""
import gzip,hashlib,io,json,os,stat,sys,tarfile,time
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OUT=BASE/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03'
PREP=BASE/'neural-cold-feature-handoff-outcome-retention-preparation02-2026-10-03'
assert hashlib.sha256((PREP/'archive01.py').read_bytes()).hexdigest()=='35b6c46bdcc3865d851843d381843c44a973051e7c415f861c7507c1311758a7'
sys.path.insert(0,str(PREP));import archive01 as a
r=json.loads(a.read(OUT/'OUTCOME_RETENTION01.json'));path=OUT/'comparison-outcome01.tar.gz';blob=a.read(path);assert len(blob)==r['archive_bytes']==3655713 and hashlib.sha256(blob).hexdigest()==r['archive_sha256']=='0df30abe430dced727edec3687a49bad739e743d62290b7972e76a8ee5d8774d'
rows=r['members'];expected={x['path']:x for x in rows};assert len(rows)==len(expected)==2313 and '.' not in expected
root=HERE/'restored-collection01';root.mkdir(mode=0o700,exist_ok=False);seen=set();start=time.monotonic()
with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tf:
 for m in tf:
  assert time.monotonic()-start<120 and len(seen)<2313
  p=PurePosixPath(m.name);assert str(p)==m.name and p.parts[0]=='collection' and len(p.parts)>1 and '..' not in p.parts and '\\' not in m.name
  name=str(PurePosixPath(*p.parts[1:]));assert name in expected and name not in seen
  row=expected[name];dest=root/name;assert dest.resolve()==dest and dest.parent.is_dir() and m.mode==row['mode'] and m.uid==m.gid==m.mtime==0 and not m.uname and not m.gname and set(m.pax_headers)<={'path'}
  if row['kind']=='directory':
   assert m.isdir() and m.size==0;dest.mkdir(mode=0o700)
  else:
   assert row['kind']=='file' and m.isfile() and m.size==row['bytes']<=4194304
   with tf.extractfile(m) as f:body=f.read(4194305)
   assert len(body)==row['bytes'] and hashlib.sha256(body).hexdigest()==row['sha256']
   with dest.open('xb') as f:f.write(body)
   os.chmod(dest,row['mode'])
  seen.add(name)
assert seen==set(expected)
for row in reversed(rows):
 if row['kind']=='directory':os.chmod(root/row['path'],row['mode'])
a.verify_tree(root,rows,limit=1024**3,seconds=120);a.verify_tree(OUT/'collection01',rows,limit=1024**3,seconds=120)
canonical=HERE/'canonical-check01.tar.gz'
with canonical.open('xb') as dest:
 with gzip.GzipFile(fileobj=dest,mode='wb',filename='',mtime=0) as g:
  with tarfile.open(fileobj=g,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for row in rows:
    m=tarfile.TarInfo('collection/'+row['path']);m.mode=row['mode'];m.uid=m.gid=m.mtime=0;m.uname=m.gname=''
    if row['kind']=='directory':m.type=tarfile.DIRTYPE;tf.addfile(m)
    else:
     body=a.read(root/row['path']);m.size=len(body);tf.addfile(m,io.BytesIO(body))
assert a.read(canonical)==blob,'canonical framing including all gzip/tar padding/trailing bytes differs'
result={'schema_version':1,'archive_sha256':hashlib.sha256(blob).hexdigest(),'archive_bytes':len(blob),'members':len(rows),'files':sum(x['kind']=='file' for x in rows),'directories':sum(x['kind']=='directory' for x in rows),'logical_bytes':sum(x.get('bytes',0) for x in rows),'local_archive':'ACCEPTED_EXACT_CANONICAL','remote_recovery':'NOT_EXECUTED','recovery_helper01':'WITHHELD_MISSING_ROOT_ROW_REWALK','retention_root_mode_observed':stat.S_IMODE((OUT/'collection01').stat().st_mode),'root_mode_not_in_archive':True,'restored_scope':'review-only-byte-copy-not-authority','arrays_decoded':False}
(HERE/'ARCHIVE_READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
