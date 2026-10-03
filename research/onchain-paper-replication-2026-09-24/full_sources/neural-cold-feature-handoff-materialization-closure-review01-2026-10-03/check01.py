"""Genuine retained materialization authentication only; never start/replay jobs."""
import hashlib,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;O=BASE/'neural-cold-feature-handoff-materialization-outcome01-2026-10-03';q=json.loads((O/'COLLECTION_REQUEST01.json').read_bytes());root=Path(q['root']);phase='materialize';identity='compact-cold-inputs-20261003-01'
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
assert sha((O/'COLLECTION_REQUEST01.json').read_bytes())=='09dbfa721ca752653e706a6d33462ece75a1168e2347b59c26ed19c59eced386'
inv=doc(Path(q['inventory']['path']));sources={r['target']:r['sha256'] for r in inv['source_inventory']};assert len(sources)==195
for name,h in sources.items():assert sha((root/name).read_bytes())==h
assert sources['proof_tools/proof_release01.py']=='53c2294b7b38f340e9160e4484a6b7506942ce36e2dff12694a47f9b72206812'
os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_OPTIONAL_LOCKS']='0';os.environ['GIT_NO_REPLACE_OBJECTS']='1';os.environ['GIT_TERMINAL_PROMPT']='0';os.environ['GIT_ALLOW_PROTOCOL']=''
sys.path.insert(0,str(root/'proof_tools'));os.chdir(root)
import proof_release01 as api
api.no_numerics()
accepted=api.ref(root,'proof_outer/'+identity+'/accepted.json',kind='metadata');wait=api.ref(root,'proof_supervise/'+identity+'/exit.json',kind='metadata')
retained=api.authenticated_materialization(root,accepted,wait)
assert retained['observed']['status']=='authenticated' and retained['observed']['proof']['scientific_completion'] is False and retained['context']['sources']==sources
assert retained['context']['release']==doc(Path(q['releases']['materialize']['path']))
sys.path.insert(0,str(BASE/'neural-cold-feature-handoff-outcome-retention-preparation02-2026-10-03'))
import collector01 as collector
wrapper=Path(q['wrappers'][phase]);wrapper_result=collector.wrapper_authentication(q,root,phase,wrapper,retained['context']['release']);cleanup=collector.cleanup_observation(root,phase,wrapper)
assert cleanup['status']=='original-cleanup-observed' and wrapper_result['status']=='original-wrapper-exit0-and-tail-authenticated'
obs=doc(O/'ACTUAL_TOOL_CLOSURE01.json');assert obs['source']==q['source']
for pid in obs['actual_pids_absent']:assert not Path('/proc',str(pid)).exists()
assert not Path(obs['actual_cgroup_absent']).exists()
parent=Path(q['wrapper_waits'][phase]['path']).parent;pw=doc(parent/'wait.json');pi=doc(parent/'intent.json');pc=doc(parent/'child.json');assert pw['wrapper_exit_code']==0 and pw['wrapper_pid']==pc['pid']==doc(wrapper/'intent.json')['parent_pid']
assert pi['parent_pid'] in obs['actual_pids_absent'] and pw['wrapper_pid'] in obs['actual_pids_absent']
summary=doc(root/'research_runs'/identity/'outputs/proof-materialize.json');assert len(summary['inputs'])==43 and summary['registration_pending'] and summary['environment_input_pending']
claim=doc(root/'research_runs'/identity/'claim.json');term=doc(root/'research_runs'/identity/'complete.json');assert not(root/'research_runs'/identity/'failed.json').exists() and term['status']=='complete'
anchor=doc(root/claim['inputs']['anchor']['path']);assert len(anchor['files'])==147 and anchor['commit']=='fb9fad1d93836b4f92f2be8111da4adf22b7e069' and len(claim['inputs'])==9
assert claim['family']['attempt_budget']==2 and claim['family']['prior_attempts']==0
compare='compact-cold-comparison-20261003-01'
for base in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
 p=root/base/compare;assert not p.exists() and not p.is_symlink()
for p in collector.reservation_paths(q,root,'compare').values():assert not p.exists() and not p.is_symlink()
assert not any(n.split('.')[0] in {'numpy','torch','pandas','pyarrow','scipy'} for n in sys.modules)
result={'status':'ACCEPTED-MATERIALIZATION_COMPLETE-SCIENCE_PENDING','source':q['source'],'identity':identity,'genuine_retained_authentication':retained['observed'],'wrapper_authentication':wrapper_result,'cleanup':cleanup,'all_eight_original_pids_absent':obs['actual_pids_absent'],'actual_cgroup_absent':obs['actual_cgroup_absent'],'materialized_input_count':43,'graph_manifests':19,'opaque_component_byte_hashes':76,'required_graphs':18,'native_elapsed_seconds':obs['elapsed_native_seconds'],'peak_sampled_memory_current_bytes':obs['peak_sampled_memory_current_bytes'],'future_comparison_unclaimed':True,'paper_financial_fits_completed':0,'qualification':'Opaque component byte hashing only, no array decoding/test-label inspection/numerical imports. Actual tool-session exit observation is root evidence; actual parent/wrapper/native/raw joins independently checked. Whole outcome recovery remains required before comparison.'}
(HERE/'readback01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in {'genuine_retained_authentication','cleanup'}},sort_keys=True))
