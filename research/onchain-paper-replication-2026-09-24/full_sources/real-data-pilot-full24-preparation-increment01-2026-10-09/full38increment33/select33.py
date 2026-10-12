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
assert HERE == ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full24-preparation-increment01-2026-10-09/full38increment33', 'deploy reviewed copies to exact H/full38increment33 before Root execution'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior = HERE.parent/'full36increment32/FRESH_GIT_RECOVERY32.json'
assert sha(prior)=='8db63835ace586bc84bb93f7ab4a87debab2e2c89ddd34cda61d353b314b3b50', 'actual32 baseline receipt changed'
review=F/'pilot36-increment32-return-release-review-2026-10-11/RETURN_REVIEW01.json'
assert sha(review)=='230a939c4ed35ed09d0fc3dda5ad9328f7920c4686769d6f3e6a852a557ec1f8', 'accepted32 return review changed'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned=['pilot38-target-boundary-coalescing-2026-10-12', 'pilot38-integration-cumulative-review-2026-10-12', 'real-data-pilot-full38-cumulative-preparation01-2026-10-12', 'real-data-pilot-full38-binding-preparation01-2026-10-12', 'pilot-efficiency-integration-2026-10-12', 'pilot38-entry-capacity-investigation-2026-10-12', 'pilot38-observer-ledger-correction-2026-10-12', 'pilot37-optimization-checks-2026-10-12', 'pilot38-admission-coalescing-2026-10-12', 'pilot36-outcome-review-2026-10-12', 'pilot38-public-binding-review-2026-10-12', 'pilot38-entry-policy-correction-2026-10-12', 'real-data-pilot-full38-entry-preparation01-2026-10-12', 'real-data-pilot-full36-entry-preparation01-2026-10-11', 'pilot36-increment32-return-release-review-2026-10-11', 'pilot36-increment32-tools-review-2026-10-11', 'pilot38-increment33-tools-candidate-2026-10-12', 'pilot38-increment33-tools-review-2026-10-12', 'pilot38-entry-registration-review-2026-10-12']
scope_directories=set()
for name in owned:
    root=F/name
    assert root.is_dir() and not root.is_symlink(), 'required final public scope absent: '+name
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():
            names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
closed_scopes=[ROOT/path for path in ['research_runs/eth-paper-real-data-end-to-end-resource-20261011-36', 'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261011-36', 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent/eth-paper-real-data-end-to-end-resource-20261011-36', 'research_artifacts/onchain_representations/4c1d07a983d266df70164d623a20d61a71499c9fec9e9d6a64a1f7ba6b1583e6/eth-paper-real-data-end-to-end-resource-20261011-36']]
for root in closed_scopes:
    assert root.is_dir() and not root.is_symlink(), 'required closed36 owned root absent: '+str(root)
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Exact generated32 receipts/raw operations only. Never traverse historical H.
prior_generated_names=['CAPTURE32.json', 'FINAL_REMOTE_CONFIRMATION32.json', 'FRESH_GIT_RECOVERY32.json', 'GIT_OPERATIONS32.json', 'ROOT_ACTUAL_OPERATIONS32.json', 'ROOT_CAPTURE_OPERATIONS32.json', 'SELECTION32.json', 'actual_external_archive_blob_return.stderr', 'actual_external_archive_blob_return.stdout', 'actual_external_commit_body.stderr', 'actual_external_commit_body.stdout', 'actual_external_commit_only_fetch.stderr', 'actual_external_commit_only_fetch.stdout', 'actual_external_selected_blob_fetch.stderr', 'actual_external_selected_blob_fetch.stdout', 'fetched_head_readback.stderr', 'fetched_head_readback.stdout', 'final_commit32.stderr', 'final_commit32.stdout', 'final_diffcheck32.stderr', 'final_diffcheck32.stdout', 'final_push32.stderr', 'final_push32.stdout', 'final_remote_readback32.stderr', 'final_remote_readback32.stdout', 'fresh_bare_init.stderr', 'fresh_bare_init.stdout', 'fresh_remote_add.stderr', 'fresh_remote_add.stdout', 'local_archive_git_tree_join.stderr', 'local_archive_git_tree_join.stdout', 'local_head.stderr', 'local_head.stdout', 'remote_actual_branch_readback.stderr', 'remote_actual_branch_readback.stdout', 'remote_get_url.stderr', 'remote_get_url.stdout', 'root_commit32.stderr', 'root_commit32.stdout', 'root_diffcheck32.stderr', 'root_diffcheck32.stdout', 'root_push32.stderr', 'root_push32.stdout', 'set_promisor.stderr', 'set_promisor.stdout', 'set_tree_zero_filter.stderr', 'set_tree_zero_filter.stdout']
for name in prior_generated_names:
    path=prior.parent/name
    assert path.is_file() and not path.is_symlink(), 'required actual32 receipt absent: '+name
    names.add(str(path.relative_to(ROOT)))
helper_names=('select33.py', 'capture33.py', 'recover33.py', 'TOOL_SCOPE01.json', 'HELPERS_MANIFEST01.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff')
for name in helper_names:names.add(str((HERE/name).relative_to(ROOT)))
fixed_public_names=['research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md', 'docs/superpowers/plans/2026-10-11-onchain-pilot-efficiency.md', 'research/onchain-paper-replication-2026-09-24/CURRENT_IMPLEMENTATION.md', 'research/onchain-paper-replication-2026-09-24/STATE.md']
for relative in fixed_public_names:
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative
    names.add(relative)
main_source_names=['tradingagents/research/admission.py', 'tradingagents/research/onchain_replication/compact_mcm.py', 'tradingagents/research/onchain_replication/imported_authority_lease.py', 'tradingagents/research/onchain_replication/imported_mcm_identity.py', 'tradingagents/research/onchain_replication/job.py', 'tradingagents/research/onchain_replication/streamed_gat.py', 'tests/research/onchain_replication/test_compact_mcm.py', 'tests/research/test_streamed_gat_lifetime_candidate.py']
# Exact closed36 owned roots above; only the new bound opaque envelope below.
scopes=[ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261012-38-01']
private=ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261012-38-01/archive_transport01.json'
assert private.is_file() and not private.is_symlink()
assert private.stat().st_size==930 and sha(private)=='267cc1d38f13245afdf27fc40fb4333ebbf775857ade36ec6fa3007f95929983', 'exact bound38 opaque bytes changed'
private_relative=str(private.relative_to(ROOT))
names.add(private_relative);scope_directories.add(private.parent)
# Already returned preparation36 archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
assert prior_receipt['capture']['path']==str((prior.parent/'CAPTURE32.json').relative_to(ROOT))
assert sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256'], 'actual32 capture receipt changed'
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('pilot36-preparation-increment32.tar','fresh-git-recovered-full36increment32.tar','actual_external_archive_blob_return.stdout')}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and not path.is_symlink() and path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256'], relative

# Only actual new or changed bodies; immutable prior recovered entry bodies are reused.
prior_selection=json.loads((prior.parent/'SELECTION32.json').read_bytes())
assert sha(prior.parent/'SELECTION32.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
assert not (HERE/'SELECTION33.json').exists(), 'selection33 already spent'
assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in helper_names for relative in names), 'generated full38increment33 products are outside selection'
# Bound actual committed/working Git deltas to this declared finite increment.
allowed_files={private_relative}|set(fixed_public_names+main_source_names)|{str((prior.parent/name).relative_to(ROOT)) for name in prior_generated_names}|{str((HERE/name).relative_to(ROOT)) for name in helper_names}
allowed_roots=[F/name for name in owned]+closed_scopes
assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names), 'Git delta outside declared full38increment33 scope'
main_source_pins={'tradingagents/research/admission.py': '793c4034d23ff4e486e2a888004b1dc69a11383c4d4460f01d1489fd5794f7a7', 'tradingagents/research/onchain_replication/compact_mcm.py': '806f1ebeb4e262f1cc0a7945e2717d538e68b3b1f45452c449cf0c42b7d49942', 'tradingagents/research/onchain_replication/imported_authority_lease.py': 'ea25f774d4165e460824eaee0425bb6d860825fb7e97784360bb914f5fada741', 'tradingagents/research/onchain_replication/imported_mcm_identity.py': '15d45478fc33602763b65acebd20f571e8fcbd1fd7b40e3aba05c9a900da1ccf', 'tradingagents/research/onchain_replication/job.py': '2f842fd6d0bcc8599a92bc89e088406df90f6c0cad171b7e2d0383d0832cab34', 'tradingagents/research/onchain_replication/streamed_gat.py': '7eb9c982b80d3a1e1801c4df8bc862fb02025016feae3e805e184506a08eacf1', 'tests/research/onchain_replication/test_compact_mcm.py': 'd3073795c7b1bbf04a111b6356ca1168eb15abe3daa0cae0b77145545547c6c6', 'tests/research/test_streamed_gat_lifetime_candidate.py': '11e758ea9f1f1e3b3b550f5e718d4142abdb5bb9b86894103e53c9df2e4469a5'}
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
    assert not relative.startswith(('research_artifacts/', 'research_runs/')) or relative==private_relative or any(path.is_relative_to(root) for root in closed_scopes), relative
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
    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],
    'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt'],
    'mandatory_public_roots':owned,
    'prior_generated_files':prior_generated_names,
    'actual_scope_states': [{'path':str(path.relative_to(ROOT)), 'exists':True,'qualification':'Exact closed36 owned root or sole new38 opaque envelope parent; no sibling historical store or referenced connection target.'} for path in closed_scopes+scopes],
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'selection_rule': 'Finite new12Oct efficiency, closed36 outcome and38 preparation bodies, exact changed source/tests, public/binding/entry/amendment reviews and actual32 postcapture receipts. Only the newly bound opaque dispatch envelope is selected from private runtime; its referenced connection path is never read. Prior typed bodies reused through actual32 recovery. No historical raw-store traversal, credential-body access or deletion authority.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION33.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
