import ast,hashlib,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry14-review01-2026-10-06';W=F/'real-data-pilot-loaded-roster-fix01-2026-10-06';D=F/'real-data-pilot-fixed14-metadata-successor01-2026-10-06';O=F/'real-data-pilot-fixed13-metadata-successor01-2026-10-06';L=F/'real-data-pilot-final14-2026-10-06';P=F/'real-data-pilot-final13-2026-10-06'
def ld(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
a='eth-paper-real-data-end-to-end-resource-20261006-13';b=a[:-2]+'14';storage=R/'tradingagents/research/onchain_replication/real_pilot_storage.py'
assert storage.read_text().count(a)==1 and storage.read_text().replace(a,b)==(D/'candidate/real_pilot_storage.py').read_text()
for name in ['build_inputs03.py','controls01.py']:
 old=(O/'candidate'/name).read_text();assert old.count(a)==1 and old.replace(a,b)==(D/'candidate'/name).read_text()
assert (D/'successor02.py').read_bytes()==(O/'successor02.py').read_bytes()
newdeps=ld(D/'DEPENDENCIES02.json');olddeps=ld(O/'DEPENDENCIES02.json');assert set(newdeps)==set(olddeps)
for key,reference in newdeps.items():
 assert ref(R/reference['path'])['sha256']==reference['sha256']
 if key not in {'builder','controls'}:assert reference==olddeps[key]
expected=(P/'preflight02.py').read_text().replace(a,b).replace('real-data-pilot-fixed13-metadata-successor01','real-data-pilot-fixed14-metadata-successor01').replace("HERE/'gate02.json'","HERE/'gate01.json'").replace('!=84','!=85').replace("'effective_attempt_budget':84","'effective_attempt_budget':85")
assert (L/'preflight01.py').read_text()==expected
assert (L/'root_io.py').read_text()==(P/'root_io02.py').read_text().replace(a,b).replace('from preflight02 import','from preflight01 import')
original=R/'tradingagents/research/onchain_replication/real_pilot_import_caller.py';candidate=W/'candidate04/real_pilot_import_caller.py'
old=original.read_text();new=candidate.read_text();tree=ast.parse(new);helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_prepare_lease_modules')
lines=new.splitlines(keepends=True); del lines[helper.lineno-1:helper.end_lineno];inverse=''.join(lines).replace('            _prepare_lease_modules()\n','',1)
assert ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
# Exact textual inverse includes just the authored helper and one call (blank separation too).
assert new.replace('\n\n'+''.join(new.splitlines(keepends=True)[helper.lineno-1:helper.end_lineno]),'',1).replace('            _prepare_lease_modules()\n','',1)==old
assert all(isinstance(n,ast.ImportFrom) and n.level==1 and n.module is None for n in helper.body[1:])
mods={a.name for n in helper.body[1:] for a in n.names};assert mods=={'chunk_durability','array_neighborhoods','held_score_consumer','stage_retention','stage_retention_reader','archive_owner_writer','mcm_raw_parts','typed_score_store','typed_tail_binding','typed_payload_operations','archive_consume','archive_owner_seal','evaluation','checkpoints','streamed_gat','feature_residency'}
assert new.count('_prepare_lease_modules()')==2 and '            _prepare_lease_modules()\n            activate(execution' in new
G=ld(P/'gate02.json');E=next(iter(G['experiments'].values()))
unchanged=['imported_authority_lease','imported_authority_interval','compact_mcm','real_pilot_training','model','training','imported_mcm_identity']
for name in unchanged:
 p=R/('tradingagents/research/onchain_replication/'+name+'.py');assert ref(p)['sha256']==E['source_files'][str(p.relative_to(R))]
policy=ld(R/E['inputs']['imported_authority_lease']['path']);assert policy['max_stale_ms']==60000
cp=ld(R/E['inputs']['compact_policy']['path']);assert 'restart_retention' in cp['stage_policy']
job=ld(R/E['inputs']['execution_job']['path']);selected=next(iter(job['payload']['representation_jobs'].values()));assert 'held_score_consumer_input' not in selected
assert 'from .feature_residency import FixedFeatureMap' in (R/'tradingagents/research/onchain_replication/evaluation.py').read_text()
probe=ld(W/'PROBE_RESULT04.json');v=json.loads(probe['stdout']);assert probe['exit']==0 and probe['killed_reason'] is None and v['status']=='passed' and v['baseline_modules']==118 and v['red_added']==['tradingagents.research.onchain_replication.chunk_durability'] and all(v[k] for k in ['green_future_kernel_import_equal','function_mutation_refused','code_mutation_refused','source_hash_mutation_refused'])
refs=[ref(p) for p in [candidate,W/'INVERSE04.patch',W/'probe04.py',W/'run_probe04.py',W/'PROBE_RESULT04.json',D/'candidate/real_pilot_storage.py',D/'successor02.py',D/'DEPENDENCIES02.json',L/'preflight01.py',L/'root_io.py']]
o={'schema_version':1,'decision':'accepted','reviewer':'pilot14_review independent changed-source reviewer','candidates':[ref(candidate),ref(D/'candidate/real_pilot_storage.py')],'references':refs,'findings':[],'resolved_pre_adoption_findings':['Actual plain-dict training batch imports feature_residency unconditionally; candidate04 prepares it before baseline.','Nested compact_policy.stage_policy.restart_retention selects stage_retention_reader; candidate04 prepares it before baseline.'],'checks':['Exact textual/AST inverse removes only import helper and call before activate. Sixteen explicit module imports only; no postactivation baseline adoption or authority renewal.','Actual unchanged Lease._loaded/_authenticate_loaded/_finger and Interval sources retain source authentication, immutable module/function/code equality, timing and object checks; 60s policy unchanged.','Actual source bounded RED/GREEN probe authenticates118 loaded admitted modules and preserves function/code/source mutation refusals; sampled import-only RSS737468416B,3.972558333s. Evidence is reviewed, not represented as a full native run.','Selected lazy imports inspected through compact preparation/kernel, matching engine, archive/typed payload and retention, raw output, actual plain-dict batch, streamed GAT and checkpoint path. Dynamic kernel/workload does not register sys.modules; their source checks remain unchanged. Held dynamic API aliases and observation-only training_batch_observer are unselected.','Storage/builder/controls fixed13→14 only; successor bytes and six dependency refs unchanged. RootIO/preflight exact identity/gate/budget85 inverses.'], 'qualification':'Accept candidate04 narrowly for preactivation module preparation. Historical13 exact changed roster entry remains unrecorded; deterministic chunk_durability late-import reproduction does not establish that exact historical entry. Metadata/live adoption/committed admission/release still required.','not_tested':['No real graphs, original raw data, Owner, claim, native run, model fit or private input inspected or executed.','No full throughput, peak native memory, capacity, end-to-end success or numerical agreement proven. Financial return/cashflow, fees/funding, exposure and timing leakage are outside this source scheduling change.']}
p=H/'SOURCE_REVIEW01.json';p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(ref(p)))
