import ast,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;P=BASE/'neural-cold-feature-handoff-root-integration02-2026-10-03';C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');refs={}
def h(b):return hashlib.sha256(b).hexdigest()
def raw(p):
 b=p.read_bytes();refs[str(p)]={'bytes':len(b),'sha256':h(b)};return b
def js(p):return json.loads(raw(p))
def require(v,m):
 if not v:raise ValueError(m)
def git(*a,input=None):return subprocess.check_output(['git','-c','protocol.allow=never',*a],cwd=C,input=input,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0'},timeout=20)
release=js(P/'CANDIDATE_RELEASE_ENVELOPE02.json');assert len((P/'CANDIDATE_RELEASE_ENVELOPE02.json').read_bytes())==1159 and h((P/'CANDIDATE_RELEASE_ENVELOPE02.json').read_bytes())=='28fd3602199eedeceae99208f84a8b923fbb457aef99a9c28b69cadf30842306'
prep=js(P/'RELEASE_ENVELOPE_PREPARATION02.json');proposal=js(P/'PROPOSED_MATERIALIZATION_RELEASE02.json');assert release=={**proposal,'status':'released','remaining':[]} and sorted(k for k in release if release[k]!=proposal[k])==['remaining','status']
assert not(C/prep['intended_capsule_path']).exists() and not(C/prep['intended_capsule_path']).is_symlink() and prep['execution_selected'] is False
A=release['source'];assert A=='9742c6ec817dd0917f9f35a52e4b83965ca1cd29' and git('rev-parse','HEAD').decode().strip()==A
for key in ('registration','sources','phase_contract','runtime','native_environment'):
 r=release[key];b=raw(C/r['path']);assert len(b)==r['bytes'] and h(b)==r['sha256'] and git('show',A+':'+r['path'])==b
sources=js(C/release['sources']['path'])['files'];assert len(sources)==195
names=sorted(sources);wire=git('cat-file','--batch',input=''.join(A+':'+n+'\n' for n in names).encode());off=0
for name in names:
 end=wire.index(b'\n',off);oid,kind,size=wire[off:end].split();size=int(size);b=wire[end+1:end+1+size];assert kind==b'blob' and h(b)==sources[name] and b==(C/name).read_bytes() and wire[end+1+size:end+2+size]==b'\n';off=end+2+size
assert off==len(wire)
reg=js(C/release['registration']['path']);identity='compact-cold-inputs-20261003-01';assert set(reg['experiments'])=={identity};e=reg['experiments'][identity];f=reg['families'][e['family']];assert f['attempt_budget']==2 and f['prior_attempts']==0 and reg['datasets']['synthetic-cold']['exposures']==[] and e['source_files']==sources and len(e['inputs'])==9
assert js(C/release['phase_contract']['path'])=={'schema_version':1,'identity':identity,'experiment':e,'family':f,'expected_outputs':e['outputs']}
for r in e['inputs'].values():assert h(raw(C/r['path']))==r['sha256'] and git('show',A+':'+r['path'])==(C/r['path']).read_bytes()
anchor=js(C/e['inputs']['anchor']['path']);assert len(anchor['files'])==147 and anchor['files']=={n:x for n,x in sources.items() if n.startswith('tradingagents/')};assert anchor['commit']=='fb9fad1d93836b4f92f2be8111da4adf22b7e069'
job=js(C/e['inputs']['execution_job']['path']);p=job['resources'];G=1073741824
assert p['memory_high_bytes']==p['memory_max_bytes']==3*G and p['reserve_bytes']==3*G and p['start_reserve_bytes']==6*G and p['wall_seconds']==1800 and p['disk_floor_bytes']==10*G and p['native_unit_limits']=={'file_size_bytes':4194304} and p['disk_paths']==[str(C)] and 'physical_policy' not in p
assert p['storage_budget']=={'root':str(C),'limits':{'max_allocated_bytes':G,'max_logical_bytes':G,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}
assert release['cpus']==[0,1] and job['payload']=={'cold_proof_input':'cold_proof','representation_jobs':{}} and release['prior_materialization'] is None
native=js(C/release['native_environment']['path']);runtime=js(C/release['runtime']['path']);assert len(runtime['distribution_records'])==251 and runtime['executable']==sys.executable and runtime['prefix']==sys.prefix
resources=ast.parse(raw(C/'tradingagents/research/onchain_replication/resources.py'));fn=next(n for n in resources.body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env');ns={'Path':Path};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-native-map','exec'),ns);assert native==ns['_native_owned_env'](C)
# Actual pure job._command only; no import or invocation of job launcher.
jtree=ast.parse(raw(C/'tradingagents/research/onchain_replication/job.py'));command=next(n for n in jtree.body if isinstance(n,ast.FunctionDef) and n.name=='_command');ns={'sys':sys,'Path':Path,'MODULE':'tradingagents.research.onchain_replication.job'};exec(compile(ast.Module(body=[command],type_ignores=[]),'actual-command-construction','exec'),ns)
args=SimpleNamespace(root=C,registration=release['registration']['path'],experiment=identity,source=A);commands={mode:ns['_command'](args,mode) for mode in ('launch','worker')}
for mode,c in commands.items():assert c==[sys.executable,'-B','-m','tradingagents.research.onchain_replication.job','--mode',mode,'--root',str(C),'--registration','cold-registration.json','--experiment',identity,'--source',A]
assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='guarded_run' and any(k.arg=='memory_swap_max_bytes' and isinstance(k.value,ast.Constant) and k.value.value==0 for k in n.keywords) for n in ast.walk(jtree))
# Actual release schema prefix only, stopping before source/authority imports.
rsource=raw(C/'proof_tools/proof_release01.py');rfn=next(n for n in ast.parse(rsource).body if isinstance(n,ast.FunctionDef) and n.name=='_release_context');assignment=next(n for n in rfn.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='fields');check=next(n for n in rfn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and 'proof source draft is not an exact release' in ast.unparse(n));code=compile(ast.Module(body=[assignment,check],type_ignores=[]),'actual-release-schema','exec')
checks=[]
for label,obj,wanted in [('candidate',release,True),('draft',proposal,False),('remaining',dict(release,remaining=['still pending']),False),('extra',dict(release,extra=True),False)]:
 try:exec(code,{'release':obj,'phase':'materialize','IDENTITIES':{'materialize':identity,'compare':'compact-cold-comparison-20261003-01'},'require':require})
 except ValueError:assert not wanted
 else:assert wanted
 checks.append(label)
# CLI remains relative to cwd; never execute supervisor.run or full check_release.
ss=raw(C/'proof_tools/proof_supervise01.py').decode();oo=raw(C/'proof_tools/proof_outer01.py').decode();rr=raw(C/'proof_tools/proof_raw01.py').decode()
assert "run(Path.cwd().resolve(),a.release,a.release_sha256,a.phase)" in ss and "'--release',release_path,'--release-sha256',expected_sha,'--phase',phase" in ss and "cwd=root" in ss
assert "not relative.is_absolute()" in rr and "root=Path.cwd().resolve();raw=body(root,args.release,META)" in oo
assert 'job_module=importlib.import_module' in rsource.decode() # explains why full check_release is not invoked
for ident in (identity,'compact-cold-comparison-20261003-01'):
 for base in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
  q=C/base/ident;assert not q.exists() and not q.is_symlink()
assert h(raw(BASE/'neural-cold-feature-handoff-sourceA2-recovery-review02-2026-10-03/REVIEW_RECOVERY02.md'))==prep['preparation_recovery_review']
assert not any(n.split('.')[0] in {'tradingagents','numpy','torch','pandas','pyarrow'} for n in sys.modules)
out={'status':'PASS-candidate-envelope-only-not-execution','candidate_sha256':prep['candidate_sha256'],'candidate_bytes':1159,'A2':A,'source_count':195,'anchor_count':147,'input_count':9,'runtime_pins':251,'only_changes':['remaining','status'],'actual_extracted_schema_cases':checks,'actual_extracted_job_commands':commands,'supervisor_expected_release_argument':prep['intended_capsule_path'],'intended_path_absent':True,'fresh_os_limits_observed':False,'full_release_checker_invoked':False,'qualification':'Envelope status is schema only; supplemental installed recovery, accepted wrapper, exact root request and fresh native/global identity eligibility remain.'}
(HERE/'readback02.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');(HERE/'refs02.json').write_text(json.dumps(refs,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
