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


prior = HERE.parent/'postnative28/FRESH_GIT_RECOVERY28.json'
assert sha(prior)=='c66a488a8bad2b51710769464c41ff92b3f0377e3f5d6ebc52733fb486fbf660', 'actual28 baseline receipt changed'
review=F/'pilot34-postnative-increment-return-review01-2026-10-11/REVIEW01.json'
assert sha(review)=='71e99df6ce8daf7226c2b91a42716cbbd35fd97d1bd6a9656365918f6d35259b', 'accepted28 return review changed'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned=['pilot34-native-owner-qualification03-2026-10-11', 'pilot34-native-owner03-outcome-review01-2026-10-11', 'pilot34-postnative-increment-return-review01-2026-10-11', 'pilot34-two-attribute-main-integration-bundle01-2026-10-11', 'pilot34-native03-increment-tools-review01-2026-10-11', 'pilot34-two-attribute-main-integration-review01-2026-10-11']
scope_directories=set()
for name in owned:
    root=F/name
    assert root.is_dir() and not root.is_symlink(), 'required final public scope absent: '+name
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():
            names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Exact generated28 receipts/raw operations only. Never traverse historical H.
prior_generated_names=['SELECTION28.json', 'CAPTURE28.json', 'FRESH_GIT_RECOVERY28.json', 'GIT_OPERATIONS28.json', 'ROOT_ACTUAL_OPERATIONS28.json', 'root_commit28.stdout', 'root_commit28.stderr', 'local_head.stdout', 'local_head.stderr', 'remote_get_url.stdout', 'remote_get_url.stderr', 'remote_actual_branch_readback.stdout', 'remote_actual_branch_readback.stderr', 'local_archive_git_tree_join.stdout', 'local_archive_git_tree_join.stderr', 'fresh_bare_init.stdout', 'fresh_bare_init.stderr', 'fresh_remote_add.stdout', 'fresh_remote_add.stderr', 'set_promisor.stdout', 'set_promisor.stderr', 'set_tree_zero_filter.stdout', 'set_tree_zero_filter.stderr', 'actual_external_commit_only_fetch.stdout', 'actual_external_commit_only_fetch.stderr', 'fetched_head_readback.stdout', 'fetched_head_readback.stderr', 'actual_external_commit_body.stdout', 'actual_external_commit_body.stderr', 'actual_external_selected_blob_fetch.stdout', 'actual_external_selected_blob_fetch.stderr', 'actual_external_archive_blob_return.stdout', 'actual_external_archive_blob_return.stderr']
for name in prior_generated_names:
    path=prior.parent/name
    assert path.is_file() and not path.is_symlink(), 'required actual28 receipt absent: '+name
    names.add(str(path.relative_to(ROOT)))
helper_names=('select29.py', 'capture29.py', 'recover29.py', 'prepare29.py', 'check_source29.py', 'HELPERS_MANIFEST01.json', 'AUTHOR_CHECK01.json', 'PROSPECTIVE_ROSTER01.json', 'PREPARATION_CHECK01.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff', 'REPORT.md')
for name in helper_names:names.add(str((HERE/name).relative_to(ROOT)))
fixed_public_names=['research/onchain-paper-replication-2026-09-24/STATE.md', 'research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md']
for relative in fixed_public_names:
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative
    names.add(relative)
main_source_names=[]
# No original failed34 scientific/runtime scopes are traversed or admitted.
scopes=[]
# Already returned postnative28 archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
assert prior_receipt['capture']['path']==str((prior.parent/'CAPTURE28.json').relative_to(ROOT))
assert sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256'], 'actual28 capture receipt changed'
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('post-native-increment28.tar','fresh-git-recovered-postnative28.tar','actual_external_archive_blob_return.stdout')}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and not path.is_symlink() and path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256'], relative

# Only actual new or changed bodies; immutable prior recovered entry bodies are reused.
prior_selection=json.loads((prior.parent/'SELECTION28.json').read_bytes())
assert sha(prior.parent/'SELECTION28.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
assert not (HERE/'SELECTION29.json').exists(), 'selection29 already spent'
assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in helper_names for relative in names), 'generated nativeoutcome29 products are outside selection'
# Bound actual committed/working Git deltas to this declared finite increment.
allowed_files=set(fixed_public_names+main_source_names)|{str((prior.parent/name).relative_to(ROOT)) for name in prior_generated_names}|{str((HERE/name).relative_to(ROOT)) for name in helper_names}
allowed_roots=[F/name for name in owned]
assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names), 'Git delta outside declared nativeoutcome29 scope'
# Main installation is outside this preparation; only public bundle bodies.

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
    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],
    'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt'],
    'mandatory_public_roots':owned,
    'prior_generated_files':prior_generated_names,
    'actual_scope_states': [{'path':str(scope.relative_to(ROOT)),'exists':scope.exists(),'empty_directories_included':True} for scope in scopes],
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'selection_rule': 'Finite postnative28 receipts and raw Git outputs, actual native03 source/outcome/review, accepted28 return review, new public integration bundle and independent tools review. Previous28 eight reused rows and67 earlier inherited rows retain accepted receipt continuity. No Main installation, empirical/private/runtime store traversal, older archive replay or deletion authority.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION29.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
