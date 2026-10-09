"""Focused offline Git-body proof; no research package or empirical inputs."""
import ast
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FUNCTIONS = {'local_path', '_git', '_committed', '_source_git_batch',
             '_source_batch_parse', '_source_files'}


def load(path):
    tree = ast.parse(path.read_bytes())
    scope = {'Path': Path, 're': re, 'subprocess': subprocess,
             'digest': lambda body: hashlib.sha256(body).hexdigest(),
             '_SOURCE_BATCH_FILES': 128, '_SOURCE_BATCH_BYTES': 8 * 1024**2}
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
    assert {node.name for node in nodes} == FUNCTIONS
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    return scope


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE)


with tempfile.TemporaryDirectory(prefix='pilot-git-dedup-') as temporary:
    root = Path(temporary)
    git(root, 'init', '--quiet')
    for name, body in [('a.py', b'alpha'), ('b.py', b'alpha'), ('odd\nname.py', b'odd')]:
        (root/name).write_bytes(body)
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Offline fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '--quiet', '-m', 'fixture design')
    design = git(root, 'rev-parse', 'HEAD').decode().strip()
    (root/'b.py').write_bytes(b'bravo')
    git(root, 'add', 'b.py')
    git(root, '-c', 'user.name=Offline fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '--quiet', '-m', 'fixture current')
    current = git(root, 'rev-parse', 'HEAD').decode().strip()
    baseline = ROOT/'tradingagents/research/admission.py'
    assert hashlib.sha256(baseline.read_bytes()).hexdigest() == '585d66f526d88f8488c6efcc4989a09328006e393566a596fe9e95c6c7f60cfd'
    cases = []

    def execute(path, source, frozen, files, mode=None, budget=None):
        scope = load(path)
        if budget is not None:
            scope['_SOURCE_BATCH_BYTES'] = budget
        original = scope['_source_git_batch']
        traffic = []

        def batch(root, requests, *, bodies=False):
            raw = original(root, requests, bodies=bodies)
            traffic.append({'body': bodies, 'requests': len(requests), 'bytes': len(raw)})
            if mode == 'size_conflict' and not bodies:
                lines = raw.splitlines()
                parts = lines[1].split()
                parts[2] = str(int(parts[2])+1).encode()
                lines[1] = b' '.join(parts)
                return b'\n'.join(lines)+b'\n'
            if bodies:
                if mode == 'short': return raw[:-1]
                if mode == 'suffix': return raw+b'extra\n'
                if mode == 'oid': return b'0'*40+raw[40:]
            return raw

        scope['_source_git_batch'] = batch
        try:
            scope['_source_files'](root, source, frozen, files)
            outcome = 'PASS'
        except ValueError as error:
            outcome = str(error)
        return outcome, traffic

    def check(name, source, frozen, files, expected, mode=None, budget=None):
        old, old_io = execute(baseline, source, frozen, files, mode, budget)
        new, new_io = execute(HERE/'admission.py', source, frozen, files, mode, budget)
        assert old == new == expected, (name, old, new, expected)
        cases.append({'name': name, 'outcome': new, 'baseline': old_io, 'candidate': new_io})
        return old_io, new_io

    pin = hashlib.sha256(b'alpha').hexdigest()
    (root/'b.py').write_bytes(b'alpha')
    old, new = check('four_positions_one_blob', design, design,
                     {'a.py': pin, 'b.py': pin}, 'PASS')
    assert sum(x['requests'] for x in old if x['body']) == 4
    assert sum(x['requests'] for x in new if x['body']) == 1
    (root/'b.py').write_bytes(b'bravo')
    check('distinct_design_retains_refusal', current, design,
          {'b.py': hashlib.sha256(b'bravo').hexdigest()}, 'source differs from design freeze')
    check('registered_digest_refusal', design, design, {'a.py': '0'*64},
          'registered source hash differs: a.py')
    (root/'a.py').write_bytes(b'wrong')
    check('local_body_and_failure_order', design, design,
          {'a.py': pin, 'b.py': '0'*64}, 'committed source differs: a.py')
    (root/'a.py').write_bytes(b'alpha')
    for mode in ('short', 'suffix', 'oid', 'size_conflict'):
        check(mode, design, design, {'a.py': pin},
              'committed source/registration cannot be verified', mode=mode)
    check('argv_newline_fallback', design, design,
          {'odd\nname.py': hashlib.sha256(b'odd').hexdigest()}, 'PASS')
    check('oversize_original_fallback', design, design, {'a.py': pin}, 'PASS', budget=4)
    check('second_call_fresh', design, design, {'a.py': pin}, 'PASS')
    (root/'a.py').write_bytes(b'wrong')
    check('second_call_mutation_refuses', design, design, {'a.py': pin},
          'committed source differs: a.py')
    result = {'status': 'PASS', 'cases': cases,
              'qualification': 'Actual tiny offline Git objects and focused response mutations only; no empirical inputs, numerical imports, live installation or measured pilot speed claim.'}
    with (HERE/'CHECK01.json').open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'status': 'PASS', 'cases': len(cases),
                      'duplicate_fixture_body_requests': {'original': 4, 'candidate': 1}}))
