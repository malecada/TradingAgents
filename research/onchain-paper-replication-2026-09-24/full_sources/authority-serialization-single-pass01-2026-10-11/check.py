"""Finite synthetic expression check; does not import or instantiate authority."""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import resource
import signal
import time
from types import MappingProxyType

resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))
signal.alarm(20)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'tradingagents/research/onchain_replication'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
result = {'status': 'RUNNING', 'scope': 'stdlib-only synthetic serializer expressions'}
try:
    baseline = (SOURCE / 'imported_authority_lease.py').read_bytes()
    candidate = baseline
    for expression in (b'self.run.admission.inputs', b"self.run.admission.experiment['source_files']", b'self.bound.context'):
        assert candidate.count(b'thaw(' + expression + b')') == 2
        candidate = candidate.replace(b'thaw(' + expression + b')', expression)
    for name, raw in [('baseline.py', baseline), ('candidate.py', candidate), ('provenance-baseline.py', (SOURCE / 'provenance.py').read_bytes())]:
        with (HERE / name).open('xb') as stream:
            stream.write(raw)
    for name, left, right in [('PATCH.diff', baseline, candidate), ('INVERSE.diff', candidate, baseline)]:
        (HERE / name).write_text(''.join(difflib.unified_diff(left.decode().splitlines(True), right.decode().splitlines(True), fromfile='a/tradingagents/research/onchain_replication/imported_authority_lease.py', tofile='b/tradingagents/research/onchain_replication/imported_authority_lease.py')))
    old_tree, new_tree = ast.parse(baseline), ast.parse(candidate)
    class Remove(ast.NodeTransformer):
        count = 0
        def visit_ClassDef(self, node):
            if node.name == 'Lease':
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name in ('__init__', '_finger'):
                        for statement in method.body:
                            if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call) and isinstance(statement.value.func, ast.Name) and statement.value.func.id == 'canonical_bytes' and isinstance(statement.value.args[0], ast.Dict):
                                fields = statement.value.args[0]
                                for i, key in enumerate(fields.keys):
                                    if key.value in ('inputs', 'sources', 'runtime'):
                                        value = fields.values[i]
                                        assert isinstance(value, ast.Call) and value.func.id == 'thaw' and len(value.args) == 1
                                        fields.values[i] = value.args[0]
                                        self.count += 1
            return node
    removal = Remove()
    stripped = removal.visit(copy.deepcopy(old_tree))
    assert removal.count == 6 and ast.dump(stripped) == ast.dump(new_tree)
    compile(new_tree, '<candidate-source-only>', 'exec')
    provenance = ast.parse((HERE / 'provenance-baseline.py').read_bytes())
    definitions = [node for node in provenance.body if isinstance(node, ast.FunctionDef) and node.name in ('thaw', 'canonical_bytes')]
    env = {'json': json}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), '<extracted-provenance-functions>', 'exec'), env)
    def expression(tree, method):
        lease = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Lease')
        body = next(node.body for node in lease.body if isinstance(node, ast.FunctionDef) and node.name == method)
        call = next(copy.deepcopy(node.value) for node in body if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'canonical_bytes' and isinstance(node.value.args[0], ast.Dict))
        fields = call.args[0]
        for i, key in enumerate(fields.keys):
            replacement = ast.Subscript(value=ast.Name(id='fields', ctx=ast.Load()), slice=key, ctx=ast.Load())
            value = fields.values[i]
            fields.values[i] = ast.Call(func=ast.Name(id='thaw', ctx=ast.Load()), args=[replacement], keywords=[]) if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == 'thaw' else replacement
        return compile(ast.fix_missing_locations(ast.Expression(body=call)), '<synthetic-field-projection>', 'eval')
    pairs = [(expression(old_tree, name), expression(new_tree, name)) for name in ('__init__', '_finger')]
    def outcome(code, fields):
        try:
            return ('bytes', eval(code, env, {'fields': fields}))
        except Exception as error:
            return (type(error).__name__, str(error))
    base = dict(prepared='00', execution='11', claim='22', source='33', registration='44', inputs={}, sources={}, runtime={})
    values = [None, True, 0, -12, 1.25, 'žluťoučký', {}, [], (), {'a': (1, {'b': [None, False]})}, MappingProxyType({'nested': (MappingProxyType({'value': 'x'}),)})]
    errors = [float('nan'), float('inf'), b'bad', {1, 2}, {'a': {1: 'one', 'two': 2}}]
    checks = 0
    for old, new in pairs:
        for key in ('inputs', 'sources', 'runtime'):
            for value in values + errors:
                fields = {**base, key: value}
                assert outcome(old, fields) == outcome(new, fields)
                checks += 1
            mutable = {'nested': [{'value': 1}]}
            fields = {**base, key: mutable}
            before = outcome(old, fields)
            assert before == outcome(new, fields)
            mutable['nested'][0]['value'] = 2
            after = outcome(old, fields)
            assert after == outcome(new, fields) and after != before
            checks += 1
        backing = {'nested': {'value': 'before'}}
        fields = {**base, 'runtime': MappingProxyType(backing)}
        before = outcome(new, fields)
        backing['nested']['value'] = 'after'
        assert outcome(old, fields) == outcome(new, fields) != before
        checks += 1
    timing = []
    old, new = pairs[1]
    for size in (16, 128):
        roster = {f'synthetic-{i}': {'path': f'synthetic/{i}', 'hash': '0'*64, 'metadata': (i, ['x', None, False])} for i in range(size)}
        fields = {**base, 'inputs': roster, 'sources': MappingProxyType(roster), 'runtime': {'nested': (roster,)}}
        assert outcome(old, fields) == outcome(new, fields)
        samples = {'old': [], 'new': []}
        for repetition in range(4):
            ordered = [('old', old), ('new', new)] if repetition % 2 == 0 else [('new', new), ('old', old)]
            for label, code in ordered:
                start = time.perf_counter_ns()
                for _ in range(12):
                    eval(code, env, {'fields': fields})
                samples[label].append(time.perf_counter_ns() - start)
        timing.append({'roster_entries': size, 'calls_per_sample': 12, 'elapsed_ns': samples})
    assert baseline == (SOURCE / 'imported_authority_lease.py').read_bytes()
    result.update(status='PASS', equivalence_checks=checks, removed_calls=6, exact_ast_delta=True, timings=timing, baseline_sha256=sha(baseline), candidate_sha256=sha(candidate), python=__import__('sys').version)
except BaseException as error:
    result.update(status='FAIL', error_type=type(error).__name__, error=str(error))
    raise
finally:
    (HERE / 'RESULT.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
