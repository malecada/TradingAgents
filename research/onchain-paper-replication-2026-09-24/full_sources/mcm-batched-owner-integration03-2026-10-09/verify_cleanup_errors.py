"""Actual AST acquisition scopes; synthetic OS failures, no numerical imports."""
from pathlib import Path
H=Path(__file__).resolve().parent
setup=(H/'verify_acquisition.py').read_text().split('results=[]')[0]
exec(compile(setup,str(H/'verify_acquisition.py'),'exec'))
results=[]
for fault in ('cleanup-error','descriptor-allocation'):
 opened={};created=[];closed=[];primary=MemoryError('synthetic descriptor allocation') if fault=='descriptor-allocation' else OSError('synthetic body failure')
 def opening(path,*a,**kw):
  fd=os.open(path,*a,**kw);opened[fd]='token' if str(path).endswith('closure-tokens.bin') else 'spool';return fd
 def closing(fd):
  closed.append(opened[fd]);os.close(fd)
  if fault=='cleanup-error' and opened[fd]=='token':raise OSError('synthetic token cleanup failure after actual close')
 proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.open=opening;proxy.close=closing
 def make(*a,**kw):
  j=journal.BatchJournal(*a,**kw);created.append(j);return j
 def drive(*a,**kw):raise primary
 class Scope(dict):
  def __getitem__(self,k):
   if k=='node_order' and fault=='descriptor-allocation':raise primary
   return super().__getitem__(k)
 ns={'os':proxy,'stat':stat,'hashlib':hashlib,'io':io,'require':io._require,'thaw':lambda x:x,'FORMAT':policy['batched']['format']}
 extract(C/'compact_mcm_batched.py',{'selected','validate','_checkpoint_inventory','_compute'},ns)
 root=H/fault;root.mkdir();stage=types.SimpleNamespace(root=root);target=types.SimpleNamespace(dictionary=None,owner=types.SimpleNamespace(policy={'pair':{},'schedule':{}},matching={}))
 mods={'journal':types.SimpleNamespace(BatchJournal=make),'executor':types.SimpleNamespace(PairExecutor=lambda *a:None),'driver':types.SimpleNamespace(drive=drive)}
 try:ns['_compute'](target,stage,None,policy,{'cells':32,'rows':1,'graph_hash':'a'*64,'scope':Scope(workflow='b'*64,node_order='c'*64)},mods,lambda:None)
 except BaseException as e:assert e is primary
 else:raise AssertionError('missing injected failure')
 assert closed==['token','spool'] and created[0].closed
 for fd in list(opened)+[created[0].fd]:
  try:os.fstat(fd)
  except OSError:pass
  else:raise AssertionError('descriptor leak')
 notes=getattr(primary,'__notes__',[])
 if fault=='cleanup-error':assert 'token cleanup failure' in notes[0]
 results.append({'fault':fault,'primary_preserved':True,'all_cleanup_attempted':True,'notes':notes})
# A healthy constructor still returns one open root descriptor and closes it.
root=H/'healthy-constructor';root.mkdir();j=journal.BatchJournal(root/'matching',batch_cells=32,max_cells=32,max_bytes=100000,max_body_bytes=1024,boundary=lambda:None);os.fstat(j.fd);j.close();assert j.closed
(H/'CLEANUP_RESULT01.json').write_text(json.dumps({'results':results,'healthy_constructor':True,'numerical_imports':False},indent=2)+'\n');print(json.dumps(results))
