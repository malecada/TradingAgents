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


prior = HERE.parent/'full35outcome31/FRESH_GIT_RECOVERY31.json'
assert sha(prior)=='527f22e70b79a040928a56dea2d7dbccb127ef1d9cc615fe042a67780a889083', 'actual31 baseline receipt changed'
review=F/'pilot35-efficiency-increment31-return-review-2026-10-11/REPORT01.md'
assert sha(review)=='9c41681cf63bb49df02873061f11bf245dab4ad6e440cb7532e9bc887d296100', 'accepted31 return review changed'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned=['pilot-efficiency-continuation-2026-10-11', 'pilot-efficiency-entry-qualification-2026-10-11', 'pilot-efficiency-entry-qualification-review-2026-10-11', 'pilot-efficiency-fixture-fix-2026-10-11', 'pilot-efficiency-integration-2026-10-11', 'pilot-efficiency-integration-review-2026-10-11', 'pilot-efficiency-solver-qualification-2026-10-11', 'pilot35-efficiency-increment31-return-review-2026-10-11', 'pilot36-entry-integration-review-2026-10-11', 'pilot36-public-cumulative-review-2026-10-11', 'real-data-pilot-full36-binding-preparation01-2026-10-11', 'real-data-pilot-full36-cumulative-preparation01-2026-10-11', 'real-data-pilot-full36-entry-preparation01-2026-10-11']
scope_directories=set()
for name in owned:
    root=F/name
    assert root.is_dir() and not root.is_symlink(), 'required final public scope absent: '+name
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():
            names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Exact generated31 receipts/raw operations only. Never traverse historical H.
prior_generated_names=['SELECTION31.json', 'CAPTURE31.json', 'FRESH_GIT_RECOVERY31.json', 'GIT_OPERATIONS31.json', 'ROOT_ACTUAL_OPERATIONS31.json', 'root_commit31.stdout', 'root_commit31.stderr', 'root_push31.stdout', 'root_push31.stderr', 'local_head.stdout', 'local_head.stderr', 'remote_get_url.stdout', 'remote_get_url.stderr', 'remote_actual_branch_readback.stdout', 'remote_actual_branch_readback.stderr', 'local_archive_git_tree_join.stdout', 'local_archive_git_tree_join.stderr', 'fresh_bare_init.stdout', 'fresh_bare_init.stderr', 'fresh_remote_add.stdout', 'fresh_remote_add.stderr', 'set_promisor.stdout', 'set_promisor.stderr', 'set_tree_zero_filter.stdout', 'set_tree_zero_filter.stderr', 'actual_external_commit_only_fetch.stdout', 'actual_external_commit_only_fetch.stderr', 'fetched_head_readback.stdout', 'fetched_head_readback.stderr', 'actual_external_commit_body.stdout', 'actual_external_commit_body.stderr', 'actual_external_selected_blob_fetch.stdout', 'actual_external_selected_blob_fetch.stderr', 'actual_external_archive_blob_return.stdout', 'actual_external_archive_blob_return.stderr']
for name in prior_generated_names:
    path=prior.parent/name
    assert path.is_file() and not path.is_symlink(), 'required actual31 receipt absent: '+name
    names.add(str(path.relative_to(ROOT)))
helper_names=('select32.py', 'capture32.py', 'recover32.py', 'TOOL_SCOPE01.json', 'HELPERS_MANIFEST01.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff')
for name in helper_names:names.add(str((HERE/name).relative_to(ROOT)))
fixed_public_names=['research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md', 'docs/superpowers/plans/2026-10-11-onchain-pilot-efficiency.md', 'research/onchain-paper-replication-2026-09-24/CURRENT_IMPLEMENTATION.md', 'research/onchain-paper-replication-2026-09-24/STATE.md']
for relative in fixed_public_names:
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative
    names.add(relative)
main_source_names=['tests/research/onchain_replication/test_archive_producer_integration.py', 'tests/research/onchain_replication/test_batched_continuation.py', 'tests/research/onchain_replication/test_entry_preparation_stop.py', 'tests/research/onchain_replication/test_matching_numeric_policy.py', 'tests/research/onchain_replication/test_phase_timing.py', 'tests/research/onchain_replication/test_pilot_efficiency_selection.py', 'tradingagents/research/onchain_replication/batched_continuation.py', 'tradingagents/research/onchain_replication/batched_driver.py', 'tradingagents/research/onchain_replication/batched_journal.py', 'tradingagents/research/onchain_replication/batched_numeric_execution.py', 'tradingagents/research/onchain_replication/batched_numeric_reuse.py', 'tradingagents/research/onchain_replication/batched_pair_executor.py', 'tradingagents/research/onchain_replication/compact_mcm_batched.py', 'tradingagents/research/onchain_replication/imported_authority_lease.py', 'tradingagents/research/onchain_replication/matching_annealing.py', 'tradingagents/research/onchain_replication/matching_immutable_session.py', 'tradingagents/research/onchain_replication/matching_numeric_policy.py', 'tradingagents/research/onchain_replication/phase_timing.py', 'tradingagents/research/onchain_replication/real_pilot_import_caller.py']
# No historical raw scopes are traversed; only the new bound opaque envelope.
scopes=[ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261011-36-01']
private=ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261011-36-01/archive_transport01.json'
assert private.is_file() and not private.is_symlink()
names.add(str(private.relative_to(ROOT)));scope_directories.add(private.parent)
# Already returned failed35 archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
assert prior_receipt['capture']['path']==str((prior.parent/'CAPTURE31.json').relative_to(ROOT))
assert sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256'], 'actual31 capture receipt changed'
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('failed35-outcome-increment31.tar','fresh-git-recovered-full35outcome31.tar','actual_external_archive_blob_return.stdout')}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and not path.is_symlink() and path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256'], relative

# Only actual new or changed bodies; immutable prior recovered entry bodies are reused.
prior_selection=json.loads((prior.parent/'SELECTION31.json').read_bytes())
assert sha(prior.parent/'SELECTION31.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
assert not (HERE/'SELECTION32.json').exists(), 'selection32 already spent'
assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in helper_names for relative in names), 'generated full36increment32 products are outside selection'
# Bound actual committed/working Git deltas to this declared finite increment.
allowed_files=set(fixed_public_names+main_source_names)|{str((prior.parent/name).relative_to(ROOT)) for name in prior_generated_names}|{str((HERE/name).relative_to(ROOT)) for name in helper_names}
allowed_roots=[F/name for name in owned]+scopes
assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names), 'Git delta outside declared full36increment32 scope'
main_source_pins={'tests/research/onchain_replication/test_archive_producer_integration.py': '1c60955988e2689df3492bed7be3b413265aed3da60ecbb2fd5c683d88b768eb', 'tests/research/onchain_replication/test_batched_continuation.py': 'e2acc34138370117b77e73a637b294884b2b4f1d3e922969766f59dd298d341d', 'tests/research/onchain_replication/test_entry_preparation_stop.py': '88e4584a59420001f5731c446b174c9f190a961d0b2707dc0c65e8e17e993ffb', 'tests/research/onchain_replication/test_matching_numeric_policy.py': '7b5437ba86a7f186ab8edb0c456b95d857be8d8f58c9908a4dc0a66b04b2d49d', 'tests/research/onchain_replication/test_phase_timing.py': '1c436c800fcf09df4b07832bb2524aa0dd7be61c35fe8cdb369658d666c5bcd4', 'tests/research/onchain_replication/test_pilot_efficiency_selection.py': '3f660cfd8e3d1b24554a9bebd94e1b300a861ed1ce7771f5d9ebe9abfaf5ccfc', 'tradingagents/research/onchain_replication/batched_continuation.py': '1accf714c9853766f9ffa48c1191fe0706d4b397599c14b7aa8d302cc09d331b', 'tradingagents/research/onchain_replication/batched_driver.py': 'f8fe3e83d4d7d55e477cc054659dd8335034f872ce7ab589573ad6cd3ee53335', 'tradingagents/research/onchain_replication/batched_journal.py': 'a550157d767f0c78dfdfdefa6fe5e46ec037e4cc2c885d9f23d330c1400b5678', 'tradingagents/research/onchain_replication/batched_numeric_execution.py': '6284a216957b50e4b5a9f0ca0640f88ef8d9e719b235d089903429b1b8a76916', 'tradingagents/research/onchain_replication/batched_numeric_reuse.py': '1362725cdf967cd4f324e0c5e410fee1971ff07610c3d2b5efb5978e96469586', 'tradingagents/research/onchain_replication/batched_pair_executor.py': '0d1c7a14866b53e6bde4b9db6e3eff4740190d16bc3db0f6532d60afd3142005', 'tradingagents/research/onchain_replication/compact_mcm_batched.py': 'dc14816d304dde383b7a10dd55558fe72d95e5c1da870a721ab512126943bae6', 'tradingagents/research/onchain_replication/imported_authority_lease.py': '926a1af06037746b095bd89faa161f74ad5e47af4512e033596a0858fd073896', 'tradingagents/research/onchain_replication/matching_annealing.py': '1f8e45c4997691d561b498467ea2cbac284fc2e0747b495e81bf97ff189146bf', 'tradingagents/research/onchain_replication/matching_immutable_session.py': 'f5adccc5fcff36ec68892f775cac7d7569ed36338cfd79d049448278ad7c2eb4', 'tradingagents/research/onchain_replication/matching_numeric_policy.py': 'cd3000fc02d126026b1ba3e6fbe779e92b1fcd516abfbcbf563ccf3479b02b03', 'tradingagents/research/onchain_replication/phase_timing.py': 'a15fd9ef808252fda0cc386e6b0f862312c56aa92a51c45b4f4e614d94a9f61a', 'tradingagents/research/onchain_replication/real_pilot_import_caller.py': '02ca18cd68375a07a6176081309469277f7b74be285a3b29d93af2fd052206ae'}
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
    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],
    'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt'],
    'mandatory_public_roots':owned,
    'prior_generated_files':prior_generated_names,
    'actual_scope_states': [{'path':str(scopes[0].relative_to(ROOT)), 'exists':True,'qualification':'One new bound opaque envelope only; no connection reference target, credential body or historical store is read.'}],
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'selection_rule': 'Finite new efficiency and36 preparation bodies, exact changed source/tests, public/binding/entry/amendment reviews and actual31 postcapture receipts. Only the newly bound opaque dispatch envelope is selected from private runtime; its referenced connection path is never read. Prior typed bodies reused through actual31 recovery. No historical raw-store traversal, credential-body access or deletion authority.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION32.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
