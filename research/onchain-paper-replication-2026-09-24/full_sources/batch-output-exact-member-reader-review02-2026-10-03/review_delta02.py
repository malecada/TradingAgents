"""Independent source delta and actual local-byte old/new counterexample."""
import ast,hashlib,importlib.util,json,os,sys
from pathlib import Path
from types import MappingProxyType
P=Path(__file__).resolve().parent;S=P.with_name('batch-output-exact-member-reader-candidate02-2026-10-03');R=P.parents[3]
def h(b):return hashlib.sha256(b).hexdigest()
m=json.loads((S/'MANIFEST02.json').read_bytes());assert h((S/'MANIFEST02.json').read_bytes())=='04ff6e68a5dfd7f30e3ecccdeaffb57995ad9647285abb7fb3d29b76c57d826e'
for row in m['files']:
 b=(S/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
for row in json.loads((S/'dependency-pins02.json').read_bytes())['files']:
 b=(R/row['path']).read_bytes();assert len(b)==row['bytes'] and h(b)==row['sha256']
old=ast.parse((S/'baseline01.py').read_bytes());new=ast.parse((S/'exact_members02.py').read_bytes());cl=next(x for x in new.body if isinstance(x,ast.ClassDef) and x.name=='LocalContent');delta=[x for x in cl.body if isinstance(x,ast.FunctionDef) and x.name=='__delattr__'];assert len(delta)==1
assert len(delta[0].body)==1 and isinstance(delta[0].body[0],ast.Raise)
cl.body=[x for x in cl.body if x not in delta];assert ast.dump(new)==ast.dump(old)
sys.path.insert(0,str(S))
def load(name,file):
 s=importlib.util.spec_from_file_location(name,S/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
mods=[load('old_reader','baseline01.py'),load('new_reader','exact_members02.py')]
def fixture(name,module):
 root=P/name;root.mkdir();data=bytes(128);(root/'matrix.f32').write_bytes(data)
 v={'schema_version':1,'kind':'compact-mcm-output','stage_sha256':'ab'*32,'contract_sha256':'cd'*32,'stage_directory':'/original/stage','scope':{k:'12'*32 for k in module.SCOPES},'owner':'ef'*32,'rows':1,'motifs':32,'dtype':'<f4','order':'row-major','array_bytes':128,'array_sha256':h(data),'execution_admitted':False}
 raw=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode();(root/'manifest.json').write_bytes(raw);return root,data,h(raw)
results=[]
for index,module in enumerate(mods):
 root,data,pin=fixture('tiny-replacement-'+str(index+1),module);out={'version':index+1}
 try:
  with module.open_local(root,kind='mcm-output',document_sha256=pin) as r:
   original=r._files['matrix.f32'][0];(root/'new.tmp').write_bytes(data);os.replace(root/'new.tmp',root/'matrix.f32')
   try:r.check()
   except ValueError:out['original_replacement_refused']=True
   else:raise AssertionError('missing initial refusal')
   try:del r._frozen
   except AttributeError:
    out['deletion_refused']=True
    try:r._pin=()
    except AttributeError:out['reassignment_refused']=True
    else:raise AssertionError('assign after refused delete')
    try:r.read_part('matrix.f32',0,8)
    except ValueError:out['replacement_still_refused']=True
    else:raise AssertionError('replacement admitted')
   else:
    out['deletion_refused']=False;files=dict(r._files);record,_=r._read('matrix.f32',128,expected=h(data),extent=128);assert record[0]!=original;files['matrix.f32']=record
    r._files=MappingProxyType(files);r._pin=tuple(sorted(files.items()));r._frozen=True;r.check();assert r.read_part('matrix.f32',0,8)==data[:8]
 except ValueError as error:out['context_exit']='refused';out['reason']=str(error)
 else:out['context_exit']='accepted'
 assert r.closed is True;results.append(out)
assert results[0]['deletion_refused'] is False and results[0]['context_exit']=='accepted'
assert results[1]['deletion_refused'] is True and results[1]['context_exit']=='refused'
module=mods[1];root,data,pin=fixture('tiny-valid-slots02',module)
with module.open_local(root,kind='mcm-output',document_sha256=pin) as r:
 for name in r.__slots__:
  old=getattr(r,name)
  for action in [lambda:delattr(r,name),lambda:setattr(r,name,old)]:
   try:action()
   except AttributeError:pass
   else:raise AssertionError('mutable slot '+name)
 assert not hasattr(r,'__dict__')
 for field in [r._files,r._payload]:
  try:field['matrix.f32']=()
  except TypeError:pass
  else:raise AssertionError('mutable map')
 assert r.read_part('matrix.f32',0,8)==data[:8]
assert r.closed is True
assert not {'numpy','torch','scipy'}&set(sys.modules)
print(json.dumps({'manifest_bodies':len(m['files']),'whole_AST_equal_except_delattr':True,'actual_old_new_results':results,'all_slots_deletion_assignment_refused':list(r.__slots__),'mapping_proxy_and_no_dict':True,'unchanged_valid_read_exit_close':True,'numerical_imports_jobs_transport':False},indent=2))
