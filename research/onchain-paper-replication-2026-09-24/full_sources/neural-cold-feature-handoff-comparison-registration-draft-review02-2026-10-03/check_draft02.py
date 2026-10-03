"""Original closed authentication + pure draft reconstruction; no admission/start."""
import ast,hashlib,importlib.abc,importlib.util,json,os,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];C=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');A=F/'neural-cold-feature-handoff-root-compare-request02-2026-10-03';G=F/'neural-cold-feature-handoff-engineering-registration-preparation04-2026-10-03/generate04.py';HEAD='9742c6ec817dd0917f9f35a52e4b83965ca1cd29';sha=lambda b:hashlib.sha256(b).hexdigest()
assert pathlib.Path.cwd()==C
os.environ.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='protocol.allow',GIT_CONFIG_VALUE_0='never')
def git(*args):return subprocess.check_output(['git',*args],cwd=C,timeout=10)
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert not (C/'.git/objects/info/alternates').exists()
assert git('diff','--name-only')==b'' and git('diff','--cached','--name-only')==b''
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'}:raise RuntimeError('review numerical import forbidden')
sys.meta_path.insert(0,Block())
assert sha(G.read_bytes())=='be286f6b9cfcbeec1f228c0c75d80663f9aa3ed02d7319e0e8ecbdd2088f06b5'
s=importlib.util.spec_from_file_location('review_generator04',G);gen=importlib.util.module_from_spec(s);s.loader.exec_module(gen)
raw=(A/'DRAFT_REQUEST02.json').read_bytes();assert sha(raw)=='85c754a5a1492fde229af222fd2df259f282091b742b24dbb0610b23443d724a';q=json.loads(raw);assert raw==(C/'cold_prep/compare-request02.json').read_bytes();assert q['source']==HEAD and q['phase']=='compare'
sources=gen.source_closure(C,HEAD,q['inventory']);api=gen.load_release(C,sources)
retained=api.authenticated_materialization(C,q['accepted'],q['wait'])
assert retained['context']['sources']==sources and len(sources)==195
assert len([p for p in sources if p.startswith('tradingagents/')])==147
assert len(retained['material']['inputs'])==43
charter=(C/q['charter_template']['path']).read_bytes();assert sha(charter)==q['charter_template']['sha256']
constructed=gen.compare_documents(retained,q['paths'],q['accepted'],q['wait'],charter)
api._registration_evolution(retained['registration'],constructed['registration'],constructed['experiment'],retained['material'])
files=constructed['files'];assert len(files)==4
for name,b in files.items():
 assert (C/name).read_bytes()==b
 assert subprocess.run(['git','cat-file','-e',HEAD+':'+name],cwd=C,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10).returncode!=0
assert sorted(files)==sorted(q['paths'].values())
assert (C/'cold_prep/comparison-gate-template02.json').read_bytes()==gen.canonical(constructed['gate_template'])+b'\n'
new=constructed['registration'];old=retained['registration'];first='compact-cold-inputs-20261003-01';second='compact-cold-comparison-20261003-01';exp=new['experiments'][second]
restored=json.loads(json.dumps(new));del restored['experiments'][second];assert restored==old
assert new['families']==old['families'] and len(new['families'])==1
family=next(iter(new['families'].values()));assert family['attempt_budget']==2 and family['prior_attempts']==0
assert exp['parent']==first and len(exp['inputs'])==44 and exp['source_files']==old['experiments'][first]['source_files']==sources
expected={('execution_job' if k=='future_execution_job' else k):v for k,v in retained['material']['inputs'].items()}|{'environment':old['experiments'][first]['inputs']['environment']};assert exp['inputs']==expected
# Complete raw body hashes only; scientific arrays are neither decoded nor read
# as values. Original genuine verifier has already authenticated their byte pins.
for k,v in exp['inputs'].items():assert sha((C/v['path']).read_bytes())==v['sha256']
evo=json.loads(files[q['paths']['evolution']]);assert len(evo['additions'])==3
assert [r['path'] for r in evo['additions']]==sorted(set(files)-{q['paths']['evolution']});assert 'source' not in evo and evo['parent_source']==HEAD
assert q['paths']['evolution'] not in {r['path'] for r in evo['additions']}
gate=constructed['gate_template'];assert gate['source'] is None and gate['status']=='draft' and gate['execution_authorized'] is False
for k in ['sources','runtime','native_environment','cpus']:assert gate[k]==retained['context']['release'][k]
assert gate['registration']['path']==q['paths']['registration'] and gate['phase_contract']['path']==q['paths']['phase_contract']
assert gate['prior_materialization']['accepted']==q['accepted'] and gate['prior_materialization']['wait']==q['wait']
assert len(retained['context']['runtime']['distribution_records'])==251 and gate['cpus']==[0,1]
claims=list((C/'research_runs').iterdir());assert len(claims)==1 and claims[0].name==first and (claims[0]/'complete.json').is_file() and not (claims[0]/'failed.json').exists()
absence=[]
for ns in ['research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs']:
 p=C/ns/second;assert not os.path.lexists(p);absence.append(str(p))
globalroot=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/compact-cold-root-launches-20261003');assert not os.path.lexists(globalroot/second);absence.append(str(globalroot/second))
assert git('rev-parse','HEAD').decode().strip()==HEAD and git('diff','--cached','--name-only')==b'' and git('diff','--name-only')==b''
assert not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'} for n in sys.modules)
summary={'schema_version':1,'status':'prospective-four-file-draft-reconstructed-from-actual-closed-authority','parent_source':HEAD,'genuine_materialization_status':retained['observed']['status'],'sources':195,'package_anchor':147,'runtime_records':251,'prior_inputs':43,'comparison_inputs':44,'closed_complete_claims':1,'family':family,'draft_files':[{'path':n,'bytes':len(b),'sha256':sha(b)} for n,b in sorted(files.items())],'three_evolution_rows_plus_own_fourth':True,'inverse_original_registration_exact':True,'gate_draft_source_null':True,'fixed_comparison_absences':absence,'no_claim_start_admission_or_numerical_import':True,'scientific_capacity_or_comparison_result':False}
(P/'READBACK02.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
