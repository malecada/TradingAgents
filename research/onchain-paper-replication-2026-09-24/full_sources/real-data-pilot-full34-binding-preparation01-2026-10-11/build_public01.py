"""Root-only fresh34 public rebase; no binder/admission/claim/numerical imports."""
import argparse
import ast
import re
import datetime
import difflib
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
OLD = HERE.parent/'real-data-pilot-full33-binding-preparation01-2026-10-11'
NAME = 'eth-paper-real-data-end-to-end-resource-20261011-34'
PRIOR = 'eth-paper-real-data-end-to-end-resource-20261011-33'
EXPECTED_COMPACT = 'abd86e24681f0df4ef3ca82cfb016662d9af5a46a38a32bafc65e7c92f2dacf8'
PRIOR_MANIFEST = '29e15f65c52c91456a4830ba83e698abcfea3e55fe9757b5be4e07e3183c0145'


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n').encode()


def load(path):
    return json.loads(path.read_bytes())


def ref(path):
    body = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(body),
            'sha256': hashlib.sha256(body).hexdigest()}


def save(path, value):
    with path.open('xb') as stream:
        stream.write(raw(value))


def main(anchor):
    assert type(anchor) is str and re.fullmatch(r'[0-9a-f]{40}', anchor), 'actual committed source anchor required'
    ANCHOR = anchor
    prior_manifest_body = (OLD/'MANIFEST01.json').read_bytes()
    assert hashlib.sha256(prior_manifest_body).hexdigest() == PRIOR_MANIFEST, 'accepted33 manifest changed'
    for name, pin in json.loads(prior_manifest_body)['files'].items():
        path = OLD/name
        assert path.resolve().is_relative_to(OLD) and not path.is_symlink(), 'prior public member redirected'
        assert ref(path) == pin, 'accepted33 public member changed'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == ANCHOR
    job = ROOT/'tradingagents/research/onchain_replication/job.py'
    function = next(n for n in ast.parse(job.read_bytes()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'required_sources')
    scope = {'Path': Path, '__file__': str(job)}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(job), 'exec'), scope)
    files = {p: ref(ROOT/p)['sha256'] for p in sorted(scope['required_sources']())}
    assert len(files) == 198
    docs = {p.stem: load(p) for p in (OLD/'public01').glob('*.json')}
    assert len(docs) == 12
    previous = docs['pair_policy']['numerical_source']['files']
    changed = [p for p in files if previous.get(p) != files[p]]
    assert set(previous) == set(files) and changed == ['tradingagents/research/onchain_replication/compact_mcm.py']
    assert files[changed[0]] == EXPECTED_COMPACT
    output = subprocess.check_output(
        ['git', '-c', 'core.packedGitWindowSize=16m', '-c', 'core.packedGitLimit=64m', 'cat-file', '--batch'],
        input=('\n'.join(ANCHOR+':'+p for p in files)+'\n').encode())
    pos = 0
    joined = []
    for path, digest in files.items():
        end = output.index(b'\n', pos)
        header = output[pos:end].split()
        assert len(header) == 3 and header[1] == b'blob', path
        size = int(header[2]); pos = end+1
        body = output[pos:pos+size]; pos += size
        assert output[pos:pos+1] == b'\n'; pos += 1
        assert body == (ROOT/path).read_bytes() and hashlib.sha256(body).hexdigest() == digest, path
        joined.append({'path': path, 'bytes': size, 'sha256': digest, 'git_oid': header[0].decode()})
    assert pos == len(output)
    docs['pair_policy']['numerical_source'] = {'commit': ANCHOR, 'files': files}
    docs['archive_policy']['remote_namespace'] = 'ethpilot-20261011-34'
    docs['archive_transport']['namespace'] = 'ethpilot-20261011-34'
    assert docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None
    for policy in (docs['execution_job']['resources'], docs['pilot']['resource_policy']):
        assert policy['storage_budget']['experiment'] == PRIOR
        assert policy['storage_budget']['roots'][1] == str(ROOT/'research_runs'/PRIOR)
        policy['storage_budget']['experiment'] = NAME
        policy['storage_budget']['roots'][1] = str(ROOT/'research_runs'/NAME)
    assert docs['execution_job']['resources'] == docs['pilot']['resource_policy']
    for item in (docs['execution_job']['payload']['representation_jobs']['original32'],
                 docs['producer_plan']['producers']['original32']):
        for role, key in [('pair_policy', 'pair_execution'), ('archive_policy', 'compact_archive_execution')]:
            item['descriptor'][key]['policy_sha256'] = hashlib.sha256(raw(docs[role])).hexdigest()
    (HERE/'public01').mkdir()
    for role, value in docs.items():
        save(HERE/'public01'/(role+'.json'), value)
    prepared = load(OLD/'PREPARED01.json')
    prepared['builder03_result']['inputs'] = {k: v for k, v in docs.items() if k != 'archive_policy'}
    assert len(prepared['builder03_result']['inputs']) == 11
    prepared['builder03_spec']['references']['archive_policy'] = ref(HERE/'public01/archive_policy.json')
    save(HERE/'PREPARED01.json', prepared)
    request = load(OLD/'REQUEST01.json')
    request.update(prepared=ref(HERE/'PREPARED01.json'), archive_policy=ref(HERE/'public01/archive_policy.json'),
                   private_parent='research_artifacts/real_pilot_runtime/pilot-transport-20261011-34-01')
    save(HERE/'REQUEST01.json', request)
    refs = load(OLD/'PUBLIC_INPUT_REFS_DRAFT01.json')
    assert len(refs) == 66 and 'archive_transport' not in refs
    for role in docs:
        if role != 'archive_transport':
            pin = ref(HERE/'public01'/(role+'.json'))
            refs[role].update(path=pin['path'], sha256=pin['sha256'])
    save(HERE/'PUBLIC_INPUT_REFS_DRAFT01.json', refs)
    before = (OLD/'bind_actual01.py').read_text()
    after = before.replace('pilot-transport-20261011-33-01', 'pilot-transport-20261011-34-01').replace('20261011-33', '20261011-34')
    ast.parse(after)
    assert (HERE/'bind_actual01.py').read_text() == after, 'reviewed fresh34 wrapper changed'
    routes = [ROOT/'research_runs'/NAME, ROOT/'research_artifacts/archive-dispatch-ethpilot-20261011-34', ROOT/request['private_parent']]
    assert all(not os.path.lexists(p) for p in routes)
    save(HERE/'CURRENT_NUMERICAL_GIT_JOIN01.json', {
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source': ANCHOR, 'count': len(joined),
        'files': joined, 'actual_git_batch_exit': 0, 'actual_git_batch_stdout_sha256': hashlib.sha256(output).hexdigest(),
        'qualification': 'Actual198 Git/current source body joins. No numerical imports/Owner/admission/claim.'})
    save(HERE/'ROOT_PREPARATION01.json', {
        'status': 'DRAFT_NOT_RELEASED', 'source_anchor': ANCHOR, 'predecessor_manifest': ref(OLD/'MANIFEST01.json'),
        'changed_source': changed, 'public_roles': 12, 'prepared_public_roles': 11, 'draft_input_roles': 66,
        'fresh_absent_paths': [str(p.relative_to(ROOT)) for p in routes], 'binder_executed': False, 'claim': False,
        'scope': 'Fresh33 exact committed imported-scope source; only numerical commit/hash and policy digest joins, fresh storage/transport identity and canonical public references change. Scientific/resource policies and original sample/dictionary identities remain.'})
    patches = []
    for name in ['PREPARED01.json', 'REQUEST01.json', 'PUBLIC_INPUT_REFS_DRAFT01.json', 'bind_actual01.py'] + ['public01/'+p.name for p in sorted((HERE/'public01').glob('*.json'))]:
        patches.extend(difflib.unified_diff((OLD/name).read_text().splitlines(True), (HERE/name).read_text().splitlines(True), fromfile=str(OLD/name), tofile=str(HERE/name)))
    with (HERE/'LITERAL_PATCH01.diff').open('x') as stream:
        stream.write(''.join(patches))
    save(HERE/'MANIFEST01.json', {
        'status': 'DRAFT_NOT_RELEASED', 'files': {str(p.relative_to(HERE)): ref(p) for p in sorted(HERE.rglob('*')) if p.is_file()},
        'scope': 'Exact fresh34 public/source preparation only. Independent review before one-use original binder; no admission/release/claim.'})
    print(json.dumps({'status': 'DRAFT_NOT_RELEASED', 'source_files': 198, 'changed_source': 1, 'public_roles': 12, 'prepared_roles': 11, 'draft_roles': 66, 'claim': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--anchor', required=True, help='Root actual installed and committed40hex source; no default')
    arguments = parser.parse_args()
    main(arguments.anchor)
