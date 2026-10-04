import ast,copy,hashlib,importlib.util,json,os,stat,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;PREP=HERE.parent/'financial-genuine-wrapper-claimedrun-source-handoff-preparation01-2026-10-04';checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
check(sha((PREP/'MANIFEST01.json').read_bytes())=='36b0a1fce80b44c3bb14f744f8c6ba52c674b736c3134f3dc2270f48372ce2f9','exact frozen manifest');m=load(PREP/'MANIFEST01.json');actual=[]
def walk(p):
 for q in p.iterdir():
  actual.append(str(q.relative_to(PREP)))
  if stat.S_ISDIR(q.lstat().st_mode):walk(q)
walk(PREP);check(set(actual)=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete source evidence including failed original generator')
for r in m['members']:
 p=PREP/r['path'];s=p.lstat();check(oct(stat.S_IMODE(s.st_mode))==r['mode'],'mode '+r['path'])
 if r['kind']=='file':check(len(p.read_bytes())==r['bytes'] and sha(p.read_bytes())==r['sha256'],'body '+r['path'])
 else:check(stat.S_ISDIR(s.st_mode),'directory type')
check(sha((PREP/'owned_io.py').read_bytes())=='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','actual accepted cleanup body')
sys.path.insert(0,str(PREP));spec=importlib.util.spec_from_file_location('review_handoff_only',PREP/'generate01.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
check(sha((PREP/'generate01.py').read_bytes())=='efcba9d1f36f2a472812ff5582a4d706c52f6a0360c7868cf2cfab34d5b072b7','exact generator');check(not os.path.lexists(g.NEW.parent),'actual future target absent before read-only build');bodies=g.build();check(not os.path.lexists(g.NEW.parent),'read-only build created no capsule');check(len(bodies)==11,'exact eleven draft bodies including8inputs/history/descriptor/readback')
for name,b in bodies.items():check((PREP/'generated01'/name).read_bytes()==b,'actual deterministic full emitted bytes '+name)
d=load(PREP/'generated01/HANDOFF01.json');check(len(d['input_roles'])==8 and d['implementation']==194 and d['package']==149 and d['changed']==1 and d['unchanged']==193,'exact role and source denominators')
for k in ('new_source','design_source','registration','charter','cumulative19_admission','independent_source_review','caller','complete_recovery','source_file_map','final_tracked_count'):check(d[k] is None,'future field remains null '+k)
check(d['release'] is False and d['checkpoint_ancestry_from_failed_recordfix'] is False and d['historical_claims_spent']==1,'no claimed authority/checkpoint')
base=g.OLD/'fixture_inputs/financial_wrapper_recordfix01';oldc=load(base/'source_closure.json');oldj=load(base/'execution_job.json');oldp=load(base/'wrapper_plan.json');c=load(PREP/'generated01/source_closure.json');j=load(PREP/'generated01/execution_job.json');p=load(PREP/'generated01/wrapper_plan.json');cc=copy.deepcopy(c);cc['installed'][g.WRAPPER]=oldc['installed'][g.WRAPPER];check(g.enc(cc)==(base/'source_closure.json').read_bytes(),'full closure byte inverse one wrapper hash');jj=copy.deepcopy(j);jj['resources']['disk_paths']=oldj['resources']['disk_paths'];jj['resources']['storage_budget']['root']=oldj['resources']['storage_budget']['root'];check(g.enc(jj)==(base/'execution_job.json').read_bytes(),'full job byte inverse two new-root fields');pp=copy.deepcopy(p);pp['experiment']=oldp['experiment'];pp['namespace']=oldp['namespace'];check(g.enc(pp)==(base/'wrapper_plan.json').read_bytes(),'full plan byte inverse only identity namespace')
for name in ('model','training','environment','runtime_mapping','synthetic_recipe'):check(bodies[name+'.json']==(base/(name+'.json')).read_bytes(),'unchanged input byte-exact '+name)
for role,ref in d['input_roles'].items():check(ref=={'path':g.PREFIX+'/'+role+'.json','sha256':sha(bodies[role+'.json'])},'exact complete role descriptor '+role)
source=load(PREP/'generated01/ORIGINAL_SOURCE_READBACK01.json');check(len(source['tracked'])==325 and source['source']==g.SOURCE,'actual325original')
for name,row in source['tracked'].items():
 b=(g.OLD/name).read_bytes();s=(g.OLD/name).stat();check(sha(b)==row['sha256'] and len(b)==row['bytes'] and stat.S_IMODE(s.st_mode)==row['mode'],'actual original body/mode '+name);check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'] and ('100755' if s.st_mode&0o111 else '100644')==row['git_mode'],'actual Git body/mode join '+name)
for name,h in oldc['installed'].items():check(sha((g.OLD/name).read_bytes())==h and (name==g.WRAPPER or c['installed'][name]==h),'all193 unchanged implementation '+name)
candidate=(PREP/'candidate.py').read_bytes();check(sha(candidate)==g.CANDIDATE,'accepted f4ea candidate exact');back=candidate.decode()
for row in reversed(load(PREP/'INVERSE01.json')['edits']):check(back.count(row['new'])==1,'unique inverse seam');back=back.replace(row['new'],row['old'])
check(back.encode()==(g.OLD/g.WRAPPER).read_bytes(),'candidate complete byte inverse to actual e2d');check(ast.dump(ast.parse(back))==ast.dump(ast.parse((g.OLD/g.WRAPPER).read_bytes())),'candidate full AST inverse')
# Complete source-cardinality and source-pin mutations with genuine derive(), no authority.
refusals=[]
def refuse(label,f):
 try:f()
 except (ValueError,KeyError,TypeError) as e:checks.append('refusal '+label);refusals.append({'case':label,'reason':str(e)})
 else:raise AssertionError('not refused '+label)
for name in oldc['installed']:
 bad=copy.deepcopy(oldc);bad['installed'][name]='0'*64;refuse('wrong source pin '+name,lambda bad=bad:g.derive(bad,oldj,oldp,candidate))
bad=copy.deepcopy(oldc);bad['installed']['extra.py']='0'*64;refuse('extra closure',lambda:g.derive(bad,oldj,oldp,candidate));refuse('wrong candidate',lambda:g.derive(oldc,oldj,oldp,candidate+b'\n'))
for field,val in [('phase','continue100'),('prior_input','prior'),('reference_input','reference')]:
 bad=copy.deepcopy(oldp);bad[field]=val;refuse('wrong first plan '+field,lambda bad=bad:g.derive(oldc,oldj,bad,candidate))
# Exact read cleanup keeps the original fatal even if its owned fd close fails.
raw=(PREP/'generate01.py').read_bytes();tree=ast.parse(raw);readfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='read');f=HERE/'owned-fatal-read';f.write_bytes(b'opaque');first=MemoryError('controlled read fatal');fds=[]
def failread(fd,n):fds.append(fd);os.close(fd);raise first
proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in ('open','close','fstat','O_RDONLY','O_NOFOLLOW','O_NONBLOCK')},read=failread)
ns={'require':g.require,'stat':stat,'os':proxy,'_cleanup':g._cleanup,'FILE':g.FILE};exec(compile(ast.Module(body=[readfn],type_ignores=[]),'<actual read fatal>','exec'),ns)
try:ns['read'](f)
except BaseException as e:check(e is first,'reader firstfatal preserved despite closeEBADF');check(not Path('/proc/self/fd/'+str(fds[0])).exists(),'reader ownedfd absent')
else:raise AssertionError('fatal disappeared')
# Exact comparison guards as scalar predicates; wrong source/runtime/role pins refuse.
for name,pin in load(PREP/'BASE_INPUT_PINS01.json').items():check(sha((base/(name+'.json')).read_bytes())==pin,'actual baseline role pin '+name);check(sha((base/(name+'.json')).read_bytes()+b'\n')!=pin,'wrong role bytes refuse '+name)
runtime=load(base/'runtime_mapping.json');check(runtime['executable']==sys.executable and runtime['prefix']==sys.prefix,'actual original runtime prefix');check(len(runtime['distribution_records'])==251,'all251runtime RECORDs');check(source['runtime_record_hashes_verified']==251 and source['runtime_dependency_bodies_recovered'] is False and source['runtime_api_observed'] is False,'metadata runtime scope only')
check(not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')),'no scientific import')
out={'decision':'WITHHELD_GENERATOR_SH1_SH2_EXISTING_DRAFT_BYTES_AUTHENTICATED','checks':len(checks),'check_names':checks,'refusals':refusals,'generator_sha256':sha(raw),'candidate_sha256':sha(candidate),'exact_current_generated_bytes_authenticated':True,'actual_325_original_bodies_modes':True,'actual_194_closure193_unchanged':True,'actual_251_RECORD_hashes_read':True,'actual_runtime_dependency_bodies_recovered':False,'actual_runtime_api_observed':False,'source_only':True,'actual_new_source':None,'actual_new_registration':None,'actual_new_caller':None,'actual_new_admission':None,'target_capsule_created':False,'findings':['SH1 reader final canonical parent path is not reauthenticated and accepts owned parent symlink substitution during read','SH2 output context-manager close can replace original write fatal with actual close error'],'note':'No actual source/capsule mutation, clone or claim performed. Candidate source and current draft bytes are coherent; generator requires separate I/O correction/review before reuse.'}
(HERE/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','refusals')}))
