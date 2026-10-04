from pathlib import Path
import json,hashlib,os,stat,ast
O=Path(__file__).resolve().parent;F=O.parent;T=F/'financial-wrapper-compatibility-operational-delta-root-remote02-2026-10-04';h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
def scan():
 rows=[]
 for p in [T]+sorted(T.rglob('*')):
  s=p.lstat();x={'path':'.' if p==T else p.relative_to(T).as_posix(),'mode':stat.S_IMODE(s.st_mode),'allocated_bytes':s.st_blocks*512}
  if stat.S_ISDIR(s.st_mode):x['kind']='directory'
  else:
   assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and p.resolve()==p;b=p.read_bytes();x.update(kind='file',bytes=len(b),sha256=h(b))
  rows.append(x)
 return rows
before=scan();failed=J(T/'FAILED01.json');assert h((T/'FAILED01.json').read_bytes())=='7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a';exit=J(T/'ROOT_REMOTE02_EXIT01.json');intent=J(T/'ROOT_REMOTE02_INTENT01.json');spawn=J(T/'ROOT_REMOTE02_SPAWN01.json');assert exit['actual_outer_exit']==1 and exit['actual_child_pid']==spawn['pid'];assert failed['status']=='failed-original-attempt' and failed['genuine_run_or_native_started'] is False
for stream in ['stdout','stderr']:
 b=(T/('ROOT_REMOTE02.'+stream)).read_bytes();assert len(b)==exit[stream+'_bytes'] and h(b)==exit[stream+'_sha256']
err=(T/'ROOT_REMOTE02.stderr').read_text();assert "elif now!=s:raise ChangingTree" in err and 'no complete census in three bounded attempts' in err
review=F/'financial-wrapper-compatibility-operational-delta-entry-review02-2026-10-04';assert h((review/'MACHINE01.json').read_bytes())==intent['entry_review_sha256'];release=J(review/'MACHINE01.json');assert h((T/'recover01.py').read_bytes())==release['remote_helper_sha256'] and h((T/'SELECTED_BODIES01.json').read_bytes())==release['selection_sha256']==intent['selection_sha256']
initial=J(review/'READBACK01.json')
for x in initial['installed']:
 p=T/x['path'];assert stat.S_IMODE(p.stat().st_mode)==x['mode'] and h(p.read_bytes())==x['sha256']
ops=failed['operations'];assert [x['operation'] for x in ops]==['remote','ls-remote','init'];assert [x['exit'] for x in ops]==[0,0,None];assert all(x['actual_reaped_exit']==0 and x['cleanup_failures']==[] and x['actual_child_limits']=={'pid':x['pid'],'fsize':[4194304,4194304]} for x in ops)
obs=failed['whole_tree_observations'];assert len(obs)==26 and failed['initial_owned_allocation']==obs[0]
for x in obs:assert x['logical_bytes']<=67108864 and x['allocated_bytes']<=100663296 and x['members']<=32768 and x['seconds']<5
pids=[intent['parent_pid'],spawn['pid']]+[x['pid'] for x in ops];absence=[]
for pid in pids:
 assert not Path('/proc',str(pid)).exists();pg=None
 try:os.killpg(pid,0)
 except ProcessLookupError:pg='absent'
 except PermissionError:pg='exists-not-permitted'
 else:pg='exists'
 if pid in [x['pid'] for x in ops]:assert pg=='absent'
 absence.append({'pid':pid,'current_proc_absent':True,'same_numeric_group_current':pg,'historical_startticks':None})
for n in ['selected','REMOTE_RECOVERY01.json','flat-operational-delta01','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json']:assert not os.path.lexists(T/n)
assert (T/'fresh-operational-source-policy01.git').is_dir();assert not list((T/'fresh-operational-source-policy01.git/objects').glob('*/*'))
source=(T/'watch01.py').read_text();assert "for attempt in range(3):" in source and "elif now!=s:raise ChangingTree" in source;assert h(source.encode())=='cd2200b071cf14c8191c7b7e95ee660b6bc9a10c49a6de252e77f9832ede8673'
assert scan()==before
(O/'FAILED_ROOT_SCOPE01.json').write_text(json.dumps({'schema_version':1,'root':str(T),'members':before,'logical_bytes':sum(x.get('bytes',0) for x in before),'allocated_bytes':sum(x['allocated_bytes'] for x in before),'qualified':'Complete current closed-tree sampled readback, not an external backup.'},indent=2)+'\n')
for n in ['FAILED01.json','ROOT_REMOTE02_EXIT01.json','ROOT_REMOTE02_INTENT01.json','ROOT_REMOTE02_SPAWN01.json','ROOT_REMOTE02.stdout','ROOT_REMOTE02.stderr']:(O/n).write_bytes((T/n).read_bytes())
r={'schema_version':1,'decision':'VERIFIED_PERMANENT_FAILED_FORENSIC_REMOTE_ATTEMPT','failed_receipt_sha256':h((T/'FAILED01.json').read_bytes()),'release_sha256':intent['entry_review_sha256'],'actual_root_exit':exit,'original_operation_observed_exits':[x['exit'] for x in ops],'separate_actual_reaped_exits':[x['actual_reaped_exit'] for x in ops],'current_pid_group_observations':absence,'actual_samples':26,'scope_members':len(before),'scope_regular':sum(x['kind']=='file' for x in before),'source_failure_branch':'whole directory signature mismatch followed by three bounded census attempts exhausted','historical_changed_path':None,'historical_changed_signature_component':None,'selected_external_body_count':0,'remote_success_receipt':None,'flat_outcome':None,'native_or_claim':False,'eligibility':'No reuse; successor source/namespace/entry review required'};(O/'READBACK01.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS failed closed scope and actual exits/nulls/current process absence',len(before))
