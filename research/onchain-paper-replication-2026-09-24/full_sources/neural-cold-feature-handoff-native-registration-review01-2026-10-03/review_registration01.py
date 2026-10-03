"""Actual SCI prospective metadata/Git/runtime review. No admission or numerical APIs."""
import ast,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';I=BASE/'neural-cold-feature-handoff-root-integration01-2026-10-03';CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-01/source');A='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e';T='a40f36541037e6d5d44317bf692705578477f4f2';S='c65287a2c70fdc38fd6335a994dfd29fe97e26b4';ID='compact-cold-inputs-20261003-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def doc(p):return json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=CAP,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=20)
def module(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def batch(commit,files):
 names=sorted(files);wire=subprocess.check_output(['git','cat-file','--batch'],cwd=CAP,input=''.join(commit+':'+n+'\n' for n in names).encode(),env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=20);off=0
 for n in names:
  end=wire.index(b'\n',off);h=wire[off:end].split();assert len(h)==3 and h[1]==b'blob';size=int(h[2]);assert size<=4194304;off=end+1;raw=wire[off:off+size];assert hashlib.sha256(raw).hexdigest()==files[n]==sha(CAP/n);off+=size;assert wire[off:off+1]==b'\n';off+=1
 assert off==len(wire)
def main():
 release=doc(I/'PROPOSED_MATERIALIZATION_RELEASE01.json');observed=doc(I/'REGISTRATION_SOURCE_A01.json');assert sha(I/'PROPOSED_MATERIALIZATION_RELEASE01.json')==observed['proposed_release_sha256'];assert release['source']==A and release['status']=='draft' and release['remaining'] and release['prior_materialization'] is None
 assert git('rev-parse','HEAD').decode().strip()==A and git('rev-list','--parents','-n','1',A).decode().split()==[A,T];git('merge-base','--is-ancestor',S,T);assert not(CAP/'.git/objects/info/alternates').exists() and not(CAP/'.venv').exists() and not(CAP/'.venv').is_symlink()
 additions={}
 for parent,child,count in ((S,T,16),(T,A,6)):
  parts=git('diff-tree','--no-commit-id','--name-status','-r','-z',parent,child).decode().split('\0');pairs=list(zip(parts[:-1:2],parts[1:-1:2]));assert len(pairs)==count and all(kind=='A' for kind,name in pairs);additions[child]=[name for kind,name in pairs]
 for k in ('registration','sources','phase_contract','runtime','native_environment'):
  r=release[k];assert sha(CAP/r['path'])==r['sha256'] and (CAP/r['path']).stat().st_size==r['bytes'];assert git('show',A+':'+r['path'])==(CAP/r['path']).read_bytes()
 sources=doc(CAP/release['sources']['path'])['files'];assert len(sources)==195;batch(A,sources)
 inv=doc(CAP/'cold_prep/source_inventory.json');assert sha(CAP/'cold_prep/source_inventory.json')=='8576e2baba60576818ee4def16fcfad32cc69bd197c4ff1b727808d9695786d2';assert sources=={r['target']:r['sha256'] for r in inv['source_inventory']}
 registration=doc(CAP/release['registration']['path']);assert registration['program_id']=='compact-cold-engineering-20261003' and set(registration['experiments'])=={ID};family=registration['families']['compact-cold-genuine-authority'];assert family=={'attempt_budget':2,'prior_attempts':0,'mechanism_id':'compact-cold-genuine-authority','history_reference':'cold_prep/HISTORY02.md'};assert registration['datasets']=={'synthetic-cold':{'exposures':[],'history_reference':'cold_prep/HISTORY02.md','identity':'compact-cold-synthetic-20261003'}}
 e=registration['experiments'][ID];assert e['source_files']==sources and e['parent'] is None and e['cells']==['cold-input-materialization'] and e['outputs']==['proof-materialize.json'];assert len(e['inputs'])==9
 contract=doc(CAP/release['phase_contract']['path']);assert contract=={'schema_version':1,'identity':ID,'experiment':e,'family':family,'expected_outputs':e['outputs']}
 for name,r in e['inputs'].items():assert r['dataset']=='synthetic-cold' and sha(CAP/r['path'])==r['sha256'];assert git('show',A+':'+r['path'])==(CAP/r['path']).read_bytes()
 genpath=BASE/'neural-cold-feature-handoff-engineering-registration-preparation03-2026-10-03/generate03.py';assert sha(genpath)=='25c8f091f36168aacffa36ae9ea8a0b1e0e1ac8b1e38adddef651ebcea5a8ba6';gen=module(genpath,'actual_reviewed_generator03')
 for filename in ('CHARTER_MATERIALIZE02.md','CHARTER_COMPARE02.md','HISTORY02.md'):assert (CAP/'cold_prep'/filename).read_bytes()==(genpath.parent/filename).read_bytes()
 assert sha(CAP/e['charter']['path'])==e['charter']['sha256'];anchor=doc(CAP/e['inputs']['anchor']['path']);assert anchor['commit']==S
 jobfile=CAP/'tradingagents/research/onchain_replication/job.py';fn=next(n for n in ast.parse(jobfile.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');ns={'Path':Path,'__file__':str(jobfile)};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual required sources','exec'),ns);assert set(anchor['files'])==ns['required_sources']() and len(anchor['files'])==147;batch(S,anchor['files'])
 job=doc(CAP/e['inputs']['execution_job']['path']);gen.resources(CAP,job['resources']);assert job['resources']==doc(CAP/e['inputs']['future_resources']['path']) and job['environment_input']=='environment' and job['payload']=={'cold_proof_input':'cold_proof','representation_jobs':{}}
 policy=doc(CAP/e['inputs']['cold_proof']['path']);assert policy['source_files']==sources and policy['phase']=='materialize' and policy['experiment']==ID and policy['watch']==job['resources']['storage_budget'];assert policy['max_file_bytes']==4194304 and policy['max_total_bytes']==268435456
 for role,h in gen.CONFIG_PINS.items():assert gen.digest(gen.canonical(doc(CAP/e['inputs'][role]['path'])))==h
 native=gen.native_environment(CAP,{'native_environment':{k:release['native_environment'][k] for k in ('path','sha256')}},sources);software=doc(CAP/e['inputs']['environment']['path']);assert set(native).isdisjoint(software) and release['cpus']==[0,1]
 runtime=doc(CAP/release['runtime']['path']);assert len(runtime['distribution_records'])==len({r['name'] for r in runtime['distribution_records']})==251
 checker=module(CAP/'proof_tools/runtime_gate01.py','actual_runtime_review01');old=Path.cwd();os.chdir(CAP)
 try:runtime_result=checker.check(CAP,runtime)
 finally:os.chdir(old)
 for identity in (ID,'compact-cold-comparison-20261003-01'):
  for prefix in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
   p=CAP/prefix/identity;assert not p.exists() and not p.is_symlink()
 assert not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow','tradingagents'} for n in sys.modules)
 return {'observed_utc':datetime.now(timezone.utc).isoformat(),'status':'accepted-prospective-local-registration-preparation-only','source_A':A,'source_T':T,'anchor_S':S,'added_metadata':additions,'source_count':195,'anchor_file_count':147,'registered_inputs':9,'runtime_records':251,'runtime_qualification':runtime_result['runtime_record_qualification'],'release_status':'draft','registered_identities':[ID],'both_fixed_identities_unclaimed':True,'numerical_imports':False,'fresh_native_limits_observed':False,'external_recovery_verified_by_this_review':False}
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
