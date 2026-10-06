import importlib.util,json,tempfile
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;S=H.parent/'real-data-pilot-second-graph-preservation-continuation01-2026-10-06/continue01.py'
spec=importlib.util.spec_from_file_location('original_metadata_helper',S);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class Primary(BaseException):pass
class Secondary(BaseException):pass
primary=Primary('synthetic transport failure');secondary=Secondary('synthetic failed-receipt publication failure')
def publish(path,value):
 if path.name=='failed.json':raise secondary
h.bind_primitives=lambda root:SimpleNamespace(publish=publish)
h.select=lambda root,binding:{'binding':{},'remote':'synthetic'}
def unavailable():raise primary
with tempfile.TemporaryDirectory(dir=H) as t:
 root=Path(t);here=root/h.DEST;here.mkdir(parents=True)
 try:h.preserve_selected(root,here,h.select(root,{}),SimpleNamespace(remaining=8*h.GIB,available=unavailable),lambda:None)
 except BaseException as e:
  assert e is secondary and e.__context__ is primary
  print(json.dumps({'source_b620_primary_replaced':True,'primary_retained_only_as_context':True,'actual_outer_error_type':'Secondary','native_or_payload_or_authority':False}))
 else:raise AssertionError('failure suppressed')
