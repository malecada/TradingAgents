import ast,hashlib,json,types
from pathlib import Path
D=Path(__file__).parent;F=D.parent;source=F/'real-data-pilot-first-graph-post-recovery-retirement01-2026-10-06/retire02.py'
raw=source.read_bytes();tree=ast.parse(raw);execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');block=next(n for n in execute.body if isinstance(n,ast.Try));code=compile(ast.fix_missing_locations(ast.Module(body=[block],type_ignores=[])),'actual-retirement-try-AST','exec')
results=[]
for fail_sync,fail_publish in [(1,False),(2,False),(1,True)]:
 state={'actual_removed':[],'records':{},'syncs':0}
 class P:
  def __init__(self,name):self.name=name
  def __truediv__(self,name):return P(name)
  @property
  def parent(self):return P('parent')
  def relative_to(self,_):return self.name
  def unlink(self):state['actual_removed'].append(self.name)
  def lstat(self):return 'identity'
 class Held:
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def fileno(self):return 3
 def sync(_):
  state['syncs']+=1
  if state['syncs']==fail_sync:raise OSError('synthetic directory sync failure')
 def publish(path,value):
  if path.name=='failed01.json' and fail_publish:raise RuntimeError('synthetic failure receipt write failure')
  state['records'][path.name]=json.loads(json.dumps(value))
 g={'os':types.SimpleNamespace(fdopen=lambda *a:Held(),open=lambda *a:3,O_RDONLY=0,O_NOFOLLOW=0,fstat=lambda fd:'identity'),'fcntl':types.SimpleNamespace(flock=lambda *a:None,LOCK_EX=1,LOCK_NB=2),'cold':types.SimpleNamespace(identity=lambda s:s,publish=publish,validate_source=lambda *a:None,sync_directory=sync),'original':P('ledger.sqlite'),'recovered':P('00-recovered.bin'),'row':{'stat_identity':'identity','bytes':4},'recovered_identity':'identity','sidecar':P('ledger.sqlite.remote.json'),'kept':{},'removed':[],'ROOT':P('root'),'HERE':P('here'),'BACKUP':P('backup'),'ID':'offline-only'}
 try:exec(code,g)
 except BaseException as error:state['escaped_type']=type(error).__name__;state['escaped_message']=str(error);state['notes']=getattr(error,'__notes__',[])
 results.append(state)
assert results[0]['actual_removed']==['ledger.sqlite'] and results[0]['records']['failed01.json']['removed']==['ledger.sqlite']
assert results[1]['actual_removed']==['ledger.sqlite','00-recovered.bin'] and results[1]['records']['failed01.json']['removed']==['ledger.sqlite','00-recovered.bin']
assert results[2]['escaped_type']=='OSError' and 'failure receipt write failure' in results[2]['notes'][0]
output={'source_sha256':hashlib.sha256(raw).hexdigest(),'results':results,'qualification':'Actual extracted try AST with fake path unlink/sync/publication; no file deleted, no native/network/graph read.'}
(D/'SOURCE_CORRECTION02.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(json.dumps(output,sort_keys=True))
