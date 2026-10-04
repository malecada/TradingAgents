import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-codec-spool-integration-preparation01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for n in ('router01.py','router02.py','router03.py','router04.py','codec01.py','local_store01.py','spool05.py','owned_io.py','recovery04.py','bounded_git01.py','MANIFEST01.json','MACHINE01.json','AUTHENTICATION01.json','REPORT01.md','CHECK01.err','RESULT04.json','ADVERSARIAL01.json'):(H/('AUTHOR_'+n)).write_bytes((A/n).read_bytes())
checks=json.loads((H/'AUTHENTICATION03.json').read_text())['checks']+json.loads((H/'INDEPENDENT04.json').read_text())['checks']+json.loads((H/'RESULT04.json').read_text())['count']+len(json.loads((H/'ADVERSARIAL01.json').read_text()))+2
write('MACHINE01.json',{'schema_version':1,'decision':'WITHHELD_IR1_IR2','candidate_sha256':sha((A/'router04.py').read_bytes()),'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'checks':checks,'report_sha256':sha((H/'REPORT01.md').read_bytes()),'witness_sha256':sha((H/'WITNESSES02.json').read_bytes()),'actual_tiny_members':95,'actual_tiny_retained_plans':14,'six_utility_bodies_unchanged':True,'full_population_executed':False,'transport_or_research_authority':None,'actual_timed_race_claim':False,'originals_preserved':True})
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
write('MANIFEST01.json',{'schema_version':1,'members':rows})
print(json.dumps({'checks':checks,'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'witness':sha((H/'WITNESSES02.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes())},sort_keys=True))
