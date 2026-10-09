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


prior = HERE.parent/'full25increment06/FRESH_GIT_RECOVERY06.json'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned = ['real-data-pilot-full25-root-closure01-2026-10-09', 'real-data-pilot-full25-outcome-review01-2026-10-09', 'pilot-admission-dedup-source01-2026-10-09','pilot-admission-dedup-review01-2026-10-09','pilot-admission-dedup-root-install01-2026-10-09']
for name in owned:
    for path in (F/name).rglob('*'):
        if path.is_file():
            names.add(str(path.relative_to(ROOT)))
for name in ('capture07.py', 'recover07.py', 'select07.py', 'TOOLS_REVIEW07.json'):
    names.add(str((HERE/name).relative_to(ROOT)))
# Exact current failed attempt and Root observations; no private runtime/history replay.
N='eth-paper-real-data-end-to-end-resource-20261009-25'
scopes=[ROOT/'research_runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/N, ROOT/'research_artifacts/onchain_representations/eaa4af06c76fe2276b9f0cedb6a361613a7db9c585d03ed8a157b0b972aadd47'/N]
for scope in scopes:
    for path in scope.rglob('*'):
        if path.is_file() or path.is_symlink(): names.add(str(path.relative_to(ROOT)))
entry=F/'real-data-pilot-full25-entry01-2026-10-09'
for leaf in ('launch-attempt01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','RESOURCE_OBSERVATION01.json','RESOURCE_OBSERVATION02.json','RESOURCE_OBSERVATION03.json','PHASE_OBSERVATION01.json','PHASE_OBSERVATION02.json','LIVE_CHECK01.json','LIVE_CHECK01.stdout','LIVE_CHECK01.stderr'):
    path=entry/leaf
    assert path.is_file(), str(path)
    names.add(str(path.relative_to(ROOT)))
# Already returned preparation archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
excluded={str((HERE.parent/'full25increment06'/name).relative_to(ROOT))
          for name in ('fresh-git-recovered-release06.tar','actual_external_archive_blob_return.stdout')}
names = sorted(names-excluded)
rows = []
directories = set()
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
    'selection_rule': 'Actual tracked public body delta since verified actual full25 preparation recoverybbf426db plus the narrowly adapted preservation tools. No full-directory replay; unchanged stores and private bodies excluded. Duplicate recovered archive/stdout bodies remain immutable at original paths and the previously verified remote blob; only their new metadata/verification receipts enter this delta.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION07.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
