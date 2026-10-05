"""One fixed current-byte increment using accepted recovery04 archival mechanics."""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import stat
import sys
import time


def metadata(base, *, omit_git=False, allocation_cap):
    rows = []; signatures = {}; allocated = base.lstat().st_blocks * 512
    deadline = time.monotonic() + 120; device = base.lstat().st_dev
    for current, dirs, files in os.walk(base):
        if Path(current) == base and omit_git:
            dirs[:] = [n for n in dirs if n != ".git"]
        assert time.monotonic() < deadline and len(rows) < 32768
        for name in sorted(dirs + files):
            p = Path(current) / name; s = p.lstat()
            assert p.resolve() == p and s.st_dev == device
            assert stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)
            r = {"path": p.relative_to(base).as_posix(), "kind": "directory" if stat.S_ISDIR(s.st_mode) else "file", "mode": stat.S_IMODE(s.st_mode)}
            if r["kind"] == "file":
                assert s.st_nlink == 1 and s.st_size <= 4 * 1024**2
                r["bytes"] = s.st_size
            rows.append(r); signatures[r["path"]] = (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            allocated += s.st_blocks * 512
            assert allocated <= allocation_cap
    return {"schema_version": 1, "root_mode": stat.S_IMODE(base.lstat().st_mode), "members": sorted(rows, key=lambda r: r["path"])}, allocated, signatures

ROOT = Path.cwd()
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
C = F / 'heartbeat-root-checkpoint10-2026-10-04'
CAP = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01')
V = F / 'financial-wrapper-serialized-prediction-binding-review01-2026-10-05'
OUT = F / 'financial-wrapper-serialized-prediction-current-capture01-2026-10-05'
IDENTITY = 'financial-wrapper-classification-eager-predict-serialized-storage-successor-20261005-01'
SOURCE = '4c66c404fd61ccdbb62c39cd91e16878df74a232'


def main():
    begun = time.monotonic()
    assert hashlib.sha256((PARENT / 'recovery04.py').read_bytes()).hexdigest() == 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
    assert not OUT.exists() and not (PARENT / 'attempt').exists()
    assert not os.path.lexists(CAP / 'research_runs' / IDENTITY)
    assert shutil.disk_usage(CAP).free >= 10 * 1024**3
    sys.path.insert(0, str(PARENT))
    import recovery04 as R
    from bounded_git01 import git
    resource.setrlimit(resource.RLIMIT_FSIZE, (R.FILE, R.FILE))
    assert git(CAP, ['rev-parse', 'HEAD'], cap=128).decode().strip() == SOURCE
    assert git(CAP, ['status', '--short', '--untracked-files=no']) == b''
    q = json.loads(R.read(PARENT, 'REQUEST_SOURCE_BOUND_DRAFT01.json'))
    assert q['source'] == q['design_source'] == SOURCE and q['identity'] == IDENTITY
    assert q['status'] == 'DRAFT_NOT_RELEASED' and q['final_review'] is None
    assert all(v is None for v in q['proofs'].values())
    for role, name, pin in [('cumulative', 'CUMULATIVE_PROOF01.json', 'd9df45415b9202ec76efe174b179a4d6b7aea3af7a60bbc1af815c5de0460ba2'), ('independent_source_input_runtime', 'SOURCE_INPUT_RUNTIME_PROOF01.json', 'b01b5e28ab009ed3f35fa7ceab350f80dab173c6c6e7ed426dce1b6b1f2e695b')]:
        raw = R.read(V, name)
        proof = json.loads(raw)
        assert R.digest(raw) == pin and proof['source'] == SOURCE and proof['identity'] == IDENTITY
        q['proofs'][role] = {'path': str(V / name), 'sha256': pin}
    prior_path = F / 'financial-wrapper-serialized-continuation-outcome-capture01-2026-10-05/new-bodies/COMPOSITION01.json'
    prior_raw = R.read(prior_path.parent, prior_path.name)
    assert R.digest(prior_raw) == '9fc6cd1bac8ad8f244b168778e9d915933aeac7d0636aef8aee294c36e2eddb1'
    prior = json.loads(prior_raw)
    basis_path = F / 'financial-wrapper-serialized-continuation-outcome-review01-2026-10-05/FULL_OUTCOME_RECOVERY_PROOF01.json'
    basis_raw = R.read(basis_path.parent, basis_path.name)
    assert R.digest(basis_raw) == '6bbe9790775c716a0657a895382d0d3860fe13e42784b5c66abb711bdfae6861'
    assert json.loads(basis_raw)['decision'] == 'accepted-actual-continue100-byte-recovery'
    R.put(PARENT / 'REQUEST_PRESERVATION_DRAFT01.json', q)
    # Original1GiB CAP/80MiB Parent watches apply to preserved live trees.
    # Archive128MiB/4MiB limits apply to the new increment snapshot only.
    cap_before, cap_allocated, cap_signatures = metadata(CAP, omit_git=True, allocation_cap=1024**3)
    git_before, git_allocated, git_signatures = metadata(CAP / '.git', allocation_cap=1024**3)
    assert cap_allocated + git_allocated <= 1024**3
    old = {r['path']: r for r in prior['capsule']['members']}
    now = {r['path']: r for r in cap_before['members']}
    assert cap_before['root_mode'] == prior['capsule']['root_mode'] and set(old) <= set(now)
    changed = {'fixture_inputs/financial_wrapper_serialized_storage01/gates.json', *['tradingagents/research/onchain_replication/' + n for n in ('operational_source_compatibility.py', 'financial_wrapper_fixture.py', 'evaluation.py')]}
    added = set(now) - set(old)
    expected_new = {'fixture_inputs/financial_wrapper_serialized_prediction01', *['fixture_inputs/financial_wrapper_serialized_prediction01/' + n for n in ('predict-plan.json', 'prediction-edge.json', 'prediction_parent_recovery.json', 'prediction_source_successor_recovery.json', 'prediction_source_successor_review.json', 'prior.json', 'source-closure.json')]}
    assert added == expected_new and len(now) == 1530
    assert sum(r['kind'] == 'file' for r in cap_before['members']) == 1188
    saved = {}; cap_rows = []
    for n, r in sorted(now.items()):
        if n in old:
            assert r['kind'] == old[n]['kind'] and r['mode'] == old[n]['mode']
        if n in changed or n in added:
            if r['kind'] == 'file':
                raw = R.read(CAP, n)
                assert len(raw) == r['bytes']
                pin = q['registration_sha256'] if n == q['registration'] else q['source_files'][n]
                assert R.digest(raw) == pin
                saved['CAP/' + n] = raw
                cap_rows.append(dict(r, sha256=pin))
            else:
                cap_rows.append(r)
        else:
            assert r == {k: v for k, v in old[n].items() if k != 'sha256'}
            cap_rows.append(old[n])
    capsule = dict(cap_before, members=cap_rows)
    assert len(saved) == 11
    for n, pin in q['source_files'].items():
        assert next(r for r in cap_rows if r['path'] == n)['sha256'] == pin
    old_git = {r['path']: r for r in prior['Git']['manifest']['members']}
    assert git_before['root_mode'] == prior['Git']['manifest']['root_mode']
    assert set(old_git) <= {r['path'] for r in git_before['members']}
    git_reused = 0; git_rows = []
    for r in git_before['members']:
        n = r['path']; previous = old_git.get(n); parts = Path(n).parts
        is_object = len(parts) == 3 and parts[0] == 'objects' and len(parts[1]) == 2 and len(parts[2]) == 38 and all(c in '0123456789abcdef' for c in ''.join(parts[1:]))
        if r['kind'] == 'file' and previous is not None and is_object:
            assert r == {k: v for k, v in previous.items() if k != 'sha256'}
            git_rows.append(previous); git_reused += 1
        elif r['kind'] == 'file':
            raw = R.read(CAP / '.git', n); assert len(raw) == r['bytes']
            saved['Git/' + n] = raw; git_rows.append(dict(r, sha256=R.digest(raw)))
        else:
            git_rows.append(r)
    git_manifest = dict(git_before, members=git_rows)
    parent_manifest = R.scan(PARENT)
    review_manifest = R.scan(V)
    for label, base, manifest in [('Parent', PARENT, parent_manifest), ('review-phase', V, review_manifest)]:
        for r in manifest['members']:
            if r['kind'] == 'file':
                saved[label + '/' + r['path']] = R.read(base, r['path'])
    root_names = ['SERIALIZED_PREDICTION_ADOPT01.py', 'SERIALIZED_PREDICTION_ADOPTION_INTENT01.json', 'SERIALIZED_PREDICTION_SOURCE_GATE_ADOPTION01.json', 'SERIALIZED_PREDICTION_ADOPT01.stdout', 'SERIALIZED_PREDICTION_ADOPT01.stderr', 'SERIALIZED_PREDICTION_ADOPT_ROOT_EXIT01.json', 'SERIALIZED_PREDICTION_READONLY_ADMISSION01.py', 'SERIALIZED_PREDICTION_READONLY_ADMISSION01.json', 'SERIALIZED_PREDICTION_READONLY_ADMISSION01.stdout', 'SERIALIZED_PREDICTION_READONLY_ADMISSION01.stderr', 'SERIALIZED_PREDICTION_READONLY_ADMISSION_ROOT_EXIT01.json', 'SERIALIZED_PREDICTION_CURRENT_CAPTURE01.py', 'SERIALIZED_PREDICTION_CURRENT_CAPTURE01_WITHHELD.json', 'SERIALIZED_PREDICTION_CURRENT_CAPTURE02.py']
    for n in root_names:
        saved['Root/' + n] = R.read(C, n)
    for n in ('SELECTED_BODIES01.json', 'REMOTE_RECOVERY01.json', 'ACTUAL_ROOT_EXIT01.json', 'ACTUAL_ROOT01.stdout', 'ACTUAL_ROOT01.stderr'):
        p = F / 'financial-wrapper-serialized-prediction-source-remote01-2026-10-05'
        saved['source-recovery/' + n] = R.read(p, n)
    assert sum(map(len, saved.values())) <= 8 * 1024**2 and time.monotonic() - begun < 120
    _, parent_allocated, _ = metadata(PARENT, allocation_cap=80 * 1024**2)
    allocated = cap_allocated + git_allocated + parent_allocated
    assert sum(map(len, saved.values())) <= 8 * 1024**2
    OUT.mkdir(mode=0o700)
    snapshot = OUT / 'snapshot'
    snapshot.mkdir(mode=0o700)
    mapped = {}
    for i, (name, body) in enumerate(sorted(saved.items())):
        flat = 'body-%04d' % i
        with R.new_file(snapshot / flat) as fd:
            offset = 0
            while offset < len(body):
                written = os.write(fd, body[offset:])
                assert written > 0
                offset += written
            os.fsync(fd)
        assert R.read(snapshot, flat) == body
        mapped[name] = {'flat': flat, 'bytes': len(body), 'sha256': R.digest(body)}
    objects = git(CAP, ['cat-file', '--batch-all-objects', '--batch-check=%(objectname) %(objecttype) %(objectsize)']).decode().splitlines()
    composition = {'schema_version': 1, 'kind': 'current-serialized-prediction-byte-increment', 'identity': IDENTITY, 'source': SOURCE, 'basis': {'path': str(basis_path), 'sha256': R.digest(basis_raw)}, 'capsule': capsule, 'Git': {'root': str(CAP / '.git'), 'manifest': git_manifest}, 'Git_object_inventory': objects, 'Git_logical_objects': len(objects), 'Parent': {'root': str(PARENT), 'manifest': parent_manifest}, 'review-phase': {'root': str(V), 'manifest': review_manifest}, 'materialized': mapped, 'accepted_unchanged_CAP_regular_reused': 1177, 'accepted_unchanged_Git_regular_reused': git_reused, 'immutable_writer_exclusion': False, 'installed_runtime_body_recovery': False, 'POSIX_reconstruction': False, 'numerical_authority': False, 'qualification': 'Declared complete current typed CAP/Git/new Parent/phase and Root byte scope through immutable6bbe plus eleven changed/new CAP bodies and actual increments. Unchanged historical hashes inherited from actual recovered bytes; current census observes names/modes/extents/inode signatures only. No fresh whole historical hashing or writer exclusion. Final released request/review remain a separate supplement. No historical body recopy or scientific representation/capacity claim.'}
    R.put(snapshot / 'COMPOSITION01.json', composition)
    manifest = R.scan(snapshot)
    R.put(OUT / 'archive-manifest.json', manifest)
    archive = R.pack(snapshot, manifest, OUT / 'increment.tar.gz')
    assert metadata(CAP, omit_git=True, allocation_cap=1024**3) == (cap_before, cap_allocated, cap_signatures)
    assert metadata(CAP / ".git", allocation_cap=1024**3) == (git_before, git_allocated, git_signatures)
    R.same(PARENT, parent_manifest)
    R.same(V, review_manifest)
    R.same(snapshot, manifest)
    assert time.monotonic() - begun < 120 and shutil.disk_usage(CAP).free >= 10 * 1024**3
    result = {'schema_version': 1, 'status': 'CAPTURED_ONCE_NOT_EXTERNALLY_RECOVERED', 'source': SOURCE, 'identity': IDENTITY, 'archive': archive, 'basis': composition['basis'], 'new_original_bodies': len(mapped), 'new_original_bytes': sum(v['bytes'] for v in mapped.values()), 'CAP_regular': 1188, 'CAP_typed': 1530, 'changed_new_CAP_regular': 11, 'Git_regular': sum(r['kind'] == 'file' for r in git_manifest['members']), 'Git_logical_objects': len(objects), 'Git_unchanged_regular_reused': git_reused, 'Parent_regular': sum(r['kind'] == 'file' for r in parent_manifest['members']), 'review_phase_regular': sum(r['kind'] == 'file' for r in review_manifest['members']), 'initial_allocated_bytes': allocated, 'external_recovery': False, 'launch_authority': False}
    R.put(OUT / 'CAPTURE01.json', result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
