from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((D/'MANIFEST01.json').read_text())
for row in old['entries']:
 p=D/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['type']=='file':assert stat.S_ISREG(s.st_mode) and p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 elif row['type']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:raise AssertionError(row)
checks=json.loads((D/'CHECKS02.json').read_text())
metadata={'schema_version':1,'status':'IMPLEMENTED_SOURCE_ONLY_PENDING_DIFFERENT_AUTHOR_REVIEW','original_composition_manifest_sha256':sha(D/'MANIFEST01.json'),'original_composition_review_manifest_sha256':sha(D/'prior-composition-review01/MANIFEST01.json'),'original_recipe_sha256':sha(D/'recipe01.py'),'successor_recipe_sha256':sha(D/'recipe02.py'),'inverse_sha256':sha(D/'RECIPE_INVERSE01.json'),'baseline_metadata_sha256':sha(D/'BASELINE01.json'),'closure_metadata_sha256':sha(D/'CLOSURE01.json'),'scientific_guard_metadata_sha256':sha(D/'SCIENTIFIC_GUARDS01.json'),'controls_sha256':sha(D/'CHECKS02.json'),'controls_count':checks['count'],'actual_read_only_plan_sha256':sha(D/'ACTUAL_READ_ONLY_RECIPE02.json'),'historical_main_commit':checks['actual_historical_main'],'observed_current_main_commit':checks['actual_current_main'],'baseline_source_count':135,'composed_source_count':138,'static_other_source_pins':137,'dynamic_self_hash':'genuine actual admitted map; unchanged from reviewed composition','future_source_commit':None,'future_design_source':None,'future_registration_commit':None,'future_gate':None,'cumulative_allowance':None,'native_execution':None,'actual_recovery':None,'source_installed':False,'authority':None,'financial_credit':0,'fund_complete_policy':'REFUSED','inherited_manifest_members_verified':len(old['entries'])}
(D/'RESULT02.json').write_text(json.dumps(metadata,sort_keys=True,indent=2)+'\n')
entries=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST02.json':continue
 s=p.lstat();r={'path':p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=sha(p))
 elif stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
 else:raise ValueError('unexpected type '+str(p))
 entries.append(r)
result={'schema_version':1,'status':metadata['status'],'scope':'Complete owned successor tree including original composition, original review, nested manifests and owned synthetic Git metadata; excludes only exact root MANIFEST02.json. No external recovery claim.','entries':entries,'members':len(entries),'regular_files':sum(e['type']=='file' for e in entries),'regular_bytes':sum(e.get('bytes',0) for e in entries),'authority':None}
(D/'MANIFEST02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'manifest_sha256':sha(D/'MANIFEST02.json'),'result_sha256':sha(D/'RESULT02.json'),'recipe_sha256':sha(D/'recipe02.py'),'members':result['members'],'files':result['regular_files'],'bytes':result['regular_bytes']}))
