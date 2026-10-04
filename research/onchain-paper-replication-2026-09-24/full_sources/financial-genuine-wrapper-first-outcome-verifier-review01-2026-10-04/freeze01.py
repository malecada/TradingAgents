from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=json.loads((D/'CHECKS01.json').read_text())
o={'schema_version':1,'verdict':'WITHHELD_VF1','candidate_source_sha256':sha(D/'source/verifier01.py'),'candidate_manifest_sha256':sha(D/'source/MANIFEST01.json'),'checks':c['count'],'finding':{'id':'VF1','priority':'P2','path':'verifier01.py','lines':[150,162,163,164,165,166,167,176,178,180],'impact':'Explicit unexpected native/lifecycle/exit evidence does not prevent planned-failure byte disposition. Not actual release authority; source semantics still require correction.','witnesses_sha256':sha(D/'VF1_WITNESSES01.json')},'checks_sha256':sha(D/'CHECKS01.json'),'report_sha256':sha(D/'REVIEW01.md'),'baseline_source_bodies':289,'actual_outcomes_inspected':0,'claims_created':0,'native_executions':0,'git_operations':0,'numerical_imports':0,'source_installed':False,'reviewed_native_file_cap_amendment':None,'author_oversize_negative_witness_bytes':4194305,'actual_case_closure_review':'separate reviewer; not duplicated here','authority':None,'paper_financial_credit':0}
(D/'REVIEW01.json').write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
rows=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST01.json':continue
 s=p.lstat();r={'path':p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,nlink=s.st_nlink,sha256=sha(p))
 elif stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
 else:raise ValueError(str(p))
 rows.append(r)
m={'schema_version':1,'status':'WITHHELD_VF1','scope':'complete independent review including all source copies, failed first harness, static no-outcome inspection, real owned link/FD controls and scalar witnesses; excludes only exact root MANIFEST01.json','entries':rows,'members':len(rows),'regular_files':sum(r['type']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows),'authority':None}
(D/'MANIFEST01.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest':sha(D/'MANIFEST01.json'),'machine':sha(D/'REVIEW01.json'),'report':sha(D/'REVIEW01.md'),'members':m['members'],'files':m['regular_files'],'bytes':m['regular_bytes']}))
