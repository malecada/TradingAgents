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


prior = HERE.parent/'full28increment12/FRESH_GIT_RECOVERY12.json'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned = ['real-data-pilot-full28-entry01-2026-10-09', 'real-data-pilot-full28-first-batch-review01-2026-10-09', 'real-data-pilot-full28-later-batches-review01-2026-10-09', 'real-data-pilot-full28-outcome-review01-2026-10-09', 'real-data-pilot-full28-group-fresh-return01-2026-10-09', 'pilot-grouped-offload-lease-poll01-2026-10-09', 'pilot-grouped-offload-lease-poll-review01-2026-10-09', 'pilot-full28-to-successor-root-integration01-2026-10-09', 'pilot-full28-outcome-increment-tools-review01-2026-10-09', 'matching-acceleration-candidates-combined-review01-2026-10-09', 'matching-acceleration-candidates-combined-review02-2026-10-09', 'matching-adaptive-edge-cache-connected-review01-2026-10-09', 'matching-adaptive-edge-cache-connected01-2026-10-09', 'matching-adaptive-edge-cache-review01-2026-10-09', 'matching-adaptive-edge-cache01-2026-10-09', 'matching-adaptive-measurement-stack-review01-2026-10-09', 'matching-adaptive-measurement-stack-review02-2026-10-09', 'matching-adaptive-measurement-stack01-2026-10-09', 'matching-adaptive-measurement-stack02-2026-10-09', 'matching-batched-small-pair-prototype01-2026-10-09', 'matching-batched-small-pair-prototype02-2026-10-09', 'matching-compiled-small-pair-prototype-review01-2026-10-09', 'matching-compiled-small-pair-prototype01-2026-10-09', 'matching-compiled-small-pair-prototype02-2026-10-09', 'matching-compiled-small-pair-prototype02-review01-2026-10-09', 'matching-compiled-small-pair-prototype03-2026-10-09', 'matching-compiled-small-pair-prototype04-2026-10-09', 'matching-real-geometry-instrumentation-review01-2026-10-09', 'matching-real-geometry-instrumentation01-2026-10-09', 'matching-real-geometry-publication-review01-2026-10-09', 'matching-real-geometry-publication01-2026-10-09', 'pilot-binding-lease-timing-publication-review01-2026-10-09', 'pilot-binding-lease-timing-publication01-2026-10-09', 'pilot-binding-lease-timing01-2026-10-09', 'pilot-coordination-consolidation02-2026-10-09', 'pilot-immutable-target-metadata01-2026-10-09']
for name in owned:
    for path in (F/name).rglob('*'):
        if path.is_file():
            names.add(str(path.relative_to(ROOT)))
for name in ('capture13.py', 'recover13.py', 'select13.py'):
    names.add(str((HERE/name).relative_to(ROOT)))
# Exact current failed attempt and Root observations; no private runtime/history replay.
N='eth-paper-real-data-end-to-end-resource-20261009-28'
scopes=[ROOT/'research_runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/N, ROOT/'research_artifacts/onchain_representations/4d8349713a3f764fe931f0dda2330c5b7de5560f291241fdd8043a75ca4f4401'/N, ROOT/'research_artifacts/onchain_compact_mcm/4d8349713a3f764fe931f0dda2330c5b7de5560f291241fdd8043a75ca4f4401'/N, ROOT/'research_artifacts/onchain_batched_offload/223798d84810b5f0f49aa89b17b35db96c6ddbcc7c86948472e81ec49573e5d6', ROOT/'research_artifacts/archive-dispatch-ethpilot-20261009-28']
scope_directories=set()
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
prior_selection=json.loads((prior.parent/'SELECTION12.json').read_bytes())
assert sha(prior.parent/'SELECTION12.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
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
    'selection_rule': 'Actual public delta since freshly returned full28 preparation12 plus original terminal28 seven store scopes, Root returned original group archive and all explicitly owned postclaim functional candidate/review directories. Only changed bodies; predecessor regular rows reused by exact type/mode/size/hash. No unchanged historical raw replay/private dispatch/runtime package bodies. Retain failed28 and partial65536 journal/61440 confirmed post_sink without wholeMCM or training credit',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION13.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
