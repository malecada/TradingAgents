"""Actual capsule source/Git/input/runtime review; no research imports or admission."""
import ast,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;REPO=HERE.parents[3]
I=BASE/'neural-cold-feature-handoff-root-integration02-2026-10-03';OLD=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-01/source');CAP=OLD.parent.parent/'neural-cold-proof-native-20261003-02/source'
A='9742c6ec817dd0917f9f35a52e4b83965ca1cd29';T='095fd51e4d65318f4ee92de9873edf98cbee6c9b';S='fb9fad1d93836b4f92f2be8111da4adf22b7e069';ID='compact-cold-inputs-20261003-01';refs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(p):
 b=p.read_bytes();refs[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(raw(p))
def git(root,*args,input=None):return subprocess.run(['git','-c','protocol.allow=never',*args],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0','GIT_NO_REPLACE_OBJECTS':'1'},input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=20)
def extracted(p,names,ns):
 nodes=[n for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-stdlib-helpers','exec'),ns);return ns
obs=js(I/'REGISTRATION_SOURCE_A02.json');prep=js(I/'INPUT_PREPARATION02.json');release=js(I/'PROPOSED_MATERIALIZATION_RELEASE02.json');snap=js(I/'SOURCE_GIT_SNAPSHOT02.json')
assert obs['source_A2']==A and obs['source_T2']==T and obs['source_S2']==S and release['source']==A and release['root']==str(CAP) and release['status']=='draft' and release['remaining'] and release['prior_materialization'] is None
assert git(CAP,'rev-parse','HEAD').stdout.decode().strip()==A
for commit,parents in [(A,[T]),(T,[S]),(S,[])]:assert git(CAP,'rev-list','--parents','-n','1',commit).stdout.decode().split()==[commit]+parents
for root in (CAP,OLD):
 assert not(root/'.git/objects/info/alternates').exists() and not(root/'.git/info/grafts').exists() and not(root/'.git/shallow').exists()
 assert git(root,'for-each-ref','--format=%(refname)','refs/replace/').stdout==b''
assert len(git(CAP,'ls-tree','-r','--name-only',S).stdout.decode().splitlines())==200
for parent,child,expected in [(S,T,prep['actual_added_files']),(T,A,obs['added_files'])]:
 parts=git(CAP,'diff-tree','--no-commit-id','--name-status','-r','-z',parent,child).stdout.decode().split('\0');pairs=list(zip(parts[:-1:2],parts[1:-1:2]));assert all(k=='A' for k,n in pairs) and sorted(n for k,n in pairs)==sorted(expected)
assert len(prep['actual_added_files'])==16 and len(obs['added_files'])==6
for k in ('registration','sources','phase_contract','runtime','native_environment'):
 r=release[k];b=raw(CAP/r['path']);assert len(b)==r['bytes'] and sha(b)==r['sha256'] and git(CAP,'show',A+':'+r['path']).stdout==b
inv=js(CAP/'cold_prep/source_inventory.json');frozen=BASE/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source_inventory04.json';assert raw(frozen)==(CAP/'cold_prep/source_inventory.json').read_bytes();assert len(inv['source_inventory'])==195 and inv['package_count']==147
sources={r['target']:r['sha256'] for r in inv['source_inventory']};assert len(sources)==195
changed=[]
for r in inv['source_inventory']:
 b=(CAP/r['target']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
 if b!=(OLD/r['target']).read_bytes():changed.append(r['target'])
assert changed==['tradingagents/research/verify.py'];assert sha((CAP/changed[0]).read_bytes())=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
reg=js(CAP/'cold-registration.json');oldreg=js(OLD/'cold-registration.json');assert set(reg['experiments'])=={ID};e=reg['experiments'][ID];oe=oldreg['experiments'][ID];assert reg['families']==oldreg['families'] and reg['datasets']==oldreg['datasets'] and reg['program_id']==oldreg['program_id']
for k in e:
 if k not in {'source_files','runtime_hashes','inputs'}:assert e[k]==oe[k],k
assert e['source_files']==sources and e['parent'] is None and len(e['inputs'])==9 and e['runtime_hashes']=={**oe['runtime_hashes'],'verify.py':sources['tradingagents/research/verify.py']}
family=reg['families'][e['family']];assert family['attempt_budget']==2 and family['prior_attempts']==0 and reg['datasets']['synthetic-cold']['exposures']==[]
assert js(CAP/release['phase_contract']['path'])=={'schema_version':1,'identity':ID,'experiment':e,'family':family,'expected_outputs':e['outputs']}
assert js(CAP/release['sources']['path'])=={'schema_version':1,'files':sources}
for r in e['inputs'].values():
 b=raw(CAP/r['path']);assert sha(b)==r['sha256'] and r['dataset']=='synthetic-cold' and git(CAP,'show',A+':'+r['path']).stdout==b
for name in ('recipe','configs','model','training','environment'):assert (CAP/e['inputs'][name]['path']).read_bytes()==(OLD/oe['inputs'][name]['path']).read_bytes()
for name in ('CHARTER_MATERIALIZE02.md','CHARTER_COMPARE02.md','HISTORY02.md','runtime.json','environment.json'):assert raw(CAP/'cold_prep'/name)==raw(OLD/'cold_prep'/name)
anchor=js(CAP/e['inputs']['anchor']['path']);jobfile=CAP/'tradingagents/research/onchain_replication/job.py';ns=extracted(jobfile,{'required_sources'},{'Path':Path,'__file__':str(jobfile)})
assert anchor['commit']==S and set(anchor['files'])==ns['required_sources']() and len(anchor['files'])==147 and anchor['files']=={p:h for p,h in sources.items() if p.startswith('tradingagents/')}
assert sum((CAP/n).stat().st_size for n in anchor['files'])==1485459
# Exact resources differ only by the new capsule's absolute root strings.
job=js(CAP/e['inputs']['execution_job']['path']);oldjob=js(OLD/oe['inputs']['execution_job']['path'])
def rebase(v):
 if isinstance(v,str):return v.replace(str(OLD),str(CAP))
 if isinstance(v,list):return [rebase(x) for x in v]
 if isinstance(v,dict):return {k:rebase(x) for k,x in v.items()}
 return v
assert job==rebase(oldjob) and job['resources']==js(CAP/e['inputs']['future_resources']['path'])
p=job['resources'];assert p['memory_max_bytes']==p['memory_high_bytes']==3*1073741824 and p['reserve_bytes']==3*1073741824 and p['start_reserve_bytes']==6*1073741824 and p['wall_seconds']==1800 and p['disk_floor_bytes']==10*1073741824 and p['native_unit_limits']=={'file_size_bytes':4194304}
assert p['storage_budget']=={'root':str(CAP),'limits':{'max_allocated_bytes':1073741824,'max_logical_bytes':1073741824,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}} and p['disk_paths']==[str(CAP)] and 'physical_policy' not in p
policy=js(CAP/e['inputs']['cold_proof']['path']);op=rebase(js(OLD/oe['inputs']['cold_proof']['path']));op['source_files']=sources;assert policy==op
native=js(CAP/release['native_environment']['path']);assert native==rebase(js(OLD/'cold_prep/native_environment.json'))
ns=extracted(CAP/'tradingagents/research/onchain_replication/resources.py',{'_native_owned_env'},{'Path':Path});assert native==ns['_native_owned_env'](CAP) and release['cpus']==[0,1]
# All actual195 Git bodies in exact prospective claim order plus appended charter.
pinned=dict(sources);pinned[e['charter']['path']]=e['charter']['sha256'];assert len(pinned)==196
names=list(pinned);groups=[];allrows=[]
for start in range(0,len(names),128):
 group=names[start:start+128];request=''.join(A+':'+n+'\n' for n in group).encode();result=git(CAP,'cat-file','--batch',input=request);wire=result.stdout;off=0;bodytotal=0
 for n in group:
  end=wire.index(b'\n',off);oid,kind,size=wire[off:end].split();size=int(size);assert kind==b'blob' and len(oid)==40 and size<=8388608
  b=wire[end+1:end+1+size];assert sha(b)==pinned[n] and b==(CAP/n).read_bytes() and wire[end+1+size:end+2+size]==b'\n';framing=end-off+2;off=end+2+size;bodytotal+=size
  allrows.append({'path':n,'commit':A,'sha256':pinned[n],'bytes':size,'git_object':oid.decode(),'request_bytes':len((A+':'+n+'\n').encode()),'framing_bytes':framing})
 assert off==len(wire) and len(request)<=65536 and len(wire)<=8404992 and len(result.stderr)<=65536
 groups.append({'rows':len(group),'request_bytes':len(request),'body_bytes':bodytotal,'stdout_bytes':len(wire),'stderr_bytes':len(result.stderr)})
# Genuine numerical anchor bodies separately at S; no fake anchor compatibility.
for name,h in anchor['files'].items():assert sha(git(CAP,'show',S+':'+name).stdout)==h
# Old archive scope remains unchanged (including source/Git and all metadata files).
oldmeta=js(BASE/'neural-cold-feature-handoff-root-integration01-2026-10-03/SOURCE_A_RETENTION01.json')
for r in oldmeta['members']:
 q=OLD/r['path'];st=q.lstat();assert stat.S_IMODE(st.st_mode)==r['mode']
 if r['kind']=='file':assert stat.S_ISREG(st.st_mode) and st.st_size==r['bytes'] and sha(q.read_bytes())==r['sha256']
 else:assert stat.S_ISDIR(st.st_mode)
assert git(OLD,'rev-parse','HEAD').stdout.decode().strip()=='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e'
withdraw=js(BASE/'claim-source-git-batch-root-integration01-2026-10-03/WITHDRAWAL_SOURCE_A01.json');assert withdraw['status']=='withdrawn-unattempted-root-selection'
assert sha(raw(BASE/'claim-source-git-batch-root-integration-review01-2026-10-03/REVIEW_INTEGRATION01.md'))=='bd3bf8f02c856366e926ba51f36a07111cca3ebd3d9201594cded0cdd05881f6'
absent=[]
for root in (CAP,OLD,REPO):
 for identity in (ID,'compact-cold-comparison-20261003-01'):
  for base in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
   q=root/base/identity;assert not q.exists() and not q.is_symlink();absent.append(str(q))
# Pinned stdlib-only checker performs actual installed RECORD/readback without package import.
runtime=js(CAP/release['runtime']['path']);assert len(runtime['distribution_records'])==len({r['name'] for r in runtime['distribution_records']})==251
checker=CAP/'proof_tools/runtime_gate01.py';assert sha(checker.read_bytes())==sources['proof_tools/runtime_gate01.py'];spec=importlib.util.spec_from_file_location('review_runtime02',checker);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);cwd=Path.cwd();os.chdir(CAP)
try: rr=mod.check(CAP,runtime)
finally:os.chdir(cwd)
assert not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow','tradingagents'} for n in sys.modules)
result={'status':'PASS-prospective-actual-A2-only','A2':A,'T2':T,'S2':S,'sources':195,'anchor':147,'package_bytes':1485459,'inputs':9,'runtime_RECORDs':251,'runtime_qualification':rr['runtime_record_qualification'],'changed_selected_sources':changed,'old_members_checked':728,'absent_namespaces':absent,'prospective_source_charter_groups':groups,'prospective_source_charter_rows':allrows,'draft_status':release['status'],'full_A2_external_recovery_verified':False,'actual_native_limits_observed':False,'qualification':'No claim/admit/Owner/verifier/builder stage/numerical import or job. Final recovered release and accepted wrapper required.'}
(HERE/'readback02.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');(HERE/'refs02.json').write_text(json.dumps(refs,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in {'prospective_source_charter_rows','absent_namespaces'}},sort_keys=True))
