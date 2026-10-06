import ast, hashlib, importlib, importlib.util, json, resource, sys
from pathlib import Path
ROOT=Path.cwd(); OUT=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-loaded-roster-fix01-2026-10-06'
PKG='tradingagents.research.onchain_replication'
source=ROOT/'tradingagents/research/onchain_replication/real_pilot_import_caller.py'
gate=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final13-2026-10-06/gate02.json').read_text())
sources=next(iter(gate['experiments'].values()))['source_files']
from tradingagents.research.onchain_replication import imported_authority_lease as lease
ns={'__package__':PKG}
tree=ast.parse(source.read_text()); execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
activation=next(n.lineno for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='activate')
imports=sorted([n for n in ast.walk(execute) if isinstance(n,(ast.Import,ast.ImportFrom)) and n.lineno<activation],key=lambda n:n.lineno)
for n in imports:exec(compile(ast.Module(body=[n],type_ignores=[]),str(source),'exec'),ns)
before=lease._loaded(ROOT,sources)
# Actual first newly deferred statement from compact_mcm._prepare.
importlib.import_module(PKG+'.chunk_durability')
after=lease._loaded(ROOT,sources)
assert after!=before
red_added=sorted(set(after)-set(before))
try:lease.require(after==before,'loaded module/function identity changed')
except ValueError as e:red=str(e)
else:raise AssertionError('original late import unexpectedly accepted')
candidate=OUT/'candidate04/real_pilot_import_caller.py'
helper=next(n for n in ast.parse(candidate.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_prepare_lease_modules')
exec(compile(ast.Module(body=[helper],type_ignores=[]),str(candidate),'exec'),ns)
ns['_prepare_lease_modules']()
baseline=lease._loaded(ROOT,sources)
lease._authenticate_loaded(baseline,sources,ROOT)
# Replay selected future imports and real original kernel/workload module loading.
ns['_prepare_lease_modules']()
path=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py'
spec=importlib.util.spec_from_file_location('compact_mcm_kernel',path)
kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)
from tradingagents.research.onchain_replication.feature_residency import FixedFeatureMap
from tradingagents.research.onchain_replication import held_score_consumer, stage_retention, stage_retention_reader, archive_owner_stage
assert lease._loaded(ROOT,sources)==baseline
# Mutation checks exercise the same actual immutable snapshot predicate.
mod=sys.modules[PKG+'.chunk_durability'];original=mod.policy
mod.policy=lambda value: value
assert lease._loaded(ROOT,sources)!=baseline
mod.policy=original
code=original.__code__;original.__code__=(lambda value: value).__code__
assert lease._loaded(ROOT,sources)!=baseline
original.__code__=code
assert lease._loaded(ROOT,sources)==baseline
wrong=dict(sources);wrong[str(Path(mod.__file__).relative_to(ROOT))]='0'*64
try:lease._authenticate_loaded(baseline,wrong,ROOT)
except ValueError as e:source_refusal=str(e)
else:raise AssertionError('source mutation was accepted')
lease._authenticate_loaded(baseline,sources,ROOT)
print(json.dumps({'status':'passed','red_added':red_added,'red_refusal':red,'prepared_added':sorted(set(baseline)-set(before)),'baseline_modules':len(baseline),'green_future_kernel_import_equal':True,'function_mutation_refused':True,'code_mutation_refused':True,'source_hash_mutation_refused':source_refusal,'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'scope':'imports and authentic snapshot helpers only; no arrays/Owner/claim/numerical work; not actual13 changed-entry identification'},sort_keys=True))
