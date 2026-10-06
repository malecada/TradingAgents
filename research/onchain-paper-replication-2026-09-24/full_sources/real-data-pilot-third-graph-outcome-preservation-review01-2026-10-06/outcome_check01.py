from pathlib import Path
import hashlib,json,stat
R=Path.cwd();N='eth-paper-real-pilot-graph-20220516-20261005-01';S='72b25ad173d8a3ee30d39750df0d7a322ed50880';O=Path(__file__).parent;P=R/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-third-graph01-2026-10-06';run=R/'research_runs'/N;art=R/'research_artifacts/onchain-paper-replication-2026-09-24';ev={}
def read(p):
 assert p.stat().st_size<4*1024**2;raw=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=read(run/'claim.json');t=read(run/'complete.json');g=read(P/'gate01.json');e=g['experiments'][N];root=read(P/'ROOT_TERMINAL01.json');guard=read(art/'runs'/N/'guard/final.json');outer=read(P/'outer-exit01.json');idx=read(run/'outputs/artifact-index.json');body=read(O/'BODY_HASH01.json')
assert c['source']==t['source']==S and c['experiment']==e and t['claim_sha256']==digest(run/'claim.json') and c['registration_sha256']==t['registration_sha256']==digest(P/'gate01.json')
assert c['effective_attempt_budget']==71 and e['parent'] is None and len(e['source_files'])==178 and len(e['inputs'])==35 and len(e['runtime_hashes'])==7
for n,h in e['source_files'].items():assert digest(R/n)==h,n;ev[n]=h
for n,h in e['runtime_hashes'].items():assert digest(R/'tradingagents/research'/n)==h,n
for info in e['inputs'].values():p=R/info['path'];assert p.stat().st_size<4*1024**2 and digest(p)==info['sha256'];ev[info['path']]=info['sha256']
assert t['status']=='complete' and t['cell_count']==2 and all(x['status']=='complete' for x in t['cells']) and t['unavailable_count']==0
assert [x['id'] for x in t['cells']]==e['cells'] and t['cells'][0]['rows']==t['cells'][1]['raw_count']==7794344 and t['cells'][1]['admitted_count']==3909412
for n,h in t['output_sha256'].items():assert digest(run/'outputs'/n)==h;ev[str((run/'outputs'/n).relative_to(R))]=h
assert root['actual_root_tool_exit_code']==0 and root['original_outer_exit_code']==0 and root['source_commit']==S
assert guard['phase']=='complete' and guard['child_exit_code']==0 and guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==5
assert not Path(guard['cgroup']).exists() and all(not Path('/proc',str(pid)).exists() for pid in root['selected_recorded_pids'])
assert root['current_unit_readback_exit_code']==0 and 'ActiveState=inactive' in root['current_unit_properties_raw'] and 'MainPID=0' in root['current_unit_properties_raw']
bodies={v['path']:v for v in body['files']};assert len(bodies)==6 and body['total_bytes']==3855665024
for n,v in idx.items():
 if n in bodies:assert bodies[n]['sha256']==v['sha256'] and bodies[n]['bytes']==v['bytes'];continue
 p=R/n;assert p.stat().st_size==v['bytes'] and digest(p)==v['sha256'];ev[n]=v['sha256']
for base in (run,art/'runs'/N,art/'sources'/N):
 for p in base.rglob('*'):
  if p.is_file() and str(p.relative_to(R)) not in bodies:
   assert p.stat().st_size<4*1024**2 and not p.is_symlink();ev[str(p.relative_to(R))]=digest(p)
ext=read(P/'RAW_EXTENT01.json');count=0
for d in ext['daily_members']:
 assert digest(R/d['mapping_path'])==d['mapping_sha256']
 for s in d['segments']:
  p=Path(s['path']);a=p.lstat();assert not p.is_symlink() and stat.S_ISREG(a.st_mode);assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==tuple(s[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns'));count+=1
assert count==232
manifest=read(art/'sources'/N/'graph-2022-05-16/manifest.json');assert digest(art/'sources'/N/'graph-2022-05-16/manifest.json')==t['cells'][1]['manifest_sha256']
for v in manifest['arrays'].values():row=bodies[str((art/'sources'/N/'graph-2022-05-16'/v['path']).relative_to(R))];assert v['sha256']==row['sha256'] and v['bytes']==row['bytes']
review={'schema_version':1,'decision':'accepted','experiment':N,'source':S,'claim_sha256':digest(run/'claim.json'),'root_actual_exit':{'exit_code':0,'receipt':str((P/'ROOT_TERMINAL01.json').relative_to(R)),'actual_tool_chunk':root['actual_root_tool_completion_chunk']},'cleanup':{'original_guard_cleanup_verified':True,'recorded_cgroup_absent':True,'selected_recorded_pids_absent':True,'original_cleanup_stop_returncode':5,'lifetime_pid_history_complete':False},'evidence':dict(sorted(ev.items())),'checks':{'source':178,'inputs':35,'runtime':7,'raw_stats':232,'complete_cells':2,'payloads':6,'same_pass_headers':5,'raw_daily_body_reads':0},'qualification':'Actual graph/source completion only. One six-body streaming hash pass; five headers captured in same pass. No numerical value decode, feature/MCM/training/financial completion, remote preservation or future storage release inferred.'}
(O/'OUTCOME_REVIEW01.json').write_text(json.dumps(review,sort_keys=True,indent=2)+'\n');print(json.dumps({'review_sha256':digest(O/'OUTCOME_REVIEW01.json'),'body_sha256':digest(O/'BODY_HASH01.json'),'evidence_count':len(ev)}))
