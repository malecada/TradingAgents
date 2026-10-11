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


prior = HERE.parent/'full35increment30/FRESH_GIT_RECOVERY30.json'
assert sha(prior)=='32023dba761dbdcfc0fccd9bb9749a5320bdd345efa26a22411ca58be0f15d62', 'actual30 baseline receipt changed'
review=F/'pilot35-preparation-increment-return-review01-2026-10-11/REVIEW01.json'
assert sha(review)=='170c85ab7eb08000467d7eeec098e1feb153ce8675b687d99f959728767dfbed', 'accepted30 return review changed'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned=['pilot-efficiency-implementation-2026-10-11', 'pilot-efficiency-admission-timing-review-2026-10-11', 'pilot-efficiency-authority-profile-2026-10-11', 'pilot-efficiency-backend-caller-2026-10-11', 'pilot-efficiency-bottleneck-model-2026-10-11', 'pilot-efficiency-error-retention-2026-10-11', 'pilot-efficiency-expected-code-review-2026-10-11', 'pilot-efficiency-numeric-kernel-2026-10-11', 'pilot-efficiency-storage-scan-2026-10-11', 'authority-expected-code-cache-candidate02-2026-10-11', 'implementation-audit-performance-2026-10-11', 'implementation-audit-science-data-2026-10-11', 'implementation-audit-runtime-storage-2026-10-11', 'pilot35-stale-boundary-investigation01-2026-10-11', 'pilot35-terminal-outcome-review-2026-10-11', 'real-data-pilot-full35-entry-preparation01-2026-10-11', 'pilot35-efficiency-increment31-tools-review-2026-10-11', 'pilot35-preparation-increment-return-review01-2026-10-11']
scope_directories=set()
for name in owned:
    root=F/name
    assert root.is_dir() and not root.is_symlink(), 'required final public scope absent: '+name
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():
            names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Exact generated30 receipts/raw operations only. Never traverse historical H.
prior_generated_names=['SELECTION30.json', 'CAPTURE30.json', 'FRESH_GIT_RECOVERY30.json', 'GIT_OPERATIONS30.json', 'ROOT_ACTUAL_OPERATIONS30.json', 'root_commit30.stdout', 'root_commit30.stderr', 'local_head.stdout', 'local_head.stderr', 'remote_get_url.stdout', 'remote_get_url.stderr', 'remote_actual_branch_readback.stdout', 'remote_actual_branch_readback.stderr', 'local_archive_git_tree_join.stdout', 'local_archive_git_tree_join.stderr', 'fresh_bare_init.stdout', 'fresh_bare_init.stderr', 'fresh_remote_add.stdout', 'fresh_remote_add.stderr', 'set_promisor.stdout', 'set_promisor.stderr', 'set_tree_zero_filter.stdout', 'set_tree_zero_filter.stderr', 'actual_external_commit_only_fetch.stdout', 'actual_external_commit_only_fetch.stderr', 'fetched_head_readback.stdout', 'fetched_head_readback.stderr', 'actual_external_commit_body.stdout', 'actual_external_commit_body.stderr', 'actual_external_selected_blob_fetch.stdout', 'actual_external_selected_blob_fetch.stderr', 'actual_external_archive_blob_return.stdout', 'actual_external_archive_blob_return.stderr']
for name in prior_generated_names:
    path=prior.parent/name
    assert path.is_file() and not path.is_symlink(), 'required actual30 receipt absent: '+name
    names.add(str(path.relative_to(ROOT)))
helper_names=('select31.py', 'capture31.py', 'recover31.py', 'prepare31.py', 'check_source31.py', 'CAPTURE_RECOVERY_LITERAL_MAP01.json', 'HELPERS_MANIFEST01.json', 'AUTHOR_CHECK01.json', 'PROSPECTIVE_ROSTER01.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff', 'REPORT.md')
for name in helper_names:names.add(str((HERE/name).relative_to(ROOT)))
fixed_public_names=['research/onchain-paper-replication-2026-09-24/STATE.md', 'research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md', 'research/onchain-paper-replication-2026-09-24/IMPLEMENTATION_REVIEW_2026-10-11.md', 'docs/superpowers/plans/2026-10-11-onchain-pilot-efficiency.md']
for relative in fixed_public_names:
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative
    names.add(relative)
main_source_names=['tests/research/onchain_replication/test_backend_entry_bundle.py', 'tests/research/onchain_replication/test_backend_input_selection.py', 'tests/research/onchain_replication/test_numeric_kernel_contract.py', 'tests/research/onchain_replication/test_phase_timing.py', 'tests/research/onchain_replication/test_pilot_storage_single_pass.py', 'tests/research/onchain_replication/test_real_pilot_phase_profile.py', 'tests/research/onchain_replication/test_training_failure_retention.py', 'tests/research/onchain_replication/test_workflow_storage_guard.py', 'tradingagents/research/lifecycle.py', 'tradingagents/research/onchain_replication/batched_numeric_execution.py', 'tradingagents/research/onchain_replication/batched_numeric_reuse.py', 'tradingagents/research/onchain_replication/compact_mcm_batched.py', 'tradingagents/research/onchain_replication/evaluation.py', 'tradingagents/research/onchain_replication/failure_reporting.py', 'tradingagents/research/onchain_replication/grouped_offload.py', 'tradingagents/research/onchain_replication/imported_authority_lease.py', 'tradingagents/research/onchain_replication/matching_numeric_kernel.py', 'tradingagents/research/onchain_replication/original_dictionary.py', 'tradingagents/research/onchain_replication/phase_timing.py', 'tradingagents/research/onchain_replication/real_pilot_import_caller.py', 'tradingagents/research/onchain_replication/real_pilot_storage.py', 'tradingagents/research/onchain_replication/training.py', 'tradingagents/research/onchain_replication/workflow_storage.py']
# Exact original35 scope from independently accepted terminal metadata.
terminal_review=F/'pilot35-terminal-outcome-review-2026-10-11/REVIEW01.json'
assert sha(terminal_review)=='7224646b35c3fe8094c19288ad81be7c1650be458b7a3723198e82bc1a86aba4'
raw_scope_states=[{'empty_directories_required': True, 'exists': True, 'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261011-35'}, {'empty_directories_required': True, 'exists': True, 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261011-35'}, {'empty_directories_required': True, 'exists': True, 'path': 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent/eth-paper-real-data-end-to-end-resource-20261011-35'}, {'empty_directories_required': True, 'exists': True, 'path': 'research_artifacts/onchain_representations/fc3ffe1ecb66f7f7ea20dd78b8a5e6e531c596c227344d3555fc72b257b4c5ab/eth-paper-real-data-end-to-end-resource-20261011-35'}, {'empty_directories_required': True, 'exists': True, 'path': 'research_artifacts/archive-dispatch-ethpilot-20261011-35'}, {'empty_directories_required': True, 'exists': False, 'path': 'research_artifacts/onchain_compact_mcm/fc3ffe1ecb66f7f7ea20dd78b8a5e6e531c596c227344d3555fc72b257b4c5ab/eth-paper-real-data-end-to-end-resource-20261011-35'}]
assert json.loads(terminal_review.read_bytes())['incremental_raw_scopes']==raw_scope_states
scopes=[]
for row in raw_scope_states:
    root=ROOT/row['path']
    if not row['exists']:
        assert not root.exists() and not root.is_symlink(), 'originally absent sixth scope appeared: '+row['path']
        continue
    assert root.is_dir() and not root.is_symlink() and root.resolve(strict=True)==root, row['path']
    scopes.append(root);scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Source snapshot is the engineering body roster, not original pilot35 source.
snapshot=F/'pilot-efficiency-implementation-2026-10-11/SOURCE_SNAPSHOT01.json'
assert sha(snapshot)=='a871be53c02a690cb286c5a85bc5fa626f9153529d731224a74d0518ce807d79', 'reviewed engineering snapshot changed'
# Already returned preparation30 archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
assert prior_receipt['capture']['path']==str((prior.parent/'CAPTURE30.json').relative_to(ROOT))
assert sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256'], 'actual30 capture receipt changed'
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('full35-preparation-increment30.tar','fresh-git-recovered-full35increment30.tar','actual_external_archive_blob_return.stdout')}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and not path.is_symlink() and path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256'], relative

# Only actual new or changed bodies; immutable prior recovered entry bodies are reused.
prior_selection=json.loads((prior.parent/'SELECTION30.json').read_bytes())
assert sha(prior.parent/'SELECTION30.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
assert not (HERE/'SELECTION31.json').exists(), 'selection31 already spent'
assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in helper_names for relative in names), 'generated full35outcome31 products are outside selection'
# Bound actual committed/working Git deltas to this declared finite increment.
allowed_files=set(fixed_public_names+main_source_names)|{str((prior.parent/name).relative_to(ROOT)) for name in prior_generated_names}|{str((HERE/name).relative_to(ROOT)) for name in helper_names}
allowed_roots=[F/name for name in owned]+scopes
assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names), 'Git delta outside declared full35outcome31 scope'
main_source_pins={'tests/research/onchain_replication/test_backend_entry_bundle.py': '4c21a52461b8b9d0a410bf29bf9dad28a732a0ad04b90c96693ff36e49d48409', 'tests/research/onchain_replication/test_backend_input_selection.py': '439f91f95d1e6a6e4eba2d088fd240b0e23cccfb457913c71f6c47fb6b4bfdaa', 'tests/research/onchain_replication/test_numeric_kernel_contract.py': '95f7dcf94fd8d7f506bb22872db2242e1a5d331f4cbf50f50e7c42ef3569c3b1', 'tests/research/onchain_replication/test_phase_timing.py': 'e9c180473a77c9ecb040f65d963fec23a5c8e748b569dc74e0e9dfc0c63b75d4', 'tests/research/onchain_replication/test_pilot_storage_single_pass.py': '61633f96e1aa34c07a06e5c9d5a703a77c6df14ac7edb216bec25e90d3b9bdc6', 'tests/research/onchain_replication/test_real_pilot_phase_profile.py': 'b33c3c21c2c5b3d7cf115ad80c4d4d2fa4ea108af81034f33a8ae67bd9da077e', 'tests/research/onchain_replication/test_training_failure_retention.py': '4586b8c9b4014f700696726e2b187719c6ad8f6d35bce908785124f12d471052', 'tests/research/onchain_replication/test_workflow_storage_guard.py': '1e13749b0e696d9d02c2547284f3e114d5960a874473360f592d77476a6d796f', 'tradingagents/research/lifecycle.py': 'e45e53661e212d55da56565372c6ff2cada93f002160f555966523cb6eee40d3', 'tradingagents/research/onchain_replication/batched_numeric_execution.py': 'a897ec57934ed2059ac1e4c706dfd7012aa0c1087977600928f46075f40cef3b', 'tradingagents/research/onchain_replication/batched_numeric_reuse.py': 'be98fdd022140325c8b3c5a59c957780a5837c43693effacb9f239cb446b436d', 'tradingagents/research/onchain_replication/compact_mcm_batched.py': '4cd753b29068aead097b609319d3165612108d597d1774f0a433664268f964c7', 'tradingagents/research/onchain_replication/evaluation.py': 'b002b7bbff472b520581e24e480e8339d8711c4c710e2fbcd47678bf5138e7d3', 'tradingagents/research/onchain_replication/failure_reporting.py': '9518a12cda242a284fdebe74a9c35b28ae010c8c782d31c32b4861a5edcb7b8a', 'tradingagents/research/onchain_replication/grouped_offload.py': 'e11ca240b89ab611c521f68adda38322ff191d17e11f6c64387b230b3708aed2', 'tradingagents/research/onchain_replication/imported_authority_lease.py': 'e6f115620ffe7f8ef1252fe83984c14adef5e98ba2269e3f52d6797129c22c67', 'tradingagents/research/onchain_replication/matching_numeric_kernel.py': 'd98da7cc1078362582d5e2fc8e7c8a7b89408d37d1fdabb3d6b63eabeca494cd', 'tradingagents/research/onchain_replication/original_dictionary.py': 'cdc4c753645859312cc9ef439d44c2d45f9f92e90dfa7c51d089e070fb85e0b1', 'tradingagents/research/onchain_replication/phase_timing.py': '97a6c5041914f27bae4b9fcbd81b6cf6bb0cdc90ae5315859c8df52794b1367f', 'tradingagents/research/onchain_replication/real_pilot_import_caller.py': 'f97c8960c0cf4c018b59af4fa93eaa2cee0875c65fb5129d0ccf9fbd4d8d751e', 'tradingagents/research/onchain_replication/real_pilot_storage.py': '5a1597a2b28895d7bd1cba5eaf375a54bc77d169a7a500a2ee02d10b7c30a078', 'tradingagents/research/onchain_replication/training.py': 'f413aeb89d72de563640b8b5fdb2bdf1159729d18f8d1de2a74733a116c3def0', 'tradingagents/research/onchain_replication/workflow_storage.py': 'c52806aec23ebc52661b02f76868919d00cf6c646e1b311e985f6ddbdec1dc6c'}
for relative,expected in main_source_pins.items():
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink() and sha(ROOT/relative)==expected, relative
    names.add(relative)

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
    'baseline_accepted_review': {'path':str(review.relative_to(ROOT)), 'sha256':sha(review)},
    'terminal_review': {'path':str(terminal_review.relative_to(ROOT)), 'sha256':sha(terminal_review)},
    'engineering_source_snapshot': {'path':str(snapshot.relative_to(ROOT)), 'sha256':sha(snapshot)},
    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],
    'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt'],
    'mandatory_public_roots':owned,
    'prior_generated_files':prior_generated_names,
    'actual_scope_states': raw_scope_states,
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'selection_rule': 'Finite failed35 five original raw scopes as opaque bodies, sixth absent; exact23 reviewed engineering source/tests, named docs/public evidence and actual30 postcapture receipts. Prior rows reused only on exact typed body match; inherited coverage retained through authenticated actual30 receipt. No private runtime, unrelated historical raw traversal or deletion authority.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION31.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
