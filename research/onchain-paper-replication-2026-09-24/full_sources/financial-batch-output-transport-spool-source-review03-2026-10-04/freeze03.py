import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-transport-spool-preparation03-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for n in ('spool05.py','owned_io.py','MANIFEST01.json','MACHINE01.json','INVERSE01.diff','INVERSE01.json','REPORT01.md','ROOT_CODEC_SPOOL_INTEGRATION_GAP01.json','SP4_WITNESS01.json','FATAL01.json','REGRESSION01.json'):(H/('AUTHOR_'+n)).write_bytes((A/n).read_bytes())
checks=json.loads((H/'CHECKS01.json').read_text())['checks']+json.loads((H/'AUTH04.json').read_text())['checks']+10
write('MACHINE03.json',{'schema_version':1,'decision':'ACCEPTED_SOURCE_ONLY_SAMPLED_SPOOL_UTILITY','candidate_sha256':sha((A/'spool05.py').read_bytes()),'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'checks':checks,'full_literal_and_AST_inverse':True,'SP4_old_sha256':sha((H/'SP4_old.json').read_bytes()),'SP4_new_sha256':sha((H/'SP4_new.json').read_bytes()),'report_sha256':sha((H/'REPORT03.md').read_bytes()),'historical_withhelds_preserved':True,'sampled_not_atomic':True,'production_or_retirement_authority':None,'numeric_or_network_work':False,'full_capacity_proved':False,'codec_spool_integration_admitted':False})
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST03.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
write('MANIFEST03.json',{'schema_version':1,'members':rows})
print(json.dumps({'checks':checks,'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'machine':sha((H/'MACHINE03.json').read_bytes()),'manifest':sha((H/'MANIFEST03.json').read_bytes()),'report':sha((H/'REPORT03.md').read_bytes())},sort_keys=True))
