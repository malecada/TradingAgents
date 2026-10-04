import hashlib,json,stat
from pathlib import Path
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();r=json.loads((H/'READBACK01.json').read_bytes());c=json.loads((H/'CONTEXT02.json').read_bytes())
v={'schema_version':1,'reviewer':'combined_worker_review','status':r['status'],'checks':r['checks']+c['checks'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'context_sha256':sha((H/'CONTEXT02.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'actual_recovery_sha256':'683d3f2ff60463975cd61eb6de7753fb7d3a06220edae1d2d3e2191a102d19e0','actual_terminal_sha256':c['full_terminal_sha256'],'restored_regular_bodies':4544,'restored_payload_bytes':52444730,'all8canonical_reencoding':True,'own_raw330_actual_selected':True,'own_literal45_actual_selected_metadata':True,'separate_final20_and_five_witness_restoration_reviewed':False,'numerical_release':False,'failed_harnesses':[]}
with (H/'VERDICT01.json').open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
rows=[]
for p in sorted(H.iterdir()):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();rows.append({'path':p.name,'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':sha(b)})
with (H/'MANIFEST01.json').open('x') as f:json.dump({'schema_version':1,'members':rows},f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'verdict':sha((H/'VERDICT01.json').read_bytes()),'readback':sha((H/'READBACK01.json').read_bytes()),'checks':v['checks'],'files':len(rows),'bytes':sum(x['bytes'] for x in rows)}))
