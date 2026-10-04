"""One genuine metadata-only _admitted call; no Run/start/Owner/native path."""
import hashlib,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
D=Path(__file__).resolve().parent;S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');PIN='9dc5c79f738920b52947b4e63fed0397f1b5b207';ID='financial-wrapper-classification-eager-complete100-20261003-01';GATE='fixture_inputs/financial_wrapper_claimedrun01/gates.json'
assert Path.cwd()==S
pre=json.loads((D/'PRECHECK01.json').read_bytes());assert pre['source']==PIN and pre['identity']==ID and pre['actual_admission_not_yet_called']is True
class NoNumericalImports:
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0]in ('numpy','torch','scipy'):raise RuntimeError('numerical import prohibited in actual readonly admission')
sys.meta_path.insert(0,NoNumericalImports());sys.path.insert(0,str(S));begun=time.monotonic()
from tradingagents.research.onchain_replication import job
assert Path(job.__file__).resolve()==S/'tradingagents/research/onchain_replication/job.py'
a=SimpleNamespace(root=str(S),registration=GATE,experiment=ID,source=PIN)
ad,plan=job._admitted(a)
assert ad.ready is True and ad.source==ad.design_source==PIN and ad.bindings is None and ad.bindings_sha256 is None
assert ad.experiment_id==ID and len(ad.experiment['source_files'])==338 and len(ad.inputs)==8 and ad.effective_attempt_budget==19
wrapper=json.loads((S/ad.inputs[plan['payload']['plan_input']]['path']).read_bytes())
assert wrapper['phase']=='complete100'and wrapper['execution']=='eager'and wrapper['task']=='classification'and wrapper['prior_input']is None and wrapper['reference_input']is None
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
assert not (S/'research_runs'/ID).exists()and not job._base(a).exists()
modules={n:{'path':str(Path(m.__file__).resolve()),'sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}for n,m in sys.modules.items()if n.startswith('tradingagents')and getattr(m,'__file__',None)}
assert all(Path(v['path']).is_relative_to(S)for v in modules.values())
claims=list((S/'research_runs').glob('*/claim.json'));assert len(claims)==2
readback={'schema_version':1,'actual_api':'tradingagents.research.onchain_replication.job._admitted','actual_calls':1,'ready':ad.ready,'source':ad.source,'design_source':ad.design_source,'root':str(ad.root),'registration':ad.registration,'registration_sha256':ad.registration_sha256,'experiment_id':ad.experiment_id,'program_id':ad.spec['program_id'],'family':ad.family,'effective_attempt_budget':ad.effective_attempt_budget,'actual_spent_claims':len(claims),'highest_actual_prior_allowance':max(json.loads(p.read_bytes())['effective_attempt_budget']for p in claims),'inputs':ad.inputs,'source_files':ad.experiment['source_files'],'runtime_hashes':ad.experiment['runtime_hashes'],'original_job':plan,'wrapper_plan':wrapper,'imported_project_modules':modules,'numerical_imports':False,'ResearchRun_start_called':False,'Owner_constructed':False,'native_launch_called':False,'new_identity_reserved':False,'bindings':ad.bindings,'bindings_sha256':ad.bindings_sha256,'seconds':time.monotonic()-begun,'qualification':'Actual genuine readonly admission and metadata inventory only; current Torch/CUDA behavior, native capacity, new Parent/caller/recovery/release remain separate.'}
with (D/'ACTUAL_ADMISSION01.json').open('x')as f:json.dump(readback,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'ready':ad.ready,'source':ad.source,'design_source':ad.design_source,'identity':ID,'ceiling':ad.effective_attempt_budget,'spent':len(claims),'source_pins':338,'inputs':8,'numerical_imports':False,'seconds':readback['seconds']}))
