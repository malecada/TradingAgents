import hashlib,importlib,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=B/'financial-genuine-wrapper-root-claimedrun-actual-admission01-2026-10-04'
N=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');H='0a2e7639b42b9423b90743feadcda4078aa21816';ID='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
assert not os.path.lexists(D);assert hashlib.sha256((B/'financial-genuine-wrapper-claimedrun-actual-source-admission-review01-2026-10-04/MANIFEST01.json').read_bytes()).hexdigest()=='d988ad9331a829b1dfbf151d4542986099401d3bf61773962fa6a58ed8988802'
assert not any(n.startswith('tradingagents') or n in ('numpy','torch','scipy','pandas') for n in sys.modules)
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
C=B/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';m=json.loads(R.read(C,'source-manifest.json'));assert R.digest(R.encode(m))=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8';R.same(N,m)
D.mkdir(mode=0o700);(D/'ADMIT01.py').write_bytes(Path(__file__).read_bytes());start=time.monotonic();pid=os.getpid();ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]
sys.path.insert(0,str(N));job=importlib.import_module('tradingagents.research.onchain_replication.job');args=SimpleNamespace(root=str(N),registration='fixture_inputs/financial_wrapper_claimedrun01/gates.json',experiment=ID,source=H)
admitted,j=job._admitted(args)
assert admitted.ready and admitted.source==admitted.design_source==H and admitted.experiment_id==ID and admitted.effective_attempt_budget==19
assert admitted.family['attempt_budget']==18 and admitted.family['prior_attempts']==0 and len(admitted.inputs)==8 and len(admitted.experiment['source_files'])==338
origins={}
for name,module in tuple(sys.modules.items()):
 if name=='tradingagents' or name.startswith('tradingagents.'):
  p=Path(module.__file__).resolve();assert p.is_relative_to(N);relative=p.relative_to(N).as_posix();h=R.digest(R.read(N,relative));assert h==admitted.experiment['source_files'][relative];origins[name]={'path':relative,'sha256':h}
assert not any(n in sys.modules for n in ('numpy','torch','scipy','pandas'))
from tradingagents.research.admission import claims
history=claims(N);assert len(history)==1 and history[0]['experiment_id']=='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01' and not os.path.lexists(N/'research_runs'/ID)
command=job._command(args,'launch');assert command[:5]==[sys.executable,'-B','-m','tradingagents.research.onchain_replication.job','--mode']
R.same(N,m)
R.put(D/'ACTUAL_ADMISSION01.json',{'status':'ACTUAL_GENUINE_READ_ONLY_METADATA_ADMISSION_READY_NOT_NUMERICAL_RELEASE','source_root':str(N),'source':admitted.source,'design_source':admitted.design_source,'experiment_id':admitted.experiment_id,'registration':admitted.registration,'registration_sha256':admitted.registration_sha256,'ready':admitted.ready,'actual_effective_metadata_budget':admitted.effective_attempt_budget,'base_budget':admitted.family['attempt_budget'],'prior_attempts':admitted.family['prior_attempts'],'actual_global_spent_claims':1,'highest_actual_claim_budget':18,'new_claim_namespace_absent':True,'source_pins':338,'input_roles':8,'inputs':admitted.inputs,'actual_imported_source_origins':origins,'numerical_imports_present':False,'genuine_job_command':command,'binding':None,'research_run':None,'owner':None,'new_claim':None,'new_native':False,'complete_source_manifest_sha256':R.digest(R.encode(m)),'source_whole_tree_unchanged_after':True,'observed_pid':pid,'observed_start_ticks':ticks,'elapsed_seconds':time.monotonic()-start,'scope':'Root actual original job._admitted/Admission result under pinned installed runtime after independent exact Source/gate/cumulative review; read-only source/input/metadata/runtime checks. Cumulative19 is effective in the prospective metadata Admission, not yet adopted by an actual claim. No ResearchRun.start, Binding, Owner, empirical inputs, numerical import, fitting or numerical release.'})
print(json.dumps({'ready':admitted.ready,'effective_metadata_budget':admitted.effective_attempt_budget,'actual_claims':1,'highest_actual_claim_budget':18,'pid':pid,'new_native':False}))
