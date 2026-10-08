import ast, hashlib, importlib.util, json, pathlib, sys, unittest
ROOT=pathlib.Path.cwd(); F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
HERE=pathlib.Path(__file__).resolve().parent
C=F/'real-data-pilot-advance-validation-correction01-2026-10-08'
D=F/'real-data-pilot-capacity-domain-correction01-2026-10-08'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'MANIFEST01.json').read_text())
for p,h in m['files'].items():assert digest(C/p)==h
old=(C/'original_matching_annealing.py').read_text(); new=(C/'matching_annealing.py').read_text()
start=new.index('    check(state,a,b,c)\n    return _advance_checked',new.index('def advance('))
end=new.index("    n,m=state['shape'];right_edges=",start)
restored=new[:start]+'    check(state,a,b,c);'+new[end+4:]
assert restored==old
assert ast.dump(ast.parse(restored))==ast.dump(ast.parse(old))
oldc=(C/'original_matching_checkpoint.py').read_text(); newc=(C/'matching_checkpoint.py').read_text()
assert newc.count('ann._advance_checked(')==1
assert newc.replace('ann._advance_checked(', 'ann.advance(')==oldc
for name in ('matching_annealing.py','matching_checkpoint.py'):
 assert (C/('original_'+name)).read_bytes()==(ROOT/'tradingagents/research/onchain_replication'/name).read_bytes()
context=json.loads((D/'LIMIT_CONTEXT01.json').read_text())
for e in context['evidence']:
 p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and digest(p)==e['sha256']
pre=json.loads((F/'real-data-pilot-final19-2026-10-08/PREPARATION_RESULT01.json').read_text())
adm=json.loads((F/'real-data-pilot-final19-2026-10-08/ACTUAL_JOB_READONLY_ADMISSION01.json').read_text())
assert context['actual_native_file_limit_bytes']==adm['resource_policy']['native_unit_limits']['file_size_bytes']==2**30
expected={k:{f:v[f] for f in ('directories','logical_bytes','max_file_bytes','regular_files')} for k,v in pre['inventory']['categories'].items()}
assert context['declaration_categories']==expected
assert context['score_tail_records_file_bytes']==80*65536 and context['pair_event_chunk_bytes']==168*49152
assert context['actual_native_file_limit_bytes']>context['source_component_envelopes']['checkpoint_single_array_file_bytes']['required']>expected['checkpoint_retention']['max_file_bytes']
# Import the candidate test loader only for its isolated modules, then run the existing focused
# checkpoint integration suite against the candidate engine. No installed module file changes.
spec=importlib.util.spec_from_file_location('review_candidate_checks',C/'checks.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
from tests.research.onchain_replication import test_matching_pair_checkpoints as existing
existing.engine=h.new; existing.m.engine=h.new
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(existing))
summary={'source_literal_and_ast_inverse':True,'originals_match_current_main':True,'capacity_evidence_hashes':True,'actual_native_limit_bytes':2**30,'inventory_categories_exact':True,'candidate_existing_suite_tests':result.testsRun,'candidate_existing_suite_pass':result.wasSuccessful(),'candidate_manifest_sha256':digest(C/'MANIFEST01.json'),'capacity_context_sha256':digest(D/'LIMIT_CONTEXT01.json'),'empirical_execution':False}
(HERE/'CHECKS01.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
if not result.wasSuccessful():sys.exit(1)
