from pathlib import Path
import hashlib,json,stat,os
D=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=json.loads((D/'CHECKS01.json').read_text())
m={'schema_version':1,'verdict':'WITHHELD_VF2','candidate_source_sha256':sha(D/'source/verifier01.py'),'candidate_manifest_sha256':sha(D/'source/MANIFEST02.json'),'prior_withheld_manifest_sha256':sha(D/'prior-MANIFEST01.json'),'inverse_sha256':sha(D/'source/INVERSE01.json'),'checks':c['checks'],'VF1_tested_seams':'corrected','finding':{'id':'VF2','priority':'P2','path':'verifier01.py','line':154,'original_resource_lines':[120,135,534,548],'impact':'Strict final CPU equality/nonemptiness rejects source-permitted subset masks or empty post-exit census and labels planned failure unexpected.','witnesses_sha256':sha(D/'WITNESSES01.json')},'report_sha256':sha(D/'REVIEW02.md'),'checks_sha256':sha(D/'CHECKS01.json'),'actual_outcomes_inspected':0,'claims_created':0,'native_executions':0,'source_installed':False,'numerical_imports':0,'release_authorized':False,'paper_financial_credit':0,'future_corrected_source':None,'future_observation_adapter':None,'future_genuine_claim_history_review':None,'future_external_recovery':None,'authority':None}
(D/'REVIEW02.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n');rows=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST02.json':continue
 s=p.lstat();r={'path':p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=sha(p))
 elif stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
 else:raise ValueError(str(p))
 rows.append(r)
manifest={'schema_version':1,'status':'WITHHELD_VF2','scope':'complete independent owned source review including original VF1 history, all nested manifests, source/inverse bodies, owned empty-procs utility and scalar witness/control evidence; excludes only exact root MANIFEST02.json','entries':rows,'members':len(rows),'regular_files':sum(r['type']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows),'authority':None}
(D/'MANIFEST02.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest':sha(D/'MANIFEST02.json'),'machine':sha(D/'REVIEW02.json'),'report':sha(D/'REVIEW02.md'),'members':manifest['members'],'files':manifest['regular_files'],'bytes':manifest['regular_bytes']}))
