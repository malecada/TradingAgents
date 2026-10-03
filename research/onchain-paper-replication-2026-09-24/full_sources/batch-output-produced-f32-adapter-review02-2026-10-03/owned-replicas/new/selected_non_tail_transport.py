"""Selected f64 SSH plaintext-channel transport; never implicit network authority.

Construction needs the actual registered durable Context/Operation/HeldBatches.
No legacy Transport cleanup, caller lease callback, credentials read, deletion,
retry, raw-f32/NPY adapter or physical encrypted-wire claim is provided.
"""
import hashlib,json,os,re,select,signal,stat,subprocess,time
from pathlib import Path
from . import archive_non_tail as durable
from . import owned_io
META=8192;BLOCK=32768;SOURCE='tradingagents/research/onchain_replication/selected_non_tail_transport.py'
def require(v,m):
 if not v:raise ValueError(m)
def digest(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return durable.encode(v)
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def charge(tx,rx,diagnostic,control):
 require(all(type(v) is int and v>=0 for v in (tx,rx,diagnostic,control)),'exact channel extents')
 # dd recovery uses floor-plus-one blocks, including its EOF probe. The other
 # channels reserve complete upper bounds, including a one-byte excess probe.
 return ((tx+BLOCK-1)//BLOCK+(rx//BLOCK+1)+((diagnostic+1+BLOCK-1)//BLOCK)+((control+BLOCK-1)//BLOCK))*BLOCK

def policy(value,context):
 if type(value) is dict and type(value.get('schema_version')) is int and value['schema_version']==2:
  require(value.get('kind')=='selected-produced-f32-ssh-plaintext-channel-v1' and context.get('schema_version')==3 and all(row['role']=='mcm-output' for row in context['slots']),'explicit completed raw-only transport selection')
  legacy=dict(value);legacy.update(schema_version=1,kind='selected-non-tail-ssh-plaintext-channel-v1')
  shape=dict(context);shape['schema_version']=2;shape['slots']=[dict(row,role='score-batches') for row in context['slots']]
  policy(legacy,shape);return json.loads(encoded(value))
 require(context.get('schema_version')!=3,'raw Context cannot select f64 transport schema')
 fields={'schema_version','kind','connection','remote_namespace','part_bytes','command_seconds','cleanup_seconds','stderr_bytes','max_commands','max_parts','max_rounded_bytes','max_channel_bytes','max_local_bytes','max_files','outputs'}
 require(type(value) is dict and set(value)==fields and type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='selected-non-tail-ssh-plaintext-channel-v1','explicit registered plaintext-channel policy required')
 c=value['connection'];require(type(c) is dict and set(c)=={'host','user','port','identity_file','known_hosts_file'},'original explicit connection fields required')
 for k in ('host','user'):require(type(c[k]) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,252}',c[k]),'unsafe SSH endpoint')
 require(type(c['port']) is int and 1<=c['port']<=65535,'SSH port')
 for k in ('identity_file','known_hosts_file'):
  v=c[k];require(type(v) is str and v.startswith('/') and len(v)<=4096 and not any(ord(x)<32 or ord(x)==127 for x in v),'absolute authentication path metadata required')
 require(type(value['remote_namespace']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,31}',value['remote_namespace']),'finite safe remote namespace')
 bounds={'part_bytes':1048576,'command_seconds':1800,'cleanup_seconds':10,'stderr_bytes':16384,'max_commands':8192,'max_parts':4096,'max_rounded_bytes':2**40,'max_channel_bytes':2**40,'max_local_bytes':1024**3,'max_files':32768}
 for k,maximum in bounds.items():require(type(value[k]) is int and 0<value[k]<=maximum,'finite strict transfer bound: '+k)
 require(value['part_bytes']==context['part_bytes'] and value['part_bytes']%8==0,'same original ordered part policy required')
 require(value['command_seconds']+value['cleanup_seconds']<=context['deadline_seconds'],'command and cleanup must fit cumulative deadline')
 require(context['max_control_bytes']>=META*(8+3*context['max_commands']+3*value['max_commands']),'complete proposal/command/failure control headroom required')
 graphs={s['graph'] for s in context['slots'] if s['role']=='score-batches'};outs=value['outputs']
 require(type(outs) is dict and set(outs)==graphs and outs,'complete f64 graph output roles required')
 require(all(type(x) is str and 0<len(x)<=80 and Path(x).name==x and x.endswith('.json') for x in outs.values()) and len(set(outs.values()))==len(outs),'unique finite transfer outputs')
 encoded(value);return json.loads(encoded(value))

def parse_policy(raw,context):
 require(type(raw) is bytes and len(raw)<=META,'bounded selected transport policy bytes')
 value=policy(json.loads(raw),context);require(encoded(value)==raw,'canonical selected policy bytes required; duplicate keys forbidden');return value

def _source_check(c):
 run=c.run
 for name,module in ((SOURCE,__file__),('tradingagents/research/onchain_replication/archive_non_tail.py',durable.__file__),('tradingagents/research/onchain_replication/owned_io.py',owned_io.__file__)):
  path=run.admission.root/name;expected=run.admission.experiment['source_files'].get(name)
  require(Path(module)==path and type(expected) is str and len(expected)==64 and digest(durable._source_body(path))==expected,'actual selected transport source closure differs')

def _selected(c):
 require(type(c) is durable.Context and c.policy['schema_version'] in (2,3),'genuine explicitly selected durable Context required')
 c.run._active();c.run._check_source();c.run._check_inputs();_source_check(c)
 name=c.policy['transport_input'];require(type(name) is str and name in c.run.admission.inputs,'registered selected transport input missing')
 raw=c.run.read_input(name);require(type(raw) is bytes and len(raw)<=META,'transport metadata cap')
 p=parse_policy(raw,c.policy)
 require(c.policy_raw==encoded(c.policy),'canonical selected population policy required')
 durable._selection_graphs(c.run,c.execution,c.input,(c.policy['receipt_output'],c.policy['terminal_output'],*p['outputs'].values()))
 require(set(p['outputs'].values())<=set(c.run.admission.experiment['outputs']) and not set(p['outputs'].values()).intersection((c.policy['receipt_output'],c.policy['terminal_output'])),'registered transport outputs differ')
 return raw,p

def preflight_context(c):
 raw,p=_selected(c)
 c._transfer_raw=raw;c._transfer_policy=p;c._transfer_spent={'commands':0,'parts':0,'rounded_bytes':0,'channel_bound':0};c._transfer_observed={'commands_started':0,'stdin_bytes':0,'stdout_bytes':0,'stderr_bytes':0,'command_argument_bytes_started':0};c._transfer_active=None

def check_context(c):
 raw,p=_selected(c);require(raw==c._transfer_raw and encoded(p)==encoded(c._transfer_policy),'selected transfer policy changed')
 names=sorted(n for n in c.expected if n.startswith('transfer-reservation-'))
 prior=json.loads(c.expected[names[-1]])['spent'] if names else {'commands':0,'parts':0,'rounded_bytes':0,'channel_bound':0}
 require(c._transfer_spent==prior,'transfer reservation refund or replacement')
 observed=[json.loads(v)['observed'] for n,v in sorted(c.expected.items()) if n.startswith('transfer-result-')]
 expected={'commands_started':0,'stdin_bytes':0,'stdout_bytes':0,'stderr_bytes':0,'command_argument_bytes_started':0}
 for row in observed:
  for key in expected:expected[key]+=row[key]
 # An active child may have unreconciled observations; its reservation remains
 # durable and no new command can start until its final receipt is published.
 if c._transfer_active is None:require(c._transfer_observed==expected,'actual channel observation accounting differs')

def _late_failure(c,primary):
 # Close uncertainty forbids retrying its old fd number. A new exclusive failure
 # marker uses a freshly opened, inode-checked original directory descriptor.
 fd=None
 try:
  require(c.root.resolve()==c.root and (c.root.lstat().st_dev,c.root.lstat().st_ino)==c.inode,'late failure root changed')
  fd=os.open(c.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
  require((os.fstat(fd).st_dev,os.fstat(fd).st_ino)==c.inode,'late failure root replaced')
  durable.write_file(fd,'selected-close-failed.json',encoded({'status':'failed','error_type':type(primary).__name__,'spent':c._transfer_spent,'observed':c._transfer_observed,'prior_receipts_are_historical':True,'disposition_authority':False}))
 finally:owned_io._cleanup(() if fd is None else (lambda:os.close(fd),))

def close_context(c,primary=None):
 require(type(c) is durable.Context and (c.policy['schema_version']==2 or (type(c.policy['schema_version']) is int and c.policy['schema_version']==3)),'genuine selected Context required')
 failure=primary
 try:
  c.check();require(c.active is None and c._transfer_active is None,'selected operation/command unfinished')
 except BaseException as e:failure=durable.select(failure,e)
 result={'status':'failed' if failure or c.failed else 'complete-selected-pipe-controls-only','reserved':c._transfer_spent,'observed':c._transfer_observed,'physical_encrypted_wire_metered':False,'disposition_authority':False,'local_bytes_retired':0}
 try:c.publish('selected-close-intent.json',result)
 except BaseException as e:failure=durable.select(failure,e)
 # A repeated close cannot close a reused integer. Every attempted close leaves
 # this context permanently closed before invoking its owned close operation.
 if not c.closed:
  c.closed=True
  try:owned_io._cleanup((lambda:os.close(c.fd),),primary=failure)
  except BaseException as e:failure=durable.select(failure,e)
 else:failure=durable.select(failure,ValueError('selected Context already closed'))
 if failure is None:
  try:c.run.write_json(c.policy['terminal_output'],result)
  except BaseException as e:failure=e
 if failure is not None:
  c.failed=True
  for operation in c.operations.values():operation.ledger.owner.poisoned=True
  try:_late_failure(c,failure)
  except BaseException as e:failure=durable.select(failure,e)
  raise failure
 return result

class Session:
 def __init__(self,operation):
  require(type(operation) is durable.Operation,'actual selected Operation required');operation.check()
  c=operation.ledger.context;require(c.policy['schema_version'] in (2,3),'legacy unselected Context cannot transfer');check_context(c)
  require(c._transfer_active is None,'another transfer command active')
  source=operation.ledger.source;source._checked();api=durable.held_score_consumer._api(c.run)
  if c.policy['schema_version']==3:
   from .completed_f32 import CompletedF32
   require(type(source) is CompletedF32 and operation.ledger.record['role']=='mcm-output','actual completed raw Produced adapter required; NPY refused')
  else:
   require(type(source) is api.HeldBatches and operation.ledger.record['role']=='score-batches','genuine f64 HeldBatches only; raw-f32/NPY live adapters absent')
  require(operation.index==0 and operation.offset==0,'transfer owns a fresh unconsumed ordered operation')
  self.op=operation;self.c=c;self.p=c._transfer_policy;self.source=source;self.inventory=tuple((r['name'],r['sha256'],r['bytes']) for r in operation.ledger.inventory);self._inventory_pin=encoded(operation.ledger.inventory)
  require(all(type(size) is int and 0<size<=4194304 and Path(name).name==name and name not in ('.','..') for name,_,size in self.inventory),'finite original member/native file extents')
  self.source_members=tuple({'name':n,'signature':list(row[0]),'sha256':row[1],'bytes':row[2]} for n,row in source._reader._pin)
  require(tuple((r['name'],r['sha256'],r['bytes']) for r in self.source_members)==self.inventory,'original source signatures/inventory differ')
  for row in self.source_members:encoded({'operation':operation.ledger.identity,'original_member':row,'recovery_mode':384,'filesystem_timestamps_and_inodes_not_rebased':True})
  self.parts=sum((size+self.p['part_bytes']-1)//self.p['part_bytes'] for _,_,size in self.inventory)
  require(self.parts*2+c._transfer_spent['parts']<=self.p['max_parts'] and self.parts*3+c._transfer_spent['commands']<=self.p['max_commands'],'whole ordered transfer command/part headroom missing')
  require(3+len(self.inventory)+self.parts*6<=self.p['max_files'] and sum(size for _,_,size in self.inventory)*2+self.parts*3*(self.p['stderr_bytes']+2)<=self.p['max_local_bytes'],'whole retained recovery/diagnostic local headroom missing')
  self.output=self.p['outputs'][source._objects[0].key]
  require(self.output not in c.run._published_outputs and not os.path.lexists(c.run.directory/'outputs'/self.output),'transport output already reserved')
  self.root=c.root.parent/('non-tail-transfer-'+operation.ledger.identity);require(self.root.resolve()==self.root and not os.path.lexists(self.root),'transport namespace already attempted')
  watch=Path(c.execution['resources']['storage_budget']['root']);require(self.root.is_relative_to(watch),'transfer tree outside actual native watch')
  self.files={};self.directories={};self.fd=None;self.closed=False;self.recovered=False;self.command_index=0;self.local_bytes=0;self._next=None;self.process_evidence=None;self.pending_files={}
  self.deadline=c.started+c.policy['deadline_seconds'];self._identity=encoded({'operation':operation.ledger.identity,'source':c.run.admission.source,'claim':c.claim,'inventory':digest(self._inventory_pin),'policy':digest(c._transfer_raw),'root':str(self.root)})
  encoded({'schema_version':1,'kind':('selected-produced-f32-transfer-attempt' if self.c.policy['schema_version']==3 else 'selected-f64-transfer-attempt'),'identity':json.loads(self._identity),'plaintext_accounting_only':True,'physical_encrypted_wire_metered':False,'disposition_authority':False})
  self.root.mkdir()
  try:
   self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);self.root_pin=signature(os.fstat(self.fd))
   for name in ('parts','recovery','diagnostics'):(self.root/name).mkdir();self.directories[name]=((self.root/name).stat().st_dev,(self.root/name).stat().st_ino)
   parent=os.open(self.root.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
   try:os.fsync(parent)
   finally:owned_io._cleanup((lambda:os.close(parent),))
   os.fsync(self.fd)
   c.publish('transfer-intent-'+operation.ledger.identity+'.json',{'schema_version':1,'kind':('selected-produced-f32-transfer-attempt' if self.c.policy['schema_version']==3 else 'selected-f64-transfer-attempt'),'identity':json.loads(self._identity),'plaintext_accounting_only':True,'physical_encrypted_wire_metered':False,'disposition_authority':False})
   for index,row in enumerate(self.source_members):c.publish('transfer-source-'+operation.ledger.identity+'-%04d.json'%index,{'operation':operation.ledger.identity,'original_member':row,'recovery_mode':384,'filesystem_timestamps_and_inodes_not_rebased':True})
   self.check()
  except BaseException as e:
   self.closed=True;owned_io._cleanup(() if self.fd is None else (lambda:os.close(self.fd),),primary=e);raise
 def check(self):
  require(not self.closed,'selected transfer session closed')
  if self.recovered:self.c.check();self.op.ledger.check();require(self.op.terminal and self.c.active is None,'recovered operation state changed')
  else:self.op.check()
  require(self.c._transfer_policy==self.p and encoded(self.op.ledger.inventory)==self._inventory_pin and self.source is self.op.ledger.source,'original transport binding changed')
  self.source._checked();require(time.monotonic()<self.deadline,'whole selected transfer deadline')
  require(self.root.resolve()==self.root and (self.root.lstat().st_dev,self.root.lstat().st_ino)==(os.fstat(self.fd).st_dev,os.fstat(self.fd).st_ino),'transfer root changed')
  for name,inode in self.directories.items():require((self.root/name).resolve()==self.root/name and (self.root/name).is_dir() and ((self.root/name).stat().st_dev,(self.root/name).stat().st_ino)==inode,'transfer subdirectory changed')
  self.check_files()
  require(encoded({'operation':self.op.ledger.identity,'source':self.c.run.admission.source,'claim':self.c.claim,'inventory':digest(self._inventory_pin),'policy':digest(self.c._transfer_raw),'root':str(self.root)})==self._identity,'transport identity changed')
 def create_owned(self,path,bound):
  self.check();name=str(path.relative_to(self.root));require(name not in self.files and name not in self.pending_files,'owned transfer file already attempted')
  require(type(bound) is int and 0<bound<=4194304,'finite owned file bound')
  parent=path.parent;require(parent.name in self.directories and parent.parent==self.root and parent.resolve()==parent,'owned parent differs')
  parentfd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fd=None;primary=None
  try:
   require((os.fstat(parentfd).st_dev,os.fstat(parentfd).st_ino)==self.directories[parent.name],'owned parent replaced')
   fd=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=parentfd)
   st=os.fstat(fd);require(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and signature(st)==signature(path.lstat()),'new transfer file changed')
   self.pending_files[name]=(st.st_dev,st.st_ino,bound);os.fsync(parentfd)
  except BaseException as e:primary=e
  try:owned_io._cleanup((lambda:os.close(parentfd),),primary=primary)
  except BaseException as e:primary=durable.select(primary,e)
  if primary is not None:
   owned_io._cleanup(() if fd is None else (lambda:os.close(fd),),primary=primary);raise primary
  return fd
 def seal_file(self,path):
  name=str(path.relative_to(self.root));pin=self.pending_files[name]
  row=_owned_snapshot(path,pin[2],self.deadline)
  require(row['identity'][:2]==list(pin[:2]),'owned transfer file replaced')
  self.files[name]=row;del self.pending_files[name]
 def check_files(self):
  names=set();total=0;dirs=set();iterator=os.scandir(self.fd)
  try:
   for entry in iterator:
    require(entry.name in self.directories and entry.name not in dirs,'unexpected transfer root member');dirs.add(entry.name)
    st=entry.stat(follow_symlinks=False);require(stat.S_ISDIR(st.st_mode) and (st.st_dev,st.st_ino)==self.directories[entry.name],'transfer directory changed')
  finally:owned_io._cleanup((iterator.close,))
  require(dirs==set(self.directories),'missing transfer directory')
  for directory in self.directories:
   dfd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=self.fd)
   try:
    st=os.fstat(dfd);require((st.st_dev,st.st_ino)==self.directories[directory],'transfer directory replaced before open');iterator=os.scandir(dfd)
    try:
     for entry in iterator:
      name=directory+'/'+entry.name;require(name in self.files or name in self.pending_files,'unexpected transfer file')
      require(name not in names,'duplicate transfer file');names.add(name);st=entry.stat(follow_symlinks=False)
      require(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600,'transfer file type/link/mode changed');total+=st.st_size
      require(len(names)+3<=self.p['max_files'] and total<=self.p['max_local_bytes'],'actual retained local capacity exceeded')
      if name in self.pending_files:
       dev,ino,limit=self.pending_files[name];require((st.st_dev,st.st_ino)==(dev,ino) and st.st_size<=limit,'active owned transfer extent/identity changed')
      else:require(_owned_snapshot(self.root/name,self.files[name]['bytes'],self.deadline)==self.files[name],'retained completed transfer file changed')
    finally:owned_io._cleanup((iterator.close,))
    st=os.stat(directory,dir_fd=self.fd,follow_symlinks=False);require((st.st_dev,st.st_ino)==self.directories[directory] and (self.root/directory).resolve()==self.root/directory,'transfer directory changed after scan')
   finally:owned_io._cleanup((lambda:os.close(dfd),))
  require(names==set(self.files)|set(self.pending_files),'owned transfer member missing');self.local_bytes=total
  require(self.root.resolve()==self.root and (self.root.lstat().st_dev,self.root.lstat().st_ino)==(os.fstat(self.fd).st_dev,os.fstat(self.fd).st_ino),'transfer root changed after scan')
 def _remote(self,member,part):
  value=self.p['remote_namespace']+'-'+self.op.ledger.identity+'-%04d-%08d'%(member,part)
  require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}',value),'finite original remote path');return value
 def _argv(self,kind,remote,count):
  require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}',remote),'safe remote member')
  c=self.p['connection'];options=['-i',c['identity_file'],'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','UserKnownHostsFile='+c['known_hosts_file'],'-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2']
  remote_args={'mkdir':['mkdir',remote],'upload':['dd','of='+remote+'/payload.bin','bs=32768','oflag=excl'],'download':['dd','if='+remote+'/payload.bin','bs=32768','count='+str(count//BLOCK+1)]}[kind]
  return ['ssh','-p',str(c['port']),*options,c['user']+'@'+c['host'],*remote_args],len(' '.join(remote_args).encode())
 def _source_part(self,name,offset,count):
  self.check();reader=self.source._reader
  if name in reader.members:raw=self.source.read_part(name,offset,count)
  else:
   row=reader._files[name];_,whole=reader._read(name,row[2],expected=row[1],extent=row[2],capture=True);raw=whole[offset:offset+count]
  require(type(raw) is bytes and len(raw)==count,'complete original part read required');self.check();return raw
 def _reserve(self,kind,control,tx,rx):
  self.check();c=self.c;require(c._transfer_active is None,'concurrent selected command refused');old=c._transfer_spent
  bounds=charge(tx,rx,self.p['stderr_bytes'],control);channel=tx+rx+1+self.p['stderr_bytes']+1+control
  new={'commands':old['commands']+1,'parts':old['parts']+(kind!='mkdir'),'rounded_bytes':old['rounded_bytes']+bounds,'channel_bound':old['channel_bound']+channel}
  require(new['commands']<=self.p['max_commands'] and new['parts']<=self.p['max_parts'] and new['rounded_bytes']<=self.p['max_rounded_bytes'] and new['channel_bound']<=self.p['max_channel_bytes'],'cumulative selected command/channel allowance exhausted')
  require(time.monotonic()+self.p['cleanup_seconds']<self.deadline,'cleanup deadline headroom absent')
  c._transfer_spent=new;c._transfer_active=self
  c.publish('transfer-reservation-%08d.json'%new['commands'],{'kind':kind,'operation':self.op.ledger.identity,'spent':new,'stdin_bound':tx,'stdout_bound':rx+1,'stderr_bound':self.p['stderr_bytes']+1,'command_channel_bytes':control,'physical_wire_bound':None,'semantics':'spent command attempt reservation, not executed-command receipt'})
  return new['commands']
 def _command(self,kind,remote,data,count):
  require(kind in ('mkdir','upload','download') and type(data) is bytes,'fixed selected command kind')
  command,control=self._argv(kind,remote,count);expected=count if kind=='download' else 0
  serial=self._reserve(kind,control,len(data),expected)
  stdout=self.root/'parts'/('%08d.bin'%serial);stderr=self.root/'diagnostics'/('%08d.stderr'%serial)
  self._next=(tuple(command),digest(data),expected,str(stdout),str(stderr),serial);self.process_evidence=None
  observed={'commands_started':0,'stdin_bytes':0,'stdout_bytes':0,'stderr_bytes':0,'command_argument_bytes_started':0};primary=None;result=None
  try:result=_pump(self,command,data,expected,stdout,stderr,observed)
  except BaseException as e:primary=e
  result=self.process_evidence
  try:
   for path in (stdout,stderr):
    if os.path.lexists(path):self.seal_file(path)
    else:self.pending_files.pop(str(path.relative_to(self.root)),None)
  except BaseException as e:primary=durable.select(primary,e)
  for k,v in observed.items():self.c._transfer_observed[k]+=v
  try:
   self.c.publish('transfer-result-%08d.json'%serial,{'operation':self.op.ledger.identity,'kind':kind,'status':'failed' if primary else 'complete-command-only','observed':observed,'process':result,'error_type':type(primary).__name__ if primary else None,'physical_encrypted_wire_metered':False})
  except BaseException as e:primary=durable.select(primary,e)
  self.c._transfer_active=None;self._next=None
  if primary is not None:raise primary
  self.check();return stdout
 def run(self):
  primary=None;summary=None
  try:
   for index,(name,expected_hash,size) in enumerate(self.inventory):
    destination=self.root/'recovery'/name;fd=self.create_owned(destination,size);h=hashlib.sha256();total=0
    try:
     for part,offset in enumerate(range(0,size,self.p['part_bytes'])):
      count=min(self.p['part_bytes'],size-offset);self.op.reserve_next(count);data=self._source_part(name,offset,count);remote=self._remote(index,part)
      self._command('mkdir',remote,b'',0);self._command('upload',remote,data,count);received=self._command('download',remote,b'',count)
      raw=_retained_part(received,count);require(raw==data,'actual recovered part differs');h.update(raw);total+=len(raw);_write_all(fd,raw)
     require(total==size and h.hexdigest()==expected_hash,'complete recovered member hash/extent differs');os.fsync(fd)
    finally:owned_io._cleanup((lambda:os.close(fd),))
    self.seal_file(destination);self.check()
   recovery=self.root/'recovery';fd=os.open(recovery,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
   try:os.fsync(fd)
   finally:owned_io._cleanup((lambda:os.close(fd),))
   self.op.verify_local_recovery(recovery);self.recovered=True;self.check()
   summary={'schema_version':1,'kind':('selected-produced-f32-remote-roundtrip' if self.c.policy['schema_version']==3 else 'selected-f64-remote-roundtrip'),'operation':self.op.ledger.identity,'original_container_sha256':self.source._reader.reference,'complete_members':len(self.inventory),'members_sha256':digest(self._inventory_pin),'remote_parts':self.parts,'reserved':self.c._transfer_spent,'observed':self.c._transfer_observed,'remote_body_roundtrip_verified':True,'physical_encrypted_wire_metered':False,'disposition_authority':False,'local_bytes_retired':0}
   encoded(summary);self.check()
  except BaseException as e:primary=e
  try:
   if self.fd is not None:owned_io._cleanup((lambda:os.close(self.fd),),primary=primary)
  except BaseException as e:primary=durable.select(primary,e)
  self.fd=None;self.closed=True
  if primary is None:
   try:self.c.run.write_json(self.output,summary)
   except BaseException as e:primary=e
  if primary is not None:
   try:self.c.publish('transfer-failed-'+self.op.ledger.identity+'.json',{'error_type':type(primary).__name__,'reserved':self.c._transfer_spent,'observed':self.c._transfer_observed,'all_partial_files_retained':True,'disposition_authority':False})
   except BaseException as e:primary=durable.select(primary,e)
   if not self.op.ledger.context.failed:self.op.fail(primary)
   raise primary
  return summary

def _owned_snapshot(path,limit,deadline):
 parentfd=fd=None
 try:
  require(path.resolve()==path and type(limit) is int and 0<=limit<=4194304,'finite canonical owned member')
  parent=path.parent;parentfd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);ps=os.fstat(parentfd)
  require(parent.resolve()==parent and signature(parent.lstat())==signature(ps),'owned parent changed')
  before=os.stat(path.name,dir_fd=parentfd,follow_symlinks=False)
  require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600 and before.st_size<=limit,'bounded owned member required')
  fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parentfd);require(signature(os.fstat(fd))==signature(before),'owned member changed before read')
  h=hashlib.sha256();total=0
  while True:
   require(time.monotonic()<deadline,'owned read deadline');b=os.read(fd,min(65536,before.st_size-total+1))
   if not b:break
   total+=len(b);require(total<=before.st_size,'owned member grew');h.update(b)
  require(total==before.st_size and signature(before)==signature(os.fstat(fd))==signature(os.stat(path.name,dir_fd=parentfd,follow_symlinks=False))==signature(path.lstat()) and signature(ps)==signature(os.fstat(parentfd))==signature(parent.lstat()) and path.resolve()==path,'owned member/parent mutated')
  return {'bytes':total,'sha256':h.hexdigest(),'identity':list(signature(before))}
 finally:owned_io._cleanup((() if fd is None else (lambda:os.close(fd),))+(() if parentfd is None else (lambda:os.close(parentfd),)))

def _write_all(fd,raw):
 offset=0
 while offset<len(raw):
  n=os.write(fd,raw[offset:offset+65536]);require(n>0,'positive owned write progress');offset+=n

def _retained_part(path,size):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
 try:
  before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==size<=1048576,'retained part extent')
  pieces=[];total=0
  while True:
   b=os.read(fd,min(65536,size-total+1))
   if not b:break
   total+=len(b);require(total<=size,'retained part grew');pieces.append(b)
  require(total==size and signature(before)==signature(os.fstat(fd))==signature(path.lstat()),'retained part changed');return b''.join(pieces)
 finally:owned_io._cleanup((lambda:os.close(fd),))

def _pump(session,command,data,expected,stdout_path,stderr_path,observed):
 require(type(session) is Session and session._next is not None and session._next[:5]==(tuple(command),digest(data),expected,str(stdout_path),str(stderr_path)),'actual internally selected session command required')
 session.check();outfd=errfd=None;proc=None;primary=None;closed_stdin=False;returncode=None;process={'pid':None,'direct_child_reaped':False,'group_kill_requested':False,'returncode':None};session.process_evidence=process
 deadline=min(time.monotonic()+session.p['command_seconds'],session.deadline-session.p['cleanup_seconds'])
 try:
  outfd=session.create_owned(stdout_path,expected+1)
  errfd=session.create_owned(stderr_path,session.p['stderr_bytes']+1)
  proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True);observed['commands_started']=1
  observed['command_argument_bytes_started']=len(' '.join(command[command.index(session.p['connection']['user']+'@'+session.p['connection']['host'])+1:]).encode())
  process['pid']=proc.pid
  for stream in (proc.stdin,proc.stdout,proc.stderr):os.set_blocking(stream.fileno(),False)
  readfds={proc.stdout.fileno():'stdout_bytes',proc.stderr.fileno():'stderr_bytes'};offset=0
  while readfds or not closed_stdin:
   session.check();require(time.monotonic()<deadline,'selected command deadline')
   if not closed_stdin and offset==len(data):
    closed_stdin=True;proc.stdin.close()
   writable=[] if closed_stdin else [proc.stdin.fileno()]
   ready,write,_=select.select(list(readfds),writable,[],min(.05,max(0.,deadline-time.monotonic())))
   if write:
    n=os.write(proc.stdin.fileno(),data[offset:offset+65536]);require(n>0,'positive SSH stdin progress');offset+=n;observed['stdin_bytes']+=n
   for fd in ready:
    key=readfds[fd];limit=expected if key=='stdout_bytes' else session.p['stderr_bytes'];chunk=os.read(fd,min(65536,limit-observed[key]+1))
    if not chunk:del readfds[fd];continue
    observed[key]+=len(chunk);_write_all(outfd if key=='stdout_bytes' else errfd,chunk);require(observed[key]<=limit,'selected channel extent exceeded')
  require(observed['stdin_bytes']==len(data) and observed['stdout_bytes']==expected,'selected exact channel extent differs')
  remaining=deadline-time.monotonic();require(remaining>0,'command wait deadline');returncode=proc.wait(timeout=remaining);process['direct_child_reaped']=True;process['returncode']=returncode
  require(returncode==0,'selected SSH command failed');session.check();os.fsync(outfd);os.fsync(errfd)
 except BaseException as e:primary=e
 actions=[]
 if proc is not None:
  def kill():
   if proc.returncode is not None:return
   try:os.killpg(proc.pid,signal.SIGKILL);process['group_kill_requested']=True
   except ProcessLookupError:pass
  def reap():
   remaining=min(session.p['cleanup_seconds'],max(0.,session.deadline-time.monotonic()));proc.wait(timeout=remaining);process['direct_child_reaped']=True;process['returncode']=proc.returncode
  actions.extend((kill,reap))
  if not closed_stdin:closed_stdin=True;actions.append(proc.stdin.close)
  actions.extend((proc.stdout.close,proc.stderr.close))
 if outfd is not None:actions.extend((lambda:os.fsync(outfd),lambda:os.close(outfd)))
 if errfd is not None:actions.extend((lambda:os.fsync(errfd),lambda:os.close(errfd)))
 try:owned_io._cleanup(actions,primary=primary)
 except BaseException as e:primary=durable.select(primary,e)
 # The outer native guard still owns complete descendant/cgroup absence proof.
 if primary is not None:raise primary
 return process

def dispatch(operation):
 require(type(operation) is durable.Operation,'actual durable Operation required')
 operation.check()
 if not (operation.ledger.context.policy.get('schema_version')==2 or (type(operation.ledger.context.policy.get('schema_version')) is int and operation.ledger.context.policy['schema_version']==3)):raise NotImplementedError('registered selected plaintext transport policy absent')
 try:return Session(operation).run()
 except BaseException as e:
  if not operation.ledger.context.failed:operation.fail(e)
  raise
