"""Select actual public increments since the last verified external return."""
import datetime
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior = HERE.parent/'full34increment26/FRESH_GIT_RECOVERY26.json'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned = ['graph-hash-current-serialization-candidate01-2026-10-11', 'pilot34-terminal-state-consolidation01-2026-10-11', 'real-data-pilot-full34-entry-preparation01-2026-10-11', 'real-data-pilot-full34-binding-preparation01-2026-10-11', 'pilot34-terminal-outcome-review01-2026-10-11', 'pilot34-outcome-increment-tools-review01-2026-10-11', 'pilot34-five-module-serialization-bundle01-2026-10-11', 'pilot34-shared-serialization-integration01-2026-10-11', 'pilot34-authority-fresh-serialization-candidate01-2026-10-11', 'pilot34-authority-fresh-serialization-source-review01-2026-10-11', 'pilot34-acceleration-candidates-source-review01-2026-10-11', 'pilot34-acceleration-candidates-source-review02-2026-10-11', 'pilot34-serializer02-focused-timing01-2026-10-11', 'pilot34-native-owner-qualification01-2026-10-11', 'pilot34-native-owner-qualification02-2026-10-11', 'pilot34-measurement-locators01-2026-10-11', 'pilot34-resource-overhead-investigation01-2026-10-11', 'pilot34-numeric-authority-call-count01-2026-10-11', 'pilot34-driver-boundary-count01-2026-10-11', 'pilot34-neighborhood-initialization-investigation01-2026-10-11', 'pilot34-large-pair-acceleration-status01-2026-10-11', 'matching-compiled-uncached-edge-chunk01-2026-10-11', 'matching-compiled-uncached-edge-chunk02-2026-10-11', 'matching-compiled-uncached-edge-caller-candidate01-2026-10-11', 'matching-compiled-uncached-edge-caller-candidate02-2026-10-11', 'matching-compiled-uncached-edge-caller-candidate03-2026-10-11', 'matching-compiled-uncached-edge-caller-source-review01-2026-10-11', 'matching-compiled-uncached-edge-caller-source-review02-2026-10-11', 'matching-compiled-two-attribute-agreement01-2026-10-11', 'matching-compiled-two-attribute-agreement-source-review01-2026-10-11', 'matching-compiled-two-attribute-qualification02-2026-10-11', 'matching-compiled-two-attribute-qualification03-2026-10-11', 'matching-compiled-two-attribute-qualification-source-review02-2026-10-11', 'matching-compiled-two-attribute-qualification-source-review03-2026-10-11']
scope_directories=set()
for name in owned:
    root=F/name
    assert root.is_dir() and not root.is_symlink(), 'required final public scope absent: '+name
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():
            names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
public_metadata_dependencies = {'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-runtime-input02-2026-10-11/RUNTIME_REFERENCE01.json': {'sha256': '8135e84845eae061bfbb68c22fc825fd5614d9b6dc313e8b39a5a0d1f0df97fb', 'bytes': 345}, 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-runtime-input02-2026-10-11/LINEAGE01.json': {'sha256': '77e85c3e10c75d6d417cb215c6a121b43d19c4a41d8e52cd803589e6f4c9eb8b', 'bytes': 1280}, 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-selected-feature-protocol01-2026-10-06/draft07/templates/environment.json': {'sha256': '3a97a20ba8058cac81c8c62a7ba3596aac2fe4deb17627d0aa57bf53a93b86dc', 'bytes': 358}, 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-runtime-input01-2026-10-10/INVENTORY01.json': {'sha256': '7f0cbd1a34389ac112c9e09241cb1bcab7b1972e77e5fe7d13dc124984266175', 'bytes': 3624}, 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-runtime-input01-2026-10-10/RUNTIME_REFERENCE01.json': {'sha256': '247d62394372e4ef10b4e79f351e5c2aee017b846cb2fc35e29b774b2a7eb366', 'bytes': 382}}
for relative,reference in public_metadata_dependencies.items():
    path=ROOT/relative
    assert path.stat().st_size==reference['bytes'] and sha(path)==reference['sha256'], relative
    names.add(relative)
for name in ('capture27.py', 'recover27.py', 'select27.py', 'HELPERS_MANIFEST01.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff', 'AUTHOR_CHECK01.json', 'REPORT.md', 'CAPTURE_GENERATION_FAILURE01.txt', 'AUTHOR_CHECK_INITIAL01.json'):
    names.add(str((HERE/name).relative_to(ROOT)))
# Exact current failed attempt and Root observations; no private runtime/history replay.
# Original failed28 scopes already actually recovered; no raw replay.
N='eth-paper-real-data-end-to-end-resource-20261011-34'
scopes=[ROOT/'research_runs'/N,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/N,ROOT/'research_artifacts/onchain_representations/eab8d86b62c9274c2888e73538431496527fc376eb1f0f73ebd3c6f9ce1da778'/N,ROOT/'research_artifacts/archive-dispatch-ethpilot-20261011-34',ROOT/'research_artifacts/onchain_compact_mcm/eab8d86b62c9274c2888e73538431496527fc376eb1f0f73ebd3c6f9ce1da778'/N]
for scope in scopes:
    if scope.exists():
        assert scope.is_dir() and not scope.is_symlink(), str(scope)
        scope_directories.add(scope)
    for path in scope.rglob('*'):
        if path.is_file() or path.is_symlink(): names.add(str(path.relative_to(ROOT)))
        elif path.is_dir(): scope_directories.add(path)
# Already returned preparation archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and sha(path)==prior_receipt['returned_archive']['sha256'], relative

# Only actual new or changed bodies; immutable prior recovered entry bodies are reused.
prior_selection=json.loads((prior.parent/'SELECTION26.json').read_bytes())
assert sha(prior.parent/'SELECTION26.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
assert not (HERE/'SELECTION27.json').exists(), 'selection27 already spent'
assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in ('capture27.py','recover27.py','select27.py','HELPERS_MANIFEST01.json','LITERAL_PATCH01.diff','LITERAL_INVERSE01.diff','AUTHOR_CHECK01.json','REPORT.md','CAPTURE_GENERATION_FAILURE01.txt','AUTHOR_CHECK_INITIAL01.json') for relative in names), 'generated outcome27 products are outside selection'
reused=[]
for relative in sorted(names-excluded):
    old=previous_rows.get(relative);path=ROOT/relative
    if old and old['type']=='regular' and not path.is_symlink() and path.is_file() and format(stat.S_IMODE(path.stat().st_mode),'04o')==old['mode'] and path.stat().st_size==old['bytes'] and sha(path)==old['sha256']:
        reused.append(relative)
names = sorted(names-excluded-set(reused))
rows = []
directories = set(scope_directories)
for relative in names:
    path = ROOT/relative
    assert path.parent.resolve(strict=True) == path.parent, relative
    assert not ({'.git', '.venv', 'node_modules', 'keys', 'apis'} & set(path.parts)), relative
    assert path.name not in ('.env', 'hf_token.txt', 'connection.json', 'id_ed25519_storagebox_u676273'), relative
    assert not relative.startswith(('research_artifacts/', 'research_runs/')) or any(path.is_relative_to(scope) for scope in scopes), relative
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode):
        target = os.readlink(path)
        row = {'path': relative, 'type': 'symlink',
               'mode': format(stat.S_IMODE(before.st_mode), '04o'),
               'linkname': target, 'bytes': 0}
    else:
        assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 64*1024**2, relative
        body = path.read_bytes()
        row = {'path': relative, 'type': 'regular',
               'mode': format(stat.S_IMODE(before.st_mode), '04o'),
               'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    after = path.lstat()
    assert all(getattr(before, k) == getattr(after, k) for k in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), relative
    rows.append(row)
    parent = path.parent
    while parent != ROOT:
        directories.add(parent)
        parent = parent.parent
dirs = []
for path in sorted(directories):
    assert path.resolve(strict=True) == path and not path.is_symlink()
    dirs.append({'path': str(path.relative_to(ROOT)), 'type': 'directory',
                 'mode': format(stat.S_IMODE(path.stat().st_mode), '04o')})
selection = {
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'baseline_actual_recovery': {'path': str(prior.relative_to(ROOT)), 'sha256': sha(prior)},
    'baseline_source': base,
    'actual_scope_states': [{'path':str(scope.relative_to(ROOT)),'exists':scope.exists(),'empty_directories_included':True} for scope in scopes],
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'selection_rule': 'Actual failed34 public outcomes, typed trees and Root entry/closure increments plus independent actual outcome review since recovered26; exact new/changed Git bodies and immutable prior row reuse. No private dispatch, scientific/raw/runtime store duplication, alias admission or deletion authority.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION27.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
