"""Finite recovered-byte inspection; never launches, admits, loads tensors or edits outcomes.
The closure adapter is NEW external Root evidence, not an original receipt field.
Caller must independently pin its hash. It grants no research authority.
"""
import argparse,hashlib,json,os,stat,time
from pathlib import Path
import recovery04 as R
QHASH='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc'
REASON='prospective engineering failed-parent fixture after one real update; no fit completion'
TOTAL=1024**3;COUNT=32768;SECONDS=120
require=R.require;sha=R.digest

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def decoded(raw):
 def unique(pairs):
  d={}
  for k,v in pairs:require(k not in d,'duplicate JSON key');d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def hashed(v):require(type(v)is str and len(v)==64 and all(c in '0123456789abcdef' for c in v),'sha256');return v

def inventory(root):
 root=Path(root);R.path_name(str(root).lstrip('/'));require(root.is_absolute() and root.resolve()==root,'canonical recovered root');rootstat=root.lstat();require(stat.S_ISDIR(rootstat.st_mode),'root directory');rows=[];total=0;deadline=time.monotonic()+SECONDS
 def visit(p,rel):
  nonlocal total
  fd=None;iterator=None
  try:
   require(time.monotonic()<deadline,'inventory deadline');fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);pin=R.sig(os.fstat(fd));iterator=os.scandir(fd);names=[]
   for entry in iterator:
    names.append(entry.name);require(len(names)+len(rows)<=COUNT,'entry ceiling')
   for name in sorted(names):
    n=R.path_name(name if not rel else rel+'/'+name);s=(root/n).lstat();require(s.st_dev==rootstat.st_dev and (root/n).resolve()==root/n,'redirect/device');row={'path':n,'mode':stat.S_IMODE(s.st_mode)}
    require(len(rows)<COUNT and time.monotonic()<deadline,'finite inventory')
    if stat.S_ISDIR(s.st_mode):row['kind']='directory';rows.append(row);visit(root/n,n)
    else:
     raw=R.read(root,n);require(R.sig((root/n).lstat())==R.sig(s),'changed file');total+=len(raw);require(total<=TOTAL,'whole reservation');row.update(kind='file',bytes=len(raw),sha256=sha(raw));rows.append(row)
   require(R.sig(p.lstat())==pin==R.sig(os.fstat(fd)) and p.resolve()==p,'changed directory')
  finally:R._cleanup((() if iterator is None else (iterator.close,))+(() if fd is None else (lambda:os.close(fd),)))
 visit(root,'');return {'root_mode':stat.S_IMODE(rootstat.st_mode),'members':sorted(rows,key=lambda r:r['path'])}

class Tree:
 def __init__(self,root):
  self.root=Path(root);self.inventory=inventory(self.root);self.rows={r['path']:r for r in self.inventory['members']}
 def raw(self,n,pin=None):
  R.path_name(n);require(n in self.rows and self.rows[n]['kind']=='file','missing regular member '+n);b=R.read(self.root,n);require(sha(b)==self.rows[n]['sha256'],'inventory changed');require(pin is None or sha(b)==hashed(pin),'body hash '+n);return b
 def value(self,n,pin=None):return decoded(self.raw(n,pin))
 def absent(self,n):R.path_name(n);return n not in self.rows
 def close_check(self):require(inventory(self.root)==self.inventory,'outcome tree changed')

def classify(*,claim_present,planned_bytes,cleanup_proved,predispatch_proved):
 require(all(type(x)is bool for x in (claim_present,planned_bytes,cleanup_proved,predispatch_proved)),'typed disposition inputs')
 if not cleanup_proved:return 'CLEANUP_UNCERTAIN'
 if not claim_present:return 'NO_CLAIM_PREDISPATCH_REFUSAL' if predispatch_proved else 'UNEXPECTED_FAILURE_NO_CLAIM'
 return 'PLANNED_FAILED_SPENT_INTERRUPT1_BYTES' if planned_bytes else 'UNEXPECTED_FAILURE_SPENT'

def cursor_manifest(m,prov,state_raw):
 require(set(m)=={'schema_version','key','provenance','members'} and type(m['schema_version'])is int and m['schema_version']==1,'checkpoint manifest fields')
 require(m['provenance']==prov and m['key']==sha(canonical({'provenance':prov,'epoch':1,'batch':0})),'checkpoint expected cursor-key/provenance')
 require(m['members']=={'state.pt':{'sha256':sha(state_raw),'size':len(state_raw)}},'opaque checkpoint exact member');return m['key']

def external_context(v,pin,cap,par,identity):
 # Explicit new adapter; actual Root observations must be supplied separately.
 require(sha(v)==hashed(pin),'external observation pin');q=decoded(v)
 require(set(q)=={'schema_version','kind','identity','capsule_inventory_sha256','parent_inventory_sha256','actual_parent_exit','process_observation','source_claim_review'},'Root observation adapter fields')
 require(type(q['schema_version'])is int and q['schema_version']==1 and q['kind']=='root-financial-first-outcome-observation-v1' and q['identity']==identity,'Root observation adapter identity')
 require(q['capsule_inventory_sha256']==sha(canonical(cap.inventory)) and q['parent_inventory_sha256']==sha(canonical(par.inventory)),'complete recovery inventory join')
 require(q['actual_parent_exit'] is None or type(q['actual_parent_exit'])is int,'actual separately observed parent exit')
 for role in ('process_observation','source_claim_review'):
  ref=q[role]
  require(ref is None or type(ref)is dict and set(ref)=={'path','sha256'},'separate evidence ref')
  if ref is not None:par.raw(ref['path'],hashed(ref['sha256']))
 return q

def pid_observations(originals,observations):
 pairs=sorted(set((r['pid'],r['ticks']) for r in originals));actual=[]
 for row in observations:
  require(set(row)=={'pid','original_ticks','current_ticks'} and type(row['pid'])is int and row['pid']>0 and type(row['original_ticks'])is str,'PID observation fields')
  require(row['current_ticks'] is None or type(row['current_ticks'])is str and row['current_ticks']!=row['original_ticks'],'original PID still present')
  actual.append((row['pid'],row['original_ticks']))
 require(actual==pairs,'complete sorted original PID-start denominator')
 return True

def cleanup_observation(body,identity,parent,tree,record,par,cap,base):
 # NEW explicitly declared external observation schema, never an original receipt.
 require(set(body)=={'schema_version','kind','identity','parent_terminal_sha256','observed_at','pid_start_observations','cgroup_observation'},'process observation adapter')
 require(type(body['schema_version'])is int and body['schema_version']==1 and body['kind']=='root-pid-cgroup-absence-observation-v1' and body['identity']==identity,'process observation identity')
 require(type(body['observed_at'])is str and body['observed_at'],'observation time required')
 require(body['parent_terminal_sha256']==sha(par.raw('attempt/parent-terminal.json')),'observed terminal pin')
 require(tree['subreaper_used'] is True and tree['dedicated_no_preexisting_children'] is True and tree['remaining_original_identities']==[],'original owned drainage')
 key='owned_tree_cleanup_sha256' if record.get('source_bound_no_dispatch') is True else 'subreaper_cleanup_sha256'
 require(record[key]==sha(par.raw('attempt/owned-tree-cleanup.json')),'original cleanup body pin')
 originals=tree['owned_pid_start_records']+record.get('native_pid_start_records',[])
 pid_observations(originals,body['pid_start_observations'])
 pairs=sorted(set((r['pid'],r['ticks']) for r in originals))
 if record.get('source_bound_no_dispatch') is True:
  require(body['cgroup_observation'] is None,'no invented native group')
 else:
  live=cap.value(base+'/guard/live.json');owner=cap.value(base+'/owner.json');launch=cap.value(base+'/launch.json')
  require(live['owner_identity']==owner and all(owner.get(k)==v for k,v in launch.items()),'native owner lineage')
  require((owner['monitor_pid'],str(owner['monitor_start_ticks'])) in pairs,'monitor PID-start lineage')
  require(record['unit']==live['unit'] and record['cgroup']==live['cgroup'] and record['joined_unit_stopped'] is True and record['cgroup_absent'] is True,'native closure fields')
  require(record['native_pid_census_is_complete_history'] is False,'do not inflate native PID census')
  observation=body['cgroup_observation'];require(observation=={'path':record['cgroup'],'lexists':False} and type(record['cgroup'])is str,'actual cgroup absence required')
  require(record['cgroup'].startswith('/sys/fs/cgroup/user.slice/') and Path(record['cgroup']).name==record['unit'],'native cgroup containment')
  require(set(record['actual_control_operations'])=={'before','stop','after'},'all control operations retained')
  for label,result in record['actual_control_operations'].items():
   require(result['stdout']==par.raw('attempt/'+label+'/stdout').decode('utf-8','strict') and result['stderr']==par.raw('attempt/'+label+'/stderr').decode('utf-8','replace'),'actual control raw streams')
  after=record['actual_control_operations']['after'];props=dict(line.split('=',1) for line in after['stdout'].splitlines() if '=' in line)
  require((props.get('ActiveState') in ('inactive','failed') and props.get('SubState') in ('dead','failed')) or (type(after['exit_code'])is int and after['exit_code']!=0 and not props),'native control terminal state')
 return True

def verify(cap_root,parent_root,context_bytes,context_sha256):
 cap=Tree(cap_root);par=Tree(parent_root)
 q=par.value('REQUEST_FINAL03.json',QHASH);identity=q['identity'];source=q['source'];run='research_runs/'+identity;base='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity
 require(q['expected_phase']=='interrupt1' and source==q['design_source']=='d4e56ba9ed968e9c24b2813656c2ca65a3dbd7a0','fixed first case')
 for n,h in q['source_files'].items():cap.raw(n,h)
 for n,h in {**q['helper_hashes'],'parent01.py':q['caller_sha256']}.items():par.raw(n,h)
 for ref in [*q['proofs'].values(),q['final_review']]:par.raw(str(Path(ref['path']).relative_to(q['parent_root'])),ref['sha256'])
 gate=cap.value(q['registration'],q['registration_sha256']);e=gate['experiments'][identity];inputs=e['inputs'];require(set(inputs)==set(q['input_hashes']) and len(inputs)==8,'exact eight roles')
 for role,ref in inputs.items():require(ref['sha256']==q['input_hashes'][role],'registered role hash');cap.raw(ref['path'],ref['sha256'])
 plan=cap.value(inputs['wrapper_plan']['path']);job=cap.value(inputs['execution_job']['path']);require(plan['experiment']==identity and plan['phase']=='interrupt1','plan case')
 context=external_context(context_bytes,context_sha256,cap,par,identity)
 missing=[];problems=[];planned=False;cleanup=False;predispatch=False
 terminal=None;claim=None;parent=None
 def observed(tree,n):
  if tree.absent(n):missing.append(n);return None
  return tree.value(n)
 parent=observed(par,'attempt/parent-terminal.json')
 if parent is not None:
  require(parent['identity']==identity and parent['source']==source and parent['actual_parent_exit'] is None and parent['outcome_semantics_accepted'] is False,'original parent fields/null')
  cleanup_record=observed(par,'attempt/owned-tree-cleanup.json');clean=parent['cleanup']
  if clean is not None and cleanup_record is not None and context['process_observation'] is not None:
   observation=par.value(context['process_observation']['path'],context['process_observation']['sha256'])
   cleanup=cleanup_observation(observation,identity,parent,cleanup_record,clean,par,cap,base)
  if clean is not None and clean.get('source_bound_no_dispatch') is True:
   require(all(cap.absent(base+'/guard/'+n) for n in ('live.json','final.json','cpu_ready.json','release.json','child.log')),'no-dispatch exact guard absence')
   require(clean.get('stable_absent_native_records')==['live.json','final.json','cpu_ready.json','release.json','child.log'],'source-bound no-dispatch denominator')
   predispatch=True
 if cap.absent(run+'/claim.json'):
  require(cap.absent(run+'/complete.json') and cap.absent(run+'/failed.json'),'terminal without claim')
 else:
  claim=cap.value(run+'/claim.json');require(claim['experiment_id']==identity and claim['source']==source and claim['design_source']==source and claim['registration']==q['registration'] and claim['registration_sha256']==q['registration_sha256'],'real claim source/registration')
  require(claim['schema_version']==1 and claim['bindings'] is None and claim['bindings_sha256'] is None and claim['windows']==e['windows'],'claim unbound initial windows')
  require(claim['experiment']==e and claim['program_id']==gate['program_id'] and claim['family']==gate['families'][e['family']],'claim gate/family');require(claim['effective_attempt_budget']==18 and claim['family']['prior_attempts']==0,'fixed cumulative allowance')
  require(set(claim['inputs'])==set(inputs),'resolved input roles')
  for role,ref in claim['inputs'].items():require(ref['path']==inputs[role]['path'] and ref['sha256']==inputs[role]['sha256'],'resolved claim input')
  require(cap.absent(run+'/complete.json'),'planned case may not COMPLETE')
  terminal=observed(cap,run+'/failed.json')
  if terminal is not None:
   require(terminal['status']=='failed' and terminal['experiment_id']==identity and terminal['claim_sha256']==sha(cap.raw(run+'/claim.json')),'lifecycle failed claim join')
   outputs={n.split('/')[-1]:r['sha256'] for n,r in cap.rows.items() if n.startswith(run+'/outputs/') and r['kind']=='file' and len(n[len(run+'/outputs/'):].split('/'))==1}
   require(terminal['output_sha256']==outputs,'actual retained lifecycle outputs')
  namespace='research_artifacts/financial_wrapper_engineering/'+plan['namespace'];fit='research_artifacts/onchain_fit_cells/'+sha(plan['cell_id'].encode())+'/'+identity
  diagnostic=observed(cap,namespace+'/interrupted-checkpoint.json');failure=observed(cap,namespace+'/failure.json');ff=observed(cap,fit+'/failed.json');fc=observed(cap,fit+'/claim.json')
  if all(x is not None for x in (terminal,diagnostic,failure,ff,fc)):
   prov=diagnostic['provenance'];closure=cap.value(inputs['source_closure']['path']);model=cap.value(inputs['model']['path']);training=cap.value(inputs['training']['path']);recipe=cap.value(inputs['synthetic_recipe']['path'])
   expected_prov={'source_hashes':sorted(set(closure['installed'].values())),'config_hash':sha(canonical({'model':model,'training':training,'task':plan['task'],'recipe':recipe})),'input_hash':inputs['synthetic_recipe']['sha256'],'dictionary_hash':sha(b'synthetic opaque MCM; no empirical dictionary fitted or recovered'),'fold_id':'synthetic-16x28-distinct','cell_id':plan['cell_id'],'source_commit':source}
   require(plan['execution']=='eager' and prov==expected_prov,'complete eager checkpoint provenance')
   require(cap.value(fit+'/schedule.json')=={'training':training,'seed':11,'task':plan['task'],'n_examples':16},'exact original training schedule')
   cp=str(Path(diagnostic['checkpoint']).relative_to(q['capsule_root']));require(cp.startswith(fit+'/checkpoints/') and cp.endswith('/manifest.json'),'checkpoint fit path')
   manifest=cap.value(cp,diagnostic['sha256']);key=cursor_manifest(manifest,prov,cap.raw(str(Path(cp).parent/'state.pt')));require(Path(cp).parent.name==key,'content-addressed checkpoint')
   planned=(diagnostic=={'checkpoint':q['capsule_root']+'/'+cp,'sha256':sha(cap.raw(cp)),'provenance':prov,'epochs_completed':1,'requires_genuine_failed_parent':True} and fc=={'experiment_id':identity,'provenance':prov,'parent_checkpoint':None} and ff=={'type':'PlannedInterruption','reason':REASON,'last_checkpoint':diagnostic['checkpoint']} and failure=={'type':'PlannedInterruption','reason':REASON,'success':False,'retry':False} and cap.absent(fit+'/complete.json') and cap.absent(namespace+'/result.json'))
  launch=observed(cap,base+'/launch.json');owner=observed(cap,base+'/owner.json');guard=observed(cap,base+'/guard/final.json')
  if launch is not None and owner is not None and guard is not None:
   require(all(owner.get(k)==v for k,v in launch.items()) and owner['experiment']==identity and owner['source_commit']==source and guard['owner_identity']==owner,'launch/monitor/native owner joins')
   require(all(guard.get(k)==v for k,v in job['resources'].items()) and guard['memory_swap_max_bytes']==0,'original native policy')
   require(guard['retry'] is False,'guard retry refused')
  relevant=[]
  for n,r in cap.rows.items():
   if n.startswith('research_runs/') and n.endswith('/claim.json') and len(n.split('/'))==3:
    old=cap.value(n)
    if old['family']['mechanism_id']==claim['family']['mechanism_id']:
     require(old['family']==claim['family'],'same mechanism family history changed');relevant.append({'path':n,'sha256':r['sha256'],'identity':old['experiment_id']})
  require(len(relevant)==1 and relevant[0]['identity']==identity,'first case root claim denominator changed')
  missing.append('independent genuine verify_claim/Git/source/cumulative-history outcome review')
 if context['actual_parent_exit'] is None:missing.append('separate actual parent exit')
 if context['source_claim_review'] is None:missing.append('pinned independent claim/history review')
 if context['actual_parent_exit'] is None:cleanup=False
 cap.close_check();par.close_check()
 return {'schema_version':1,'disposition':classify(claim_present=claim is not None,planned_bytes=planned,cleanup_proved=cleanup,predispatch_proved=predispatch),'byte_semantics':'planned interruption consistent' if planned else 'planned interruption not established','claim_present':claim is not None,'spent_if_genuine_claim_verified':claim is not None,'original_actual_parent_exit':None if parent is None else parent['actual_parent_exit'],'separate_actual_parent_exit':context['actual_parent_exit'],'missing_requirements':sorted(set(missing)),'capsule_inventory':cap.inventory,'parent_inventory':par.inventory,'tensor_cursor_decoded':False,'joint_gradients_verified':False,'capacity_verified':False,'paper_financial_fit_credit':0,'release_authorized':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capsule',required=True);p.add_argument('--parent',required=True);p.add_argument('--context',required=True);p.add_argument('--context-sha256',required=True);a=p.parse_args();path=Path(a.context);raw=R.read(path.parent,path.name);print(json.dumps(verify(a.capsule,a.parent,raw,a.context_sha256),sort_keys=True,allow_nan=False))
