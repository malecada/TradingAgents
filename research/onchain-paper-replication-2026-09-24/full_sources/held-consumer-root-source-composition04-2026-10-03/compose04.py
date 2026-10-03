"""Root-only local byte/Git source composition; no empirical authority."""
import datetime
import hashlib
import json
from pathlib import Path
import stat
import subprocess

repo = Path.cwd()
root = repo / 'research/onchain-paper-replication-2026-09-24/full_sources'
out = Path(__file__).resolve().parent
digest = lambda body: hashlib.sha256(body).hexdigest()
old = json.loads((root / 'held-consumer-root-source-composition03-2026-10-03/SOURCE_COMPOSITION03.json').read_bytes())
oldcap = Path(old['source_root'])
oldhead = '903488c49ad25e8026ec849a1c8b30ca5f90bcff'
candidate = root / 'held-consumer-fixture-dispatch-preparation02-2026-10-03/resource_fixture.py'
review = root / 'held-consumer-fixture-dispatch-review02-2026-10-03'
assert digest((review / 'MANIFEST02.json').read_bytes()) == '6edc91233b26900728c88382b44837b366b8e22731e5c37c53bf00fd45541c4d'
assert digest((review / 'REVIEW_DISPATCH02.md').read_bytes()) == '851c349e4baddda8301ef4b7a68a0397f21bb09ca06946abfe70cb15fa0c0cc9'
body = candidate.read_bytes()
assert digest(body) == '3ea9902ec4067edc59bc897081c5ad5f6738350ccd3a339b0b423c863212a97e'
observations = []


def git(args, cwd, record=False):
    result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, timeout=60)
    assert max(len(result.stdout), len(result.stderr)) <= 4194304
    if record:
        observations.append({'args': args, 'cwd': str(cwd), 'exit_code': result.returncode,
                             'stdout': result.stdout.decode(errors='replace'),
                             'stderr': result.stderr.decode(errors='replace')})
    assert result.returncode == 0, result.stderr
    return result.stdout


assert not (out / 'SOURCE_COMPOSITION04.json').exists()
assert git(['rev-parse', 'HEAD'], oldcap).decode().strip() == oldhead
for row in old['source_entries']:
    raw = (oldcap / row['target']).read_bytes()
    assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
    assert git(['show', oldhead + ':' + row['target']], oldcap) == raw
cap = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-04/source')
assert not cap.parent.exists()
cap.parent.mkdir()
git(['clone', '--no-checkout', '--no-hardlinks', str(oldcap), str(cap)], repo, True)
git(['checkout', '--detach', oldhead], cap, True)
git(['config', 'user.name', 'Research source preparation'], cap, True)
git(['config', 'user.email', 'research-source@localhost'], cap, True)
name = 'tradingagents/research/onchain_replication/resource_fixture.py'
(cap / name).write_bytes(body)
git(['add', '--', name], cap, True)
git(['commit', '--quiet', '-m', 'Integrate independently reviewed optional held consumer dispatch'], cap, True)
anchor = git(['rev-parse', 'HEAD'], cap, True).decode().strip()
assert git(['rev-parse', 'HEAD^'], cap).decode().strip() == oldhead
assert git(['diff', '--name-only', oldhead, anchor], cap).decode().splitlines() == [name]
# A real empty source snapshot separates the declared source from its package anchor.
git(['commit', '--quiet', '--allow-empty', '-m', 'Freeze reviewed held consumer source snapshot'], cap, True)
head = git(['rev-parse', 'HEAD'], cap, True).decode().strip()
assert git(['rev-parse', 'HEAD^'], cap).decode().strip() == anchor
assert git(['rev-parse', head + '^{tree}'], cap) == git(['rev-parse', anchor + '^{tree}'], cap)
entries = []
for row in old['source_entries']:
    item = dict(row)
    raw = (cap / item['target']).read_bytes()
    assert git(['show', head + ':' + item['target']], cap) == raw
    if item['target'] == name:
        item.update(baseline_sha256=row['sha256'], origin=str(candidate.relative_to(repo)),
                    change='reviewed optional held dispatch; all other code inverse unchanged',
                    sha256=digest(raw), bytes=len(raw))
    else:
        assert len(raw) == row['bytes'] and digest(raw) == row['sha256']
        item['change'] = 'unchanged'
    item['actual_git_commit'] = head
    entries.append(item)
package = [row for row in entries if row['package_source']]
assert len(entries) == 199 and len(package) == 148
for row in package:
    assert git(['show', anchor + ':' + row['target']], cap) == (cap / row['target']).read_bytes()
assert len(git(['ls-tree', '-r', '--name-only', head], cap).decode().splitlines()) == 204
for row in old['retained_auxiliary_tracked_bodies']:
    raw = (cap / row['path']).read_bytes()
    assert digest(raw) == row['sha256'] and len(raw) == row['bytes']
collection = json.loads((root / 'held-target-input-reuse-root-collection01-2026-10-03/INPUT_COLLECTION03.json').read_bytes())
inputrows = []
for row in collection['rows']:
    source = oldcap / row['path']
    raw = source.read_bytes()
    info = source.lstat()
    assert source.resolve() == source and stat.S_ISREG(info.st_mode) and info.st_nlink == 1
    assert digest(raw) == row['sha256'] and len(raw) == row['bytes']
    target = cap / row['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    target.chmod(stat.S_IMODE(info.st_mode))
    inputrows.append({'path': row['path'], 'sha256': digest(raw), 'bytes': len(raw),
                      'mode': stat.S_IMODE(target.lstat().st_mode),
                      'authenticated_original': row['original_path'],
                      'authenticated_source03': str(source), 'arrays_decoded': False})
runtime_rel = 'fixture_inputs/held/runtime-role01.json'
runtime_source = oldcap / runtime_rel
runtime_body = runtime_source.read_bytes()
runtime_target = cap / runtime_rel
runtime_target.parent.mkdir(parents=True, exist_ok=True)
with runtime_target.open('xb') as stream:
    stream.write(runtime_body)
runtime_target.chmod(stat.S_IMODE(runtime_source.lstat().st_mode))
binding = json.loads((root / 'held-consumer-original-git-runtime-root-binding01-2026-10-03/ORIGINAL_GIT_RUNTIME_BINDING01.json').read_bytes())
# The real no-hardlinks local clone copies unreachable objects; verify all34 anew.
for row in binding['objects']:
    kind = git(['cat-file', '-t', row['object']], cap).decode().strip()
    assert kind == row['type']
    raw = git(['cat-file', kind, row['object']], cap)
    assert digest(raw) == row['sha256'] and len(raw) == row['bytes']
for row in binding['source_paths']:
    raw = git(['show', binding['actual_original_source'] + ':' + row['path']], cap)
    assert digest(raw) == row['sha256'] and len(raw) == row['bytes']
assert git(['rev-parse', 'HEAD'], oldcap).decode().strip() == oldhead
receipt = {
    'schema_version': 1, 'status': 'actual-local-reviewed-held-source-composition-not-execution-release',
    'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_root': str(cap), 'authentic_parent_source': oldhead,
    'actual_148_package_anchor': anchor, 'actual_source_commit': head,
    'source_snapshot_commit_kind': 'real explicit empty Git commit; same tracked tree as package anchor',
    'source_count': 199, 'package_count': 148, 'whole_tracked_body_count': 204,
    'logical_source_bytes': sum(row['bytes'] for row in entries), 'source_entries': entries,
    'retained_auxiliary_tracked_bodies': old['retained_auxiliary_tracked_bodies'],
    'opaque_prior_input_count': len(inputrows), 'opaque_prior_input_bytes': sum(row['bytes'] for row in inputrows),
    'opaque_prior_inputs': inputrows,
    'runtime_role': {'path': runtime_rel, 'sha256': digest(runtime_body), 'bytes': len(runtime_body),
                     'mode': stat.S_IMODE(runtime_target.lstat().st_mode)},
    'authenticated_original_git_objects': 34, 'authenticated_original_source_lookups': 26,
    'accepted_dispatch_review_sha256': '851c349e4baddda8301ef4b7a68a0397f21bb09ca06946abfe70cb15fa0c0cc9',
    'registration': None, 'adopted_allowance': None, 'native_claims_or_numerical_jobs': 0,
    'current_source_external_recovery': False, 'actual_git_command_observations': observations,
    'qualification': 'Genuine local integration only; original snapshots immutable. Exact13roles, current native/accounting/registration/sourcefreeze and whole writable external recovery remain required. Selected C6objects do not prove fullC6history; runtime role is metadata pins, not package-body backup. No offload, saving, scientific completion or financial fit.'
}
raw = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode()
assert len(raw) <= 4194304
with (out / 'SOURCE_COMPOSITION04.json').open('xb') as stream:
    stream.write(raw)
manifest = {'schema_version': 1, 'files': [
    {'path': 'SOURCE_COMPOSITION04.json', 'bytes': len(raw), 'sha256': digest(raw)}]}
with (out / 'MANIFEST04.json').open('xb') as stream:
    stream.write((json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode())
print(json.dumps({'source_commit': head, 'package_anchor': anchor, 'source_count': 199,
                  'package_count': 148, 'tracked_bodies': 204, 'opaque_inputs': len(inputrows),
                  'runtime_role_sha256': digest(runtime_body), 'receipt_sha256': digest(raw),
                  'native_claims': 0}))
