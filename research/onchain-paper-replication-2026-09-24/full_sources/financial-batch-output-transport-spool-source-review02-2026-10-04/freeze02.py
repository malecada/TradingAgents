import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-transport-spool-preparation02-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for n in ('spool03.py','spool04.py','owned_io.py','INVERSE01.diff','INVERSE01.json','MANIFEST01.json','MACHINE01.json','REPORT01.md','WITNESS01.json','FATAL01.json','REGRESSION01.json'):(H/('AUTHOR_'+n)).write_bytes((A/n).read_bytes())
checks=json.loads((H/'CHECKS01.json').read_text())['checks']+json.loads((H/'AUTH05.json').read_text())['checks']+6
write('MACHINE02.json',{'schema_version':1,'decision':'WITHHELD_SP4','candidate_sha256':sha((A/'spool04.py').read_bytes()),'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'original_SP1_SP2_SP3_corrected':True,'SP4_scheduled_cleanup_witness_sha256':sha((H/'SP4_WITNESS01.json').read_bytes()),'checks':checks,'literal_and_AST_inverse':True,'actual_timed_race_observed':False,'report_sha256':sha((H/'REPORT02.md').read_bytes()),'numerical_or_network_execution':False,'production_authority':None,'full_capacity_proved':False})
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST02.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
write('MANIFEST02.json',{'schema_version':1,'members':rows})
print(json.dumps({'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'checks':checks,'manifest':sha((H/'MANIFEST02.json').read_bytes()),'machine':sha((H/'MACHINE02.json').read_bytes()),'witness':sha((H/'SP4_WITNESS01.json').read_bytes()),'report':sha((H/'REPORT02.md').read_bytes())},sort_keys=True))
