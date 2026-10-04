import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-codec-spool-integration-preparation02-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
for n in ('router05.py','MANIFEST01.json','MACHINE01.json','INVERSE01.json','INVERSE01.diff','REPORT01.md'):(H/('AUTHOR_'+n)).write_bytes((A/n).read_bytes())
checks=json.loads((H/'AUTHENTICATION03.json').read_text())['checks']+json.loads((H/'INDEPENDENT04.json').read_text())['checks']+json.loads((H/'RESULT04.json').read_text())['count']+len(json.loads((H/'ADVERSARIAL01.json').read_text()))+11
write('MACHINE02.json',{'schema_version':1,'decision':'WITHHELD_IR3','candidate_sha256':sha((A/'router05.py').read_bytes()),'author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes()),'checks':checks,'IR1_IR2_corrected':True,'IR3_witness_sha256':sha((H/'IR3_WITNESS01.json').read_bytes()),'report_sha256':sha((H/'REPORT02.md').read_bytes()),'whole_byte_AST_inverse':True,'all_six_utility_sources_unchanged':True,'actual_tiny_pipeline_files':95,'actual_tiny_retained_plans':14,'actual_full_population':False,'live_production_authority':None,'originals_unchanged':True})
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST02.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
write('MANIFEST02.json',{'schema_version':1,'members':rows})
print(json.dumps({'checks':checks,'members':len(rows),'files':sum(r['kind']=='file' for r in rows),'manifest':sha((H/'MANIFEST02.json').read_bytes()),'machine':sha((H/'MACHINE02.json').read_bytes()),'witness':sha((H/'IR3_WITNESS01.json').read_bytes()),'report':sha((H/'REPORT02.md').read_bytes())},sort_keys=True))
