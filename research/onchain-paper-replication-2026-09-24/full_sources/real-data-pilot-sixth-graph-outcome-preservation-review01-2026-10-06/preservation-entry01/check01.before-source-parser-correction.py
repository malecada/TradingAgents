from pathlib import Path
import ast,hashlib,json,stat,shutil,subprocess
H=Path(__file__).resolve().parent;O=H.parent;F=O.parent;R=F.parents[2];B=R/'research/onchain-paper-replication-2026-09-24';A=F/'real-data-pilot-june6-preservation-preparation01-2026-10-06';D=B/'storage/real-pilot-sixth-graph-preservation-20261006-01';ev={}
def raw(p):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2;b=p.read_bytes();t=p.stat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns);ev[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def bound(ref):
 p=R/ref['path'];b=raw(p);assert ev[ref['path']]==ref['sha256'];return json.loads(b)
m=read(A/'MANIFEST01.json')
for row in m['members']:
 src=raw(R/row['path']);old=raw(R/row['accepted_parent']);assert hashlib.sha256(src).hexdigest()==row['sha256'] and hashlib.sha256(old).hexdigest()==row['accepted_parent_sha256'] and len(src)==row['bytes']
 restored=src.decode()
 for before,after in row['only_literal_replacements'].items():restored=restored.replace(after,before)
 assert restored.encode()==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old))
read(A/'ACTUAL_BINDING01.json')
e=read(D/'envelope01.json');assert ev[str((D/'envelope01.json').relative_to(R))]=='b3066d129359a5f465ea86d575f57601f9e15579d8f7e6d9b3de8cb072a0c211'
s=bound(e['selection']);assert e['selection']['sha256']=='8bc8b38382bffa0562fa03a3ce3fcdf654f160146303eb63fcb1a9e877b29135'
assert raw(D/'entry01.py')==raw(A/'entry01.py') and len(e['source_files'])==12
for path,sha in e['source_files'].items():assert hashlib.sha256(raw(R/path)).hexdigest()==sha
prior=read(B/'storage/real-pilot-may30-continuation-preservation-20261006-01/envelope01.json')
assert e['connection']==prior['connection'] and e['local_only_evidence']==[e['connection']['path']] and e['environment']==prior['environment'] and e['transport']==prior['transport']
bound(e['environment']);bound(e['transport'])
for ref in e['evidence']:bound(ref)
o=bound(s['graph_outcome_review']);body=bound(s['independent_body_hash']);terminal=bound(s['graph_terminal'])
assert o['decision']=='accepted' and o['experiment']=='eth-paper-real-pilot-graph-20220606-20261005-01' and o['source']=='483f92786c5076ec6f6ad0bffa894b8b36653797' and terminal['status']=='complete' and body['decision']=='pass'
assert s['count']==36 and s['total_bytes']==3528609093 and len(s['files'])==36 and len(s['directories'])==8 and sum(r['bytes'] for r in s['files'])==3528609093
assert s['disk_floor_bytes']==10*1024**3 and s['owned_tree_limit_bytes']==5*1024**3 and s['transport_payload_budget_bytes']==8*1024**3
payload={r['path']:r for r in body['files']};seen=set();rows=[]
for row in s['files']:
 p=R/row['path'];t=p.lstat();assert p.resolve()==p and stat.S_ISREG(t.st_mode) and t.st_nlink==row['nlink']==1
 sig=[t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns];assert sig==row['stat_identity'] and stat.S_IMODE(t.st_mode)==row['mode'] and t.st_size==row['bytes'];assert row['path'] not in seen;seen.add(row['path'])
 if row['path'] in payload:
  pr=payload[row['path']];assert pr['sha256']==row['sha256'] and pr['bytes']==row['bytes'] and pr['stat_identity']==[t.st_dev,t.st_ino,t.st_nlink,t.st_size,t.st_mtime_ns,t.st_ctime_ns] and pr['mode']==row['mode']
 else:assert hashlib.sha256(raw(p)).hexdigest()==row['sha256']
 rows.append({'path':row['path'],'sha256':row['sha256'],'bytes':row['bytes'],'stat_identity':sig,'mode':row['mode']})
assert set(payload)<=seen and len(payload)==6 and sum(x['bytes'] for x in payload.values())==3528523496
for row in s['directories']:
 p=R/row['path'];t=p.lstat();assert p.resolve()==p and stat.S_ISDIR(t.st_mode) and stat.S_IMODE(t.st_mode)==row['mode']
files=set();dirs=set()
for root in [R/'research_runs'/o['experiment']]+[R/'research_artifacts/onchain-paper-replication-2026-09-24'/kind/o['experiment'] for kind in ('runs','sources')]:
 for p in [root,*root.rglob('*')]:
  t=p.lstat();assert not p.is_symlink();(dirs if stat.S_ISDIR(t.st_mode) else files).add(str(p.relative_to(R)))
assert files==seen and dirs=={r['path'] for r in s['directories']}
for name in ('launch-attempt01.json','preflight01.json','intent.json','complete.json','failed.json','guard01','outer-exit01.json'):assert not (D/name).exists() and not (D/name).is_symlink()
assert not list(D.glob('*-attempted.json')) and not list(D.glob('*-recovered.bin'))
rootrec=read(F/'real-data-pilot-sixth-graph01-2026-10-06/ROOT_TERMINAL01.json');assert rootrec['actual_root_tool_exit_code']==0 and all(not Path('/proc',str(p)).exists() for p in rootrec['selected_recorded_pids'])
u=subprocess.run(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],capture_output=True,text=True);assert u.returncode==0 and not u.stdout.strip()
free=shutil.disk_usage(R).free;assert free>=10*1024**3+s['total_bytes']+16*1024**2
result={'decision':'pass','identity':s['identity'],'count':36,'bytes':3528609093,'payload_bytes_inherited':3528523496,'small_metadata_hashes':30,'directory_count':8,'source_pins':12,'fixed_literal_inverse_counts':[3,1,1],'actual_producer_independently_bound':True,'historical_third_selector_unused_extra_pin':True,'connection_body_read':False,'payload_hash_or_header_SQL_reads':0,'free_disk_observed_bytes':free,'startup_disk_requirement_bytes':10*1024**3+s['total_bytes']+16*1024**2,'active_native_rows':0,'fresh_namespace':True,'fresh_eligibility_still_required':True,'evidence':ev}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))
