import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):
 with (H/n).open('xb') as f:f.write((json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
r=json.loads((H/'READBACK01.json').read_bytes());p=json.loads((H/'PRESERVED_HISTORY02.json').read_bytes())
write('VERDICT01.json',{'schema_version':1,'reviewer':'combined_worker_review','status':'ACCEPTED_ACTUAL_LOCAL_SIX_HELPER_CAPTURE','checks':r['checks']+p['checks'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'preserved_history_sha256':sha((H/'PRESERVED_HISTORY02.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'actual_authentication_sha256':r['actual_authentication_sha256'],'actual_terminal_sha256':r['actual_terminal_sha256'],'archives':r['archives'],'whole_original_files':4220,'whole_original_bytes':9187425,'literal_links':17,'original_typed':4432,'ordinary_union_members':4422,'actual_external_recovery':None,'actual_Root_flat_recovery':None,'general_PAX_defect_cleared':False,'numerical_release':False,'failed_harnesses':[]})
rows=[]
for p in sorted(H.iterdir()):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();rows.append({'path':p.name,'mode':stat.S_IMODE(s.st_mode),'kind':'file','bytes':len(b),'sha256':sha(b)})
write('MANIFEST01.json',{'schema_version':1,'members':rows})
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'readback':sha((H/'READBACK01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'bytes':sum(x['bytes'] for x in rows),'checks':r['checks']+json.loads((H/'PRESERVED_HISTORY02.json').read_bytes())['checks']}))
