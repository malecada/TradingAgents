from pathlib import Path
import ast,hashlib,importlib.util,json
D=Path(__file__).resolve().parent;S=D.parent/'real-data-pilot-throughput-measurement01-2026-10-05';P=Path('candidate/tradingagents/research/onchain_replication')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(S/'MANIFEST01.json')=='7d45e5d90610200b2cddb5b0417e97e4ab64e03d009d6093c187d504f99c56eb'
for r in json.loads((S/'MANIFEST01.json').read_text())['members']:
 assert h(S/r['path'])==r['sha256'] and (S/r['path']).stat().st_size==r['bytes']
delta=json.loads((S/'SOURCE_DELTA01.json').read_text());origin=Path(delta['origin']);assert h(origin)==delta['origin_sha256']==h(S/'caller.baseline.py')
assert h(origin.parents[4]/'MANIFEST01.json')==delta['origin_manifest_sha256']
text=(S/P/'real_pilot_import_caller.py').read_text();lines=text.splitlines(True)
for edit in reversed(delta['edits']):
 assert lines[edit['new_start']:edit['new_end']]==edit['new'];lines[edit['new_start']:edit['new_end']]=edit['old']
assert ''.join(lines)==origin.read_text()
old={n.name:ast.dump(n) for n in ast.parse(origin.read_text()).body if isinstance(n,ast.FunctionDef)}
new={n.name:ast.dump(n) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
assert set(old)==set(new) and all(old[k]==new[k] for k in old if k!='execute')
spec=importlib.util.spec_from_file_location('measurement',S/P/'real_pilot_throughput.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
nodes={f'{i:064x}':2 for i in range(7)};now=[10.];v=m.MCMMeasurements(nodes,population_scope='resource_pilot_subset',clock=lambda:now[0])
for k in nodes:
 v.begin(k);now[0]+=1;v.completed(k,{'graph_hash':k,'rows':2,'motifs':32,'cells':64})
v.failed(MemoryError('synthetic later closure failure'));r=v.summary(None)
assert r['complete_graphs']==7 and r['verified_completed_motif_cells']==448 and r['completed_mcm_seconds']==7 and r['one_update_phase_seconds'] is None and r['guard_resource_evidence'] is None and r['financial_fit_complete'] is False
for bad in (float('nan'),float('inf'),-1):
 try:m.seconds(bad)
 except ValueError:pass
 else:raise AssertionError('invalid duration admitted')
v=m.MCMMeasurements(nodes,population_scope='resource_pilot_subset',clock=lambda:now[0]);v.begin(next(iter(nodes)))
try:v.summary(None)
except ValueError:pass
else:raise AssertionError('active interval summarized')
print(json.dumps({'manifest_and_baseline_authenticated':True,'literal_inverse':True,'other_functions_ast_identical':True,'later_failure_preserves_verified_counts_without_training_or_financial_credit':True,'invalid_time_and_active_summary_refuse':True,'author_three_methods':'retained raw stderr/stdout and checks authenticated; not rerun','numerical_native_execution':False},sort_keys=True))
