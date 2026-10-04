import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-transport-spool-preparation01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for n in ('spool01.py','spool02.py','owned_io.py','MANIFEST01.json','MACHINE01.json','SOURCE_PINS01.json','REPORT01.md','CHECK01.err','CHECK01.out','CHECK02.err','CHECK02.out','RESULT02.json','check01.py','check02.py'):(H/('ORIGINAL_'+n)).write_bytes((A/n).read_bytes())
readback={'schema_version':1,'decision':'WITHHELD_SP1_SP2_SP3','candidate_sha256':sha((A/'spool02.py').read_bytes()),'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'checks':json.loads((H/'CHECKS01.json').read_text())['checks'],'witness_sha256':sha((H/'WITNESSES01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'findings':['SP1 canonical ancestor redirection survives current check','SP2 bool values satisfy exact integer Ack equality','SP3 post-cleanup deadline can pass while return remains nonfailed'],'scope':'source review and tiny opaque local controls only','actual_remote_or_numerical_work':False,'scientific_authority':None,'actual_full_capacity':False,'original_sources_unchanged':True}
write('MACHINE01.json',readback)
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
write('MANIFEST01.json',{'schema_version':1,'members':rows})
print(json.dumps({'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'checks':readback['checks'],'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'witnesses':sha((H/'WITNESSES01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes())},sort_keys=True))
