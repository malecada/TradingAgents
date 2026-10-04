import importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;B=H.parent;out=[]
for label,directory,name in [('actual-original',B/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04','original_workflow_storage.py'),('withheld01',B/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04','workflow_storage.py'),('successor02',B/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04','workflow_storage.py')]:
 s=importlib.util.spec_from_file_location('m',directory/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.os=SimpleNamespace(**vars(os));p=H/'diagnostic-boundary'/label;p.mkdir(parents=True);(p/'f').write_bytes(b'x');hooks=[];closed=[]
 class First(KeyboardInterrupt):
  @property
  def __cause__(self):hooks.append('cause-property');raise SystemExit('diagnostic replacement')
 first=First('original fatal')
 def st(path,*a,**kw):
  if path=='f':raise first
  return os.stat(path,*a,**kw)
 def close(fd):os.close(fd);closed.append(fd)
 m.os.stat=st;m.os.close=close
 try:m.StorageWatch(p,dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)).check()
 except BaseException as selected:
  q=[selected];found=[]
  while q:
   e=q.pop()
   if any(e is x for x in found):continue
   found.append(e)
   for key in ('__cause__','__context__'):
    node=BaseException.__dict__[key].__get__(e)
    if node is not None:q.append(node)
  assert selected is not first and type(selected)is SystemExit and len(closed)==1 and any(first is x for x in found)
  trace=[];tb=selected.__traceback__
  while tb:trace.append({'source':tb.tb_frame.f_code.co_filename,'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno});tb=tb.tb_next
  out.append({'source':label,'selected_type':type(selected).__name__,'original_fatal_selected':False,'original_fatal_retained_in_context':True,'hooks':hooks,'actual_root_descriptor_closed_once':True,'traceback':trace})
 else:raise AssertionError('fatal swallowed')
(H/'DIAGNOSTIC_BOUNDARY01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
