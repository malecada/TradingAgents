from pathlib import Path
import ast,hashlib,importlib.util,json,textwrap,sys,copy
R=Path.cwd();O=Path(__file__).resolve().parent;C=O/'candidate';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in C.glob('*.py'):ast.parse(p.read_bytes())
v=json.loads((O/'DISPATCH_INVERSE01.json').read_bytes());s=(R/v['baseline']).read_text();assert h(R/v['baseline'])==v['baseline_sha256']
for e in v['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'])
assert s==(C/'graph_production.py').read_text()
v=json.loads((O/'SCIENTIFIC_INVERSE01.json').read_bytes());base=(R/v['baseline']).read_text();assert h(R/v['baseline'])==v['baseline_sha256']
anchor="        observed=db.execute('SELECT DISTINCT asset,week FROM events ORDER BY asset,week').fetchall()\n"
body=textwrap.dedent(base[base.index(anchor):]).replace(v['literal_edit']['before'],v['literal_edit']['after'])
candidate=ast.parse((C/'weekly_retained_ledger.py').read_bytes());fn=next(x for x in candidate.body if isinstance(x,ast.FunctionDef))
assert ast.dump(ast.Module(body=fn.body,type_ignores=[]),include_attributes=False)==ast.dump(ast.parse(body),include_attributes=False)
spec=importlib.util.spec_from_file_location('retained_metadata_only',C/'graph_ledger_continuation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
raw={k:(R/ref['path']).read_bytes() for k,ref in m.FIXED.items()}
values,checkpoints=m.original_metadata(raw.__getitem__)
assert len(checkpoints)==7 and sum(r[2] for r in checkpoints)==checkpoints[-1][3]==7507236
assert values['old_failed']['status']=='failed' and values['old_source_cell']['status']=='complete'
p=json.loads((O/'PLAN_DRAFT01.json').read_bytes())
try:m.plan_check(p)
except ValueError as e:assert 'identity unbound' in str(e)
else:raise AssertionError('unbound identity accepted')
p['new_experiment_id']='synthetic-schema-refusal-only'
try:m.plan_check(p)
except ValueError as e:assert 'ledger SHA unbound' in str(e)
else:raise AssertionError('unknown ledger bytes admitted')
p['new_experiment_id']=m.OLD
try:m.plan_check(p)
except ValueError:pass
else:raise AssertionError('old identity reuse admitted')
x=dict(raw);d=json.loads(x['old_boundary_6']);d['total_rows']-=1;x['old_boundary_6']=json.dumps(d).encode()
try:m.original_metadata(x.__getitem__)
except ValueError as e:assert 'metadata bytes differ' in str(e)
else:raise AssertionError('boundary substitution accepted')
source=(C/'graph_ledger_continuation.py').read_text();assert "'?mode=ro'" in source and 'PRAGMA integrity_check' in source and "original ledger changed during continuation" in source
assert all(name not in sys.modules for name in ('sqlite3','numpy','torch'))
agg=R/m.LEDGER;assert agg.stat().st_size==3189231616
assert not (agg.parent/'complete.json').exists() and not (agg.parent/'failed.json').exists()
graph=agg.parent.parent/'graph-2022-05-30';assert not (graph/'manifest.json').exists();names=sorted(p.name for p in graph.iterdir());assert len(names)==2
print(json.dumps({'decision':'pass-source-metadata-only','exact_original_post_ingestion_AST':True,'dispatch_two_hunk_inverse':True,'source_markers':7,'committed_rows':7507236,'parent_failed':True,'aggregation_terminal_absent':True,'graph_manifest_absent':True,'partial_graph_names':names,'unbound_identity_and_hash_refused':True,'old_identity_and_altered_marker_refused':True,'sqlite_connections':0,'payload_reads':0,'scientific_imports':0,'numerical_equivalence_run':False}))
