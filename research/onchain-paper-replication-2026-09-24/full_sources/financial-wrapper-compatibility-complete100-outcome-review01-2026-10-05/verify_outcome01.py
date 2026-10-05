"""Prepared read-only verifier. Actual terminal Root evidence is required.
No scientific imports, tensor/checkpoint deserialization or run authority.
"""
import argparse,hashlib,importlib.util,json,math,os,stat,time
from pathlib import Path
C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
ID='financial-wrapper-classification-eager-complete100-compatibility-20261004-01';CELL='financial-wrapper-classification-eager-reference-compatibility-20261004-01';SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
H=lambda b:hashlib.sha256(b).hexdigest()
# Exact already accepted owned descriptor/fatal cleanup; no scientific imports.
def owned_io():
 p=P/'owned_io.py';raw=p.read_bytes();need(H(raw)=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','owned IO pin')
 spec=importlib.util.spec_from_file_location('outcome_owned_io',p);m=importlib.util.module_from_spec(spec);exec(compile(raw,str(p),'exec'),m.__dict__);return m
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def need(v,m):
 if not v:raise ValueError(m)
class Reader:
 def __init__(self):self.pins={};self.bytes=0;self.deadline=time.monotonic()+180;self.io=owned_io()
 def read(self,p,pin=None):
  p=Path(p);s=p.lstat();before=self.signature(p);need(p.is_absolute() and p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded canonical regular input')
  need(time.monotonic()<self.deadline and self.bytes+s.st_size<=512*1024**2,'finite audit bound')
  with self.io._opened(p,'rb') as f:b=f.read(4194305)
  self.bytes+=len(b);need(self.signature(p)==before and len(b)==s.st_size,'input changed')
  if pin:need(H(b)==pin,'input hash differs '+str(p))
  need(p not in self.pins or self.pins[p]==before,'cohort changed');self.pins[p]=before;return b
 def json(self,p,pin=None):return json.loads(self.read(p,pin))
 @staticmethod
 def signature(p):
  s=p.lstat();return tuple(getattr(s,k)for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
 def finish(self):
  for p,s in self.pins.items():need(self.signature(p)==s,'terminal sampled currentness')
  need(time.monotonic()<self.deadline,'audit deadline')
def verify(tool_path,tool_sha):
 r=Reader();tool=r.json(tool_path,tool_sha);need(tool.get('actual_root_exit')==0,'genuine separate actual Root exit0 required')
 q=r.json(P/'REQUEST_FINAL01.json','cfecfd3e12d81628b9bc6f10171dd0345ac6e62c5481edccab64e5207254e03d');need(q['identity']==ID and q['source']==SOURCE,'fixed final request')
 for n,h in {'parent01.py':q['caller_sha256'],**q['helper_hashes']}.items():r.read(P/n,h)
 reg=r.json(C/q['registration'],q['registration_sha256']);exp=reg['experiments'][ID];need(exp['source_files']==q['source_files'] and exp['parent'] is None,'fixed independent reference registration')
 plan=r.json(C/exp['inputs']['wrapper_plan']['path'],q['input_hashes']['wrapper_plan']);training=r.json(C/exp['inputs']['training']['path'],q['input_hashes']['training'])
 need(plan['cell_id']==CELL and plan['phase']=='complete100' and plan['execution']=='eager' and plan['task']=='classification' and plan['prior_input'] is None and plan['reference_input'] is None,'fixed phase topology')
 need(training['epochs']==100 and training['batch_size']==16,'fixed training')
 run=C/'research_runs'/ID;claim=r.json(run/'claim.json');terminal=r.json(run/'complete.json');need(not os.path.lexists(run/'failed.json'),'contradictory/failed lifecycle')
 need(claim['source']==claim['design_source']==SOURCE and claim['experiment_id']==ID and claim['bindings'] is None and claim['bindings_sha256'] is None,'actual claim and scientific binding null')
 need(claim['experiment']==exp and claim['registration_sha256']==q['registration_sha256'] and claim['effective_attempt_budget']==20,'genuine fixed claim/ceiling')
 need(terminal['claim_sha256']==H(r.read(run/'claim.json')) and terminal['source']==SOURCE and terminal['experiment_id']==ID and terminal['registration_sha256']==q['registration_sha256'],'lifecycle joins')
 need(terminal['cell_count']==1 and terminal['unavailable_count']==0 and terminal['cells']==[{'id':CELL,'status':'complete','kind':'finite synthetic engineering'}],'full declared one-cell denominator')
 need(set(terminal['output_sha256'])==set(exp['outputs'])=={'cell-ledger.json','wrapper-summary.json','artifact-index.json'},'exact lifecycle output closure')
 for n,h in terminal['output_sha256'].items():r.read(run/'outputs'/n,h)
 need(r.json(run/'outputs/cell-ledger.json')==terminal['cells'],'cell ledger agrees')
 eng=C/'research_artifacts/financial_wrapper_engineering'/ID;intent=r.json(eng/'intent.json');result=r.json(eng/'result.json');need(not os.path.lexists(eng/'failure.json'),'wrapper failure retained cannot accept')
 need(intent['plan']==plan and intent['scientific_epochs']==100 and intent['paper_financial_fits']==0,'wrapper intent')
 need(result==r.json(run/'outputs/wrapper-summary.json') and result['phase']=='complete100' and result['epochs']==100 and result['paper_financial_fits']==0 and result['full_size_capacity'] is False,'actual complete100 wrapper-only result')
 index=r.json(run/'outputs/artifact-index.json');actual={str(p.relative_to(C))for p in eng.rglob('*')if p.is_file()};need(set(index)==actual,'complete artifact index incl replay evidence')
 for n,v in index.items():need(len(r.read(C/n,v['sha256']))==v['bytes'],'artifact extent')
 fit=C/'research_artifacts/onchain_fit_cells'/H(CELL.encode())/ID;fc=r.json(fit/'claim.json');need(fc=={'experiment_id':ID,'provenance':intent['provenance'],'parent_checkpoint':None},'fresh fit claim')
 need(not os.path.lexists(fit/'failed.json'),'fit failure cannot become complete');schedule=r.json(fit/'schedule.json');need(schedule=={'training':training,'seed':11,'task':'classification','n_examples':16},'original schedule')
 logs=[]
 for epoch in range(100):
  log=r.json(fit/f'epoch-{epoch:04d}.json');need(set(log)=={'epoch','loss','examples','seed'} and log['epoch']==epoch and log['examples']==16 and log['seed']==11 and isinstance(log['loss'],(int,float))and math.isfinite(log['loss']),'durable epoch record');logs.append(log)
 need({p.name for p in fit.glob('epoch-*.json')}=={f'epoch-{e:04d}.json'for e in range(100)},'exact100 epoch denominator')
 prov=intent['provenance'];need(prov['source_commit']==SOURCE and prov['cell_id']==CELL and prov['fold_id']=='synthetic-16x28-distinct' and 'model_execution' not in prov,'eager provenance')
 closure=r.json(C/exp['inputs']['source_closure']['path'],q['input_hashes']['source_closure']);model=r.json(C/exp['inputs']['model']['path'],q['input_hashes']['model']);recipe=r.json(C/exp['inputs']['synthetic_recipe']['path'],q['input_hashes']['synthetic_recipe'])
 expected_prov={'source_hashes':sorted(set(closure['installed'].values())),'config_hash':H(canonical({'model':model,'training':training,'task':'classification','recipe':recipe})),'input_hash':q['input_hashes']['synthetic_recipe'],'dictionary_hash':H(b'synthetic opaque MCM; no empirical dictionary fitted or recovered'),'fold_id':'synthetic-16x28-distinct','cell_id':CELL,'source_commit':SOURCE}
 need(prov==expected_prov and len(closure['installed'])==195,'complete truthful195 installed source provenance')
 for name,pin in closure['installed'].items():need(q['source_files'][name]==pin,'closure registered');r.read(C/name,pin)
 expected=set()
 for epoch in range(1,101):
  key=H(canonical({'provenance':prov,'epoch':epoch,'batch':0}));expected.add(key);cp=fit/'checkpoints'/key/'manifest.json';m=r.json(cp)
  need(set(m)=={'schema_version','key','provenance','members'}and m['schema_version']==1 and m['key']==key and m['provenance']==prov and set(m['members'])=={'state.pt'},'checkpoint metadata provenance')
  info=m['members']['state.pt'];need(len(r.read(cp.parent/'state.pt',info['sha256']))==info['size'],'opaque checkpoint member hash')
  need({p.name for p in cp.parent.iterdir()}=={'manifest.json','state.pt'},'complete checkpoint members')
 need({p.name for p in (fit/'checkpoints').iterdir()}==expected,'exact100 durable checkpoint publications')
 complete=r.json(fit/'complete.json');last=fit/'checkpoints'/H(canonical({'provenance':prov,'epoch':100,'batch':0}))/'manifest.json'
 need(complete=={'checkpoint':str(last),'sha256':H(r.read(last)),'epochs':100} and result['checkpoint']==str(last)and result['checkpoint_sha256']==complete['sha256'],'fit/wrapper final checkpoint join')
 replay=r.json(eng/'replay/manifest.json');need(replay['provenance']==prov and r.read(eng/'replay'/replay['checkpoint'])==r.read(last),'replay checkpoint metadata copy')
 for n,h in replay['files'].items():r.read(eng/'replay'/n,h)
 # Native owner is an operational process identity, not a scientific Owner.
 base=C/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID;owner=r.json(base/'owner.json');launch=r.json(base/'launch.json');live=r.json(base/'guard/live.json');guard=r.json(base/'guard/final.json')
 need(owner['experiment']==ID and owner['source_commit']==SOURCE and all(owner[k]==v for k,v in launch.items())and live['owner_identity']==owner and guard['owner_identity']==owner,'native identity chain')
 need(guard['phase']=='complete'and guard['cleanup_verified'] is True and guard['child_exit_code']==0 and guard['limit_reason'] is None and all(guard.get('memory_events',{}).get(k)==0 for k in ('oom','oom_kill')),'genuine terminal native resource outcome')
 parent=r.json(P/'attempt/parent-terminal.json');cleanup=r.json(P/'attempt/owned-tree-cleanup.json');need(parent['identity']==ID and parent['source']==SOURCE and parent['actual_child_exit']==0 and parent['actual_parent_exit'] is None and parent['primary_exception_observed'] is False,'original Parent null and successful child')
 need(cleanup['subreaper_used'] is True and cleanup['remaining_original_identities']==[],'actual owned process cleanup')
 need(parent['cleanup']['joined_unit_stopped'] is True and parent['cleanup']['cgroup_absent'] is True,'actual native cleanup')
 for row in cleanup['owned_pid_start_records']:
  p=Path('/proc')/str(row['pid'])/'stat'
  if p.exists():parts=p.read_text().rsplit(')',1)[1].split();need(parts[19]!=str(row['ticks']),'original owned PID remains')
 if live.get('cgroup'):need(not Path(live['cgroup']).exists(),'actual native cgroup remains')
 claim_hash=H(r.read(run/'claim.json'));terminal_hash=H(r.read(run/'complete.json'));r.finish()
 return {'decision':'OBSERVED_COMPLETE100_REQUIRES_INDEPENDENT_INTERPRETATION','identity':ID,'source':SOURCE,'epochs':100,'durable_checkpoint_publications':100,'actual_cell_count':1,'unavailable_count':0,'paper_financial_fits':0,'scientific_binding':None,'checkpoint_deserialized':False,'numerical_replay_independently_executed':False,'original_parent_exit':None,'separate_actual_root_exit':0,'files_hashed':len(r.pins),'bytes_hashed':r.bytes,'actual_claim_sha256':claim_hash,'actual_terminal_sha256':terminal_hash,'actual_checkpoint_sha256':complete['sha256'],'capacity_claim':False}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--actual-root-tool-exit',type=Path,required=True);a.add_argument('--sha256',required=True);v=a.parse_args();print(json.dumps(verify(v.actual_root_tool_exit,v.sha256),sort_keys=True))
