import importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;out=[]
limits=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
for module in ('DRAFT02_interleaved_rejoin','workflow_storage'):
 s=importlib.util.spec_from_file_location(module,H/(module+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.os=SimpleNamespace(**{k:getattr(os,k) for k in dir(os)})
 p=H/'controls17'/module;p.mkdir(parents=True);(p/'a').write_bytes(b'x');(p/'z').mkdir();(p/'z'/'q').write_bytes(b'y')
 done=False;scandir=os.scandir
 class Iterator:
  def __init__(self,path):self.path=path;self.inner=scandir(path)
  def __iter__(self):return self
  def __next__(self):return next(self.inner)
  def close(self):
   global done
   self.inner.close()
   if self.path==p/'z' and not done:
    done=True
    with (p/'a').open('ab') as f:f.write(b'zz')
 m.os.scandir=Iterator
 r=m.StorageWatch(p,limits).check();row={'module':module,'logical_returned':r['logical_file_bytes'],'actual_logical':4,'attempts':r['scan_attempts'],'later_namespace_close_callback_executed':done};out.append(row)
 if module=='workflow_storage':assert done and r['logical_file_bytes']==4 and r['scan_attempts']==2
 else:assert done and r['logical_file_bytes']==2 and r['scan_attempts']==1
print(json.dumps({'status':'EXACT_PRELIMINARY_STALE_CLOSE_RED_FINAL_GREEN','results':out},indent=2))
