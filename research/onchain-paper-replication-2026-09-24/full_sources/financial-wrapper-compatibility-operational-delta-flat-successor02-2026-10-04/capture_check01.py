from pathlib import Path
import json,hashlib,stat,os,io,gzip,tarfile
O=Path(__file__).resolve().parent;F=O.parent;C=F/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());c=J(C/'CAPTURE01.json');m=J(C/'FAILED_PAYLOAD_MANIFEST01.json');original=J(C/'ORIGINAL_FAILED_ROOT_SCOPE43.json');root=Path(c['original_root']);snap=C/'snapshot'
assert h((C/'CAPTURE01.json').read_bytes())=='58d76ef3d7da87994ec7052e1d16c6facadcfd53535c15fe7532956515eab740';assert h((C/'FAILED_PAYLOAD_MANIFEST01.json').read_bytes())==c['manifest_sha256']==c['archive']['manifest_sha256'];assert h((C/'ORIGINAL_FAILED_ROOT_SCOPE43.json').read_bytes())==c['original_scope_sha256'];assert len(original['members'])==43 and len(m['members'])==42
for base in [root,snap]:
 assert stat.S_IMODE(base.stat().st_mode)==m['root_mode'];actual={p.relative_to(base).as_posix() for p in base.rglob('*')};assert actual=={x['path'] for x in m['members']}
 for x in m['members']:
  p=base/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
  if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
  else:assert stat.S_ISDIR(s.st_mode)
archive=(C/'failed-remote02.tar.gz').read_bytes();assert h(archive)==c['archive']['sha256'];out=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as z:
 with tarfile.open(fileobj=z,mode='w|',format=tarfile.PAX_FORMAT) as t:
  for x in m['members']:
   a=tarfile.TarInfo(x['path']);a.mode=x['mode'];a.uid=a.gid=a.mtime=0;a.uname=a.gname=''
   if x['kind']=='directory':a.type=tarfile.DIRTYPE;t.addfile(a)
   else:b=(snap/x['path']).read_bytes();a.size=len(b);t.addfile(a,io.BytesIO(b))
assert out.getvalue()==archive
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as t:
 assert [x.name for x in t.getmembers()]==[x['path'] for x in m['members']]
f=J(root/'FAILED01.json');assert h((root/'FAILED01.json').read_bytes())==c['actual_FAILED_sha256'];assert f['operations'][2]['exit'] is None and f['operations'][2]['actual_reaped_exit']==0 and c['historical_changed_directory_path_or_field'] is None
result={'schema_version':1,'capture_sha256':h((C/'CAPTURE01.json').read_bytes()),'archive_sha256':h(archive),'manifest_sha256':h((C/'FAILED_PAYLOAD_MANIFEST01.json').read_bytes()),'original_current_and_snapshot_all_members':43,'payload_descendants':42,'regular':31,'logical':sum(x.get('bytes',0) for x in m['members']),'canonical_byte_equal':True,'actual_external_receipt':None,'qualification':'Authenticated local capture of permanently failed namespace, no restoration/external proof.'};(O/'CAPTURE_READBACK01.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS genuine failed local43/42/31 original modes/body/archive/nulls')
