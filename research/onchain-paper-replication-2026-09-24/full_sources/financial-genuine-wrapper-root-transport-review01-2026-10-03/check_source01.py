"""Bounded independent financial transport delta and extracted scalar controls only."""
import ast,copy,difflib,hashlib,json,pathlib,stat,time,types
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';OUT=pathlib.Path(__file__).resolve().parent
OLD=BASE/'held-consumer-post-outcome-root-remote-recovery01-2026-10-03/recover_post_outcome01.py';NEW=BASE/'financial-genuine-wrapper-root-remote-recovery01-2026-10-03/recover_financial01.py';H=lambda b:hashlib.sha256(b).hexdigest();checks=0
def ok(v,n):
 global checks
 if not v:raise AssertionError(n)
 checks+=1
def read(p):
 s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'bounded source/metadata');b=p.read_bytes();ok(len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns,'stable bytes');return b
old=read(OLD);new=read(NEW);ok(H(old)=='4d16cb824ca1e301cc0cc80303966806011bd8a1c8f2eb1bbebfc1a65dac4284','accepted baseline');ok(H(new)=='20a37f3026233ffcd69c6424c38416a27baf01ccc34b1d410f18f5ec0cd59310','new exact source')
ot,nt=ast.parse(old),ast.parse(new);oldcs=[n.value for n in ast.walk(ot) if isinstance(n,ast.Constant) and type(n.value)is str];newcs=[n.value for n in ast.walk(nt) if isinstance(n,ast.Constant) and type(n.value)is str]
changes={
 'fresh-financial01.git':'fresh-post-outcome01.git',
 'fresh-actual-remote-financial-source-archive-and-supporting-bodies-recovered':'fresh-actual-remote-failed-post-outcome-archives-and-selected-supporting-bodies-recovered',
 next(s for s in newcs if s.startswith('Complete current financial source archive')):next(s for s in oldcs if s.startswith('Complete current supplied closed capsule'))}
ok(len(changes)==3,'exact three literal changes')
restored=new.decode()
for n,o in changes.items():ok(restored.count(n)==1 and old.decode().count(o)==1,'unique literal delta');restored=restored.replace(n,o)
ok(restored.encode()==old,'full byte inverse outside three literals')
class Restore(ast.NodeTransformer):
 def visit_Constant(self,n):
  if type(n.value)is str and n.value in changes:n.value=changes[n.value]
  return n
norm=Restore().visit(copy.deepcopy(nt));ok(ast.dump(norm,include_attributes=False)==ast.dump(ot,include_attributes=False),'whole normalized AST exact inverse')
od={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nd={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)};ok(od.keys()==nd.keys(),'same all functions')
for n in od:
 actual=Restore().visit(copy.deepcopy(nd[n]))
 ok(ast.dump(actual,include_attributes=False)==ast.dump(od[n],include_attributes=False),'complete function inverse '+n)
 if n!='main':ok(ast.dump(nd[n],include_attributes=False)==ast.dump(od[n],include_attributes=False),'unaltered full helper '+n)
# Only actual pure helpers and bounded selection/guard expressions are executed.
env={'hashlib':hashlib,'json':json};exec(compile(ast.Module(body=[nd[n] for n in ['require','digest','encode']],type_ignores=[]),'<actual-source-pure-helpers>','exec'),env)
main=nd['main'];start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Expr) and 'explicit frozen selection pin' in ast.unparse(n));end=next(i for i,n in enumerate(main.body) if any(isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='git' for v in ast.walk(n)))
pre=compile(ast.Module(body=main.body[start:end],type_ignores=[]),'<actual-pre-network-selection>','exec');cases=[]
base={'remote_commit':'1'*40,'rows':[{'path':'research/opaque','bytes':1,'sha256':'a'*64}]}
def case(name,value,want,pin=None,raw=None):
 b=env['encode'](value) if raw is None else raw;e=dict(env,selection_body=b,args=types.SimpleNamespace(selection_sha256=H(b) if pin is None else pin));err=None
 try:exec(pre,e)
 except BaseException as ex:err=type(ex).__name__+': '+str(ex)
 ok((err is None)==want,name);cases.append({'name':name,'accepted':err is None,'error':err})
case('valid tiny opaque pinned',base,True);case('wrong external pin',base,False,pin='0'*64);case('noncanonical serialized body',base,False,raw=json.dumps(base).encode())
for name,commit in [('null commit',None),('uppercase commit','A'*40),('short commit','1'*39),('invalidhex commit','z'*40)]:v=copy.deepcopy(base);v['remote_commit']=commit;case(name,v,False)
for name,rows in [('empty',[]),('duplicate',base['rows']*2),('unsorted',[{'path':'research/z','bytes':0},{'path':'research/a','bytes':0}]),('too many',[{'path':f'research/{i:04}','bytes':0} for i in range(513)])]:v=copy.deepcopy(base);v['rows']=rows;case(name,v,False)
v=copy.deepcopy(base);v['rows'][0]['bytes']=64*1024**2+1;case('aggregate >64MiB',v,False)
v=copy.deepcopy(base);v['rows']=[{'path':f'research/{i:04}','bytes':0} for i in range(506)];case('506 scalar schema',v,True);v['rows'] += [{'path':f'research/{i:04}','bytes':0} for i in range(506,512)];case('512 schema passes only - does not fit operations',v,True)
# Actual late per-row predicates are tested separately; they are not relabelled pre-network checks.
loop=next(n for n in main.body if isinstance(n,ast.For) and ast.unparse(n.target)=='row')
late=[n for n in loop.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require' and n.value.args[-1].value in ['selected path scope','selected actual Git file','selected size pin']]
ok(len(late)==3,'three exact late predicates');latecode=compile(ast.Module(body=late,type_ignores=[]),'<actual-late-row-predicates>','exec');latecases=[]
for name,path,mode,kind,size,want in [('valid','research/opaque','100644','blob',1,True),('dotdot','research/../outside','100644','blob',1,False),('absolute','/research/opaque','100644','blob',1,False),('nonresearch','outside/opaque','100644','blob',1,False),('symlink','research/opaque','120000','blob',1,False),('tree','research/opaque','040000','tree',1,False),('negative','research/opaque','100644','blob',-1,False),('over4MiB','research/opaque','100644','blob',4*1024**2+1,False),('exact4MiB','research/opaque','100644','blob',4*1024**2,True)]:
 err=None;e=dict(env,name=path,Path=pathlib.Path,mode=mode,kind=kind,row={'bytes':size},FILE=4*1024**2)
 try:exec(latecode,e)
 except BaseException as ex:err=type(ex).__name__+': '+str(ex)
 ok((err is None)==want,name);latecases.append({'name':name,'accepted':err is None,'error':err})
guard=compile(ast.Module(body=[nd['git'].body[1]],type_ignores=[]),'<actual-budget-expression>','exec');budget=[]
for count,elapsed,want in [(1023,0,True),(1024,0,False),(0,601,False)]:
 err=None;e=dict(env,time=time,START=time.monotonic()-elapsed,CALLS=[None]*count)
 try:exec(guard,e)
 except BaseException as ex:err=type(ex).__name__+': '+str(ex)
 ok((err is None)==want,'exact bounded Git guard');budget.append({'calls_before':count,'elapsed':elapsed,'accepted':err is None,'error':err})
ok(11+2*506==1023 and 11+2*507==1025,'strict effective506 operation ceiling')
# Authenticate existing capture metadata only. No repeated full tree/archive scientific audit.
p=BASE/'financial-genuine-wrapper-root-preservation01-2026-10-03';capture_raw=read(p/'CAPTURE01.json');capture=json.loads(capture_raw);manifest_raw=read(p/'complete-manifest01.json');manifest=json.loads(manifest_raw);archive=read(p/'complete-source01.tar.gz');req=json.loads(read(p/'REQUEST01.json'));terminal=json.loads(read(p/'ACTUAL_CAPTURE_TERMINAL01.json'))
ok(H(capture_raw)=='2d3e86ca91407119be4ca56ccff260f069a44a4d1988f649f25e4f571a62da30','actual local capture receipt');ok(H(manifest_raw)==capture['complete_manifest_sha256']==req['complete_manifest_sha256'],'actual complete metadata pin');ok(H(archive)==capture['archive']['sha256']=='2e267a231ba56777a42af32db38b47a380f98a7bae84643ee86e4b4aafc41f1b' and len(archive)==2218058,'actual local opaque full archive pin')
ok(capture['actual_HEAD']==req['actual_HEAD']==terminal['actual_financial_HEAD']=='44bf99d199acae5a043cf5b472a53e2fcf4caf1b','exact archived financial source epoch');ok(capture['manifest_members']==len(manifest['members'])==748 and sum(r['kind']=='file' for r in manifest['members'])==527,'actual full manifest cardinalities');ok(sum(r.get('bytes',0) for r in manifest['members'])==capture['logical_bytes']==4924712,'actual full manifest extent')
ok(capture['complete_tracked']==242 and capture['implementation_sources']==194 and capture['auxiliary_drafts']==48 and capture['claimed_phases']==0,'source242 composition distinct admission')
ok(terminal['exit']==0 and terminal['receipt_sha256']==H(capture_raw) and terminal['actual_external_recovery'] is False,'actual capture terminal still historical local only')
reviewpins={}
for dirname,filename,prefix in [('financial-genuine-wrapper-full-scope-preservation-review01-2026-10-03','REVIEW01.md','e9ab6627'),('financial-genuine-wrapper-full-scope-preservation-review01-2026-10-03','MANIFEST01.json','eea3fc89'),('financial-genuine-wrapper-installed-auxiliary-review01-2026-10-03','REVIEW01.md','d9e82b1d')]:
 pp=BASE/dirname/filename;pin=H(read(pp));ok(pin.startswith(prefix),'declared independent prior review body');reviewpins[str(pp.relative_to(ROOT))]=pin
for n in ['SELECTED_BODIES01.json','fresh-financial01.git','selected','REMOTE_RECOVERY01.json','FAILED01.json']:ok(not (NEW.parent/n).exists(),'initial future transport state absent '+n)
diff=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile=str(OLD.relative_to(ROOT)),tofile=str(NEW.relative_to(ROOT))))
with (OUT/'EXACT_DELTA01.diff').open('x') as f:f.write(diff)
r={'schema_version':1,'assertions':checks,'decision':'ACCEPTED_NARROW_SOURCE_ONLY_PENDING_EXACT_SELECTION','source_sha256':H(new),'baseline_sha256':H(old),'exact_literal_new_to_old':changes,'full_byte_inverse':True,'whole_normalized_AST_inverse':True,'unchanged_helper_functions':[n for n in od if n!='main'],'pre_network_scalar_controls':cases,'late_row_scalar_controls':latecases,'git_budget_controls':budget,'maximum_successful_rows_under_1024_operations':506,'source_captured_commit':capture['actual_HEAD'],'local_capture_sha256':H(capture_raw),'local_archive_sha256':H(archive),'local_manifest_sha256':H(manifest_raw),'independent_prior_review_pins':reviewpins,'actual_selection_sha256':None,'actual_remote_commit':None,'actual_remote_receipt_sha256':None,'actual_flat_receipt_sha256':None,'scientific_or_runtime_or_native_authority':False,'source44_is_final_future_release_source':False,'network_or_subprocess_executed':False,'numerical_imports':False,'note':'Main transport program was never imported or invoked. Actual extracted pure predicates only; no fake Git, Run or Owner.'}
with (OUT/'SOURCE_CHECKS01.json').open('x') as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'pre_network_controls':len(cases),'late_row_controls':len(latecases),'budget_controls':len(budget),'changes':3,'maxrows':506,'actual_transport':False}))
