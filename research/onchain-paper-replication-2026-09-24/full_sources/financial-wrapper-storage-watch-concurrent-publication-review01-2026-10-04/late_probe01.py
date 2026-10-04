import importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04';out=[]
for i in range(12):
 spec=importlib.util.spec_from_file_location('candidate',A/'workflow_storage.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.os=SimpleNamespace(**vars(os))
 p=H/'lateprobe'/str(i);p.mkdir(parents=True);(p/'a').write_bytes(b'x');(p/'z').mkdir();(p/'z'/'q').write_bytes(b'y');events=[];done=[False]
 class It:
  def __init__(self,path):self.path=path;self.inner=os.scandir(path)
  def __iter__(self):return self
  def __next__(self):return next(self.inner)
  def close(self):
   self.inner.close()
   if self.path==p/'z' and not done[0]:
    done[0]=True;b=m._signature(p.stat());(p/'extra').write_bytes(b'new');a=m._signature(p.stat());events.append({'event':'add','before':b,'after':a})
 m.os.scandir=It
 w=m.StorageWatch(p,dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5));r=w.check();out.append({'i':i,'logical':r['logical_file_bytes'],'attempts':r['scan_attempts'],'events':events})
(H/'LATE_PROBE01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
