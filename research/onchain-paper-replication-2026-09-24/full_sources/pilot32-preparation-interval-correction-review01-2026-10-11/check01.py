"""Independent source/synthetic review; no candidate scientific module import."""
import ast,copy,difflib,hashlib,json,resource,signal,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456));resource.setrlimit(resource.RLIMIT_CPU,(20,20));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(30)
H=Path(__file__).resolve().parent;F=H.parent;R=F.parents[2];C=F/'pilot32-preparation-interval-correction01-2026-10-11';P=R/'tradingagents/research/onchain_replication';checks=[];refs={}
def ck(ok,name):
 assert ok,name
 checks.append(name)
def read(p):
 b=p.read_bytes();assert len(b)<4194304;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def sha(p):return hashlib.sha256(read(p)).hexdigest()
ck(sha(C/'MANIFEST01.json')=='c061661baaa90eb4791c4ba5a96629014885c4443dc0407896c1f5e2926ecebc','frozen candidate manifest')
for name,pin in json.loads(read(C/'MANIFEST01.json'))['files'].items():ck(sha(C/name)==pin['sha256'] and (C/name).stat().st_size==pin['bytes'],'exact candidate artifact '+name)
old=read(P/'compact_mcm.py').decode();new=read(C/'compact_mcm.py').decode();ck(hashlib.sha256(old.encode()).hexdigest()=='228f9199bf5b12f104dd91ee678fb12792d0295dc9adf9a3ddd8fbaeb2c4c574','exact installed predecessor');ck(hashlib.sha256(new.encode()).hexdigest()=='becaab002648c440852553ebf1e662702affee96283a07bcb90bdfc2ca7379ca','exact candidate body')
a=ast.parse(old);b=ast.parse(new);fa=next(x for x in a.body if isinstance(x,ast.FunctionDef) and x.name=='_prepare');fb=next(x for x in b.body if isinstance(x,ast.FunctionDef) and x.name=='_prepare')
# Independently identify the sole new if imported whose else owns legacy matching.
branch=next(x for x in fb.body if isinstance(x,ast.If) and isinstance(x.test,ast.Name) and x.test.id=='imported' and x.orelse)
start=next(i for i,x in enumerate(fa.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='matching' for t in x.targets));stop=next(i for i in range(start,len(fa.body)) if isinstance(fa.body[i],ast.If));legacy=fa.body[start:stop];override=fa.body[stop]
ck(ast.dump(ast.Module(body=legacy,type_ignores=[]))==ast.dump(ast.Module(body=branch.orelse,type_ignores=[])),'nonimported legacy entire AST exact')
ck(ast.dump(ast.Module(body=override.body,type_ignores=[]))==ast.dump(ast.Module(body=branch.body,type_ignores=[])),'imported derive and scope equality AST exact')
restored=copy.deepcopy(b);rf=next(x for x in restored.body if isinstance(x,ast.FunctionDef) and x.name=='_prepare');i=fb.body.index(branch);rf.body[i:i+1]=copy.deepcopy(fa.body[start:stop+1]);ck(ast.dump(restored)==ast.dump(a),'full module AST exact inverse outside single branch')
oldlines=old.splitlines(True);newlines=new.splitlines(True);ob=''.join(oldlines[fa.body[start].lineno-1:override.end_lineno]);nb=''.join(newlines[branch.lineno-1:branch.end_lineno]);ck(new.replace(nb,ob,1)==old,'full literal byte inverse')
for filename,x,y,px,py in [('forward.patch',old,new,P/'compact_mcm.py',C/'compact_mcm.py'),('inverse.patch',new,old,C/'compact_mcm.py',P/'compact_mcm.py')]:ck(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=str(px.relative_to(R)),tofile=str(py.relative_to(R))))==read(C/filename).decode(),'independent exact '+filename)
# Removed names cannot affect the later function body.
removed={'matching','ordered','order','scope'};later=fa.body[stop+1:];ck(not any(isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id in removed for x in later for n in ast.walk(x)),'discarded locals have no later reads')
def invoke(nodes,imported,mutation=False,fail=None):
 events=[];scope={'graph':'g','workflow':'w','node_order':'fixed'};d=types.SimpleNamespace(identity='d',matching_config_hash='m',representatives=('u','v'));dictionary=types.SimpleNamespace(scope=dict(scope));owner=types.SimpleNamespace(matching={'n':1},bound=types.SimpleNamespace(record={'workflow_identity':'w'}));graph=types.SimpleNamespace(node_ids=('a','b'))
 def require(value,why):
  events.append('scope-check')
  if not value:raise ValueError(why)
 def derive():
  events.append('derive')
  if fail=='derive':raise LookupError('derive failure')
  return {**scope,'graph':'changed'} if mutation else dict(scope)
 dictionary.derive_scope=derive
 def order(v):
  events.append('order')
  if fail=='order':raise LookupError('order failure')
  return 'order'
 def ident(v):events.append('motif:'+v);return v
 def thaw(v):events.append('thaw');return dict(v)
 ns={'dictionary':dictionary,'owner':owner,'graph':graph,'d':d,'imported':imported,'key':'g','BACKEND':'b','_imported':lambda d:imported,'require':require,'node_order_hash':order,'graph_identity':ident,'thaw':thaw,'cache_key':lambda v:json.dumps(v,sort_keys=True)}
 try:exec(compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes),type_ignores=[])),'extracted scope only','exec'),ns);return ns['expected'],events,None
 except Exception as e:return None,events,(type(e).__name__,str(e))
oldnodes=fa.body[start:stop+1];newnodes=[branch]
for imported in (False,True):
 x=invoke(oldnodes,imported);y=invoke(newnodes,imported);ck(x[0]==y[0] and x[2]==y[2],'scope values equal '+str(imported))
 if not imported:ck(x==y,'legacy exact hook order')
 else:ck(x[1]==['thaw','motif:u','motif:v','order','derive','scope-check'] and y[1]==['derive','scope-check'],'imported discarded traversal removed and equality retained')
for fail in ('derive',None):ck(invoke(oldnodes,True,True,fail)[2]==invoke(newnodes,True,True,fail)[2],'fresh scope or derive failure refusal '+str(fail))
ck(invoke(oldnodes,False,False,'order')==invoke(newnodes,False,False,'order'),'legacy traversal exception unchanged')
ck(invoke(oldnodes,True,False,'order')[2] is not None and invoke(newnodes,True,False,'order')[2] is None,'explicit discarded-hook exception semantics differ; outside scope')
# Genuine source bracket remains identical, including both dictionary.check calls and final joins.
checks_calls=[n for n in ast.walk(fa) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='dictionary' and n.func.attr=='check'];ck(len(checks_calls)==2,'both actual Target checks preserved')
target=ast.parse(read(P/'imported_mcm_identity.py').decode());tc=next(n for n in target.body if isinstance(n,ast.ClassDef) and n.name=='Target');check=next(n for n in tc.body if isinstance(n,ast.FunctionDef) and n.name=='check');final=next(n for n in tc.body if isinstance(n,ast.FunctionDef) and n.name=='final');ck('self.final()' in ast.unparse(check) and 'graph_hash(self.graph)' in ast.unparse(final) and 'node_order_hash(self.graph.node_ids)' in ast.unparse(final),'genuine Target final content/order validators remain')
# Execute only stdlib scheduler source; synthetic callbacks issue no authority.
interval=read(P/'imported_authority_interval.py');ck(hashlib.sha256(interval).hexdigest()=='e61ef97f883ed9d27107f6316b774697b8949d83c313928150a0ae717b283f6f','exact unchanged Interval');ns={};exec(compile(interval,'original stdlib Interval','exec'),ns)
policy={'schema_version':1,'kind':ns['KIND'],'live_interval_ms':1000,'fingerprint_interval_ms':2000,'full_interval_ms':30000,'max_stale_ms':60000,'max_calls_between_full':100000,'assumption':ns['ASSUMPTION']}
def timing(age,cost,error=None):
 clock=[0.0];i=ns['Interval'](policy,clock=lambda:clock[0]);events=[];i.validate(lambda:None,lambda:None,lambda:None,boundary=True);clock[0]=age
 def full():
  events.append('full');clock[0]+=cost
  if error is not None:raise error
 try:i.validate(full,lambda:events.append('finger'),lambda:events.append('live'),boundary=True);return i,None,events
 except BaseException as e:return i,e,events
age=49.924078479001764;cost=10.453950685994641
for savings,passes in ((0,False),(.1,False),(.5,True)):
 i,e,events=timing(age-savings,cost);ck((e is None)==passes,'conditional clock only saving '+str(savings))
 if not passes:ck(i.closed and i.full==0 and 'stale interval cannot refresh' in str(e) and 'finger' not in events,'stale poisons without refresh/fingerprint '+str(savings))
 else:ck(i.full==age-savings+cost and 'finger' in events,'success records actual callback completion only')
primary=KeyboardInterrupt('synthetic');i,e,_=timing(1,1,primary);ck(e is primary and i.closed and i.full==0,'fatal identity and poison without refresh')
i,e,events=timing(61,0);ck(e is not None and not events and i.closed,'already stale rejects before callback')
out={'decision':'ACCEPT_SOURCE_ONLY_DISCARDED_IMPORTED_SCOPE_REMOVAL','candidate':refs[str((C/'compact_mcm.py').relative_to(R))],'checks':checks,'references':refs,'observed_interval_seconds':age+cost,'hypothetical_saving_cases_seconds':[0,.1,.5],'actual_speed_saving_seconds':None,'limitations':['No actual speed saving or successful60s empirical preparation demonstrated.','Discarded helper/hook invocation and exception semantics intentionally differ on imported route; no arbitrary side-effect equivalence.','Scope fixtures execute extracted blocks only, no real Target/Owner/scientific imports or authority creation.','Candidate not installed/admitted; independent Root integration/source closure update and preserved failed32 required.']}
(H/'REVIEW01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':out['decision'],'checks':len(checks),'review_sha256':hashlib.sha256((H/'REVIEW01.json').read_bytes()).hexdigest()}))
