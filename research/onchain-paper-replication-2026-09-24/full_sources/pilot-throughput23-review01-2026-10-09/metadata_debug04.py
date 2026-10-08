import json,hashlib,subprocess,os,resource,signal,copy
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(60)
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;N=F/'real-data-pilot-final23-2026-10-09';O=F/'real-data-pilot-final22-2026-10-08';ev={};checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):ev[str(p.relative_to(R))]=sha(p);return json.loads(p.read_bytes())
def ck(n,v):
 assert v,n
 checks.append(n)
name='eth-paper-real-data-end-to-end-resource-20261009-23';old='eth-paper-real-data-end-to-end-resource-20261008-22'
def rename(x):return json.loads(json.dumps(x).replace(old,name).replace('ethpilot-20261008-22','ethpilot-20261009-23'))
exit=read(N/'PREPARATION_EXIT02.json');pair=read(N/'templates02/pair_policy01.json');opair=read(O/'templates02/pair_policy01.json');pins=pair['numerical_source']['files'];anchor=exit['source_anchor']
ck('anchor',anchor=='f29c6177d2beae01bd7ffff499fe014f3adf3714'==pair['numerical_source']['commit'])
ck('181_same_source_paths',len(pins)==181 and pins.keys()==opair['numerical_source']['files'].keys())
changed={p:{'before':opair['numerical_source']['files'][p],'after':h} for p,h in pins.items() if opair['numerical_source']['files'][p]!=h}
ck('exact_four_changed_sources',changed==exit['changed_source_pins'] and len(changed)==4)
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0');raw=subprocess.check_output(['git','-c','core.packedGitWindowSize=1m','-c','core.packedGitLimit=16m','cat-file','--batch'],input=''.join(anchor+':'+p+'\n' for p in pins).encode(),env=env);offset=0
for p,h in pins.items():
 end=raw.index(b'\n',offset);head=raw[offset:end].split();assert head[1]==b'blob';size=int(head[2]);offset=end+1
 assert hashlib.sha256(raw[offset:offset+size]).hexdigest()==h==sha(R/p);offset+=size+1
ck('181_current_and_committed_bodies',offset==len(raw))
a=copy.deepcopy(pair);a['numerical_source']=opair['numerical_source'];ck('all_pair_numeric_policy_unchanged',a==opair)
for fn in ['job_template01.json','pilot.json','archive_policy.json','producer_plan.json']:
 prev=rename(read(O/'templates02'/fn));now=read(N/'templates02'/fn)
 if fn=='job_template01.json':next(iter(prev['payload']['representation_jobs'].values()))['descriptor']['pair_execution']['policy_sha256']=sha(N/'templates02/pair_policy01.json')
 if fn=='producer_plan.json':
  for producer in prev['producers'].values():producer['descriptor']['pair_execution']['policy_sha256']=sha(N/'templates02/pair_policy01.json')
 ck('template_full_inverse_'+fn,prev==now)
d=read(N/'INPUT_DRAFT02.json');od=read(O/'INPUT_DRAFT02.json');baseline=read(N/'BASELINE02.json');ob=baseline['result']['observation'];expected=copy.deepcopy(od)
for role,fn in [('pair_policy','pair_policy01.json'),('execution_job','job_template01.json'),('pilot','pilot.json'),('archive_policy','archive_policy.json'),('producer_plan','producer_plan.json')]:
 p=N/'templates02'/fn;ref={'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size};expected['protocol']['references'][role]=ref
expected['protocol']['transport_limits']['namespace']='ethpilot-20261009-23';p=N/'BASELINE02.json';expected['protocol']['physical_baseline']={'evidence':{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size},'logical_bytes':ob['logical_file_bytes'],'allocated_bytes':ob['allocated_bytes'],'entries':ob['entries']}
ck('draft_full_inverse_original_graphs_and_policy',d==expected)
prepared=read(N/'PREPARATION_RESULT02.json');previous=rename(read(O/'PREPARATION_RESULT02.json'))
# Reference replacement and only declared physical baseline deltas; all other result fields must coincide.
replacements={}
for role in ['pair_policy','execution_job','pilot','archive_policy','producer_plan']:
 a=od['protocol']['references'][role];b=d['protocol']['references'][role]
 for k in ['path','sha256']:replacements[a[k]]=b[k]
a=od['protocol']['physical_baseline']['evidence'];b=d['protocol']['physical_baseline']['evidence']
for k in ['path','sha256']:replacements[a[k]]=b[k]
def rewrite(x):
 if isinstance(x,dict):return {k:rewrite(v) for k,v in x.items()}
 if isinstance(x,list):return [rewrite(v) for v in x]
 return replacements.get(x,x) if isinstance(x,str) else x
previous=rewrite(previous)
for loc in [previous['builder03_spec']['physical_store'],previous['builder03_result']['physical_store_declaration']]:
 loc['baseline_logical_bytes']=ob['logical_file_bytes'];loc['baseline_allocated_bytes']=ob['allocated_bytes']
oldbase=od['protocol']['physical_baseline']
for k,bkey in [('logical_bytes','logical_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries')]:previous['inventory']['total_with_declared_baseline'][k]+=d['protocol']['physical_baseline'][bkey]-oldbase[bkey]

def diff(a,b,p=''):
 if type(a)!=type(b): print(p,'TYPE');return
 if isinstance(a,dict):
  for k in a.keys()|b.keys():
   if k not in a or k not in b:print(p+'/'+k,'MISSING')
   else:diff(a[k],b[k],p+'/'+k)
 elif isinstance(a,list):
  if a!=b:print(p,'LIST')
 elif a!=b:print(p,repr(a),repr(b))
diff(prepared,previous)
