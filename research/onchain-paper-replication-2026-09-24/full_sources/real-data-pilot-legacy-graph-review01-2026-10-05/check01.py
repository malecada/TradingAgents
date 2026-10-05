"""Independent metadata/source check only; no scientific modules or authorities."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREFIX = 'tradingagents/research/onchain_replication/'
sha = lambda b: hashlib.sha256(b).hexdigest()
names = [PREFIX + 'graph_legacy_coverage.py', PREFIX + 'graph_production.py',
         'tests/research/onchain_replication/test_graph_legacy_coverage.py']
pins = {}
for name in names:
    body = (ROOT / name).read_bytes()
    pins[name] = {'sha256': sha(body), 'bytes': len(body)}
    (HERE / ('source-' + Path(name).name)).write_bytes(body)
spec = importlib.util.spec_from_file_location('reviewed_legacy_metadata', ROOT / names[0])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
evidence_path = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-legacy-graph-evidence01-2026-10-05/EVIDENCE01.json'
evidence_raw = evidence_path.read_bytes()
evidence = json.loads(evidence_raw)
assert len(module.EVIDENCE) == 19
bodies = {}
body_pins = {}
for name, ref in module.EVIDENCE.items():
    raw = (ROOT / ref['path']).read_bytes()
    assert sha(raw) == ref['sha256']
    if name.endswith('_source'):
        original = subprocess.check_output(['git', 'show', module.SOURCE + ':' + ref['path']], cwd=ROOT)
        assert original == raw
        assert evidence['current_source_pins'][ref['path']] == ref['sha256']
    elif name != 'graph_config':
        assert evidence['pins'][ref['path']]['sha256'] == ref['sha256']
    bodies[name] = raw
    body_pins[name] = {'sha256': sha(raw), 'bytes': len(raw)}

# Independently reconstruct the actual denominator, rather than use returned summary.
index = json.loads(bodies['source_index'])
manifest = json.loads(bodies['graph_manifest'])
week = index['weeks']['2022-06-13']
assert week['members'] == evidence['authenticated_members']
counts = [member['expected_rows'] for member in week['members']]
assert counts == [1109435, 1086757, 1097000, 1100312, 1110579, 1058336, 1018674]
assert sum(counts) == 7581093 == manifest['metadata']['raw_count']
assert manifest['graph_hash'] == evidence['graph_hash']
claim, terminal = map(lambda k: json.loads(bodies[k]), ['claim', 'terminal'])
assert claim['source'] == module.SOURCE == evidence['source_commit']
assert terminal['status'] == 'failed' and terminal['output_sha256'] == {}
proof = {'schema_version': 2, 'kind': module.KIND,
         'roles': {name: name for name in bodies}}
graph = SimpleNamespace(**copy.deepcopy(manifest['metadata']))
reads = []
def read(role):
    reads.append(role)
    return bodies[role]
result = module.verify_legacy_coverage(proof, graph, sha(bodies['graph_manifest']), read)
assert reads == list(module.EVIDENCE)
assert result['parent_status'] == 'failed' and result['graph_cell_status'] == 'complete'
assert result['modern_producer_plan_present'] is False

# A graph-availability substitution must fail even with all 19 genuine bodies.
graph.available_at = graph.end_utc
try:
    module.verify_legacy_coverage(proof, graph, sha(bodies['graph_manifest']), bodies.__getitem__)
except ValueError as error:
    availability_refusal = str(error)
    assert 'graph available_at differs' in availability_refusal
else:
    raise AssertionError('graph availability substitution accepted')

# A unique but swapped role map must fail at the fixed body hash, not just uniqueness.
swapped = copy.deepcopy(proof)
swapped['roles']['claim'], swapped['roles']['terminal'] = 'terminal', 'claim'
try:
    module.verify_legacy_coverage(swapped, graph, sha(bodies['graph_manifest']), bodies.__getitem__)
except ValueError as error:
    role_refusal = str(error)
    assert 'claim body differs' in role_refusal
else:
    raise AssertionError('role substitution accepted')

# Remove only the new branch, callback argument, and its genuine caller binding.
# Exact full-module AST equality then proves all original paths are unchanged.
baseline = subprocess.check_output(['git', 'show', 'HEAD:' + names[1]], cwd=ROOT)
assert sha(baseline) == 'ef5ee5e2c8f6438e4e334d1a468397ad6f60e176d157e7849b7132737c7c85e8'
(HERE / 'baseline-graph_production.py').write_bytes(baseline)
tree = ast.parse((ROOT / names[1]).read_bytes())
func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_verify_graph_coverage')
assert len(func.args.kwonlyargs) == 1 and func.args.kwonlyargs[0].arg == 'read_input'
assert isinstance(func.body[0], ast.If)
assert ast.unparse(func.body[0].test) == "isinstance(proof, dict) and proof.get('schema_version') == 2"
guard = copy.deepcopy(func)
guard.body = [guard.body[0]]
guard_module = ast.Module(body=[guard], type_ignores=[])
ns = {}
exec(compile(guard_module, '<schema2-reader-guard>', 'exec'), ns)
try:
    ns['_verify_graph_coverage'](proof, None, '')
except ValueError as error:
    missing_reader_refusal = str(error)
    assert missing_reader_refusal == 'legacy graph evidence requires admitted original inputs'
else:
    raise AssertionError('missing registered reader accepted')
func.body.pop(0)
func.args.kwonlyargs = []
func.args.kw_defaults = []
callback_calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_verify_graph_coverage' and node.keywords:
        assert len(node.keywords) == 1
        assert node.keywords[0].arg == 'read_input'
        assert ast.unparse(node.keywords[0].value) == 'run.read_input'
        callback_calls.append(node.lineno)
        node.keywords = []
assert len(callback_calls) == 1
assert ast.dump(tree, include_attributes=False) == ast.dump(ast.parse(baseline), include_attributes=False)
out = {'status': 'PASS_SOURCE_METADATA_ONLY', 'source_pins': pins,
       'evidence_report_sha256': sha(evidence_raw), 'body_pins': body_pins,
       'source_commit': module.SOURCE, 'original_git_source_pins_match': True,
       'member_count': 7, 'rows_declared_and_original_completed_count': sum(counts),
       'read_count': len(reads), 'summary': result,
       'availability_substitution_refusal': availability_refusal,
       'unique_role_substitution_refusal': role_refusal,
       'missing_reader_refusal': missing_reader_refusal,
       'exact_original_full_module_ast_after_removing_three_edits': True,
       'genuine_read_input_call_lines': callback_calls,
       'no_arrays_raw_spans_financial_execution_authority_objects': True}
(HERE / 'CHECK01.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
print(json.dumps({'status': out['status'], 'body_count': len(bodies), 'rows': sum(counts),
                  'CHECK01_sha256': sha((HERE / 'CHECK01.json').read_bytes())}))
