"""Tiny byte IO controls; AST load excludes NumPy imports and never calls numerical code."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys,types,tempfile
R=Path.cwd();O=Path(__file__).parent.resolve();C=O/'candidate';B=R/'tradingagents/research/onchain_replication'
pkg=types.ModuleType('durability_checks');pkg.__path__=[];sys.modules[pkg.__name__]=pkg

def load(name,path,without_numpy=False):
 tree=ast.parse(path.read_text())
 if without_numpy:tree.body=[n for n in tree.body if not isinstance(n,ast.Import) or all(a.name!='numpy' for a in n.names)]
 m=types.ModuleType('durability_checks.'+name);m.__package__=pkg.__name__;sys.modules[m.__name__]=m;setattr(pkg,name,m);exec(compile(tree,str(path),'exec'),m.__dict__);return m
load('owned_io',B/'owned_io.py');io=load('score_batches',B/'score_batches.py',True);helper=load('chunk_durability',C/'chunk_durability.py');pair=load('compact_pair_log',C/'compact_pair_log.py');tail=load('score_tail',C/'score_tail.py',True)
policy={'schema_version':1,'scope':'resource-pilot-only','pair_records':3,'tail_records':3,'max_interval_ms':60000};scope={k:'1'*64 for k in pair.FIELDS};limits={'chunk_events':4,'max_events':8,'max_pairs':4,'max_logical_bytes':8*pair.RECORD_BYTES+2*io.META_LIMIT}
base=O/'tiny';base.mkdir();sync=os.fsync;calls=[]
def counted(fd):calls.append((os.fstat(fd).st_ino,os.fstat(fd).st_size));return sync(fd)
os.fsync=counted
try:
 logs=[]
 for mode in ('legacy','selected'):
  log=pair.PairLog(base/mode,owner='2'*64,scope=scope,limits=limits,max_iterations=3,lease=lambda:None)
  if mode=='selected':log.enable_durability(policy)
  for i in range(3):
   log.begin('3'*64,'4'*64);log.complete(.5,'temperature_complete',1)
  if mode=='selected':assert log.durability_status['durable_records']==4 and log.events==6
  log.finish();logs.append(log)
 for n in ('start.json','events-000000000000.bin','events-000000000001.bin','terminal.json'):
  assert (logs[0].root/n).read_bytes()==(logs[1].root/n).read_bytes(),n
 # Count only record fsyncs, excluding empty creation and all metadata/directory IO.
 counts=[]
 for log in logs:
  inodes={(log.root/n).stat().st_ino for n in ('events-000000000000.bin','events-000000000001.bin')}
  counts.append(sum(ino in inodes and size>0 for ino,size in calls))
 assert counts==[6,3],counts
 tscope={k:'5'*64 for k in io.SCOPE_FIELDS};tails=[]
 for mode in ('tail-legacy','tail-selected'):
  t=tail.ScoreTail(base/mode,scope=tscope,owner='2'*64,start_cell=0,cells=4,destination='6'*64,lease=lambda:None,durability=policy if mode.endswith('selected') else None)
  for i in range(2):t.append(i,'7'*64,.25)
  if mode.endswith('selected'):assert t.durability_status['durable_records']==0
  t.close();tails.append(t)
 assert (tails[0].root/'start.json').read_bytes()==(tails[1].root/'start.json').read_bytes()
 assert (tails[0].root/'records.bin').read_bytes()==(tails[1].root/'records.bin').read_bytes()
 assert tails[1].durability_status['durable_records']==2
 # Actual fsync error must not advance durable prefix or permit later writes.
 log=pair.PairLog(base/'fsync-failure',owner='2'*64,scope=scope,limits=limits,max_iterations=3,lease=lambda:None);log.enable_durability(policy);log.begin('3'*64,'4'*64);assert log.durability_status['durable_records']==0
 primary=OSError('injected actual fsync refusal');target=log.chunk_fd
 def fail(fd):
  if fd==target:raise primary
  return sync(fd)
 os.fsync=fail
 try:log.durability_barrier()
 except OSError as e:assert e is primary
 else:raise AssertionError('fsync failure accepted')
 assert log.durability_status['durable_records']==0 and log._durability.poisoned
 try:log.complete(.5,'temperature_complete',1)
 except ValueError:pass
 else:raise AssertionError('poison reused')
 os.fsync=sync
 try:log.close()
 except BaseException:pass
 assert log.closed
 # Finite elapsed-time check at next writer activity, with a clock selected before construction.
 clock=[0.0];real_clock=helper.time.monotonic;helper.time.monotonic=lambda:clock[0]
 d=helper.BatchSync(policy,'tail');helper.time.monotonic=real_clock
 fd=os.open(base/'clock.bin',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600)
 try:
  os.write(fd,b'x');d.acknowledge(fd,1,'a');assert d.durable==0;clock[0]=61.;d.before(fd);assert d.durable==1
  clock[0]=60.
  try:d.before(fd)
  except ValueError:pass
  else:raise AssertionError('reversed clock accepted')
 finally:os.close(fd)
finally:os.fsync=sync
for name,v in json.loads((O/'INVERSE01.json').read_bytes()).items():
 s=(R/v['baseline']).read_text();assert hashlib.sha256(s.encode()).hexdigest()==v['before_sha256']
 for e in v['literal_edits']:assert e['before'] in s;s=s.replace(e['before'],e['after'])
 assert s==(C/name).read_text();ast.parse(s)
print(json.dumps({'decision':'pass','pair_binary_and_start_terminal_parity':True,'pair_record_fsyncs':counts,'tail_bytes_and_close_flush':True,'failed_flush_does_not_advance_or_allow_reuse':True,'time_due_and_backward_refusal':True,'exact_source_inverses':6,'numpy_imported':'numpy' in sys.modules,'scientific_execution':False}))
