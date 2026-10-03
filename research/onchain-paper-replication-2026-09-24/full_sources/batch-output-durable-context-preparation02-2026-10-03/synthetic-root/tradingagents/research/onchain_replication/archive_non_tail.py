"""Separate durable original-member population; never reuses event allowances.

Positive network dispatch is intentionally unavailable until an exact non-tail
transport/recovery capability replaces the unsafe legacy transfer IO seam.
Actual durable Context birth/ledger/operation requires genuine current handles.
"""
import hashlib,json,os,stat,sys,time
from pathlib import Path
from threading import get_ident
from ..lifecycle import ResearchRun
from . import job,matching_owner,compact_owner,held_score_consumer
META=131072;BLOCK=32768;KEY='non_tail_transport_input'
from .owned_io import CleanupFailure
def require(v,m):
 if not v:raise ValueError(m)
def encode(v):
 b=(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();require(len(b)<=META,'non-tail control metadata cap');return b
def fatal(e):return isinstance(e,MemoryError) or (not isinstance(e,Exception) and not isinstance(e,CleanupFailure))
def select(first,later):
 if first is None:return later
 if fatal(first):return first
 if fatal(later):return later
 if isinstance(later,CleanupFailure):return later
 return first
def close_all(actions,primary=None):
 selected=primary;uncertain=False
 for action in actions:
  try:action()
  except BaseException as e:selected=select(selected,e);uncertain=True
 if uncertain and not fatal(selected) and not isinstance(selected,CleanupFailure):selected=CleanupFailure('owned non-tail IO uncertain')
 if selected is not None:raise selected

def read_file(fd,name):
 require(type(name) is str and name not in ('','.','..') and Path(name).name==name,'single metadata member')
 child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd);primary=None;result=None
 try:
  before=os.fstat(child);require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=META,'bounded single-link metadata')
  pieces=[];count=0
  while True:
   b=os.read(child,min(65536,META-count+1))
   if not b:break
   count+=len(b);require(count<=META,'metadata grew');pieces.append(b)
  after=os.fstat(child);path=os.stat(name,dir_fd=fd,follow_symlinks=False)
  sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  require(sig(before)==sig(after)==sig(path) and count==before.st_size,'metadata changed');result=b''.join(pieces)
 except BaseException as e:primary=e
 close_all([lambda:os.close(child)],primary);return result

def write_file(fd,name,raw):
 require(type(name) is str and name not in ('','.','..') and Path(name).name==name and type(raw) is bytes and len(raw)<=META,'bounded single metadata write')
 child=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd);primary=None
 try:
  before=os.fstat(child);offset=0
  while offset<len(raw):
   count=os.write(child,raw[offset:offset+65536]);require(count>0,'write progress');offset+=count
  os.fsync(child);after=os.fstat(child);path=os.stat(name,dir_fd=fd,follow_symlinks=False)
  sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
  require(stat.S_ISREG(after.st_mode) and after.st_nlink==1 and after.st_size==len(raw) and (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino) and sig(after)==sig(path),'write identity differs')
 except BaseException as e:primary=e
 close_all([lambda:os.close(child)],primary);os.fsync(fd);require(read_file(fd,name)==raw,'durable metadata readback differs')

def validate_policy(p):
 fields={'schema_version','kind','category','namespace','deadline_seconds','max_rounded_bytes','max_commands','max_parts','max_control_bytes','part_bytes','receipt_output','terminal_output','slots'}
 require(type(p) is dict and set(p)==fields and type(p['schema_version']) is int and p['schema_version']==1 and p['kind']=='non-tail-durable-population-v1' and p['category']=='non-tail-original-members','separate non-tail registered population required')
 for k in ('deadline_seconds','max_rounded_bytes','max_commands','max_parts','max_control_bytes','part_bytes'):require(type(p[k]) is int and 0<p[k]<2**63,'strict positive finite bound')
 require(p['deadline_seconds']<=1800 and p['part_bytes']<=1048576 and p['max_parts']<=65536 and p['max_commands']<=131072 and p['max_rounded_bytes']<=2**40,'finite non-tail limits')
 require(p['max_control_bytes']>=META*(8+2*p['max_commands']),'durable failure/terminal headroom required')
 for k in ('namespace','receipt_output','terminal_output'):
  n=p[k];require(type(n) is str and 0<len(n)<=80 and all(c.isascii() and (c.isalnum() or c in '-_.') for c in n) and n not in ('.','..'),'single safe namespace/output')
 require(p['receipt_output']!=p['terminal_output'],'distinct non-tail outputs')
 require(type(p['slots']) is list and 0<len(p['slots'])<=128,'finite registered slots')
 seen=set()
 for s in p['slots']:
  require(type(s) is dict and set(s)=={'graph','role','max_bytes','max_members'},'slot schema')
  require(type(s['graph']) is str and len(s['graph'])==64 and all(c in '0123456789abcdef' for c in s['graph']) and s['role'] in ('score-batches','mcm-output','graph-artifact'),'exact graph/role')
  require((s['graph'],s['role']) not in seen,'duplicate slot');seen.add((s['graph'],s['role']))
  require(type(s['max_bytes']) is int and 0<s['max_bytes']<=64*1024**3 and type(s['max_members']) is int and 0<s['max_members']<=4096,'finite complete member ceiling')
 encode(p);return json.loads(encode(p))
def project(spent,size,p):
 require(type(size) is int and 0<size<=p['part_bytes'],'exact finite part reservation')
 new=dict(rounded_bytes=spent['rounded_bytes']+((size+BLOCK-1)//BLOCK)*BLOCK,commands=spent['commands']+1,parts=spent['parts']+1)
 require(new['rounded_bytes']<=p['max_rounded_bytes'] and new['commands']<=p['max_commands'] and new['parts']<=p['max_parts'],'non-tail cumulative no-refund allowance exhausted');return new

class Context:
 def __init__(self,run,*,policy_input,job_input):
  require(type(run) is ResearchRun,'genuine admitted ResearchRun required');run._active();run._check_source();run._check_inputs()
  require(type(policy_input) is str and policy_input in run.admission.inputs and job_input in run.admission.inputs,'registered non-tail/job inputs required')
  self.run=run;self.input=policy_input;self.job_input=job_input;self.policy_raw=run.read_input(policy_input);self.policy=validate_policy(json.loads(self.policy_raw));self.job_raw=run.read_input(job_input);self.execution=json.loads(self.job_raw)
  require(self.execution['kind']=='compact_resource' and set(self.execution['payload'])=={'representation_jobs'},'actual resource-only payload required')
  graphs=set();selected=0
  for value in self.execution['payload']['representation_jobs'].values():
   item=json.loads(run.read_input(value['plan_input']))['producers'][value['producer']]
   if KEY not in value and KEY not in item:continue
   require(value.get(KEY)==item.get(KEY)==policy_input,'both original job/plan non-tail policy selectors required')
   require(value.get('operation')=='produce','original producer required');graphs.update(value['descriptor']['required_graphs']);selected+=1
  require(selected>0 and {v['graph'] for v in self.policy['slots']}==graphs,'whole selected original graph population differs')
  require({self.policy['receipt_output'],self.policy['terminal_output']}<=set(run.admission.experiment['outputs']),'registered non-tail outputs required')
  source='tradingagents/research/onchain_replication/archive_non_tail.py';require(Path(__file__).resolve()==run.admission.root/source and run.admission.experiment['source_files'].get(source)==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actual new source not registered')
  self.claim=run._claim_sha256;self.base=run.admission.root/job.PREFIX/'runs'/run.admission.experiment_id
  self.guard,self.guard_hash=matching_owner.metadata(self.base/'owner.json',run.admission.root)
  launch,self.launch_hash=matching_owner.metadata(self.base/'launch.json',run.admission.root)
  require(launch['experiment']==run.admission.experiment_id and launch['source_commit']==run.admission.source and all(self.guard.get(k)==v for k,v in launch.items()),'original native launch/owner mismatch')
  matching_owner._guard(run,self.execution['resources'],self.guard,self.base)
  parent=run.admission.root/'research_artifacts';self.root=parent/('non-tail-'+self.policy['namespace'])
  watch=Path(self.execution['resources']['storage_budget']['root']);require(parent.resolve()==parent and self.root.is_relative_to(watch),'whole writable Context not guarded')
  require(not os.path.lexists(self.root),'non-tail identity already reserved')
  self.started=time.monotonic();self.spent=dict(rounded_bytes=0,commands=0,parts=0);self.failed=False;self.closed=False;self.active=None;self.operations={};self.expected={};self.control_bytes=0;self.thread=get_ident()
  self._config=encode({'policy':self.policy,'job_sha256':hashlib.sha256(self.job_raw).hexdigest(),'claim':self.claim,'root':str(self.root)})
  self.root.mkdir();self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);self.inode=(os.fstat(self.fd).st_dev,os.fstat(self.fd).st_ino)
  try:
   pfd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
   try:os.fsync(pfd)
   except BaseException as e:close_all([lambda:os.close(pfd)],e)
   else:close_all([lambda:os.close(pfd)])
   self.publish('intent.json',{'schema_version':1,'kind':'non-tail-context','source':run.admission.source,'claim':self.claim,'policy_sha256':hashlib.sha256(self.policy_raw).hexdigest(),'job_input':job_input,'job_sha256':hashlib.sha256(self.job_raw).hexdigest(),'policy':self.policy,'semantics':'durable original-member reservations; no disposition authority'})
   run.write_json(self.policy['receipt_output'],{'context':str(self.root.relative_to(run.admission.root)),'intent_sha256':hashlib.sha256(self.expected['intent.json']).hexdigest()});self.receipt=run._published_outputs[self.policy['receipt_output']]
   self.check()
  except BaseException as e:self.failed=True;self.closed=True;close_all([lambda:os.close(self.fd)],e)
 def publish(self,name,value):
  raw=encode(value);require(self.control_bytes+len(raw)<=self.policy['max_control_bytes'],'non-tail control capacity')
  require((self.root.lstat().st_dev,self.root.lstat().st_ino)==(os.fstat(self.fd).st_dev,os.fstat(self.fd).st_ino)==self.inode and self.root.resolve()==self.root,'Context root replaced');write_file(self.fd,name,raw);self.expected[name]=raw;self.control_bytes+=len(raw)
 def check(self):
  require(not self.closed and not self.failed and get_ident()==self.thread,'non-tail Context revoked/closed/thread mismatch')
  require(time.monotonic()-self.started<self.policy['deadline_seconds'],'non-tail cumulative deadline')
  self.run._active();self.run._check_source();self.run._check_inputs()
  require(self.run._claim_sha256==self.claim and self.run.read_input(self.input)==self.policy_raw and self.run.read_input(self.job_input)==self.job_raw,'original non-tail admission changed')
  require(encode({'policy':self.policy,'job_sha256':hashlib.sha256(self.job_raw).hexdigest(),'claim':self.claim,'root':str(self.root)})==self._config,'non-tail configuration changed')
  require(matching_owner.metadata(self.base/'owner.json',self.run.admission.root)[1]==self.guard_hash and matching_owner.metadata(self.base/'launch.json',self.run.admission.root)[1]==self.launch_hash,'original native records changed')
  require(encode(self.execution)==encode(json.loads(self.job_raw)),'original parsed resource configuration changed')
  matching_owner._guard(self.run,self.execution['resources'],self.guard,self.base)
  require(self.run._published_outputs[self.policy['receipt_output']]==self.receipt and matching_owner.metadata(self.run.directory/'outputs'/self.policy['receipt_output'],self.run.admission.root)[1]==self.receipt,'non-tail output anchor changed')
  require((self.root.lstat().st_dev,self.root.lstat().st_ino)==(os.fstat(self.fd).st_dev,os.fstat(self.fd).st_ino)==self.inode and self.root.resolve()==self.root,'non-tail root changed')
  iterator=os.scandir(self.fd)
  try:require({e.name for e in iterator}==set(self.expected),'non-tail durable membership changed')
  except BaseException as e:close_all([iterator.close],e)
  else:close_all([iterator.close])
  for name,raw in self.expected.items():require(read_file(self.fd,name)==raw,'durable original non-tail receipt changed')
  reservations=sorted(n for n in self.expected if n.startswith('reservation-'))
  expected=json.loads(self.expected[reservations[-1]])['spent'] if reservations else dict(rounded_bytes=0,commands=0,parts=0)
  require(self.spent==expected,'non-tail cumulative reservation refund/replacement')
 def bind(self,source):return Ledger(self,source)
 def close(self,primary=None):
  failure=primary
  try:self.check();require(self.active is None,'non-tail operation unfinished')
  except BaseException as e:failure=select(failure,e)
  result={'status':'failed' if failure or self.failed else 'complete-local-controls-only','spent':self.spent,'remote_verified':False,'local_bytes_retired':0}
  for action in (lambda:self.publish('terminal.json',result),lambda:self.run.write_json(self.policy['terminal_output'],result)):
   try:action()
   except BaseException as e:failure=select(failure,e)
  if failure is None:
   try:self.check()
   except BaseException as e:failure=e
  if failure is not None:
   try:self.publish('close-failed.json',{'error_type':type(failure).__name__,'spent':self.spent,'reservations_retained':True})
   except BaseException as e:failure=select(failure,e)
  self.closed=True;close_all([lambda:os.close(self.fd)],failure)

class Ledger:
 def __init__(self,context,source):
  require(type(context) is Context,'actual non-tail Context required');context.check();api=held_score_consumer._api(context.run)
  require(type(source) is api.HeldBatches,'genuine held score-batch adapter required; raw/NPY typed authority not implemented')
  source._checked();target,stage,held,stream,owner,bound,run=source._objects
  require(run is context.run and type(owner) is compact_owner.Owner and type(stage) is compact_owner.Stage and type(held) is compact_owner._HeldTransition,'actual current imported held owner chain')
  selected=target.execution._stage.prepared._selection_now();a=selected['selected'];b=selected['producer']
  require(a.get(KEY)==b.get(KEY)==context.input,'identical original job/plan non-tail selector required')
  slots=[s for s in context.policy['slots'] if s['graph']==target.key and s['role']=='score-batches'];require(len(slots)==1,'registered non-tail graph/role missing')
  local=source._reader;inventory=[{'name':n,'sha256':p[1],'bytes':p[2]} for n,p in local._pin]
  require(len(inventory)<=slots[0]['max_members'] and sum(x['bytes'] for x in inventory)<=slots[0]['max_bytes'],'complete original member population exceeds registration')
  self.context=context;self.source=source;self.owner=owner;self.stage=stage;self.held=held;self.inventory=inventory;self.pin=encode(inventory)
  self.record={'owner':owner.identity,'stage':stage.name,'stage_intent_sha256':stage.intent_sha256,'source':run.admission.source,'claim':run._claim_sha256,'role':'score-batches','scope':target.derive_scope(),'container_sha256':local.reference,'members':inventory}
  self.identity=hashlib.sha256(encode(self.record)).hexdigest();self.closed=False
 def check(self):
  require(not self.closed,'non-tail Ledger closed');self.context.check();self.source._checked();self.held.check(self.owner)
  require(self.source._objects[4] is self.owner and self.source._objects[1] is self.stage and encode(self.inventory)==self.pin,'non-tail original owner/member inventory changed')
 def claim(self):
  self.check();c=self.context;require(c.active is None and self.identity not in c.operations,'non-tail original operation already claimed')
  op=Operation(self);c.operations[self.identity]=op;c.active=op
  try:c.publish('operation-'+self.identity+'.json',self.record);op.check();return op
  except BaseException as e:op.fail(e);raise

class Operation:
 def __init__(self,ledger):self.ledger=ledger;self.index=0;self.offset=0;self.terminal=False;self._record_pin=encode(ledger.record)
 def check(self):
  require(not self.terminal and self.ledger.context.active is self and self.ledger.context.operations.get(self.ledger.identity) is self,'non-tail operation revoked or replaced')
  self.ledger.check();require(encode(self.ledger.record)==self._record_pin,'non-tail original operation record changed')
 def reserve_next(self,count):
  try:
   self.check();c=self.ledger.context;members=self.ledger.inventory;require(self.index<len(members),'complete member denominator exhausted');member=members[self.index]
   require(type(count) is int and count==min(c.policy['part_bytes'],member['bytes']-self.offset),'exact ordered original part required')
   updated=project(c.spent,count,c.policy);c.spent=updated
   record={'operation':self.ledger.identity,'member':member,'offset':self.offset,'bytes':count,'spent':updated,'semantics':'durable proposal reservation; not a transfer receipt'}
   c.publish('reservation-%08d.json'%updated['commands'],record)
   self.offset+=count
   if self.offset==member['bytes']:self.index+=1;self.offset=0
   self.check();return record
  except BaseException as e:self.fail(e);raise
 def verify_local_recovery(self,root):
  try:
   self.check();require(self.index==len(self.ledger.inventory) and self.offset==0,'all original ordered parts required')
   source=self.ledger.source;api=held_score_consumer._api(self.ledger.context.run);root=Path(root)
   require(root.resolve()==root and root!=source._reader.root,'distinct local complete recovery root')
   with api.content.open_local(root,kind='score-batches',document_sha256=source._reader.reference) as recovered:
    actual=[{'name':n,'sha256':p[1],'bytes':p[2]} for n,p in recovered._pin];require(encode(actual)==self.ledger.pin,'whole original recovered membership differs');recovered.check();self.check()
   c=self.ledger.context;c.publish('local-recovery-'+self.ledger.identity+'.json',{'operation':self.ledger.identity,'members_sha256':hashlib.sha256(self.ledger.pin).hexdigest(),'remote_verified':False,'disposition_authority':False})
   self.terminal=True;c.active=None
  except BaseException as e:self.fail(e);raise
 def dispatch(self,*args,**kwargs):
  self.check();raise NotImplementedError('legacy Transport transfer cleanup is not selected for this population; exact first-fatal non-tail transfer/recovery engine remains required')
 def fail(self,primary):
  c=self.ledger.context;c.failed=True;self.terminal=True;self.ledger.closed=True;self.ledger.owner.poisoned=True;failure=primary
  try:c.publish('failed-'+self.ledger.identity+'.json',{'operation':self.ledger.identity,'error_type':type(primary).__name__,'spent':c.spent,'reservations_retained':True})
  except BaseException as e:failure=select(failure,e)
  raise failure
