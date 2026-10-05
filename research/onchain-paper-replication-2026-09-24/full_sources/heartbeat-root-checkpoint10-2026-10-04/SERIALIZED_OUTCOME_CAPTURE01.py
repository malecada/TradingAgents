"""Exact new closed continuation bytes; accepted immutable bases/sharder reused."""
from pathlib import Path
import hashlib,json,os,stat,sys,time,resource,importlib.util
root=Path.cwd();F=root/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-serialized-storage-root-launch-20261005-01');i='financial-wrapper-classification-eager-continue100-serialized-storage-successor-20261005-01';source='6b07c0f841e7d38102814aabb335751fd71fb7f7';review=F/'financial-wrapper-serialized-storage-binding-review01-2026-10-05';outcome=F/'financial-wrapper-serialized-continuation-outcome-review01-2026-10-05';out=F/'financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05';tool=F/'financial-wrapper-compatibility-complete100-outcome-capture-preparation03-2026-10-05'
assert hashlib.sha256((tool/'capture01.py').read_bytes()).hexdigest()=='d8b61b8bc45e69da0df50bfa4694c0c0d103aaa5dce6668fccd0686c275958bb'
for n,h in {'recovery_pax01.py':'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():assert hashlib.sha256((tool/'utilities'/n).read_bytes()).hexdigest()==h
spec=importlib.util.spec_from_file_location('accepted_opaque_sharder',tool/'capture01.py');S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S);R=S.R;resource.setrlimit(resource.RLIMIT_FSIZE,(R.FILE,R.FILE));start=time.monotonic();assert not out.exists();S.boundary(start,128*1024**2)
assert R.digest(R.read(outcome,'OUTCOME_CHECK01.json'))=='35620dcd8b86f48656f6057c9df73765fa04908a97e42260c87d2519b9f9916c';assert R.digest(R.read(outcome,'TERMINAL_RAW_INDEX01.json'))=='e28b41f729a8b588bcaf15855ac27acae1c333bb8ae68ae8c9f75a3ed2db0c48'
assert R.digest(R.read(C,'SERIALIZED_NUMERICAL_ROOT_EXIT01.json'))=='5eba29296ef6cde7721dedb0bd37b3bc1dfa332ad71d42d078686bdef5da8707'
assert R.digest(R.read(CAP/'research_runs'/i,'claim.json'))=='2dd47f07f3ad3e250ff2e668a8e1a62d88f450635c056c2391cba0d27f9064ea';assert R.digest(R.read(CAP/'research_runs'/i,'complete.json'))=='da8548ec714e0c47b0b6ad82eb5e994b9630b7c765a118cb7c83922bdeaccec9' and not (CAP/'research_runs'/i/'failed.json').exists()
terminal=json.loads(R.read(P/'attempt','parent-terminal.json'));cleanup=json.loads(R.read(P/'attempt','owned-tree-cleanup.json'));assert terminal['actual_parent_exit'] is None and terminal['actual_child_exit']==0 and terminal['cleanup']['cgroup_absent'];assert not os.path.lexists(terminal['cleanup']['cgroup'])
for rec in cleanup['owned_pid_start_records']:
 proc=Path('/proc')/str(rec['pid'])
 if proc.exists():assert int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])!=rec['ticks']
basis=review/'FULL_CURRENT_RECOVERY_PROOF01.json';assert R.digest(R.read(review,basis.name))=='3aef2b627c679d753a43b7055ea412fcf55a34b3e51d82afbe666c6c45a245b9';oldraw=R.read(F/'financial-wrapper-serialized-storage-current-capture01-2026-10-05/snapshot','COMPOSITION01.json');assert R.digest(oldraw)=='c64ea59653e5acca064b21c2e0d4a9f93718fc9f82c923d3fbe7d045136daa4b';old=json.loads(oldraw)
assert R.digest(R.read(review,'FINAL_ENVELOPE_RECOVERY_CHECK01.json'))=='40a2e5ab80678acdd391230e9f639a393f42067ec01aec7e656d3d54e825347b'
def metadata(base,omit_git=False):
 rows=[];deadline=time.monotonic()+10
 for current,dirs,files in os.walk(base):
  assert time.monotonic()<deadline and len(rows)<4096
  if Path(current)==base and omit_git:dirs[:]=[n for n in dirs if n!='.git']
  for name in sorted(dirs+files):
   p=Path(current)/name;s=p.lstat();assert p.resolve()==p and (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode));row={'path':p.relative_to(base).as_posix(),'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file','mode':stat.S_IMODE(s.st_mode)}
   if row['kind']=='file':assert s.st_nlink==1 and s.st_size<=R.FILE;row['bytes']=s.st_size
   rows.append(row)
 return sorted(rows,key=lambda v:v['path'])
known={r['path']:r for r in old['capsule']['members']};before=metadata(CAP,True);actual={r['path']:r for r in before};assert set(known)<=set(actual) and stat.S_IMODE(CAP.lstat().st_mode)==old['capsule']['root_mode']
for n,row in known.items():assert actual[n]=={k:v for k,v in row.items() if k!='sha256'}
new=set(actual)-set(known);prefixes=('research_runs/'+i,'research_artifacts/onchain-paper-replication-2026-09-24/runs/'+i,'research_artifacts/financial_wrapper_engineering/'+i,'research_artifacts/onchain_fit_cells/a6079f0a1e103f77815d4bfa98a8479fa719ea55a658a662cf0a16e6e579f381/'+i);assert sum(actual[n]['kind']=='file' for n in new)==325 and all(any(n==p or n.startswith(p+'/') for p in prefixes) for n in new)
assert sum(n.endswith('/state.pt') and n.startswith(prefixes[3]+'/checkpoints/') for n in new)==99
gitbefore=metadata(CAP/'.git');assert gitbefore==[{k:v for k,v in r.items() if k!='sha256'} for r in old['scopes']['Git']['manifest']['members']]
head=R.read(CAP/'.git','HEAD').decode().strip();assert head.startswith('ref: ') and R.read(CAP/'.git',head[5:]).decode().strip()==source
pk={r['path']:r for r in old['scopes']['Parent']['manifest']['members']};direct=json.loads(R.read(F/'financial-wrapper-serialized-storage-final-direct01-2026-10-05','FINAL_TYPED_SCOPE01.json'));final=next(v for v in direct['original_members'] if v['original_path']==str(P/'REQUEST_FINAL01.json'));pk['REQUEST_FINAL01.json']={k:final[k] for k in ('kind','mode','bytes','sha256')}|{'path':'REQUEST_FINAL01.json'};pbefore=metadata(P);pa={r['path']:r for r in pbefore};assert set(pk)<=set(pa)
for n,row in pk.items():assert pa[n]=={k:v for k,v in row.items() if k!='sha256'}
pnew=set(pa)-set(pk);assert pnew and all(n=='attempt' or n.startswith('attempt/') for n in pnew)
out.mkdir(mode=0o700);snapshot=out/'new-bodies';snapshot.mkdir(mode=0o700);mapped={};total=0

def save(label,b):
 global total
 assert label not in mapped and len(b)<=S.GROUP;total+=len(b);assert total<S.RAW;leaf='body-%04d.bin'%len(mapped);S.write(snapshot/leaf,b,start);mapped[label]={'flat':leaf,'bytes':len(b),'sha256':R.digest(b)}
capcurrent=[]
for row in before:
 n=row['path']
 if row['kind']=='file' and n in new:
  b=R.read(CAP,n);assert len(b)==row['bytes'];save('CAP/'+n,b);capcurrent.append(dict(row,sha256=R.digest(b)))
 else:capcurrent.append(known.get(n,row))
pc=[]
for row in pbefore:
 n=row['path']
 if row['kind']=='file' and n in pnew:
  b=R.read(P,n);assert len(b)==row['bytes'];save('Parent/'+n,b);pc.append(dict(row,sha256=R.digest(b)))
 else:pc.append(pk.get(n,row))
closed=R.scan(review)
for row in closed['members']:
 if row['kind']=='file':save('closed-preparation-review/'+row['path'],R.read(review,row['path']))
phase=('LIVE_SAMPLE01.json','CLAIM_CHECK01.json','TERMINAL_RAW_INDEX01.json','OUTCOME_CHECK01.json');phasepins={n:R.digest(R.read(outcome,n)) for n in phase}
for n in phase:save('outcome-phase/'+n,R.read(outcome,n))
rootnames=('SERIALIZED_NUMERICAL_ROOT01.stdout','SERIALIZED_NUMERICAL_ROOT01.stderr','SERIALIZED_NUMERICAL_ROOT_EXIT01.json','SERIALIZED_GENUINE_CLAIM_OBSERVED01.json','SERIALIZED_FULL_PREFLIGHT01.json','SERIALIZED_FULL_PREFLIGHT01.stdout','SERIALIZED_FULL_PREFLIGHT01.stderr','SERIALIZED_FRESH_ELIGIBILITY01.json','SERIALIZED_OUTCOME_CAPTURE01.py')
for n in rootnames:save('Root/'+n,R.read(C,n))
composition={'schema_version':1,'kind':'closed-continuation-actual-byte-increment','identity':i,'source':source,'basis':{'path':str(basis),'sha256':'3aef2b627c679d753a43b7055ea412fcf55a34b3e51d82afbe666c6c45a245b9'},'final_envelope_basis':{'path':str(review/'FINAL_ENVELOPE_RECOVERY_CHECK01.json'),'sha256':'40a2e5ab80678acdd391230e9f639a393f42067ec01aec7e656d3d54e825347b'},'capsule':{'schema_version':1,'root_mode':old['capsule']['root_mode'],'members':capcurrent},'Parent':{'root':str(P),'manifest':{'schema_version':1,'root_mode':old['scopes']['Parent']['manifest']['root_mode'],'members':pc}},'Git':old['scopes']['Git'],'Git_logical_objects':454,'closed_preparation_review':{'root':str(review),'manifest':closed},'outcome_phase':{'root':str(outcome),'exact_files':phasepins},'materialized':mapped,'accepted_unchanged_CAP_regular_reused':856,'accepted_unchanged_Parent_regular_reused':12,'accepted_unchanged_Git_regular_reused':479,'all99_checkpoint_states_included':True,'original_parent_exit':None,'actual_Root_exit':0,'actual_child_exit':0,'native_PID_history_complete':False,'numerical_updates':99,'paper_financial_fits':0,'POSIX_reconstruction':False,'installed_runtime_body_recovery':False,'immutable_writer_exclusion':False,'external_recovery':None,'qualification':'Complete retained CAP/Git/Parent byte scope through accepted current and final direct byte bases plus every new case-owned body, all99opaque epoch checkpoints, fixed genuine review and Root records. No unchanged empirical-store recopy, numerical rerun, fabricated original null or full-size capacity claim.'}
R.put(snapshot/'COMPOSITION01.json',composition);assert before==metadata(CAP,True) and pbefore==metadata(P) and gitbefore==metadata(CAP/'.git');R.same(review,closed);assert all(R.digest(R.read(outcome,n))==pin for n,pin in phasepins.items());result=S.capture({'increment':snapshot},out/'shards',start);assert before==metadata(CAP,True) and pbefore==metadata(P) and gitbefore==metadata(CAP/'.git');R.same(review,closed);assert all(R.digest(R.read(outcome,n))==pin for n,pin in phasepins.items())
R.put(out/'INCREMENT01.json',{'schema_version':1,'identity':i,'source':source,'basis':composition['basis'],'final_envelope_basis':composition['final_envelope_basis'],'new_original_bodies':len(mapped),'new_original_bytes':total,'new_CAP_regular':325,'CAP_regular':sum(r['kind']=='file' for r in capcurrent),'CAP_typed':len(capcurrent),'Parent_regular':sum(r['kind']=='file' for r in pc),'piece_count':len(result['pieces']),'shard_capture_sha256':R.digest(R.read(out/'shards','CAPTURE01.json')),'all99_checkpoint_states_included':True,'external_recovery':False,'qualification':composition['qualification']});print(json.dumps({'status':'ACTUAL_TERMINAL_INCREMENT_CAPTURED_ONCE','bodies':len(mapped),'bytes':total,'pieces':len(result['pieces'])}))
