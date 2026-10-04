import importlib.util,json,os
from pathlib import Path
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('m',H/'workflow_storage.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=H/'final-no-primary';p.mkdir();rows=[]
for cls in (RuntimeError,KeyboardInterrupt,MemoryError,SystemExit):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);error=cls('close')
 def action():os.close(fd);raise error
 try:m._cleanup(action)
 except BaseException as selected:
  if cls is RuntimeError:assert type(selected) is m.StorageCleanupFailure and selected.storage_cleanup_errors==(error,)
  else:assert selected is error
  try:os.fstat(fd)
  except OSError:pass
  else:raise AssertionError('not closed')
  rows.append({'secondary':cls.__name__,'selected':type(selected).__name__,'original_error_retained':True,'actual_descriptor_closed':True})
 else:raise AssertionError('failed close accepted')
print(json.dumps({'cases':len(rows),'results':rows},indent=2))
