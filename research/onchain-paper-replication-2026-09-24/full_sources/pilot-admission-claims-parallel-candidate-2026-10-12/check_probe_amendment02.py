"""Focused scheduler interruption + final done-probe secondary fatal control."""
import concurrent.futures,json,runpy,tempfile,time
from pathlib import Path
from unittest.mock import patch
ns=runpy.run_path(str(Path(__file__).with_name('check_candidate01.py')))
original=concurrent.futures.ThreadPoolExecutor
primary=KeyboardInterrupt('original wait interruption');secondary=SystemExit('final probe fatal')
class Executor(original):
 def shutdown(self,**kw):
  result=super().shutdown(**kw)
  for f in futures:
   f.done=lambda:(_ for _ in ()).throw(secondary)
  return result
 def submit(self,*a,**kw):
  f=super().submit(*a,**kw);futures.append(f);return f
futures=[];completed=[]
with tempfile.TemporaryDirectory() as d:
 root=Path(d);folder=root/'research_runs';folder.mkdir()
 for name in ('a','b'):(folder/name).mkdir();(folder/name/'claim.json').write_text('{}')
 def proof(p):time.sleep(.025);completed.append(p.name);return {'experiment_id':p.name}
 env=ns['load'](Path(__file__).with_name('admission.py'),proof)
 with patch.object(concurrent.futures,'ThreadPoolExecutor',Executor),patch.object(concurrent.futures,'wait',side_effect=primary):
  try:env['claims'](root,workers=2)
  except BaseException as caught:
   assert caught is primary
   assert any('SystemExit' in n for n in caught.__notes__)
  else:raise AssertionError('must preserve failure')
 assert set(completed)=={'a','b'}
print(json.dumps({'status':'PASS','primary_preserved':True,'launched_drained':2,'probe_failure_recorded':True}))
