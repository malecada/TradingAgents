import ast,copy,datetime,hashlib,importlib.util,json,os,re,stat,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;N=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');O=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');S='0a2e7639b42b9423b90743feadcda4078aa21816';OLD='649fb8a11089524aaef7843dffeeb90a3a55ca17';ID='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01';PREV='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';PREFIX='fixture_inputs/financial_wrapper_claimedrun01/';GATE=PREFIX+'gates.json';checks=[];refusals=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();check(stat.S_ISREG(s.st_mode) and p.resolve()==p and s.st_size<=4*1024**2,'bounded canonical regular '+str(p.relative_to(N) if p.is_relative_to(N) else p.name));raw=p.read_bytes();t=p.lstat();check((s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_mode,t.st_size,t.st_mtime_ns,t.st_ctime_ns),'stable '+p.name);return raw
def load(p):return json.loads(read(p))
def git(root,*args,input=None):
 q=subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30);check(q.returncode==0,'read-only Git '+args[0]);return q.stdout
def module(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
check(git(N,'rev-parse','HEAD').decode().strip()==S,'actual current exact');check(git(N,'show','-s','--format=%P',S).decode().strip()==OLD,'direct original649 parent');check(git(O,'rev-parse','HEAD').decode().strip()==OLD,'original HEAD immutable');check(git(N,'diff','--name-only','HEAD')==b'','actual tracked clean')
check((N/'.git').is_dir() and (N/'.git').resolve()==N/'.git','standalone Git');check(not (N/'.git/objects/info/alternates').exists(),'no alternate Git dependency')
def tree(root,source):
 out={}
 for line in git(root,'ls-tree','-r','-z',source).split(b'\0'):
  if not line:continue
  a,n=line.split(b'\t');mode,kind,oid=a.decode().split();check(kind=='blob','tracked regular Gitblob');out[n.decode()]={'mode':mode,'oid':oid}
 return out
t=tree(N,S);ot=tree(O,OLD);check(len(t)==339 and len(ot)==325,'339 current325 historical');g=load(N/GATE);check(sha(read(N/GATE))=='3a20293832fa7ecc5e2821fb27dc940d1a997ab7f2ad373bc28f73e893e8781a','exact gate');og=load(O/'fixture_inputs/financial_wrapper_recordfix01/gates.json');e=g['experiments'][ID];check(set(e['source_files'])==set(t)-{GATE} and len(e['source_files'])==338,'exact338pins only selfgate excluded');check(len(g['experiments'])==12 and {k:v for k,v in g['experiments'].items() if k!=ID}==og['experiments'],'all11 historical definitions exact');gg=copy.deepcopy(g);del gg['experiments'][ID];check(gg==og,'entire original gate unchanged except new entry')
changed=[];inventory=[]
for name,row in t.items():
 p=N/name;raw=read(p);mode=stat.S_IMODE(p.lstat().st_mode);check(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['oid'],'committed body '+name);check(row['mode']==('100755' if mode&0o111 else '100644'),'Git executable mode '+name)
 if name!=GATE:check(e['source_files'][name]==sha(raw),'exactsourcepin '+name)
 if name in ot:
  check(mode==stat.S_IMODE((O/name).lstat().st_mode),'original literal mode '+name)
  if raw!=read(O/name):changed.append(name)
 inventory.append({'path':name,'mode':mode,'bytes':len(raw),'sha256':sha(raw),'git_blob':row['oid'],'git_mode':row['mode']})
wrapper='tradingagents/research/onchain_replication/financial_wrapper_fixture.py';check(changed==[wrapper],'sole changed original325 body');check(sha(read(N/wrapper))=='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e','accepted wrapper');check(set(t)-set(ot)=={PREFIX+n for n in ('model.json','training.json','environment.json','execution_job.json','runtime_mapping.json','source_closure.json','synthetic_recipe.json','wrapper_plan.json','allocation19.json','extension19.json','extension-review19.json','closed-history-relocation.json','charter.json','gates.json')},'exact14metadata additions')
# Complete original reachable Git objects, raw content and computed object identity.
gspec=load(B/'financial-genuine-wrapper-claimedrun-history-copy-admission-review01-2026-10-04/GIT_ANCESTRY_SPEC01.json');objs=gspec['objects'];check(len(objs)==363,'original363objects');raw=git(N,'cat-file','--batch',input=b''.join((r['oid']+'\n').encode() for r in objs));offset=0
for r in objs:
 end=raw.index(b'\n',offset);oid,kind,size=raw[offset:end].decode().split();n=int(size);body=raw[end+1:end+1+n];check((oid,kind,n)==(r['oid'],r['type'],r['bytes']) and sha(body)==r['content_sha256'],'historical object '+oid);check(hashlib.sha1((kind+' '+size+'\0').encode()+body).hexdigest()==oid,'actual object ID '+oid);check(raw[end+1+n:end+2+n]==b'\n','object framing');offset=end+2+n
check(offset==len(raw),'no extra Git response');check(git(N,'rev-list','--parents',OLD).decode().splitlines()==gspec['ancestry_lines'],'all6 original ancestry commits')
# Full exact failed claim history, directories and modes. No creation/claim/admit.
spec=load(B/'financial-genuine-wrapper-claimedrun-history-copy-admission-review01-2026-10-04/CLAIM_COPY_SPEC01.json');d=N/'research_runs'/PREV;od=O/'research_runs'/PREV
check({p.name for p in (N/'research_runs').iterdir() if not p.name.startswith('.')}=={PREV},'exact one nonhidden historical claim');check({'.'}|{p.relative_to(d).as_posix() for p in d.rglob('*')}=={r['path'] for r in spec['members']},'complete4nodes')
for r in spec['members']:
 p=d/r['path'];o=od/r['path'];check(stat.S_IMODE(p.lstat().st_mode)==r['mode']==stat.S_IMODE(o.lstat().st_mode),'claim literal modes '+r['path']);check(p.resolve()==p,'claim canonical path')
 if r['kind']=='file':check(read(p)==read(o) and sha(read(p))==r['sha256'],'historical bytes '+r['path'])
 else:check(p.is_dir() and not p.is_symlink(),'claim directory')
v=module('actual_source_verify',N/'tradingagents/research/verify.py');claim=v.verify_claim(d);closed=v.verify_run(d);check(closed['status']=='failed' and closed['output_count']==0,'genuine structural verifier failed0outputs');check(claim==v.verify_claim(od),'genuine original-relocated verify_claim equality');check(claim['experiment']==g['experiments'][PREV] and claim['effective_attempt_budget']==18,'genuine closedparent definition and ceiling18');check(not (N/'research_runs'/ID).exists(),'newidentity unclaimed')
rel=load(N/(PREFIX+'closed-history-relocation.json'));check(rel['old_root']==str(O) and rel['new_root']==str(N) and rel['same_global_spent_claim']==PREV and rel['historical_owner_or_job_runtime_authority_transferred'] is False and rel['scientific_checkpoint_present_or_relocated'] is False,'exact relocation historical-only');check(rel['copied_relative_claim_tree']==spec['members'],'all four mapped nodes exact')
# Actual original admission primitives only; never call admit or construct Admission.
a=module('actual_admission_source_only',N/'tradingagents/research/admission.py');a._source_files(N,S,S,e['source_files']);check(True,'genuine _source_files all338current/design');check(e['runtime_hashes']==a.runtime_hashes(),'genuine runtime_hashes');check(a._committed(N,S,GATE)==read(N/GATE),'genuine committed gate');check(a._committed(N,S,e['charter']['path'],e['charter']['sha256'])==read(N/e['charter']['path']),'genuine charter current/design pin')
family=g['families'][e['family']];check(family==claim['family'] and family['attempt_budget']==18 and family['prior_attempts']==0,'unchanged base family18prior0');check(e['parent']==PREV,'correction ancestry same failedparent');check(e['stage']=='development' and e['reuse']=='exploratory' and e['selection'] is None,'no fresh confirmatory data');check(e['windows']==claim['experiment']['windows'],'same exposed administrative clock')
for w in e['windows']:check(a._window(w)[1]<=datetime.datetime.now(datetime.timezone.utc) and w['availability']=='existing','ended existing window')
check({i['dataset'] for i in e['inputs'].values()}=={w['dataset'] for w in e['windows']},'input/window complete map')
for k in ('cells','outputs'):check(len(e[k])==len(set(e[k])) and all(a.identity(n,k)==n for n in e[k]),'exactunique '+k)
bud=module('actual_budget_source_only',N/'tradingagents/research/budget_extensions.py')
def bound(ref):
 if set(ref)!={'path','sha256'} or not isinstance(ref['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',ref['sha256']) or e['source_files'].get(ref['path'])!=ref['sha256']:raise ValueError('sourcepin')
 return a._committed(N,S,ref['path'],ref['sha256'])
ceiling=bud.effective_budget(N,g['program_id'],ID,e,family,[claim],bound);check(ceiling==19,'genuine budget metadata helper computes prospective19');check(len([claim])+family['prior_attempts']==1<ceiling,'spent1 preserved18remaining');base=copy.deepcopy(e);del base['cumulative_budget_extension'];check(bud.effective_budget(N,g['program_id'],ID,base,family,[claim],bound)==18,'without extension genuine base18');check(sha(read(N/(PREFIX+'extension-review19.json')))=='3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e','genuine independent review exact')
def refuse(name,f):
 try:f()
 except (ValueError,KeyError,TypeError) as error:refusals.append({'case':name,'error':str(error)});check(True,'refusal '+name)
 else:raise AssertionError('not refused '+name)
refuse('wrong first adopter',lambda:bud.effective_budget(N,g['program_id'],PREV,e,family,[claim],bound));refuse('missing preserved history',lambda:bud.effective_budget(N,g['program_id'],ID,e,family,[],bound));bad=copy.deepcopy(e);bad['cumulative_budget_extension']['review']['sha256']='0'*64;refuse('wrong actualreview pin',lambda:bud.effective_budget(N,g['program_id'],ID,bad,family,[claim],bound));refuse('wrong source pin',lambda:a._source_files(N,S,S,{wrapper:'0'*64}));refuse('changedsource against olddesign',lambda:a._source_files(N,S,OLD,{wrapper:e['source_files'][wrapper]}))
# Actual role bodies, source-only schema/plan functions extracted without package import.
gen=B/'financial-genuine-wrapper-root-claimedrun-handoff-generation01-2026-10-04/generated01';check(len(e['inputs'])==8,'eight actualinputs')
for role,ref in e['inputs'].items():check(read(N/ref['path'])==read(gen/(role+'.json')) and sha(read(N/ref['path']))==ref['sha256']==e['source_files'][ref['path']],'actual generated role '+role)
c=load(N/(PREFIX+'source_closure.json'));check(len(c['installed'])==194 and sum(n.startswith('tradingagents/') for n in c['installed'])==149,'194/149closure')
for n,pin in c['installed'].items():check(sha(read(N/n))==pin==e['source_files'][n],'science closure '+n)
check(sum(read(N/n)==read(O/n) for n in c['installed'])==193,'193 unchanged sciencebodies');j=load(N/(PREFIX+'execution_job.json'));plan=load(N/(PREFIX+'wrapper_plan.json'));raw=read(N/wrapper);nodes=ast.parse(raw);want={'Unavailable','require','validate_plan','schema'};ns={'GIB':1024**3,'FILE':4*1024**2,'PHASES':('agreement','interrupt1','complete100','continue100','predict')};exec(compile(ast.Module(body=[n for n in nodes.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in want],type_ignores=[]),'<genuine scalar schemas>','exec'),ns);ns['schema'](j);ns['validate_plan'](plan);check(plan['experiment']==plan['namespace']==ID and plan['phase']=='interrupt1' and plan['prior_input'] is None and plan['reference_input'] is None and e['cells']==[plan['cell_id']],'freshinterrupt ancestry notcheckpoint');check(set(e['outputs'])=={'cell-ledger.json','wrapper-summary.json','artifact-index.json'},'complete output denominator');check(j['resources']['disk_paths']==[str(N)] and j['resources']['storage_budget']['root']==str(N),'whole newroot resources')
for key,val in [('phase','continue100'),('prior_input','prior'),('reference_input','reference')]:
 pp=copy.deepcopy(plan);pp[key]=val;refuse('invalid plan '+key,lambda pp=pp:ns['validate_plan'](pp))
for key,val in [('memory_max_bytes',4*1024**3),('wall_seconds',1801),('disk_floor_bytes',1)]:
 jj=copy.deepcopy(j);jj['resources'][key]=val;refuse('nativepolicy '+key,lambda jj=jj:ns['schema'](jj))
ch=load(N/e['charter']['path']);check(ch['actual_claims_started']==1 and ch['base_attempt_budget']==18 and ch['paper_fit_credit']==0 and len(ch['phases'])==18,'charter denominators');check(ch['denominator']['training_optimizer_updates']==800 and ch['denominator']['agreement_optimizer_updates']==4 and ch['denominator']['completed_100epoch_fits']==8,'original800+4/8complete contract');check(ch['operational_source_correction']['new_source_design_review'] is None and ch['operational_source_correction']['new_caller_release'] is None and ch['operational_source_correction']['new_full_source_caller_recovery'] is None,'future releases withheld')
check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numerical import');check(git(N,'rev-parse','HEAD').decode().strip()==S and git(N,'diff','--name-only','HEAD')==b'','final unchanged current source');check(not (N/'research_runs'/ID).exists(),'no fresh claim created')
out={'decision':'ACCEPTED_ACTUAL_SOURCE_GATE_PROSPECTIVE_BUDGET_METADATA_ONLY','source':S,'design_source':S,'gate_sha256':sha(read(N/GATE)),'checks':len(checks),'check_names':checks,'refusals':refusals,'current_tracked':339,'current_source_pins':338,'implementation':194,'package':149,'unchanged_science':193,'old_entries_retained':11,'new_gate_entries':12,'original_git_objects_authenticated':363,'actual_claim_count':1,'actual_failed_count':1,'actual_outputs':0,'actual_highest_claim_budget':18,'prospective_effective_budget_helper':19,'genuine_admit_called':False,'Admission_Run_Owner_created':False,'new_numerical_or_claim':False,'actual_caller_release':None,'actual_full_new_source_recovery':None,'actual_runtime_api_observed':False,'native_capacity':None,'paper_fit_credit':0,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(H/'SOURCE_MAP01.json').write_text(json.dumps(inventory,sort_keys=True,indent=2)+'\n');(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','refusals')}))
