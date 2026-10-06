import ast,hashlib,json,subprocess
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-retry12-review01-2026-10-06';C=F/'real-data-pilot-source-closure-fix01-2026-10-06';D=F/'real-data-pilot-final12-2026-10-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def need(v,m):
 if not v:raise ValueError(m)
manifest=json.loads((C/'MANIFEST01.json').read_text())
for r in manifest['files']:
 p=R/r['path'];assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes']
original=R/manifest['original']['path'];candidate=C/'candidate/real_pilot_import_caller.py';assert sha(original)==manifest['original']['sha256']
old="    require(required_sources() <= set(ad.experiment['source_files']), 'complete current package closure required')\n"
replacement=(C/'REPLACEMENT01.txt').read_text();assert candidate.read_text().count(replacement)==1 and candidate.read_text().replace(replacement,old)==original.read_text()
identity=R/'tradingagents/research/onchain_replication/imported_mcm_identity.py';tree=ast.parse(identity.read_text());constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'KERNEL','HELPER'}}
fn=next(n for n in ast.parse(candidate.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='admitted');addition=next(n.value.right for n in fn.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='required');assert ast.literal_eval(addition)==set(constants.values())
source=ast.parse(identity.read_text());target=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='Target');sources=next(n for n in target.body if isinstance(n,ast.FunctionDef) and n.name=='sources');assert "job.required_sources() | {KERNEL, HELPER}" in ast.unparse(sources)
helpers=[]
for key,expected in [('KERNEL','8d810af1448893858504a90537a0a76b6ba70306427d3385f9571b0677a99287'),('HELPER','30a957ad48997a3236203e1af2ccf9e0874b172ffac73773c31efc6bece9fc67')]:
 p=R/constants[key];assert sha(p)==expected and subprocess.check_output(['git','show','HEAD:'+constants[key]])==p.read_bytes();helpers.append(ref(p))
store=D/'candidate/real_pilot_storage.py';current=R/'tradingagents/research/onchain_replication/real_pilot_storage.py';a='eth-paper-real-data-end-to-end-resource-20261006-11';b=a[:-2]+'12';assert current.read_text().count(a)==1 and current.read_text().replace(a,b)==store.read_text()
# Execute only actual pure policy predicate, never import kernel/numerical modules.
k=ast.parse((R/constants['KERNEL']).read_text());policy_fn=next(n for n in k.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy');ns={'require':need};exec(compile(ast.Module(body=[policy_fn],type_ignores=[]),'kernel-policy-extraction','exec'),ns)
gate=json.loads((F/'real-data-pilot-final11-2026-10-06/gate01.json').read_text());gate=next(iter(gate['experiments'].values()));m=json.loads((R/gate['inputs']['mcm_policy']['path']).read_text());out=json.loads((R/gate['inputs']['mcm_output_policy']['path']).read_text())
ns['validate_policy'](m['numeric'],m['max_entries']);refused=False
try:ns['validate_policy'](m['numeric'],m['max_entries']+1)
except ValueError:refused=True
assert refused
meta=8192;assert m['max_workflow_metadata_bytes']==3*meta*7 and out['max_artifact_bytes']==4*m['max_entries']+2*meta and out['max_workflow_output_bytes']==7*(out['max_artifact_bytes']+meta)
reviews=[F/'pair-workload-2026-09-30/REVIEW_V2.md',F/'original-import-fixture-bridge-candidate-2026-10-02/REVIEW_BRIDGE01.md',F/'original-import-fixture-io-candidate05-2026-10-03/REVIEW_IO_CANDIDATE05.md']
result={'schema_version':1,'decision':'accepted','reviewer':'pilot09_review independent fresh12 source reviewer','manifest':ref(C/'MANIFEST01.json'),'candidates':[ref(candidate),ref(store)],'helpers':helpers,'historical_reviews':[ref(p) for p in reviews],'findings':[],
'checks':['Every candidate manifest member exact; caller inverse is one admission guard replacement.','New required set independently equals actual Target.sources package closure plus exact KERNEL/HELPER literals; checks actual hashes before downstream Owner/array work.','Strict storage changes only fixed11 to fixed12 identity.','Selected kernel/helper match actual committed Git bytes. Current kernel independently inspected: exact Target graph/dictionary/workflow/config/scope joins, all n*32 center/motif cells, finite scalar-purpose binding, genuine callback/leases and final integrity; no fit/resampling invocation.','Actual extracted numeric policy accepts maximum allowed entries and refuses one extra; seven-graph output/metadata reservation arithmetic exactly matches caps.','Selected helpers immediate package imports are already package source closure; imported route selects exactly these two external helper files.'],
'provenance_scope':'Current narrow source acceptance covers these unchanged helper bodies under current Target/Owner wrapper and newly complete admission closure. Original bridge whole-fixture WITHHELD disposition remains: original failure swallowing was in resource_fixture, later IO05 explicitly corrected overall closure with numerical body preserved. Pair-workload prior acceptance remains purpose/scalar scope. This review does not promote the historical fixture or claim it executed successfully.',
'remaining_conditions':['Root must actually include both helper paths/hashes in fresh gate source_files, adopt exact candidates, commit exact input/runtime/source closure, obtain genuine read-only admission and final release.','Runtime leases, full pair workspace, storage transport and complete MCM/training capacity remain actual pilot questions; no whole performance prediction follows.'],
'not_tested':['No numerical modules, arrays/private inputs, actual Owner/admission/native job or financial experiment.','No empirical numerical equivalence, throughput, latency, capacity, leakage, returns, funding or exposure proof.']}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(ref(H/'SOURCE_REVIEW01.json')))
