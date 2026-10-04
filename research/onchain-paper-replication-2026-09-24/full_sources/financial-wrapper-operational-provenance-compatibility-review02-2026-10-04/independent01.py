from pathlib import Path
import ast,atexit,copy,fcntl,hashlib,importlib.util,json,os,stat,time
H=Path(__file__).resolve().parent;SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');rows=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def ck(n,v):
 rows.append({'case':n,'passed':bool(v)})
 assert v,n
atexit.register(lambda:save('INDEPENDENT_PROGRESS01.json',rows))
def refusal(n,call):
 try:call()
 except (ValueError,KeyError,TypeError,OSError) as e:ck(n,True);return type(e).__name__
 else:ck(n,False)
spec=importlib.util.spec_from_file_location('independent_pure_compatibility',H/'operational_source_compatibility.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ck('stdlib module import has no numerical package',not any(n in __import__('sys').modules for n in ('torch','numpy','pandas')))
pin=sha((H/'operational_source_compatibility.py').read_bytes());target=dict(m.OLD_MAP)|m.CONTROL_TARGETS|{m.HELPER:pin}
ck('exact source hash',pin=='d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8')
original=H/'source-original';original.mkdir();source_rows=[]
for p,h in m.OLD_MAP.items():
 q=SRC/p;s=q.lstat();raw=q.read_bytes();ck('actual full194 source '+p,stat.S_ISREG(s.st_mode) and not q.is_symlink() and len(raw)<4*1024**2 and sha(raw)==h)
 dest=original/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);source_rows.append({'path':p,'sha256':h,'bytes':len(raw)})
ck('194 historical paths and193 hashes',len(source_rows)==194 and len(set(m.OLD_MAP.values()))==193)
ck('195 target paths194 hashes191 exact originals',len(target)==195 and len(set(target.values()))==194 and sum(target[p]==h for p,h in m.OLD_MAP.items())==191)
for p,h in m.CONTROL_TARGETS.items():ck('actual replacement body '+p,sha((H/Path(p).name).read_bytes())==h)
closure=json.loads((SRC/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json').read_bytes());ck('actual installed closure',closure['installed']==m.OLD_MAP)
# Reconstruct the actual original full bytes, not merely allowed function names.
inv=json.loads((H/'SOURCE_INVERSES02.json').read_bytes());inverse=[]
for name,changes in inv['changes'].items():
 back=(H/name).read_text()
 for change in reversed(changes):ck('inverse unique '+name+str(len(back)),back.count(change['new'])==1);back=back.replace(change['new'],change['old'])
 ck('entire actual original inverse '+name,back.encode()==(SRC/m.PREFIX/name).read_bytes());inverse.append({'file':name,'sha256':sha(back.encode())})
 oldtree=ast.parse(back);newtree=ast.parse((H/name).read_bytes());allowed={'_reserve'} if name=='training.py' else {'authorize','_parent','_reference_state'}
 oldtree.body=[n for n in oldtree.body if getattr(n,'name',None) not in allowed];newtree.body=[n for n in newtree.body if getattr(n,'name',None) not in allowed]
 ck('entire unaffected scientific AST '+name,ast.dump(oldtree)==ast.dump(newtree))
# A195 set must not stand in for its exact path map.
a,b=next((a,b) for a in target for b in target if target[a]!=target[b] and a!=m.HELPER and b!=m.HELPER);wrong=dict(target);wrong[a],wrong[b]=wrong[b],wrong[a]
ck('swapped map preserves hash set',set(wrong.values())==set(target.values()));refusal('same-set target path substitution',lambda:m.validate_maps(m.OLD_MAP,wrong,pin))
# Build only explicitly opaque pure metadata; no Run/Admission/claim objects.
policy=json.loads((H/'POLICY_DRAFT01.json').read_bytes());refusal('unresolved real draft',lambda:m.validate_contract(policy,pin))
for key in ('closure_input','claim_input','failed_input','checkpoint_input','plan_input','job_input'):policy['historical'][key]='opaque-'+key
old={'source_commit':m.HISTORICAL_SOURCE,'source_hashes':sorted(set(m.OLD_MAP.values())),'opaque_science':{'seed':11,'epochs':100,'batch':16},'cell_id':'opaque-continued-cell'}
policy['historical']['provenance']=old;policy['target']['closure_input']='opaque-closure'
for phase in policy['consumers']:policy['consumers'][phase]={'experiment':'opaque-'+phase,'cell_id':'opaque-continued-cell' if phase!='complete100' else 'opaque-reference-cell'}
m.validate_contract(policy,pin);ck('opaque policy valid without runtime authority',True)
other=copy.deepcopy(policy);other['consumers']['predict']['experiment']='opaque-changed-predict';m.validate_contract(other,pin)
pa=m.sha(m.canonical(policy));pb=m.sha(m.canonical(other));closurepin=m.sha(m.canonical({'installed':target}));parentid=policy['consumers']['continue100']['experiment'];cells=[policy['consumers']['continue100']['cell_id']];inputs={m.ROLE:{'sha256':pa},'opaque-closure':{'sha256':closurepin}}
new={'source_commit':'1'*40,'source_hashes':sorted(set(target.values())),'opaque_science':old['opaque_science'],'cell_id':old['cell_id']}
m.validate_relation(m.OLD_MAP,target,old,new);ck('exact one directional source relation',True)
for label,bad in [('wrong oldsource',old|{'source_commit':'9'*40}),('lost oldhash',old|{'source_hashes':old['source_hashes'][:-1]}),('old provenance rewritten',old|{'source_hashes':new['source_hashes']})]:refusal(label,lambda bad=bad:m.validate_relation(m.OLD_MAP,target,bad,new))
for label,bad in [('changed science',new|{'opaque_science':{'seed':12,'epochs':100,'batch':16}}),('missing provenance key',{k:v for k,v in new.items() if k!='cell_id'}),('reverse edge',new|{'source_commit':m.HISTORICAL_SOURCE}),('duplicate hash',new|{'source_hashes':new['source_hashes']+[new['source_hashes'][0]]})]:refusal(label,lambda bad=bad:m.validate_relation(m.OLD_MAP,target,old,bad))
wrapper=ast.parse((H/'financial_wrapper_fixture.py').read_bytes());parent=next(n for n in wrapper.body if isinstance(n,ast.FunctionDef) and n.name=='_parent');source=ast.unparse(parent)
branch=next(n for n in parent.body if isinstance(n,ast.If) and 'require_parent_compatibility' in ast.unparse(n));comparison=next(n for n in ast.walk(branch.orelse[0]) if isinstance(n,ast.Compare) and isinstance(n.left,ast.DictComp));expr=compile(ast.Expression(comparison),'actual-production-scientific-compare','eval')
prior=new|{'source_commit':'2'*40};ck('exact original comparison RED permits policy differences',eval(expr,{}, {'value':{'provenance':prior},'prov':new}))
refusal('exact witnessed policy change GREEN',lambda:m.validate_prediction_parent(other,pb,closurepin,parentid,inputs,target,cells))
result=m.validate_prediction_parent(policy,pa,closurepin,parentid,inputs,target,cells);ck('same-policy GREEN',result['policy_sha256']==pa)
for key in ('consumers','historical','target'):
 altered=copy.deepcopy(policy)
 if key=='consumers':altered[key]['predict']['cell_id']='opaque-other'
 elif key=='historical':altered[key]['plan_input']='opaque-alternate-plan'
 else:altered[key]['closure_input']='opaque-alternate-closure'
 m.validate_contract(altered,pin);hash2=m.sha(m.canonical(altered));refusal('valid changed policy '+key,lambda altered=altered,hash2=hash2:m.validate_prediction_parent(altered,hash2,closurepin,parentid,inputs,target,cells))
for label,ins in [('missing role',{'opaque-closure':inputs['opaque-closure']}),('wrongrole',{m.ROLE:{'sha256':pb},'opaque-closure':inputs['opaque-closure']}),('missing closure',{m.ROLE:inputs[m.ROLE]}),('changed closure',inputs|{'opaque-closure':{'sha256':'f'*64}})]:refusal(label,lambda ins=ins:m.validate_prediction_parent(policy,pa,closurepin,parentid,ins,target,cells))
for label,identity,cs in [('wrong id','opaque-other',cells),('historical failed id',m.HISTORICAL_ID,cells),('wrong cell',parentid,['other']),('extra cell',parentid,cells+['extra'])]:refusal(label,lambda identity=identity,cs=cs:m.validate_prediction_parent(policy,pa,closurepin,identity,inputs,target,cs))
for p in target:
 bad=dict(target);del bad[p];refusal('prediction parent missing target '+p,lambda bad=bad:m.validate_prediction_parent(policy,pa,closurepin,parentid,inputs,bad,cells))
refusal('prediction parent same-set swap',lambda:m.validate_prediction_parent(policy,pa,closurepin,parentid,inputs,wrong,cells))
# Strict legacy behavior and exact placement; no fake authority object executed.
ck('source guard follows verify and COMPLETE/strict source comparison',source.index('claim = verify_claim(directory)')<source.index('actual prior lifecycle status differs')<source.index('prior scientific provenance differs')<source.index('require_prediction_policy(run, claim)')<source.index("info = run.admission.inputs[value['checkpoint_input']]"))
predbranch=next(n for n in parent.body if isinstance(n,ast.If) and any(isinstance(c,ast.Name) and c.id=='require_prediction_policy' for c in ast.walk(n)))
class PureInputs(ast.NodeTransformer):
 def visit_Attribute(self,n):
  if ast.unparse(n)=='run.admission.inputs':return ast.copy_location(ast.Name(id='opaque_inputs',ctx=ast.Load()),n)
  return self.generic_visit(n)
guard=compile(ast.fix_missing_locations(ast.Expression(PureInputs().visit(copy.deepcopy(predbranch.test)))),'exact-guard-pure-input-substitution','eval')
for present in (False,True):
 for phase in ('interrupt1','complete100','continue100','predict'):
  ck('optional phase guard '+str((present,phase)),eval(guard,{}, {'opaque_inputs':{m.ROLE:{}} if present else {},'p':{'phase':phase}})==(present and phase=='predict'))
ck('legacy identical provenance allowed',eval(expr,{}, {'value':{'provenance':prior},'prov':new}))
ck('legacy changed science refused',not eval(expr,{}, {'value':{'provenance':prior},'prov':new|{'opaque_science':'different'}}))
# Source-only absence of recursive lock and exact checkpoint load/save wiring.
helper=ast.parse((H/'operational_source_compatibility.py').read_bytes());func={n.name:n for n in helper.body if isinstance(n,ast.FunctionDef)}
for n in ('_require_parent_under_fit_lock','_parent_predicate','_context','_registered_unlocked'):
 calls=[ast.unparse(x.func) for x in ast.walk(func[n]) if isinstance(x,ast.Call)];ck('heldlock source call graph '+n,not any(x.endswith('.read_input') or x in ('_lock','authorize') for x in calls))
ck('heldlock reader selected',ast.unparse(func['_require_parent_under_fit_lock']).endswith('return _parent_predicate(run, old, new, checkpoint, _registered_unlocked)'))
train=ast.parse((H/'training.py').read_bytes());fit=next(n for n in train.body if isinstance(n,ast.FunctionDef) and n.name=='fit_cell');fittext=ast.unparse(fit)
ck('exact old checkpoint load and truthful new save',"load_checkpoint(continuation['checkpoint'], model, optimizer, rng, continuation['provenance'])" in fittext and "save_checkpoint(directory / 'checkpoints', model, optimizer, rng, provenance," in fittext)
for fname in ('checkpoints.py','cache.py','financial_execution.py','evaluation.py'):ck('unchanged generic/scientific '+fname,m.PREFIX+fname in m.OLD_MAP and target[m.PREFIX+fname]==m.OLD_MAP[m.PREFIX+fname])
# Physical tiny leaf IO under owned lock, with no authority wrapper invocation.
owned=H/'owned';owned.mkdir();body=owned/'opaque-body';raw=b'independent opaque\x00\xff';body.write_bytes(raw);lock=owned/'engineering-only.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
budget=lambda:{'begun':time.monotonic(),'bytes':0}
try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);ck('actual opaque read under owned nonrecursive flock',m._read(body,budget())==raw)
finally:os.close(fd)
realread,realclose=os.read,os.close
class HostileFatal(KeyboardInterrupt):
 def __getattribute__(self,key):
  if key in ('__cause__','__context__','storage_cleanup_errors','__dict__'):raise SystemExit('hostile diagnostic getter')
  return super().__getattribute__(key)
 def __setattr__(self,key,value):raise SystemExit('hostile diagnostic setter')
 def __str__(self):raise SystemExit('hostile formatting')
 def __repr__(self):raise SystemExit('hostile representation')
def graph(e):
 todo=[e];seen=set()
 while todo:
  x=todo.pop()
  if id(x) in seen:continue
  seen.add(id(x));state=BaseException.__dict__['__dict__'].__get__(x)
  for name in ('__cause__','__context__'):
   val=BaseException.__dict__[name].__get__(x)
   if isinstance(val,BaseException):todo.append(val)
  todo.extend(x for x in state.get('storage_cleanup_errors',()) if isinstance(x,BaseException))
 return seen
fatal=lambda e:not isinstance(e,Exception) or isinstance(e,MemoryError)
fdcontrols=[]
for pi,kind in enumerate((None,ValueError,KeyboardInterrupt,MemoryError,SystemExit,HostileFatal)):
 for ci,kinds in enumerate(((OSError,OSError,OSError),(OSError,MemoryError,SystemExit),(SystemExit,OSError,MemoryError),(MemoryError,SystemExit,OSError))):
  primary=kind('opaque primary') if kind else None;errors=[k('opaque close') for k in kinds];closed=[]
  def reading(f,n):
   if primary is not None:raise primary
   return realread(f,n)
  def closing(f):
   realclose(f);closed.append(f)
   if len(closed)<=len(errors):raise errors[len(closed)-1]
  m.os.read=reading;m.os.close=closing
  try:
   try:m._read(body,budget())
   except BaseException as caught:
    expected=primary if primary is not None and fatal(primary) else next((e for e in errors if fatal(e)),None)
    selected=caught is expected if expected is not None else isinstance(caught,m.CleanupFailure)
    reached=graph(caught);retained=all(id(e) in reached for e in errors) and (primary is None or id(primary) in reached)
   else:selected=retained=False
  finally:m.os.read=realread;m.os.close=realclose
  ck('actual nested descriptor precedence '+str((pi,ci)),selected);ck('actual full exception graph '+str((pi,ci)),retained);ck('all descriptors attempted once '+str((pi,ci)),len(closed)==len(body.parts) and len(set(closed))==len(closed))
  for f in closed:
   try:os.fstat(f)
   except OSError:pass
   else:raise AssertionError('descriptor retained')
  fdcontrols.append({'primary':None if kind is None else kind.__name__,'close_types':[k.__name__ for k in kinds],'opened_closed':len(closed),'all_graph_objects_retained':retained,'first_fatal_selected':selected})
# Late owned endpoint replacement/growth/disappearance is refused; files retained.
for mode in ('replacement','growth','shrink','disappear','symlink'):
 p=owned/('endpoint-'+mode);p.write_bytes(b'abcdef');done=[False]
 def read_mutating(f,n):
  chunk=realread(f,n)
  if chunk and not done[0]:
   done[0]=True
   if mode=='replacement':p.rename(p.with_suffix('.old'));p.write_bytes(b'abcdef')
   elif mode=='growth':
    with p.open('ab') as stream:stream.write(b'grow')
   elif mode=='shrink':
    with p.open('wb') as stream:stream.write(b'x')
   elif mode=='disappear':p.rename(p.with_suffix('.old'))
   else:p.rename(p.with_suffix('.old'));p.symlink_to(p.with_suffix('.old'))
  return chunk
 m.os.read=read_mutating
 try:refusal('actual late endpoint '+mode,lambda:m._read(p,budget()))
 finally:m.os.read=realread
refusal('aggregate limit before read',lambda:m._read(body,{'begun':time.monotonic(),'bytes':m.TOTAL}))
refusal('deadline before open',lambda:m._read(body,{'begun':time.monotonic()-121,'bytes':0}))
link=owned/'redirect';link.symlink_to(body);refusal('lexical symlink refused',lambda:m._read(link,budget()))
# Drafts carry no actual authority receipts.
proofs=json.loads((H/'PROOF_ROLES_DRAFT01.json').read_bytes());ck('every actual proof decision/policy is null',all(p['decision'] is None and p['policy_sha256'] is None for p in proofs.values()))
req=json.loads((H/'ROOT_REQUIREMENTS02.json').read_bytes());ck('all actual adoption fields null',all(v is None for k,v in req.items() if k.startswith('actual_')))
ck('no numerical package imported at end',not any(n in __import__('sys').modules for n in ('torch','numpy','pandas')))
save('SOURCE_AUTHENTICATION01.json',{'old_map':m.OLD_MAP,'target_map':target,'actual_source_rows':source_rows,'inverses':inverse})
save('FD_CONTROLS01.json',fdcontrols)
save('WITNESS02.json',{'finding01':'OPC-PREDICT-POLICY-01','old_exact_comparison_accepts':True,'new_pure_metadata_predicate_refuses':True,'same_policy_predicate_passes':True,'policy_a_sha256':pa,'policy_b_sha256':pb,'all_195_parent_paths_tested':True,'actual_genuine_objects_or_claims':False,'no_role_boundary':'Legacy no-role routes intentionally remain unchanged; Root release must bind the explicit policy role on all three fixed consumers. No-role success is not compatibility admission.'})
print(json.dumps({'status':'PASS_SOURCE_ONLY','checks':len(rows),'real_nested_descriptor_matrices':len(fdcontrols),'numerical_packages_imported':False}))
