import ast,copy,hashlib,importlib.util,json,os,stat,sys,time
from pathlib import Path
P=Path(__file__).absolute().parent;B=P.parent;A=B/'financial-wrapper-compatibility-preclaim-source01-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('reviewed_preclaim',P/'CANDIDATE_preclaim01.py');checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n);(P/'CHECK_PROGRESS01.json').write_text(json.dumps(checks,indent=2)+'\n')
def refuse(n,f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError):ck(n,True)
 else:raise AssertionError('accepted '+n)
def sha(b):return hashlib.sha256(b).hexdigest()
ck('exact source',sha((A/'preclaim01.py').read_bytes())=='24b6c2a51759bf992fb0da479f46ba6d582b0e24f1c5c40c5055a34f859de71e')
manifest=json.loads((A/'MANIFEST01.json').read_bytes())
actual=[]
def census(p):
 for f in p.iterdir():
  rel=f.relative_to(A).as_posix()
  if rel=='MANIFEST01.json':continue
  s=f.lstat();actual.append(rel)
  if stat.S_ISDIR(s.st_mode):census(f)
census(A)
ck('complete candidate membership',set(actual)=={r['path'] for r in manifest['members']})
for row in manifest['members']:
 p=A/row['path'];s=p.lstat();ck('mode:'+row['path'],stat.S_IMODE(s.st_mode)==row['mode'])
 if row['kind']=='file':ck('body:'+row['path'],stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'])
 elif row['kind']=='symlink':ck('literal-link:'+row['path'],os.readlink(p)==row['target'])
 else:ck('directory:'+row['path'],stat.S_ISDIR(s.st_mode))
policy=json.loads((A/'POLICY01.json').read_bytes());ck('policy pin',sha((A/'POLICY01.json').read_bytes())==m.POLICY_SHA)
sourcebytes=0
for name,pin in policy['target']['installed'].items():
 raw=(S/name).read_bytes();sourcebytes+=len(raw);ck('currentsource:'+name,sha(raw)==pin)
ck('source195full',len(policy['target']['installed'])==195 and sourcebytes==2062446)
# Pure role schemas, no Admission object.
for role in m.BASE:refuse('missingrole:'+role,lambda role=role:m._roles(m.BASE-{role},'complete100'))
m._roles(m.BASE,'complete100');ck('pure11role',True)
refuse('extrareferencerole',lambda:m._roles(m.BASE|{'extra'},'complete100'))
O=P/'owned01';O.mkdir(mode=0o700);a=O/'a';b=O/'b';a.write_bytes(b'opaque a');b.write_bytes(b'opaque b')
r=m.Reader();reg={'a':{'path':'a','sha256':sha(a.read_bytes()),'dataset':'synthetic'},'b':{'path':'b','sha256':sha(b.read_bytes()),'dataset':'synthetic'}}
x=m.Inputs(O,reg,r);ck('eager-allinputs',set(x.bodies)==set(reg));r.finish();ck('stable-readback',True)
for key,val in [('sha256',None),('sha256','A'*64),('path','../x'),('path','.env'),('dataset','empirical')]:
 rr=copy.deepcopy(reg);rr['b'][key]=val;refuse('input:'+key+str(val),lambda rr=rr:m.Inputs(O,rr,m.Reader()))
link=O/'link';link.symlink_to(a);refuse('real-link',lambda:m.Reader().read(link))
refuse('real-directory',lambda:m.Reader().read(O))
r=m.Reader();r.read(a);a.rename(O/'original-a');a.write_bytes(b'altered!');refuse('endpoint-replacement',r.finish)
r=m.Reader();r.deadline=0;refuse('deadline-beforeopen',lambda:r.read(b))
# Closed observed per-file cap via sparse owned negative, not an admitted body.
sparse=O/'over-cap-negative';fd=os.open(sparse,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.ftruncate(fd,m.FILE+1);os.close(fd)
refuse('actual4MiBplus1negative',lambda:m.Reader().read(sparse))
# Authentic fixed independent review bundle; no synthetic recovery.
refs=json.loads((A/'RELEASE_REFS_DRAFT01.json').read_bytes());main=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
registered={m.REVIEW_ROLE:{'path':str(Path(refs['review_proof']['path']).relative_to(main)),'sha256':refs['review_proof']['sha256'],'dataset':'synthetic'},'source_closure':{'path':str((A/'SOURCE_CLOSURE01.json').relative_to(main)),'sha256':sha((A/'SOURCE_CLOSURE01.json').read_bytes()),'dataset':'synthetic'}}
r=m.Reader();inputs=m.Inputs(main,registered,r);v=m._proof_bundle('review',refs,inputs,policy,r);r.finish();ck('actual-authored-review-join',v['decision']=='ACCEPTED_EXACT_CONCRETE_POLICY_ONLY')
for key in ('review_proof','review_machine','review_manifest','review_report'):
 mutated=copy.deepcopy(refs);mutated[key]['sha256']='0'*64;refuse('actual-review-hash:'+key,lambda mutated=mutated:m._proof_bundle('review',mutated,inputs,policy,m.Reader()))
refuse('null-recovery',lambda:m._proof_bundle('recovery',refs,inputs,policy,m.Reader()))
# Original generic checkpoint validator on actual historical opaque metadata.
roles=json.loads((A/'HISTORICAL_ROLE_MAP01.json').read_bytes());registered={n:{k:r[k] for k in ('path','sha256','dataset')} for n,r in roles.items()}
cp=json.loads((S/registered['historical_checkpoint']['path']).read_bytes());cpp=S/registered['historical_checkpoint']['path'];state=cpp.parent/'state.pt'
registered['opaque_state']={'path':state.relative_to(S).as_posix(),'sha256':cp['members']['state.pt']['sha256'],'dataset':'synthetic'}
r=m.Reader();hist=m.Inputs(S,registered,r);m._checkpoint(hist,'historical_checkpoint',cp['provenance'],cpp.parents[2],r);r.finish();ck('real-historical-checkpoint-opaque',True)
for key,value in [('schema_version',True),('key','0'*64),('members',{}),('provenance',dict(cp['provenance'],source_commit='0'*40))]:
 bad=copy.deepcopy(cp);bad[key]=value;hist.bodies['historical_checkpoint']=json.dumps(bad).encode();refuse('checkpoint:'+key,lambda:m._checkpoint(hist,'historical_checkpoint',cp['provenance'],cpp.parents[2],m.Reader()))
# Real descriptors and primary/secondary object retention; no numerical handle.
fdcases=[]
def reachable(root):
 found={};stack=[root]
 while stack:
  e=stack.pop()
  if e is None or id(e) in found:continue
  found[id(e)]=e
  for name in ('__cause__','__context__'):
   try:stack.append(BaseException.__getattribute__(e,name))
   except BaseException:pass
  try:stack.extend(BaseException.__dict__['__dict__'].__get__(e).get('storage_cleanup_errors',()))
  except BaseException:pass
 return found
for i,(p,e1,e2) in enumerate([(KeyboardInterrupt(),OSError(),SystemExit()),(MemoryError(),OSError(),OSError()),(ValueError(),KeyboardInterrupt(),OSError()),(ValueError(),OSError(),SystemExit()),(None,OSError(),OSError()),(None,KeyboardInterrupt(),SystemExit())]):
 fds=[os.open(b,os.O_RDONLY),os.open(b,os.O_RDONLY)];original=m.os.close;pending=list(zip(fds,[e1,e2]));selected=p
 def close(fd):
  original(fd)
  for wanted,error in pending:
   if wanted==fd:raise error
 m.os.close=close
 try:
  for fd in fds:
   try:m._close(fd,selected)
   except BaseException as error:selected=error
 finally:m.os.close=original
 g=reachable(selected);ck('fatalgraph:'+str(i),all(e is None or id(e) in g for e in (p,e1,e2)))
 fatal=next((e for e in (p,e1,e2) if e is not None and (not isinstance(e,Exception) or isinstance(e,MemoryError))),None)
 if fatal is not None:ck('fatalprimary:'+str(i),selected is fatal)
 for fd in fds:
  try:os.fstat(fd)
  except OSError:ck('fdclosed:'+str(i)+':'+str(fd),True)
  else:raise AssertionError('openfd')
 fdcases.append({'case':i,'alloriginalexceptionsreachable':True,'allfdsclosed':True})
# Static actual API and phase topology comparisons; never call public preclaim.
t=ast.parse((A/'preclaim01.py').read_bytes());public=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='validate_preclaim');text=ast.unparse(public)
ck('exactAdmissiononly','type(admission) is admission_module.Admission' in text)
ck('sourcepin195body','for rel, pin in policy[\'target\'][\'installed\'].items()' in text)
ck('no forbidden execution calls',not any(isinstance(n,ast.Call) and ast.unparse(n.func).split('.')[-1] in ('admit','start','load_checkpoint','save_checkpoint','torch','read_pickle') for n in ast.walk(t)))
ck('no NUM imports',not any(n.split('.')[0] in ('numpy','torch','scipy','pandas') for n in sys.modules))
(P/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'fd_cases':fdcases,'source_bytes':sourcebytes,'source_double_read_bytes':sourcebytes*2,'source_only':True,'public_success_tested':False,'actual_recovery_complete_outcome_fabricated':False,'finding':'Reader.finish stale earlier path after later cleanup; see WITNESS01','author_manifest_sha256':sha((A/'MANIFEST01.json').read_bytes())},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'status':'bounded-controls-pass-with-material-currentness-finding'}))
