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


prior = HERE.parent/'outcome27/FRESH_GIT_RECOVERY27.json'
assert sha(prior)=='4bf7836d45312d5a089f94825cf97762c9121cff163d2ddd9bbb889cdaa199ca', 'actual27 baseline receipt changed'
review=F/'pilot34-outcome-increment-return-review01-2026-10-11/REVIEW01.json'
assert sha(review)=='15f94fd288e1bf89feb911e578829303e9b223be70524047a70053b894381af8', 'accepted27 return review changed'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned = ['pilot34-outcome-increment-return-review01-2026-10-11', 'pilot34-native-owner-qualification02-2026-10-11', 'pilot34-linux-memfd-compatibility-probe01-2026-10-11', 'pilot34-serializer-postclosure-install01-2026-10-11', 'pilot34-native-owner02-outcome-and-serializer-install-review01-2026-10-11', 'matching-compiled-two-attribute-caller-candidate01-2026-10-11', 'matching-compiled-two-attribute-caller-candidate02-2026-10-11', 'matching-compiled-two-attribute-caller-candidate03-2026-10-11', 'matching-compiled-two-attribute-caller-source-review01-2026-10-11', 'matching-compiled-two-attribute-caller-source-review02-2026-10-11', 'matching-compiled-two-attribute-caller-source-review03-2026-10-11', 'pilot34-native-owner-qualification03-2026-10-11', 'pilot34-native-owner-qualification03-entry-review01-2026-10-11', 'pilot34-postnative-increment-tools-review01-2026-10-11']
scope_directories=set()
for name in owned:
    root=F/name
    assert root.is_dir() and not root.is_symlink(), 'required final public scope absent: '+name
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():
            names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Exact generated27 receipts/raw operations only. Never traverse historical H.
prior_generated_names=['SELECTION27.json', 'CAPTURE27.json', 'FRESH_GIT_RECOVERY27.json', 'GIT_OPERATIONS27.json', 'ROOT_ACTUAL_OPERATIONS27.json', 'local_head.stdout', 'local_head.stderr', 'remote_get_url.stdout', 'remote_get_url.stderr', 'remote_actual_branch_readback.stdout', 'remote_actual_branch_readback.stderr', 'local_archive_git_tree_join.stdout', 'local_archive_git_tree_join.stderr', 'fresh_bare_init.stdout', 'fresh_bare_init.stderr', 'fresh_remote_add.stdout', 'fresh_remote_add.stderr', 'set_promisor.stdout', 'set_promisor.stderr', 'set_tree_zero_filter.stdout', 'set_tree_zero_filter.stderr', 'actual_external_commit_only_fetch.stdout', 'actual_external_commit_only_fetch.stderr', 'fetched_head_readback.stdout', 'fetched_head_readback.stderr', 'actual_external_commit_body.stdout', 'actual_external_commit_body.stderr', 'actual_external_selected_blob_fetch.stdout', 'actual_external_selected_blob_fetch.stderr', 'actual_external_archive_blob_return.stdout', 'actual_external_archive_blob_return.stderr']
for name in prior_generated_names:
    path=prior.parent/name
    assert path.is_file() and not path.is_symlink(), 'required actual27 receipt absent: '+name
    names.add(str(path.relative_to(ROOT)))
helper_names=('capture28.py', 'recover28.py', 'select28.py', 'HELPERS_MANIFEST01.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff', 'AUTHOR_CHECK01.json', 'REPORT.md', 'prepare28.py', 'check_source28.py', 'PROSPECTIVE_ROSTER01.json', 'PREPARATION_CHECK01.json')
for name in helper_names:names.add(str((HERE/name).relative_to(ROOT)))
fixed_public_names=['research/onchain-paper-replication-2026-09-24/STATE.md', 'research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md']
for relative in fixed_public_names:
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative
    names.add(relative)
main_source_names=['tradingagents/research/onchain_replication/provenance.py', 'tradingagents/research/onchain_replication/neighborhoods.py', 'tradingagents/research/onchain_replication/imported_mcm_identity.py', 'tradingagents/research/onchain_replication/imported_authority_lease.py', 'tradingagents/research/onchain_replication/original_import_preparation.py']
# No original failed34 scientific/runtime scopes are traversed or admitted.
scopes=[]
# Already returned outcome27 archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
assert prior_receipt['capture']['path']==str((prior.parent/'CAPTURE27.json').relative_to(ROOT))
assert sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256'], 'actual27 capture receipt changed'
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('failed-outcome-increment27.tar','fresh-git-recovered-outcome27.tar','actual_external_archive_blob_return.stdout')}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and not path.is_symlink() and path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256'], relative

# Only actual new or changed bodies; immutable prior recovered entry bodies are reused.
prior_selection=json.loads((prior.parent/'SELECTION27.json').read_bytes())
assert sha(prior.parent/'SELECTION27.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
assert not (HERE/'SELECTION28.json').exists(), 'selection28 already spent'
assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in helper_names for relative in names), 'generated postnative28 products are outside selection'
# Bound actual committed/working Git deltas to this declared finite increment.
allowed_files=set(fixed_public_names+main_source_names)|{str((prior.parent/name).relative_to(ROOT)) for name in prior_generated_names}|{str((HERE/name).relative_to(ROOT)) for name in helper_names}
allowed_roots=[F/name for name in owned]
assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names), 'Git delta outside declared postnative28 scope'
assert set(main_source_names)<=names, 'actual five installed Main changes absent from Git delta'
installation=json.loads((F/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json').read_bytes())
assert sha(F/'pilot34-serializer-postclosure-install01-2026-10-11/INTEGRATION01.json')=='bbab2992398b06cd8a9fd583f95cc973d7944364279ccfb2bffdf0a3f5b9da59', 'accepted serializer receipt changed'
assert not (F/'pilot34-native-owner-qualification03-2026-10-11/attempt01').exists(), 'prospective native03 identity already attempted'
assert len(installation['modules'])==5 and {m['destination']['path'] for m in installation['modules']}==set(main_source_names)
for item in installation['modules']:
    reference=item['destination'];path=ROOT/reference['path']
    assert path.stat().st_size==reference['bytes'] and sha(path)==reference['sha256'], 'installed serializer differs'

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
    'mandatory_public_roots':owned,
    'prior_generated_files':prior_generated_names,
    'actual_scope_states': [{'path':str(scope.relative_to(ROOT)),'exists':scope.exists(),'empty_directories_included':True} for scope in scopes],
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'selection_rule': 'Exact post-outcome27 public receipts, failed native02, compatibility probe, five installed serializers, prospective native03 and caller/review increments. Prior27 archive plus inherited prior26 rows retained by accepted receipt continuity; no original failed34 scope traversal, private/runtime/scientific store replay or deletion authority.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION28.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
