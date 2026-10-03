"""Read-only finite original JSON/source binding census; no execution modules."""
import hashlib,json,os,pathlib,stat,subprocess
P=pathlib.Path(__file__).parent;BASE=P.parent;ROOT=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');A='9742c6ec817dd0917f9f35a52e4b83965ca1cd29';FIRST='compact-cold-inputs-20261003-01';SECOND='compact-cold-comparison-20261003-01'
def raw(path):
 assert path.resolve()==path and not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in path.parts)
 s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304
 b=path.read_bytes();assert path.lstat()==s and len(b)==s.st_size;return b
def ref(name,kind='document'):
 b=raw(ROOT/name);return {'path':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'kind':kind}
def doc(name):return json.loads(raw(ROOT/name))
def bound(r):
 b=raw(ROOT/r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256'];assert 'bytes' not in r or len(b)==r['bytes'];return json.loads(b)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1'},timeout=15)
assert git('rev-parse','HEAD').decode().strip()==A
release_path='cold_release/materialize02/released-envelope02.json';release=doc(release_path);assert release['source']==A
accepted_ref=ref('proof_outer/'+FIRST+'/accepted.json','metadata');wait_ref=ref('proof_supervise/'+FIRST+'/exit.json','metadata');accepted=bound(accepted_ref);wait=bound(wait_ref)
assert accepted['release']==wait['release']==ref(release_path,'metadata');assert accepted['status']==wait['status']=='accepted' and wait['controller_exit_code']==0
observed=bound(accepted['authentication']);material=bound(observed['proof']['future_inputs']);registration=bound(release['registration']);first=registration['experiments'][FIRST];family=registration['families'][first['family']]
assert set(registration['experiments'])=={FIRST} and family['attempt_budget']==2 and family['prior_attempts']==0
claimref=ref('research_runs/'+FIRST+'/claim.json');terminalref=ref('research_runs/'+FIRST+'/complete.json');claim=bound(claimref);terminal=bound(terminalref)
assert terminal['status']=='complete' and terminal['claim_sha256']==claimref['sha256'] and terminal['source']==claim['source']==A and claim['experiment']==first
roles={}
for name,r in sorted(material['inputs'].items()):
 assert r['path'].endswith('.json');b=raw(ROOT/r['path']);assert hashlib.sha256(b).hexdigest()==r['sha256'];roles['execution_job' if name=='future_execution_job' else name]=r
assert len(roles)==43 and 'environment' not in roles;roles['environment']=first['inputs']['environment'];bound(roles['environment']);assert len(roles)==44
sources=bound(release['sources'])['files'];assert len(sources)==195 and sum(x.startswith('tradingagents/') for x in sources)==147
for path,h in sources.items():assert hashlib.sha256(raw(ROOT/path)).hexdigest()==h
charter=ref('cold_prep/CHARTER_COMPARE02.md');assert git('show',A+':'+charter['path'])==raw(ROOT/charter['path'])
paths={'registration':'cold-comparison-registration02.json','charter':'cold_prep/CHARTER_COMPARE_REGISTERED02.md','phase_contract':'cold_prep/compare-phase-contract02.json','evolution':'cold_prep/compare-evolution02.json'}
assert len(set(paths.values()))==4 and all(not os.path.lexists(ROOT/p) and (ROOT/p).parent.is_dir() for p in paths.values())
ns=('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs');absence={n:not os.path.lexists(ROOT/n/SECOND) for n in ns};assert all(absence.values())
assert git('rev-parse','HEAD').decode().strip()==A
result={'schema_version':1,'scope':'bounded read-only metadata/source census; not a rerun of full authentication or a draft registration','root':str(ROOT),'observed_source_A2':A,'B2':None,'original_release':ref(release_path,'metadata'),'original_registration':release['registration'],'original_sources':release['sources'],'original_runtime':release['runtime'],'original_native_environment':release['native_environment'],'cpus':release['cpus'],'accepted':accepted_ref,'wait':wait_ref,'original_claim':claimref,'original_terminal':terminalref,'future_inputs':observed['proof']['future_inputs'],'actual_materialized_role_count':43,'prospective_comparison_roles':roles,'prospective_comparison_role_count':44,'environment_reused_exactly':True,'source_count':195,'package_count':147,'charter_template':charter,'family':family,'family_prior_attempts':0,'family_max_attempts':2,'observed_original_claims':1,'remaining_if_no_other_claim':1,'prospective_four_paths_NOT_CREATED':paths,'comparison_namespace_absence':absence,'scientific_completion':False,'numpy_or_torch_imported':False,'opaque_components_read':False,'registration_rendered':False,'Git_write_performed':False}
(P/'bindings01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'read-only-census-passed','source_A2':A,'B2_created':False,'roles':len(roles),'metadata_paths_checked':43,'source_bodies_checked':195,'all_comparison_namespaces_absent':True}))
