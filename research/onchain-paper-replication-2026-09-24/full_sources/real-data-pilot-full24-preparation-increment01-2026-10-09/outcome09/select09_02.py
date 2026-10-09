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


prior = HERE.parent/'full26increment08/recovery02/FRESH_GIT_RECOVERY08.json'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned = ['real-data-pilot-full26-root-closure01-2026-10-09', 'real-data-pilot-full26-outcome-review01-2026-10-09', 'pilot-preparation-callpath-investigation01-2026-10-09', 'pilot-preparation-eager-sweep-removal01-2026-10-09', 'pilot-preparation-eager-sweep-removal-review01-2026-10-09', 'pilot-first-batch-preparation-callpath01-2026-10-09', 'array-neighborhood-sparse-selection01-2026-10-09', 'array-neighborhood-sparse-selection-review01-2026-10-09', 'array-neighborhood-sparse-benchmark01-2026-10-09', 'pilot-batched-authority-poll-fix01-2026-10-09', 'pilot-batched-authority-poll-review01-2026-10-09']
for name in owned:
    for path in (F/name).rglob('*'):
        if path.is_file():
            names.add(str(path.relative_to(ROOT)))
for name in ('capture09.py', 'recover09.py', 'select09.py', 'select09_02.py', 'TOOLS_REVIEW09.json', 'TOOLS_REVIEW09_02.json'):
    names.add(str((HERE/name).relative_to(ROOT)))
# Exact current failed attempt and Root observations; no private runtime/history replay.
N='eth-paper-real-data-end-to-end-resource-20261009-26'
scopes=[ROOT/'research_runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/N, ROOT/'research_artifacts/onchain_representations/ccea3f67e8da09a42a57dca672b9426c4f437c63f2fbc50aa6efbf79c022f1e3'/N, ROOT/'research_artifacts/onchain_compact_mcm/ccea3f67e8da09a42a57dca672b9426c4f437c63f2fbc50aa6efbf79c022f1e3'/N, ROOT/'research_artifacts/onchain_batched_offload/80b7bd11452bc082a48fcde522aaec5269abe5325fe06040695ed2336dfcd0c8']
scope_directories=set()
for scope in scopes:
    if scope.exists():
        assert scope.is_dir() and not scope.is_symlink(), str(scope)
        scope_directories.add(scope)
    for path in scope.rglob('*'):
        if path.is_file() or path.is_symlink(): names.add(str(path.relative_to(ROOT)))
        elif path.is_dir(): scope_directories.add(path)
entry=F/'real-data-pilot-full26-entry01-2026-10-09'
for leaf in ('launch-attempt01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','RESOURCE_OBSERVATION01.json','RESOURCE_OBSERVATION02.json','RESOURCE_OBSERVATION03.json','PHASE_OBSERVATION01.json','PHASE_OBSERVATION02.json','PID_ROLE_CORRECTION01.json','LIVE_CHECK01.json','LIVE_CHECK01.stdout','LIVE_CHECK01.stderr'):
    path=entry/leaf
    assert path.is_file(), str(path)
    names.add(str(path.relative_to(ROOT)))
# Already returned preparation archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and sha(path)==prior_receipt['returned_archive']['sha256'], relative

names = sorted(names-excluded)
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
    'selection_rule': 'Actual tracked public body delta since verified actual full26 preparation recovery91bd4bee plus the narrowly adapted preservation tools. Owned new source candidates/reviews, corrected Root telemetry and all five existing failed26 stores plus the absent offload namespace are declared; no historical store replay; unchanged stores and private bodies excluded. Duplicate recovered archive/stdout bodies remain immutable at original paths and the previously verified remote blob; only their new metadata/verification receipts enter this delta.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION09.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
