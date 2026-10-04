from pathlib import Path
import ast,atexit,copy,hashlib,importlib.util,json,os,stat,sys,time
H=Path(__file__).resolve().parent;B=H.parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');rows=[]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
m=load('bounded_preclaim_candidate',H/'preclaim01.py');sha=m.sha
helper=load('actual_pure_compatibility',S/m.HELPER);fixture=load('actual_stdlib_fixture',S/m.PREFIX/'financial_wrapper_fixture.py');verify=load('actual_readonly_verifier',S/'tradingagents/research/verify.py')
def save(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def ck(n,v):rows.append({'case':n,'passed':bool(v)});assert v,n
atexit.register(lambda:save('CHECK_PROGRESS01.json',rows))
def refuse(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError):ck(n,True)
 else:ck(n,False)
ck('actual pinned compatibility source',sha((S/m.HELPER).read_bytes())==m.HELPER_SHA)
for name,module in [('financial_wrapper_fixture.py',fixture),('verify.py',verify)]:
 rel=m.PREFIX+name if name!='verify.py' else 'tradingagents/research/verify.py';ck('authentic imported stdlib helper '+name,sha(Path(module.__file__).read_bytes())==helper.CONTROL_TARGETS.get(rel,helper.OLD_MAP.get(rel)))
ck('no genuine authority or numerical imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
# Original base8 is genuine source evidence but has no registered compatibility
# policy/proof roles. Actual current source does not extend admitted() for these.
oldclaim=json.loads((S/'research_runs'/helper.HISTORICAL_ID/'claim.json').read_bytes());ck('actual historical claim hash',sha((S/'research_runs'/helper.HISTORICAL_ID/'claim.json').read_bytes())==helper.HISTORICAL_CLAIM_SHA256)
ck('actual original8 input roles',len(oldclaim['inputs'])==8 and m.ROLE not in oldclaim['inputs'])
refuse('actual original8 policy gap now refuses before claim',lambda:m._roles(oldclaim['inputs'],'complete100'))
source=(S/m.PREFIX/'financial_wrapper_fixture.py').read_text();tree=ast.parse(source);admitted=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admitted')
ck('actual admitted source has no compatibility role prerequisite',m.ROLE not in ast.unparse(admitted))
for role in m.BASE:refuse('one missing mandatory base role '+role,lambda role=role:m._roles(m.BASE-{role},'complete100'))
m._roles(m.BASE,'complete100');ck('exact11 role-set pure predicate',True);refuse('reference extra role refuses',lambda:m._roles(m.BASE|{'opaque-extra'},'complete100'))
# Every input is read, including unused extra aliases; no lazy metadata gap.
owned=H/'owned';owned.mkdir();a=owned/'first';a.write_bytes(b'first opaque');b=owned/'second';b.write_bytes(b'second opaque')
reg={'first':{'path':'first','sha256':sha(a.read_bytes()),'dataset':'synthetic'},'second':{'path':'second','sha256':sha(b.read_bytes()),'dataset':'synthetic'}}
x=m.Inputs(owned,reg,m.Reader());ck('both real registered input bodies read eagerly',set(x.bodies)==set(reg))
bad=copy.deepcopy(reg);bad['second']['sha256']='0'*64;refuse('unused registered input wrong hash still refuses',lambda:m.Inputs(owned,bad,m.Reader()))
for label,info in [('null pin',{'path':'first','sha256':None,'dataset':'synthetic'}),('wrongdataset',{'path':'first','sha256':reg['first']['sha256'],'dataset':'empirical'}),('traversal',{'path':'../first','sha256':reg['first']['sha256'],'dataset':'synthetic'}),('secret',{'path':'.env','sha256':reg['first']['sha256'],'dataset':'synthetic'})]:refuse('input '+label,lambda info=info:m.Inputs(owned,{'x':info},m.Reader()))
reader=m.Reader();reader.read(a);a.rename(owned/'first-original');a.write_bytes(b'altered');refuse('cached input changed after validation',reader.finish)
# Tiny real reader resource controls, lowered solely for synthetic bounds.
oldfile,oldtotal=m.FILE,m.TOTAL
try:
 m.FILE=4;refuse('regular file size bound before read',lambda:m.Reader().read(b))
 m.FILE=oldfile;m.TOTAL=20;r=m.Reader();r.read(b);refuse('double-read aggregate cap enforced',r.finish)
finally:m.FILE,m.TOTAL=oldfile,oldtotal
r=m.Reader();r.deadline=time.monotonic()-1;refuse('deadline before descriptor open',lambda:r.read(b))
link=owned/'redirect';link.symlink_to(b);refuse('lexical symlink refuses',lambda:m.Reader().read(link))
refuse('directory input refuses',lambda:m.Reader().read(owned))
fifo=owned/'empty-fifo-control';os.mkfifo(fifo)
try:refuse('nonblocking FIFO type refusal',lambda:m.Reader().read(fifo));fifo_stat=fifo.lstat();ck('FIFO witness type',stat.S_ISFIFO(fifo_stat.st_mode))
finally:fifo.unlink()
save('FIFO_CONTROL01.json',{'path':str(fifo),'kind':'fifo','mode':stat.S_IMODE(fifo_stat.st_mode),'refused_before_read':True,'empty_control_removed_after_check':True})
# Descriptor close uncertainty and first fatal: actual opened FDs close once.
realread,realclose=os.read,os.close
class Hostile(KeyboardInterrupt):
 def __getattribute__(self,k):
  if k in ('__dict__','__cause__','__context__','storage_cleanup_errors'):raise SystemExit('hostile diagnostic')
  return super().__getattribute__(k)
 def __setattr__(self,k,v):raise SystemExit('hostile setter')
 def __str__(self):raise SystemExit('hostile string')
 def __repr__(self):raise SystemExit('hostile repr')
def graph(e):
 todo=[e];seen=set()
 while todo:
  x=todo.pop()
  if id(x) in seen:continue
  seen.add(id(x));state=BaseException.__dict__['__dict__'].__get__(x)
  for k in ('__cause__','__context__'):
   y=BaseException.__dict__[k].__get__(x)
   if isinstance(y,BaseException):todo.append(y)
  todo.extend(z for z in state.get('storage_cleanup_errors',()) if isinstance(z,BaseException))
 return seen
fat=lambda e:not isinstance(e,Exception) or isinstance(e,MemoryError);fdrows=[]
for primarytype in (None,ValueError,KeyboardInterrupt,MemoryError,SystemExit,Hostile):
 for types in ((OSError,OSError,OSError),(OSError,MemoryError,SystemExit),(SystemExit,OSError,MemoryError),(MemoryError,SystemExit,OSError)):
  first=primarytype('primary') if primarytype else None;errors=[t('close') for t in types];closed=[]
  def read(fd,n):
   if first is not None:raise first
   return realread(fd,n)
  def close(fd):
   realclose(fd);closed.append(fd)
   if len(closed)<=len(errors):raise errors[len(closed)-1]
  m.os.read=read;m.os.close=close
  try:
   try:m.Reader().read(b)
   except BaseException as e:
    expect=first if first is not None and fat(first) else next((x for x in errors if fat(x)),None);right=e is expect if expect is not None else isinstance(e,m.CleanupFailure);seen=graph(e);retained=all(id(x) in seen for x in errors) and (first is None or id(first) in seen)
   else:right=retained=False
  finally:m.os.read=realread;m.os.close=realclose
  name=str((None if primarytype is None else primarytype.__name__,[t.__name__ for t in types]));ck('real close first fatal '+name,right);ck('all actual exception objects retained '+name,retained);ck('all acquired FDs attempted once '+name,len(closed)==len(b.parts) and len(set(closed))==len(closed))
  for fd in closed:
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('FD retained')
  fdrows.append({'primary':None if primarytype is None else primarytype.__name__,'close_types':[t.__name__ for t in types],'closed_once':len(closed),'first_fatal':right,'all_errors':retained})
save('FD_CONTROLS01.json',fdrows)
# Endpoint mutations must not become accepted registered bytes.
for mode in ('replacement','growth','shrink','disappear'):
 p=owned/('endpoint-'+mode);p.write_bytes(b'abcdef');done=[False]
 def mutate(fd,n):
  block=realread(fd,n)
  if block and not done[0]:
   done[0]=True
   if mode=='replacement':p.rename(p.with_suffix('.original'));p.write_bytes(b'abcdef')
   elif mode=='growth':
    with p.open('ab') as f:f.write(b'grew')
   elif mode=='shrink':p.write_bytes(b'x')
   else:p.rename(p.with_suffix('.original'))
  return block
 m.os.read=mutate
 try:refuse('late actual namespace/extent '+mode,lambda:m.Reader().read(p))
 finally:m.os.read=realread
# Actual independent review bundle, no manufactured accepted proof.
P=B/'financial-wrapper-compatibility-root-policy01-2026-10-04';V=B/'financial-wrapper-compatibility-concrete-policy-review01-2026-10-04';policy=json.loads((P/'POLICY01.json').read_bytes());main=B.parents[2]
ck('actual policy pin',sha((P/'POLICY01.json').read_bytes())==m.POLICY_SHA)
refs={'review_'+key:{'path':str(V/name),'sha256':sha((V/name).read_bytes())} for key,name in [('proof','REVIEW_PROOF01.json'),('machine','MACHINE01.json'),('report','REPORT01.md'),('manifest','MANIFEST01.json')]}
registered={m.REVIEW_ROLE:{'path':str((V/'REVIEW_PROOF01.json').relative_to(main)),'sha256':refs['review_proof']['sha256'],'dataset':'synthetic'},'source_closure':{'path':str((P/'SOURCE_CLOSURE01.json').relative_to(main)),'sha256':sha((P/'SOURCE_CLOSURE01.json').read_bytes()),'dataset':'synthetic'}}
r=m.Reader();actualinputs=m.Inputs(main,registered,r);actual=m._proof_bundle('review',refs,actualinputs,policy,r);r.finish();ck('authentic independent review manifest/body/proof joins',actual['decision']=='ACCEPTED_EXACT_CONCRETE_POLICY_ONLY')
for name in refs:
 bad=copy.deepcopy(refs);bad[name]['sha256']='0'*64;refuse('external proof substitution '+name,lambda bad=bad:m._proof_bundle('review',bad,actualinputs,policy,m.Reader()))
refuse('missing actual recovery refuses',lambda:m._proof_bundle('recovery',{},actualinputs,policy,m.Reader()))
# Authentic historical phase component uses actual committed verify_claim. No
# Admission/Run is created and no future COMPLETE outcome is fabricated.
I=B/'financial-wrapper-operational-provenance-compatibility-investigation01-2026-10-04';req=json.loads((I/'PARENT_INPUT_REQUIREMENTS01.json').read_bytes());registered={k:{f:v[f] for f in ('path','sha256','dataset')} for k,v in json.loads((P/'HISTORICAL_ROLE_MAP01.json').read_bytes()).items()}
fields={r['descriptor_field']:r for r in req['rows']};aliases={'fit_claim_input':'old_fit_claim','failed_fit_input':'old_failed_fit','diagnostic_input':'old_diagnostic','schedule_input':'old_schedule'}
for key,role in aliases.items():row=fields[key];registered[role]={'path':row['path'],'sha256':row['sha256'],'dataset':'synthetic'}
row=fields['checkpoint_member:state.pt'];registered['old_state']={'path':row['path'],'sha256':row['sha256'],'dataset':'synthetic'}
oldplan=json.loads((S/registered['historical_plan']['path']).read_bytes());oldcp=policy['historical']['provenance'];registered['training']=dict(oldclaim['inputs'][oldplan['training_input']]);reader=m.Reader();actualinputs=m.Inputs(S,registered,reader)
prior={'parent':helper.HISTORICAL_ID,'claim_input':'historical_claim','terminal_input':'historical_failed','checkpoint_input':'historical_checkpoint','completion_input':None,'provenance':oldcp,'parent_job_input':'historical_execution_job','parent_plan_input':'historical_plan',**aliases}
plan=dict(oldplan,phase='continue100',experiment=m.FIXED['continue100']['experiment'],namespace=m.FIXED['continue100']['experiment']);newprov=dict(oldcp,source_commit='7b056a574e3e7b3c7ba209a39ee6a615e649d60c',source_hashes=sorted(set(policy['target']['installed'].values())))
m._historical(actualinputs,prior,policy,plan,newprov,S,helper,fixture,verify,reader);reader.finish();ck('actual original failed source/claim/checkpoint history pure component',True)
for key,value in [('completion_input','manufactured'),('parent','other'),('provenance',dict(oldcp,source_commit='0'*40)),('checkpoint_input','missing')]:
 wrong=dict(prior);wrong[key]=value;refuse('historical descriptor refusal '+key,lambda wrong=wrong:m._historical(actualinputs,wrong,policy,plan,newprov,S,helper,fixture,verify,m.Reader()))
refuse('missing genuine COMPLETE reference refuses',lambda:m._complete(actualinputs,{'claim_input':'unavailable'},policy,'complete100',newprov,S,helper,verify,m.Reader()))
refuse('original FAILED cannot serve as COMPLETE continuation',lambda:m._complete(actualinputs,prior,policy,'continue100',newprov,S,helper,verify,m.Reader()))
# Authentic source predicates are parsed/executed as pure expressions only.
node=next(n for n in ast.parse((H/'preclaim01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='validate_preclaim');text=ast.unparse(node)
ck('genuine exact Admission requirement','type(admission) is admission_module.Admission' in text)
ck('every input read before compatibility validation',text.index('inputs = Inputs(')<text.index('helper.validate_contract('))
ck('module origin checked before compatibility call',text.index('original imported module origin differs')<text.index('helper.validate_contract('))
ck('all role/phase checks before final metadata status',text.index('unconsumed registered role denominator differs')<text.index('reader.finish()')<text.index('PRECLAIM_METADATA_VALIDATED_NO_CLAIM'))
ck('no Run.start/admit/numerical API call',not any(isinstance(n,ast.Call) and (ast.unparse(n.func).endswith('.start') or ast.unparse(n.func).endswith('.admit') or ast.unparse(n.func).endswith('load_checkpoint')) for n in ast.walk(ast.parse((H/'preclaim01.py').read_text()))))
job=json.loads((S/oldclaim['inputs']['execution_job']['path']).read_bytes());fixture.schema(job)
for key,value in [('wall_seconds',1801),('memory_max_bytes',4*1024**3),('disk_floor_bytes',9*1024**3),('native_unit_limits',{'file_size_bytes':5*1024**2})]:
 wrong=copy.deepcopy(job);wrong['resources'][key]=value;refuse('original resource policy refuses '+key,lambda wrong=wrong:fixture.schema(wrong))
ck('candidate own caps fixed4MiB8MiB120s',(m.FILE,m.TOTAL,m.SECONDS)==(4*1024**2,8*1024**2,120))
ck('still stdlib no scientific import',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
save('CHECKS01.json',{'status':'PASS_SOURCE_OPAQUE_COMPONENTS_ONLY','count':len(rows),'rows':rows,'actual_missing_policy_RED':True,'real_FD_matrices':len(fdrows),'genuine_Admission_or_Run_created':False,'accepted_synthetic_recovery_or_COMPLETE_created':False,'actual_historical_component_only':True,'new_complete_reference_or_prediction_success_untested':True})
print(json.dumps({'status':'PASS_SOURCE_OPAQUE_COMPONENTS_ONLY','checks':len(rows),'real_FD_matrices':len(fdrows)}))
