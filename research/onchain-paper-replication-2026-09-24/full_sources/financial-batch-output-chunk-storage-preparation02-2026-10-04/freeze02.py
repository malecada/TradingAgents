import ast,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-chunk-storage-preparation01-2026-10-04';V=H.parent/'financial-batch-output-chunk-storage-source-review01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
pins={'MANIFEST01.json':'21c95e8ca55a7c76f7eb6cdb4cd293e1efb7f77d0122587dd67a2cb92f22e1f0','WITNESSES01.json':'c7355b108ef4af2311b59653bb8f54491b7a15c29acd7349a1e813cd25c7bbd6'}
for n,h in pins.items():assert sha((V/n).read_bytes())==h
# Authenticate the original author seal and all of its exact typed members.
assert sha((A/'MANIFEST01.json').read_bytes())=='1181852868d880e624caf3e4a3982f6bd27301983cc3fe2e7a2a0c92f6e3ef8d'
checks=0
for r in json.loads((A/'MANIFEST01.json').read_text())['members']:
 p=A/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode'];checks+=1
 if r['kind']=='file':b=p.read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'];checks+=1
 elif r['kind']=='directory':assert stat.S_ISDIR(s.st_mode);checks+=1
 else:assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'];checks+=1
# Copy only the small exact original reviewer source/findings, never mutate or
# unlink its real retained hardlink witnesses. Their original metadata is pinned.
reviewrefs=[]
for n in ('MANIFEST01.json','WITNESSES01.json','witness01.py','REPORT01.md','CHECKS01.json'):
 b=(V/n).read_bytes();(H/('REVIEW01_'+n)).write_bytes(b);reviewrefs.append({'path':str(V/n),'sha256':sha(b),'bytes':len(b)})
hardlinks=[]
for n in ('start.json','page-0000.json'):
 p=V/'ownership-hardlink'/n;s=p.lstat();hardlinks.append(dict(path=str(p),device=s.st_dev,inode=s.st_ino,nlink=s.st_nlink,mode=stat.S_IMODE(s.st_mode),bytes=s.st_size,sha256=sha(p.read_bytes())))
assert hardlinks[0]['inode']==hardlinks[1]['inode'] and all(r['nlink']==2 for r in hardlinks)
refs=json.loads((A/'SOURCE_READBACK01.json').read_text())
for r in refs['read_only_sources']:
 p=Path(r['path']);b=p.read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes'] and stat.S_IMODE(p.lstat().st_mode)==r['mode'];checks+=1
write('PROVENANCE02.json',{'schema_version':1,'original_author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'original_review':reviewrefs,'unchanged_original_hardlink_witness':hardlinks,'unchanged_read_only_scientific_sources':refs,'original_author_checks':checks})
for p in H.glob('*.py'):ast.parse(p.read_bytes())
c=json.loads((H/'CHECKS03.json').read_text());w=[json.loads((H/n).read_text()) for n in ('WITNESS_OLD02.json','WITNESS_NEW02.json')]
write('MACHINE02.json',{'schema_version':1,'decision':'SOURCE_SUCCESSOR_AWAITING_INDEPENDENT_REVIEW','codec_sha256':sha((H/'codec01.py').read_bytes()),'local_store_sha256':sha((H/'local_store01.py').read_bytes()),'independent_predecessor_verdict':'WITHHELD_CS1_CS2_CS3','new_checks':c['checks'],'red_green_checks':sum(v['checks'] for v in w),'inherited_passing_test_methods':13,'source_and_author_checks':checks,'full_inverse':True,'actual_64MiB_capacity_measured':False,'kernel_quota_installed':False,'filesystem_allocation_bound_verified':False,'live_publication':'UNAVAILABLE','scientific_authority':None,'representation_complete':False})
entries=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST02.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 entries.append(r)
write('MANIFEST02.json',{'schema_version':1,'members':entries})
print(json.dumps({'members':len(entries),'files':sum(r['kind']=='file' for r in entries),'codec':sha((H/'codec01.py').read_bytes()),'local':sha((H/'local_store01.py').read_bytes()),'manifest':sha((H/'MANIFEST02.json').read_bytes()),'machine':sha((H/'MACHINE02.json').read_bytes()),'controls':c['checks']+sum(v['checks'] for v in w)+checks},sort_keys=True))
