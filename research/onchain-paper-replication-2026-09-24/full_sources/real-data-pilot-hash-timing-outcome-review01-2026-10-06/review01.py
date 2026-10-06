"""Bounded engineering timing outcome; accepted increment checks reused, no numerical imports."""
from pathlib import Path
import hashlib,json,stat
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
H=F/'real-data-pilot-hash-timing-outcome-review01-2026-10-06';D=F/'real-data-pilot-hash-timing01-2026-10-06'
N='eth-real-graph-canonical-hash-timing-20261006-01';SOURCE='3da4749fc5b4a131f5cc740e423a6cefddfc0966'
P=Path('research_artifacts/onchain-paper-replication-2026-09-24');A=P/'hash-timing'/N
cache={}
def raw(p):
 p=Path(p)
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
  cache[p]=b
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):
 assert Path(p).name!='resource-population.json'
 return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(n,v):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(v,sort_keys=True,indent=2)+'\n')
 return p
files=[];directories=[]
for p in sorted([A,*A.rglob('*')]):
 s=p.lstat();assert (R/p).resolve(strict=True)==R/p and not stat.S_ISLNK(s.st_mode)
 if stat.S_ISDIR(s.st_mode):directories.append({'path':str(p),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
 else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;files.append(p)
dynamic=('ROOT_LAUNCH01.json','ROOT_ACTIVE01.json','ROOT_TERMINAL01.json');files.extend(D/n for n in dynamic)
assert len(files)==len(set(files))==16 and len(directories)==2
rows=[]
for p in sorted(files):
 b=raw(p);s=p.lstat();rows.append({'path':str(p),'kind':'regular','bytes':len(b),'sha256':sha(p),'mode':stat.S_IMODE(s.st_mode),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
c=read(D/'registration01.json');claim=read(A/'claim.json');result=read(A/'result.json');terminal=read(A/'terminal.json');root=read(D/'ROOT_TERMINAL01.json');launch=read(D/'ROOT_LAUNCH01.json');guard=read(A/'guard/final.json')
assert claim['identity']==result['identity']==terminal['identity']==root['identity']==c['identity']==N
assert claim['source']==launch['source']==SOURCE and c['allowance']==claim['allowance']==1 and c['prior_attempts']==0
assert c['paper_budget_credit'] is False and c['scientific_owner'] is None and claim['scientific_owner'] is None and terminal['scientific_owner'] is None
assert all(v['financial_credit'] is False for v in (claim,result,terminal))
assert sha(D/'registration01.json')==claim['registration']==launch['registration_sha256']=='9416dd15be3272fec10966a3aedda0f45b54556f23ee96a32961864a7524ba85'
assert sha(D/'profile.py')==launch['profile_sha256']=='7220a65eb32cc3103e855ba8c9acfd3a7e3f2b6f5fc4bacd436322151fa56bbc'
assert sha(launch['review']['path'])==launch['review']['sha256']==claim['review']
entry=read(launch['review']['path']);assert entry['decision']=='accepted' and entry['registration_sha256']==claim['registration'] and entry['profile_sha256']==launch['profile_sha256']
assert sha(c['candidate']['path'])==c['candidate']['sha256']
assert result['graph']==c['graph'] and result['graph']['payload_bytes']==sum(v['bytes'] for v in c['graph']['arrays'].values())==604276056
assert len(c['all_graph_manifest_denominators'])==7 and max(v['payload_bytes'] for v in c['all_graph_manifest_denominators'])==604276056
phases=[read(A/f'phase{i:02d}.json') for i in range(1,5)]
assert phases==result['measurements']==root['cells'] and [p['phase'] for p in phases]==c['cells']
assert [p['seconds'] for p in phases]==[50.70451907900042,46.867963153000346,22.086420933000227,1.0327307670004302]
for p in phases[1:3]:
 assert p['matches'] is True and p['digest']==p['expected']==c['graph']['graph_hash']=='0e60be7088611cebfd04839fcc7bb4aa4fdd05a28d84e27aeaf9456391997459'
 assert p['payload_bytes']==604276056 and p['payload_bytes_per_second']==604276056/p['seconds']
assert len(phases[3]['digest'])==64 and result['nodes']==2265481 and result['edges']==3149567 and result['original_metadata_unchanged'] is True
assert sha(A/'result.json')==root['result_sha256']=='9d70dff2c1d10bd8e766f3e3ff3b7dff3529e035cbdf59a5590297d36d09925e'
assert sha(A/'guard/final.json')==root['guard_sha256']=='f4102dd413e098e8cbbf18fa899f2b17a1874b0977064702800d56172701b1c4'
assert terminal['disposition']=='COMPLETE' and terminal['guard']==guard and guard['phase']=='complete'
assert root['root_session']==56486 and root['root_terminal_chunk']=='c5a498' and root['root_exit']==root['native_child_exit']==guard['child_exit_code']==0
assert root['native_elapsed_seconds']==guard['elapsed_seconds']==121.27021315500042
assert root['cleanup_verified'] and guard['cleanup_verified'] and guard['cleanup_stop_returncode']==5 and guard['owner_identity'] is None and guard['limit_reason'] is None
assert guard['memory_max_bytes']==guard['memory_high_bytes']==c['limits']['memory_max_bytes']==3221225472 and guard['memory_swap_max_bytes']==0
assert all(v==0 for v in guard['memory_events'].values()) and root['current_cgroup_absent'] and not Path(guard['cgroup']).exists()
assert root['current_unit_properties']['MainPID']=='0' and root['current_unit_properties']['ControlGroup']=='' and root['current_unit_properties']['Result']=='success'
assert not (A/'worker-failed.json').exists() and not (A/'parent-failed.json').exists()
pids=set()
def collect(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if (k=='pid' or k.endswith('_pid')) and type(x) is int and x>0:pids.add(x)
   else:collect(x)
 elif isinstance(v,list):
  for x in v:collect(x)
for v in (guard,read(A/'guard/child_exit.json'),read(A/'guard/cpu_ready.json')):collect(v)
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
# Current file sizes/identity only; no graph/array body read or rerun.
current_graph_stats=[]
manifest=Path(c['graph']['path'])
for p,size in [(manifest,None)]+[(manifest.parent/v['path'],v['bytes']) for v in c['graph']['arrays'].values()]:
 s=p.lstat();assert (R/p).resolve(strict=True)==R/p and stat.S_ISREG(s.st_mode) and s.st_nlink==1
 if size is not None:assert s.st_size==size
 current_graph_stats.append({'path':str(p),'bytes':s.st_size,'mode':stat.S_IMODE(s.st_mode),'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
selection={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,'files':rows,'directories':directories,'regular_count':len(rows),'directory_count':len(directories),'original_regular_bytes':sum(r['bytes'] for r in rows),'dynamic_entry_records':[str(D/n) for n in dynamic],'scope':'All public actual engineering output files and guard receipts, including empty child log; three Root launch/active/terminal records; typed directories.','exclusions':['Already committed registration/source/runtime-check/entry review bodies','Graph manifests and numeric arrays; all historical/scientific/raw/private/runtime bodies','Shared parent directories outside output root'],'qualification':'Exact public increment only; original bodies retained. Capture and external recovery not yet reviewed; no deletion or execution authorization.'}
bp=write('INCREMENT_SELECTION01.json',selection)
outcome={'schema_version':1,'decision':'accepted','identity':N,'source':SOURCE,'increment_selection':ref(bp),'evidence':{str(p):sha(p) for p in sorted(files)},'registration':ref(D/'registration01.json'),'profile':ref(D/'profile.py'),'entry_review':ref(launch['review']['path']),'candidate':ref(c['candidate']['path']),'scope':'Independent public evidence authentication of one COMPLETE engineering timing profile, no numerical rerun.','denominator':{'registered_phases':4,'retained_phases':4,'graph_selection':'Largest retained payload among seven registered manifest descriptors; one actual graph measured','nodes':result['nodes'],'edges':result['edges'],'payload_bytes':604276056,'financial_credit':False,'scientific_owner':None},'measurements':phases,'statistics':{'observed_legacy_to_candidate_ratio':phases[1]['seconds']/phases[2]['seconds'],'observed_wall_seconds_saved':phases[1]['seconds']-phases[2]['seconds'],'qualification':'Single warm serial observations, not replication, cold performance, uncertainty estimate or seven-graph extrapolation. Payload throughput denominator is original NPY file bytes including headers, not JSON bytes.'},'native':{'root_session':56486,'root_terminal_chunk':'c5a498','root_exit':0,'child_exit':0,'seconds':guard['elapsed_seconds'],'cleanup_verified':True,'original_cleanup_stop_returncode':5,'memory_events':guard['memory_events'],'last_cache_inclusive_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},'current_cleanup':{'selected_pid_exists':{str(pid):False for pid in sorted(pids)},'cgroup_absent':True,'lifetime_process_history':None},'current_graph_stat_only':current_graph_stats,'metadata_limit':'During-run before/after equality is the worker-recorded assertion, not an independently reconstructed prior stat snapshot. Current sizes/type verified without any array bytes.','disposition':'Engineering identity permanently COMPLETE; allowance consumed, no relaunch or paper/scientific credit. Original07 failure remains unchanged.','not_tested':['No arrays, graph bodies, original manifests, private/runtime bodies, numerical imports or timing rerun.','Candidate algorithm generality, broad source closure, cold speed, uncertainty, seven-graph lease/callback capacity, pilot eligibility, MCM/training or finance.','External recovery and POSIX reconstruction remain pending.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'selection':ref(bp),'manifest':ref(mp),'regulars':len(rows),'directories':len(directories),'bytes':selection['original_regular_bytes'],'decision':'accepted'},sort_keys=True))
