import dataclasses,importlib.util,json,os,sys
from pathlib import Path
import spool05 as new
P=Path(__file__).resolve().parent
oldpath=P.with_name('financial-batch-output-transport-spool-preparation02-2026-10-04')/'spool04.py'
spec=importlib.util.spec_from_file_location('old04',oldpath);old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
rows=[]
for label,M in (('old',old),('new',new)):
 for method in ('check','transfer'):
  parent=P/(label+'-'+method);parent.mkdir(mode=0o700);root=parent/'root';root.mkdir(mode=0o700)
  plan=M.Plan((M.Member(0,0,1,M.digest(b'x')),),1,0,0);l,a=plan.required();plan=dataclasses.replace(plan,logical_reservation=l,allocated_reservation=a);s=M.Spool(root,plan);consumed=s.consumed
  realclose=os.close;events=[];moved=parent.with_name(parent.name+'-moved');error=None;calls=[]
  def close(fd):
   realclose(fd);events.append(fd)
   if len(events)==1:parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
  def send(identity,m,body):
   calls.append('send');return M.Ack(identity,m.page,m.chunk,m.size,m.sha256,'a'*64)
  try:
   os.close=close
   if method=='check':s.check()
   else:s.transfer(b'x',send,lambda a:M.Recovery(a,b'x'))
  except BaseException as e:error=e
  finally:os.close=realclose
  assert s.root.resolve()!=s.root
  if label=='new':
   assert isinstance(error,ValueError) and str(error)=='post-cleanup canonical root changed'
   if method=='transfer':assert s.failed and calls==[] and s.states==('ABSENT',) and 'terminal' in s._sealed
  elif method=='check':assert error is None
  else:
   # Old check first accepts; the subsequent pre-send check sees the already
   # installed symlink and refuses. This is NOT an old successful transfer claim.
   assert isinstance(error,OSError) and s.failed
  for fd in events:
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('ancestry descriptor leaked')
  assert consumed==s.consumed
  rows.append({'source':label,'operation':method,'error':None if error is None else type(error).__name__,'message':None if error is None else str(error),'failed':s.failed,'states':s.states,'callbacks':calls,'actual_walk_closes':len(events),'literal_target':os.readlink(parent),'consumed_unchanged':True,'sampled_not_continuous':True})
  s.close()
(P/'SP4_WITNESS01.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n');print(len(rows),'SP4 controls passed')
