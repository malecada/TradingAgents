import ast,hashlib,json,os,stat,types,importlib.util,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;R=H.parents[3];C=H.parent/'mcm-batched-owner-integration03-2026-10-09'
def extract(path,names,ns):
 nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
owned=load('owned',R/'tradingagents/research/onchain_replication/owned_io.py');journal=load('journal',C/'batched_journal.py')
z={'json':json,'hashlib':hashlib,'META_LIMIT':8192};extract(R/'tradingagents/research/onchain_replication/score_batches.py',{'_signature','_json','_require'},z)
io=types.SimpleNamespace(**{k:z[k] for k in ('_signature','_json','_require')},_cleanup=owned._cleanup,_release=owned._release)
policy={'schema_version':4,'max_entries':32,'max_workflow_metadata_bytes':65536,'numeric':{'max_buffer_bytes':100000,'edge_chunk':2,'extraction_limit':3},'batched':{'format':'ordered-mcm-batch-closure-v2','authority_boundaries':'entry-batch-checkpoint-final','batch_cells':32,'max_journal_bytes':100000,'max_body_bytes':1024,'max_closure_token_bytes':168,'max_checkpoint_bytes':100000,'retention':'local-v2','max_spool_bytes':128,'max_offload_metadata_bytes':1000,'max_offload_entries':100,'max_offload_anchor_bytes':0}}
results=[]
for fault in ('token-open','token-fstat','spool-open','spool-fstat','boundary-callback'):
 primary=OSError('synthetic '+fault);opened={};created=[]
 def opening(path,*a,**kw):
  kind='token' if str(path).endswith('closure-tokens.bin') else 'spool'
  if fault==kind+'-open':raise primary
  fd=os.open(path,*a,**kw);opened[fd]=kind;return fd
 def fstat(fd):
  if fault==opened.get(fd,'')+'-fstat':raise primary
  return os.fstat(fd)
 proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.open=opening;proxy.fstat=fstat
 def make(*a,**kw):
  j=journal.BatchJournal(*a,**kw);created.append(j);return j
 def boundary():raise primary
 def drive(*a,**kw):kw['journal'].boundary()
 ns={'os':proxy,'stat':stat,'hashlib':hashlib,'io':io,'require':io._require,'thaw':lambda x:x,'FORMAT':policy['batched']['format']}
 extract(C/'compact_mcm_batched.py',{'selected','validate','_checkpoint_inventory','_compute'},ns)
 root=H/fault;root.mkdir();stage=types.SimpleNamespace(root=root);target=types.SimpleNamespace(dictionary=None,owner=types.SimpleNamespace(policy={'pair':{},'schedule':{}},matching={}))
 mods={'journal':types.SimpleNamespace(BatchJournal=make),'executor':types.SimpleNamespace(PairExecutor=lambda *a:None),'driver':types.SimpleNamespace(drive=drive)}
 try:ns['_compute'](target,stage,None,policy,{'cells':32,'rows':1,'graph_hash':'a'*64,'scope':{'workflow':'b'*64,'node_order':'c'*64}},mods,boundary)
 except OSError as e:assert e is primary
 else:raise AssertionError('no failure')
 live=[]
 for fd,kind in list(opened.items())+[(j.fd,'journal') for j in created]:
  try:os.fstat(fd)
  except OSError:pass
  else:live.append(kind);os.close(fd)
 results.append({'fault':fault,'primary_preserved':True,'leaked_descriptors':live,'journal_closed':created[0].closed})
assert all(not x['leaked_descriptors'] and x['journal_closed'] for x in results)
# Constructor's inherited resource acquisition is separately fault-injected;
# no actual ownership capability or numerical module is involved.
constructor=[]
for fault in ('journal-fstat','parent-open','parent-fsync'):
 original_os=journal.os;fds={};primary=OSError('synthetic '+fault)
 def opening(path,*a,**kw):
  kind='journal' if str(path).endswith('/matching') else 'parent'
  if fault=='parent-open' and kind=='parent':raise primary
  fd=os.open(path,*a,**kw);fds[fd]=kind;return fd
 def fstat(fd):
  if fault=='journal-fstat':raise primary
  return os.fstat(fd)
 def fsync(fd):
  if fault=='parent-fsync':raise primary
  return os.fsync(fd)
 proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.open=opening;proxy.fstat=fstat;proxy.fsync=fsync;journal.os=proxy
 root=H/fault;root.mkdir()
 try:journal.BatchJournal(root/'matching',batch_cells=32,max_cells=32,max_bytes=100000,max_body_bytes=1024,boundary=lambda:None)
 except OSError as e:assert e is primary
 else:raise AssertionError('no failure')
 finally:journal.os=original_os
 live=[]
 for fd,kind in fds.items():
  try:os.fstat(fd)
  except OSError:pass
  else:live.append(kind);os.close(fd)
 assert live==[];constructor.append({'fault':fault,'leaked_descriptors':live,'primary_preserved':True})
out={'compute_cases':results,'inherited_journal_constructor_cases':constructor,'authority_objects':False,'numerical_imports':False};(H/'ACQUISITION02.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
