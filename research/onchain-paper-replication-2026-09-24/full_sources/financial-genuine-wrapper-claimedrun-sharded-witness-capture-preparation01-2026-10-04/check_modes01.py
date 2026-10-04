import ast,importlib.util,json,os,sys,time,types
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
s=(H/'capture_witness01.py').read_text();ns={'__name__':'offline','__file__':str(H/'capture_witness01.py')};exec(compile(s,'candidate','exec'),ns)
spec=importlib.util.spec_from_file_location('planner',H/'shards01.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
n=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main');start=next(i for i,x in enumerate(n.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in x.targets));f=ast.FunctionDef(name='fixture',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=n.body[start:],decorator_list=[]);ast.fix_missing_locations(f)
checks=[]
for kind in ('mode','link','body'):
 here=H/('mutation-'+kind);here.mkdir();root=here/'original';root.mkdir();(root/'byte').write_bytes(b'opaque');(root/'link').symlink_to('literal');source=here/'source';source.mkdir();(source/'byte').write_bytes(b'opaque source');m=R.scan(source)
 local=dict(ns,HERE=here,SCOPES={'single':root},SOURCE=source,source_manifest=m,start=time.monotonic(),planner=P);proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)})
 def pack(a,b,c):
  result=R.pack(a,b,c)
  if kind=='mode':(root/'byte').chmod(0o600 if (root/'byte').stat().st_mode&0o777!=0o600 else 0o644)
  elif kind=='link':(root/'link').unlink();(root/'link').symlink_to('other literal')
  else:(root/'byte').write_bytes(b'changed opaque')
  return result
 proxy.pack=pack;exec(compile(ast.Module(body=[f],type_ignores=[]),'owned suffix','exec'),local)
 try:local['fixture'](proxy)
 except ValueError as e:assert 'complete original membership' in str(e);checks.append(kind+' changed refuses before auth')
 else:raise AssertionError(kind)
 assert not (here/'UNION_AUTHENTICATION01.json').exists()
(H/'MODE_CHECKS01.json').write_text(json.dumps(checks,indent=2)+'\n');print(len(checks))
