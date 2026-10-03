"""Read-only genuine comparison release check; no admission/start/numerics."""
import ast,hashlib,importlib.abc,importlib.util,json,os,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;F=P.parent;C=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');A=F/'neural-cold-feature-handoff-root-compare-request02-2026-10-03';B='361339125a3f1cd57e7ba8611f5a994ae649fa0b';OLD='9742c6ec817dd0917f9f35a52e4b83965ca1cd29';sha=lambda b:hashlib.sha256(b).hexdigest();assert pathlib.Path.cwd()==C
os.environ.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='protocol.allow',GIT_CONFIG_VALUE_0='never')
def git(*args):return subprocess.check_output(['git',*args],cwd=C,timeout=10)
assert git('rev-list','--parents','-n','1','HEAD').decode().strip().split()==[B,OLD]
assert not (C/'.git/objects/info/alternates').exists() and git('diff','--name-only')==b'' and git('diff','--cached','--name-only')==b''
source=json.loads((A/'SOURCE_B2.json').read_bytes());assert source['source_B2']==B and source['sole_parent_A2']==OLD
parts=git('diff-tree','--no-commit-id','--name-status','-r','-z',OLD,B).decode().split('\0');assert parts[-1]=='';changes=list(zip(parts[:-1:2],parts[1:-1:2]));assert len(changes)==4 and all(s=='A' for s,n in changes);assert {n for s,n in changes}=={r['capsule_path'] for r in source['actual_additions']}
for row in source['actual_additions']:
 raw=(C/row['capsule_path']).read_bytes();assert raw==git('show',B+':'+row['capsule_path']);assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'}:raise RuntimeError('no numerical imports in review')
sys.meta_path.insert(0,Block())
inv=json.loads((C/'cold_prep/source_inventory.json').read_bytes());assert len(inv['source_inventory'])==195 and inv['package_count']==147
for r in inv['source_inventory']:
 raw=(C/r['target']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)==r['bytes'];assert git('show',B+':'+r['target'])==git('show',OLD+':'+r['target'])==raw
anchor=json.loads((C/'cold_prep/anchor.json').read_bytes());assert len(anchor['files'])==147
for n,h in anchor['files'].items():assert sha((C/n).read_bytes())==h and git('show',anchor['commit']+':'+n)==(C/n).read_bytes()
sys.path.insert(0,str(C/'proof_tools'));import proof_release01 as api
raw=(A/'CANDIDATE_RELEASE_ENVELOPE02.json').read_bytes();assert len(raw)==1692 and sha(raw)=='407642fc43b41b40dc918e40ce81d375fcc0067d2af7d99c44beb42548f64011';release=json.loads(raw)
gate=json.loads((C/'cold_prep/comparison-gate-template02.json').read_bytes());expected={**gate,'kind':'cold-proof-outer-release-v1','status':'released','source':B,'remaining':[]};del expected['execution_authorized'];assert expected==release
ctx=api.check_release(C,release,'compare')
checker=api.module('review_runtime',C/'proof_tools/runtime_gate01.py',ctx['sources']['proof_tools/runtime_gate01.py']);runtime=checker.check(C,ctx['runtime']);assert len(ctx['runtime']['distribution_records'])==251
# Actual source-defined environment mapping is pure and does not touch runtime.
tree=ast.parse((C/'tradingagents/research/onchain_replication/resources.py').read_bytes());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_native_owned_env');ns={'Path':pathlib.Path};exec(compile(ast.Module(body=[fn],type_ignores=[]),'source-native-env','exec'),ns);assert ns['_native_owned_env'](C)==ctx['environment']
assert ctx['release']['cpus']==[0,1] and len(ctx['experiment']['inputs'])==44 and ctx['family']['attempt_budget']==2 and ctx['family']['prior_attempts']==0
for n,r in ctx['experiment']['inputs'].items():assert sha((C/r['path']).read_bytes())==r['sha256']
readback=json.loads((F/'neural-cold-feature-handoff-materialization-closure-review01-2026-10-03/PROCESS_NATIVE_READBACK01.json').read_bytes());pids=readback['all_observed_pids'];assert len(pids)==11 and all(not pathlib.Path('/proc',str(pid)).exists() for pid in pids);assert not pathlib.Path(readback['cgroup']).exists();assert sha(pathlib.Path(readback['guard_reference']['path']).read_bytes())==readback['guard_reference']['sha256']
second='compact-cold-comparison-20261003-01';absences=[C/ns/second for ns in ['research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs']]+[pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/compact-cold-root-launches-20261003')/second,A/'actual-parent-wait01'];assert all(not os.path.lexists(p) for p in absences)
assert git('rev-parse','HEAD').decode().strip()==B and git('diff','--name-only')==b'' and git('diff','--cached','--name-only')==b''
assert not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'} for n in sys.modules)
result={'schema_version':1,'status':'actual-B2-and-external-candidate-release-read-only-verified','source_B2':B,'sole_parent_A2':OLD,'source_record_sha256':sha((A/'SOURCE_B2.json').read_bytes()),'candidate_sha256':sha(raw),'candidate_bytes':len(raw),'actual_four_additions':changes,'source_files':195,'anchor_files':147,'runtime_distribution_records':251,'runtime_module_origins':len(runtime['module_origins']),'inputs':44,'family':ctx['family'],'native_environment_sha256':release['native_environment']['sha256'],'cpus':release['cpus'],'resources':ctx['job']['resources'],'all11_original_pid_tid_absent':pids,'original_cgroup_absent':readback['cgroup'],'comparison_unreserved_paths':[str(p) for p in absences],'launch_command':ctx['launch_command'],'worker_command':ctx['worker_command'],'no_admission_start_numerical_import_or_job':True,'candidate_installed_or_selected_by_review':False}
(P/'READBACK02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
