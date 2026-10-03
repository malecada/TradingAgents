"""Exact source/preflight scalar review. Never invokes transport or a process."""
import ast,copy,difflib,hashlib,json,pathlib,time,types
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';OUT=pathlib.Path(__file__).resolve().parent
OLD=BASE/'held-consumer-final-released-scope-root-remote-recovery01-2026-10-03/recover_final03.py';NEW=BASE/'held-consumer-post-outcome-root-remote-recovery01-2026-10-03/recover_post_outcome01.py'
old=OLD.read_bytes();new=NEW.read_bytes();H=lambda b:hashlib.sha256(b).hexdigest();assert H(old)=='6b4d6671f852ab6893a2219c4185efb7106253b3bf48eb07da500bafe54dbfce';assert H(new)=='4d16cb824ca1e301cc0cc80303966806011bd8a1c8f2eb1bbebfc1a65dac4284'
ot,nt=ast.parse(old),ast.parse(new);od={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nd={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
assert od.keys()==nd.keys()
unchanged=[]
for n in od:
 if n!='main':assert ast.dump(od[n],include_attributes=False)==ast.dump(nd[n],include_attributes=False);unchanged.append(n)
om,nm=od['main'],nd['main'];oi=next(i for i,n in enumerate(om.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='rows');ni=next(i for i,n in enumerate(nm.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='rows')
normal=copy.deepcopy(nt);nmain=next(n for n in normal.body if isinstance(n,ast.FunctionDef) and n.name=='main');nmain.body[:ni]=copy.deepcopy(om.body[:oi])
normal.body=[n for n in normal.body if not (isinstance(n,ast.Import) and len(n.names)==1 and n.names[0].name=='argparse')]
oldcommit=next(n for n in ot.body if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='COMMIT')
for i,n in enumerate(normal.body):
 if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='COMMIT':normal.body[i]=copy.deepcopy(oldcommit)
oldconstants=[n.value for n in ast.walk(ot) if isinstance(n,ast.Constant) and isinstance(n.value,str)];newconstants=[n.value for n in ast.walk(nt) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
replacement={
 'fresh-post-outcome01.git':'fresh-final01.git',
 'fresh-actual-remote-failed-post-outcome-archives-and-selected-supporting-bodies-recovered':'fresh-actual-remote-final950-archives-and-selected-supporting-bodies-recovered',
 'REMOTE_RECOVERY01.json':'REMOTE_RECOVERY03.json','FAILED01.json':'FAILED03.json'}
newqual=next(s for s in newconstants if s.startswith('Complete current supplied closed'));oldqual=next(s for s in oldconstants if s.startswith('Both original and final950'));replacement[newqual]=oldqual
class Normalize(ast.NodeTransformer):
 def visit_Constant(self,n):
  if type(n.value)is str and n.value in replacement:n.value=replacement[n.value]
  return n
normal=Normalize().visit(normal);assert ast.dump(normal,include_attributes=False)==ast.dump(ot,include_attributes=False)
ops=[];ol=old.decode().splitlines(keepends=True);nl=new.decode().splitlines(keepends=True)
for tag,i,j,k,l in difflib.SequenceMatcher(a=ol,b=nl,autojunk=False).get_opcodes():
 if tag!='equal':ops.append({'old_line':i+1,'new_line':k+1,'old':''.join(ol[i:j]),'new':''.join(nl[k:l])})
restored=new.decode()
for change in reversed(ops):
 assert restored.count(change['new'])==1;restored=restored.replace(change['new'],change['old'])
assert restored.encode()==old
env={}
for n in ['require','digest','encode']:exec(compile(ast.Module(body=[nd[n]],type_ignores=[]),'<actual-pure-tool-def>','exec'),{'hashlib':hashlib,'json':json},env)
# Functions' own globals require their source libraries; bind all in one namespace.
env={'hashlib':hashlib,'json':json}
exec(compile(ast.Module(body=[nd[n] for n in ['require','digest','encode']],type_ignores=[]),'<actual-pure-tool-defs>','exec'),env)
start=next(i for i,n in enumerate(nm.body) if isinstance(n,ast.Expr) and 'explicit frozen selection pin' in ast.unparse(n))
end=next(i for i,n in enumerate(nm.body) if any(isinstance(v,ast.Call) and isinstance(v.func,ast.Name) and v.func.id=='git' for v in ast.walk(n)))
fragment=compile(ast.Module(body=nm.body[start:end],type_ignores=[]),'<exact-pre-network-selection-checks>','exec')
cases=[]
base={'remote_commit':'1'*40,'rows':[{'path':'research/opaque-a','bytes':1,'sha256':'a'*64}]}
def case(label,value,pin=None,expected=True,body=None):
 b=env['encode'](value) if body is None else body;e=dict(env,selection_body=b,args=types.SimpleNamespace(selection_sha256=H(b) if pin is None else pin));error=None
 try:exec(fragment,e)
 except BaseException as ex:error=type(ex).__name__+': '+str(ex)
 assert (error is None)==expected,(label,error)
 cases.append({'name':label,'accepted':error is None,'error':error})
case('valid opaque pinned',base)
case('wrong external pin',base,pin='0'*64,expected=False)
for label,commit in [('uppercase','A'*40),('short','1'*39),('nontext',None),('invalidhex','z'*40)]:v=copy.deepcopy(base);v['remote_commit']=commit;case(label,v,expected=False)
v=copy.deepcopy(base);v['rows']=[];case('empty rows',v,expected=False)
v=copy.deepcopy(base);v['rows']*=2;case('duplicate rows',v,expected=False)
v=copy.deepcopy(base);v['rows'][0]['bytes']=64*1024**2+1;case('aggregate over64MiB',v,expected=False)
case('noncanonical selection',base,expected=False,body=json.dumps(base).encode())
v=copy.deepcopy(base);v['rows']=[{'path':'research/'+str(i).zfill(4),'bytes':0,'sha256':'a'*64} for i in range(513)];case('513rows',v,expected=False);v['rows'].pop();case('512 passes schema only',v)
guard=compile(ast.Module(body=[nd['git'].body[1]],type_ignores=[]),'<exact-git-budget-guard>','exec')
assert isinstance(nd['git'].body[0],ast.Expr) and isinstance(nd['git'].body[0].value,ast.Constant)
witness=[]
for n in (506,507,512):
 e=dict(env,time=time,START=time.monotonic(),CALLS=[]);failed=None
 for index in range(11+2*n):
  try:exec(guard,e)
  except ValueError as ex:failed={'one_based_operation':index+1,'message':str(ex)};break
  e['CALLS'].append(None)
 witness.append({'rows':n,'required_git_calls':11+2*n,'completed_guard_passes':len(e['CALLS']),'failure':failed})
assert witness[0]['failure'] is None and witness[1]['failure']['one_based_operation']==1025 and witness[2]['failure']['one_based_operation']==1025
out={'schema_version':1,'baseline_sha256':H(old),'source_sha256':H(new),'full_text_inverse':ops,'normalized_whole_AST_inverse':True,'unchanged_complete_function_AST':unchanged,'selection_controls':cases,'inherited_operation_budget_witness':witness,'maximum_successful_rows_under_current_budget':506,'network_or_process_execution':False,'actual_selection_sha256':None,'actual_remote_recovery_sha256':None,'qualification':'bounded literal source/CLI adaptation accepted only with independently frozen exact safe selection; no blanket512-row completion claim'}
with (OUT/'TRANSPORT_SOURCE_RESULTS01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'controls':len(cases),'source':H(new),'budget_maximum_rows':506,'other_AST_unchanged':True}))
