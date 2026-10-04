import ast,gc,hashlib,importlib.util,json,weakref
from pathlib import Path
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('metadata_only_detached',D/'overlay/compact_detached_handoff.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
n=0
def yes(v):
 global n
 assert v;n+=1
def refuse(fn):
 try:fn()
 except (ValueError,AttributeError):yes(True)
 else:raise AssertionError('expected refusal')
class Sentinel:pass
s=Sentinel();ref=weakref.ref(s)
for value in [s,lambda:s,{'producer':s},{'x':float('nan')},{'x':float('inf')},{1:'non-string'},(1,2)]:refuse(lambda:m.encoded(value))
value=None
payload={'status':m.STATUS,'lifetime':'original-reader-sampled-content-v1','components':{'a':{'nodes':3,'shape':[3,32]}}}
r=m.Record(payload);payload['components']['a']['nodes']=999;yes(r.metadata()['components']['a']['nodes']==3)
copy=r.metadata();copy['components'].clear();yes(len(r.metadata()['components'])==1)
refuse(lambda:setattr(r,'_raw',b'changed'));refuse(lambda:m.Authority(r,s,_key=object()))
s=None;gc.collect();yes(ref() is None)
yes(m.Record.__slots__==('_raw',));yes(m.Authority.__slots__==('_record','_run_ref'))
refuse(lambda:m.Record({'status':'representation_complete'}));refuse(lambda:m.Record({'status':m.STATUS}).require_loader())
# No project/numerical imports were executed by the tests.
import sys
yes(not any(x in sys.modules for x in ('numpy','torch','pandas')))
old=ast.parse((D/'ORIGINAL_compact_native_features.py.txt').read_text());new=ast.parse((D/'overlay/compact_native_features.py').read_text())
for node in old.body:
 if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
  found=next(x for x in new.body if type(x)is type(node) and x.name==node.name);yes(ast.dump(node)==ast.dump(found))
source=(D/'overlay/compact_detached_handoff.py').read_text();tree=ast.parse(source)
a=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Authority');yes('weakref.ref(run)' in ast.unparse(a));yes(not any(isinstance(x,ast.Name) and x.id=='terminal' for x in ast.walk(a)))
f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='prepare');yes('lease=authority.lease' in ast.unparse(f) and 'read_lease=authority.lease' in ast.unparse(f));yes('terminal.check()' in ast.unparse(f))
for p in (D/'overlay').glob('*.py'):ast.parse(p.read_text());yes(True)
print(json.dumps({'checks':n,'actual_genuine_factory':False,'actual_loader_or_arrays':False,'record_does_not_retain_sentinel':True}))
