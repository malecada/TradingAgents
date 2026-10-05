"""Exact new branch, with clearly synthetic metadata adapters; no genuine handles."""
from pathlib import Path
import ast,copy,hashlib,json,weakref,sys
D=Path(__file__).resolve().parent;s=(D/'training_batch_observer.py').read_text();old=(D/'original_training_batch_observer.py').read_text();checks=[]
def ck(n,v):assert v,n;checks.append(n)
def require(v,m):
 if not v:raise ValueError(m)
def refusal(n,fn):
 try:fn()
 except (ValueError,KeyError):checks.append(n);return
 raise AssertionError(n)
t=ast.parse(s);f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='authority');tr=next(n for n in f.body if isinstance(n,ast.Try));branch=copy.deepcopy(tr.body[0]);branch.body=[n for n in branch.body if not isinstance(n,ast.ImportFrom)]
# Only import resolution is replaced. The complete actual new branch is retained.
fn=ast.FunctionDef(name='branch',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='run'),ast.arg(arg='features')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[branch],decorator_list=[])
class SyntheticRun:pass
class SyntheticRecord:
 def __init__(self,valid=True):self.valid=valid
 def require_loader(self):require(self.valid,'synthetic exact lifetime predicate refusal')
class SyntheticAuthority:
 def __init__(self,run,value):self._run_ref=weakref.ref(run);self._record=SyntheticRecord();self.value=value;self.failure=None;self.calls=0
 def lease(self):
  self.calls+=1
  if self.failure is not None:raise self.failure
  return copy.deepcopy(self.value)
class SyntheticFeatures:pass
base={'lifetime':'original-reader-sampled-content-v1','binding':{'feature_hashes':{'opaque':'pin'}},'terminal':{'owner':'opaque-metadata-owner','resident_originals_retained':True}}
env={'_DetachedFeatures':SyntheticFeatures,'Authority':SyntheticAuthority,'require':require,'thaw':lambda x:x,'sha':lambda b:hashlib.sha256(b).hexdigest(),'encode':lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'exact-new-branch','exec'),env);call=env['branch']
r=SyntheticRun();a=SyntheticAuthority(r,base);feature=SyntheticFeatures();feature._authority=a;feature._hashes={'opaque':'pin'}
# Old exact type predicate refuses a detached object, irrespective of metadata.
oldf=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name=='authority');oldtr=next(n for n in oldf.body if isinstance(n,ast.Try));oldreq=oldtr.body[0];oldenv={'run':r,'features':feature,'ResearchRun':SyntheticRun,'_Features':type('SyntheticResident',(),{}),'require':require};refusal('old resident predicate refuses detached',lambda:exec(compile(ast.Module(body=[oldreq],type_ignores=[]),'original-predicate','exec'),oldenv))
result=call(r,feature);ck('one delegated lease',a.calls==1);ck('current retention unknown',result['resident_originals_retained'] is None and result['parent_population_object_census'] is None);ck('historical flag distinguished',result['historical_resident_originals_retained'] is True);ck('no invented owner binding hash',result['binding_sha256'] is None)
other=SyntheticRun();refusal('wrong run',lambda:call(other,feature));a._record.valid=False;refusal('record loader lifetime',lambda:call(r,feature));a._record.valid=True
for name,mutate in [('lifetime',lambda v:v.update(lifetime='sealed-copy')),('lineageflag',lambda v:v['terminal'].update(resident_originals_retained=False)),('population',lambda v:v['binding'].update(feature_hashes={'other':'pin'}))]:
 a.value=copy.deepcopy(base);mutate(a.value);refusal(name,lambda:call(r,feature))
a.value=copy.deepcopy(base);a.failure=ValueError('saved terminal namespace changed');refusal('saved lineage lease refusal propagates',lambda:call(r,feature));fatal=KeyboardInterrupt('original lease fatal');a.failure=fatal
try:call(r,feature)
except BaseException as exc:ck('original fatal identity',exc is fatal)
fatal.__traceback__=None;a.failure=None;refs=[weakref.ref(r),weakref.ref(a),weakref.ref(feature)];del r,a,feature,oldenv;ck('result retains no authority/run/features',all(x() is None for x in refs))
back=s
for x,y in reversed(json.loads((D/'INVERSE01.json').read_bytes())):assert back.count(y)==1;back=back.replace(y,x)
ck('full literal inverse',back==old);ck('fullAST inverse',ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
oldfunctions={n.name:ast.dump(n) for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)}
for n in t.body:
 if isinstance(n,ast.FunctionDef) and n.name!='authority':ck('unchanged '+n.name,ast.dump(n)==oldfunctions[n.name])
# Exact resident try body remains as before, after the new detached branch.
ck('resident body unchanged',[ast.dump(n) for n in tr.body[1:]]==[ast.dump(n) for n in oldtr.body])
ck('no numerical imports',not set(('numpy','torch','pandas')).intersection(sys.modules));(D/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'synthetic_metadata_adapters':True,'genuine_authority_executed':False,'native':False},indent=2)+'\n');print(len(checks))
