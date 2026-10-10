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

ALIAS_MEMBERS = {'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-body.bin': {'bytes': 14, 'device': 66310, 'inode': 7865445, 'mode': '0664', 'nlink': 2, 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-body.bin', 'sha256': '881ae31e592d550b22be2352b13010241c0598cf2b8fffec8bfd9da0cb6a806e'}, 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-hardlink': {'bytes': 14, 'device': 66310, 'inode': 7865445, 'mode': '0664', 'nlink': 2, 'path': 'research/onchain-paper-replication-2026-09-24/full_sources/matching-compiled-normalization-connected-review01-2026-10-10/reference-hardlink', 'sha256': '881ae31e592d550b22be2352b13010241c0598cf2b8fffec8bfd9da0cb6a806e'}}

def alias_signature(info):
    return (info.st_dev,info.st_ino,info.st_nlink,info.st_size,stat.S_IMODE(info.st_mode),stat.S_ISREG(info.st_mode))

def authenticate_alias_pair(root):
    # Exact historical fixture only; no general hardlink admission.
    before={}
    for name,metadata in ALIAS_MEMBERS.items():
        path=root/name
        assert path.parent.resolve(strict=True)==path.parent, name
        before[name]=path.lstat()
        assert alias_signature(before[name])==(66310,7865445,2,14,0o664,True), name
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
        try:
            assert alias_signature(os.fstat(fd))==alias_signature(before[name]), name
            body=os.read(fd,15)
            assert len(body)==14 and hashlib.sha256(body).hexdigest()==metadata['sha256'], name
            assert all(getattr(before[name],k)==getattr(os.fstat(fd),k) for k in ('st_dev','st_ino','st_nlink','st_mode','st_size','st_mtime_ns','st_ctime_ns')), name
        finally:os.close(fd)
    for name,info in before.items():
        after=(root/name).lstat()
        assert all(getattr(info,k)==getattr(after,k) for k in ('st_dev','st_ino','st_nlink','st_mode','st_size','st_mtime_ns','st_ctime_ns')), name
    return ALIAS_MEMBERS

SYNTHETIC_GIT_EXCLUSIONS = ['research/onchain-paper-replication-2026-09-24/full_sources/claim-source-dedup-candidate01-2026-10-10/tiny-repository01/.git', 'research/onchain-paper-replication-2026-09-24/full_sources/claim-source-dedup-candidate01-2026-10-10/tiny-repository02/.git', 'research/onchain-paper-replication-2026-09-24/full_sources/claim-source-dedup-review01-2026-10-10/synthetic-git01/.git']

def excluded_synthetic_git(relative):
    return any(relative==prefix or relative.startswith(prefix+'/') for prefix in SYNTHETIC_GIT_EXCLUSIONS)



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior = HERE.parent/'full29increment14/FRESH_GIT_RECOVERY14.json'
base = json.loads(prior.read_bytes())['source']
assert sha(prior)=='4b78e2df7d12a414920f18e121712d7d6a0b26150204c69fb94b19de68fbff25' and base=='f58540f5e55ca701bab4b20969a5b77ad43e5260', 'accepted preparation14 baseline differs'
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned = ['claim-source-dedup-candidate01-2026-10-10', 'claim-source-dedup-review01-2026-10-10', 'matching-compiled-connected-qualification-review01-2026-10-10', 'matching-compiled-connected-qualification-review02-2026-10-10', 'matching-compiled-connected-qualification01-2026-10-10', 'matching-compiled-connected-qualification02-2026-10-10', 'matching-compiled-library-mapping-lifetime-investigation01-2026-10-10', 'matching-compiled-normalization-connected-review01-2026-10-10', 'matching-compiled-normalization-connected-review02-2026-10-10', 'matching-compiled-normalization-connected-review03-2026-10-10', 'matching-compiled-normalization-connected-review04-2026-10-10', 'matching-compiled-normalization-connected01-2026-10-10', 'matching-compiled-normalization-connected02-2026-10-10', 'matching-compiled-normalization-connected03-2026-10-10', 'matching-compiled-normalization-connected04-2026-10-10', 'matching-compiled-runtime-input-review01-2026-10-10', 'matching-compiled-runtime-input01-2026-10-10', 'matching-compiled-runtime-policy-preparation01-2026-10-10', 'matching-compiled-runtime-policy-scope-review01-2026-10-10', 'pilot29-first-batch-metadata-review01-2026-10-10', 'pilot29-first-group-actual-recovery01-2026-10-10', 'pilot29-first-group-recovery-review01-2026-10-10', 'pilot29-first-group-review01-2026-10-10', 'pilot29-neural-tensor-footprint-review01-2026-10-10', 'pilot29-neural-tensor-footprint01-2026-10-10', 'pilot29-observed-overhead01-2026-10-11', 'pilot29-pre-mcm-io-investigation01-2026-10-10', 'pilot29-prior-throughput-investigation01-2026-10-10', 'pilot29-second-group-actual-recovery01-2026-10-10', 'pilot29-second-group-recovery-review01-2026-10-10', 'pilot29-terminal-outcome-review01-2026-10-11', 'pilot29-third-group-actual-recovery01-2026-10-10', 'pilot29-third-group-recovery-review01-2026-10-10', 'pilot29-training-handoff-readiness01-2026-10-09', 'real-data-pilot-full24-preparation-increment01-2026-10-09/outcome15', 'real-data-pilot-full29-entry01-2026-10-09']
for name in owned:
    for path in (F/name).rglob('*'):
        if path.is_file():
            names.add(str(path.relative_to(ROOT)))
for name in ('capture16.py', 'recover16.py', 'select16.py', 'HELPERS_MANIFEST01.json', 'LITERAL_INVERSE01.json'):
    names.add(str((HERE/name).relative_to(ROOT)))
# Exact terminal29 public outputs/Owner/Parent/dispatch scopes; no private dispatch read.
names.add('research/onchain-paper-replication-2026-09-24/STATE.md')
names.add('research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md')
N='eth-paper-real-data-end-to-end-resource-20261009-29'
scopes=[ROOT/'research_runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N, ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/N, ROOT/'research_artifacts/onchain_representations/5efca533e6c821207f9cdb0b69d090f6b6ae02ef4e32e89f4d7793c6cd9787b5'/N, ROOT/'research_artifacts/onchain_compact_mcm/5efca533e6c821207f9cdb0b69d090f6b6ae02ef4e32e89f4d7793c6cd9787b5'/N, ROOT/'research_artifacts/onchain_batched_offload/c64f82cdaebfcadd2c0227b40ac26bfdf7c53705c0d8f56903f3183c0ea49cc2', ROOT/'research_artifacts/archive-dispatch-ethpilot-20261009-29']
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
prior_selection=json.loads((prior.parent/'SELECTION14.json').read_bytes())
assert sha(prior.parent/'SELECTION14.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
names={relative for relative in names if not excluded_synthetic_git(relative)}
assert set(ALIAS_MEMBERS)<=names
authenticate_alias_pair(ROOT)
reused=[]
for relative in sorted(names-excluded):
    old=previous_rows.get(relative);path=ROOT/relative
    if relative not in ALIAS_MEMBERS and old and old['type']=='regular' and not path.is_symlink() and path.is_file() and format(stat.S_IMODE(path.stat().st_mode),'04o')==old['mode'] and path.stat().st_size==old['bytes'] and sha(path)==old['sha256']:
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
        assert stat.S_ISREG(before.st_mode) and (before.st_nlink == 1 or (relative in ALIAS_MEMBERS and alias_signature(before)==(66310,7865445,2,14,0o664,True))) and before.st_size <= 64*1024**2, relative
        body = path.read_bytes()
        row = {'path': relative, 'type': 'regular',
               'mode': format(stat.S_IMODE(before.st_mode), '04o'),
               'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    after = path.lstat()
    assert all(getattr(before, k) == getattr(after, k) for k in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), relative
    if relative in ALIAS_MEMBERS:
        assert row['type']=='regular' and row['mode']=='0664' and row['bytes']==14 and row['sha256']==ALIAS_MEMBERS[relative]['sha256'], relative
        row['original_alias']=ALIAS_MEMBERS[relative]
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
authenticate_alias_pair(ROOT)
selection = {
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'baseline_actual_recovery': {'path': str(prior.relative_to(ROOT)), 'sha256': sha(prior)},
    'baseline_source': base,
    'actual_scope_states': [{'path':str(scope.relative_to(ROOT)),'exists':scope.exists(),'empty_directories_included':True} for scope in scopes],
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'excluded_synthetic_git_subtrees':SYNTHETIC_GIT_EXCLUSIONS,
    'original_alias_members':ALIAS_MEMBERS,
    'alias_qualification':'Two exact authenticated fixture aliases archived as two regular bodies; original inode/nlink metadata recorded, no POSIX/hardlink reconstruction or deletion authority. Three exact synthetic .git subtrees remain local and are not claimed recovered.',
    'selection_rule': 'Actual public delta since accepted returned full29 preparation14/source f58540f5 plus original terminal29 seven public store scopes, three actual group recovery directories/reviews, and explicitly retained post-preparation source/withheld/failed/review/Root-observation directories. Exact type/mode/size/hash predecessor regular rows reused; three hash-joined prior archive duplicates excluded. No unchanged historical store replay/private dispatch/runtime package capture. Retain all selected actual29 partial outputs and attempted/unavailable entries without whole-MCM/training/financial credit.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION16.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
