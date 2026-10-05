"""Closed prediction increment only; accepted metadata, R4 and recovered bases."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import time

ROOT = Path.cwd()
F = ROOT / 'research/onchain-paper-replication-2026-09-24/full_sources'
C = F / 'heartbeat-root-checkpoint10-2026-10-04'
CAP = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PARENT = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-predict-serialized-storage-root-launch-20261005-01')
V = F / 'financial-wrapper-serialized-prediction-binding-review01-2026-10-05'
REVIEW = F / 'financial-wrapper-serialized-prediction-outcome-review01-2026-10-05'
OUT = F / 'financial-wrapper-serialized-prediction-outcome-capture01-2026-10-05'
IDENTITY = 'financial-wrapper-classification-eager-predict-serialized-storage-successor-20261005-01'
SOURCE = '4c66c404fd61ccdbb62c39cd91e16878df74a232'


def main():
    begun = time.monotonic()
    assert not OUT.exists() and shutil.disk_usage(CAP).free >= 10 * 1024**3
    module_path = C / 'SERIALIZED_PREDICTION_CURRENT_CAPTURE02.py'
    assert hashlib.sha256(module_path.read_bytes()).hexdigest() == 'b36bd8e9c676cd92897dd17a35f3c550443156ea70958b04221dde70825fd86c'
    spec = importlib.util.spec_from_file_location('accepted_prediction_metadata', module_path)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    assert hashlib.sha256((PARENT / 'recovery04.py').read_bytes()).hexdigest() == 'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
    sys.path.insert(0, str(PARENT))
    import recovery04 as R
    from bounded_git01 import git
    resource.setrlimit(resource.RLIMIT_FSIZE, (R.FILE, R.FILE))

    def pinned(path, pin):
        raw = R.read(path.parent, path.name)
        assert R.digest(raw) == pin
        return json.loads(raw)

    prior_path = F / 'financial-wrapper-serialized-prediction-current-capture01-2026-10-05/snapshot/COMPOSITION01.json'
    prior = pinned(prior_path, '0f19fb6c4e8fdca56bf4c082153cf54250d11543b63be8eff89c70e6103b7e45')
    basis = V / 'FULL_CURRENT_RECOVERY_PROOF01.json'
    pinned(basis, '105330459532576a56dc3aee8b035ca411bd058385c2b441f15b705cb431da41')
    envelope = V / 'FINAL_ENVELOPE_RECOVERY_PROOF01.json'
    pinned(envelope, 'aab3471c56911bf01aaffc9fdd6d13ab8e4fe8699e65409d38b8d151a13c89b7')
    outcome = pinned(REVIEW / 'OUTCOME_CHECK01.json', 'ff9ca638eb3ff4a9f153a218594f4d46d45f5d7057365533186ab5e01ed4a364')
    assert outcome['source'] == SOURCE and outcome['identity'] == IDENTITY
    assert outcome['decision'] == 'accepted-actual-complete-synthetic-prediction-outcome-pending-recovery'
    assert outcome['paper_financial_fits'] == outcome['optimizer_updates'] == 0
    assert outcome['Parent']['separate_actual_Root_exit'] == outcome['native']['child_exit'] == 0
    pinned(CAP / 'research_runs' / IDENTITY / 'claim.json', 'ad9e3d8a40caa468a69f77af9488bdf25675d44080736d9adf9ca8048b03068b')
    pinned(CAP / 'research_runs' / IDENTITY / 'complete.json', 'f915624f0f328f6bc0cceb299878427f97d864029f2f7d94a7920951c1712e04')
    assert not os.path.lexists(CAP / 'research_runs' / IDENTITY / 'failed.json')
    assert not os.path.lexists('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/' + outcome['native']['unit'])
    for pid in outcome['Parent']['known_recorded_PIDs_currently_absent']:
        assert not (Path('/proc') / str(pid)).exists()
    assert git(CAP, ['rev-parse', 'HEAD'], cap=128).decode().strip() == SOURCE
    assert git(CAP, ['status', '--short', '--untracked-files=no']) == b''

    cap_before, cap_allocated, cap_signatures = M.metadata(CAP, omit_git=True, allocation_cap=1024**3)
    git_before, git_allocated, git_signatures = M.metadata(CAP / '.git', allocation_cap=1024**3)
    parent_before, parent_allocated, parent_signatures = M.metadata(PARENT, allocation_cap=80 * 1024**2)
    assert cap_allocated + git_allocated <= 1024**3
    old = {r['path']: r for r in prior['capsule']['members']}
    now = {r['path']: r for r in cap_before['members']}
    assert cap_before['root_mode'] == prior['capsule']['root_mode'] and set(old) <= set(now)
    for name, row in old.items():
        assert now[name] == {k: v for k, v in row.items() if k != 'sha256'}
    added = set(now) - set(old)
    prefixes = ('research_runs/' + IDENTITY, 'research_artifacts/onchain-paper-replication-2026-09-24/runs/' + IDENTITY, 'research_artifacts/financial_wrapper_engineering/' + IDENTITY)
    assert len(now) == 1563 and len(added) == 33 and sum(now[n]['kind'] == 'file' for n in added) == 25
    assert all(any(n == p or n.startswith(p + '/') for p in prefixes) for n in added)
    assert sum(r['kind'] == 'file' for r in now.values()) == 1213
    saved = {}
    cap_rows = []
    for n, row in sorted(now.items()):
        if n in added and row['kind'] == 'file':
            raw = R.read(CAP, n)
            assert len(raw) == row['bytes']
            saved['CAP/' + n] = raw
            cap_rows.append(dict(row, sha256=R.digest(raw)))
        else:
            cap_rows.append(old.get(n, row))

    old_git = {r['path']: r for r in prior['Git']['manifest']['members']}
    assert git_before['root_mode'] == prior['Git']['manifest']['root_mode']
    assert set(old_git) == {r['path'] for r in git_before['members']}
    git_reused = 0
    git_rows = []
    for row in git_before['members']:
        n = row['path']; previous = old_git[n]; parts = Path(n).parts
        assert row == {k: v for k, v in previous.items() if k != 'sha256'}
        is_object = len(parts) == 3 and parts[0] == 'objects' and len(parts[1]) == 2 and len(parts[2]) == 38 and all(c in '0123456789abcdef' for c in ''.join(parts[1:]))
        if row['kind'] == 'file' and is_object:
            git_rows.append(previous); git_reused += 1
        elif row['kind'] == 'file':
            raw = R.read(CAP / '.git', n)
            assert len(raw) == row['bytes'] and R.digest(raw) == previous['sha256']
            saved['Git/' + n] = raw
            git_rows.append(previous)
        else:
            git_rows.append(row)

    known_parent = {r['path']: r for r in prior['Parent']['manifest']['members']}
    typed = pinned(F / 'financial-wrapper-serialized-prediction-final-direct02-2026-10-05/FINAL_TYPED_SCOPE01.json', '0ace87f6df2270e8cb7fda94d64d19245a7805df5151b72ab109e3f694f305c0')
    for row in typed['original_regular_files']:
        p = Path(row['path'])
        if p.parent == PARENT and p.name in ('REQUEST_FINAL01.json', 'REQUEST_RELEASE_CANDIDATE01.json'):
            known_parent[p.name] = {k: row[k] for k in ('kind', 'mode', 'bytes', 'sha256')} | {'path': p.name}
    assert len(known_parent) == 13 and parent_before['root_mode'] == prior['Parent']['manifest']['root_mode']
    current_parent = {r['path']: r for r in parent_before['members']}
    assert set(known_parent) <= set(current_parent)
    for n, row in known_parent.items():
        assert current_parent[n] == {k: v for k, v in row.items() if k != 'sha256'}
    parent_added = set(current_parent) - set(known_parent)
    assert parent_added and all(n == 'attempt' or n.startswith('attempt/') for n in parent_added)
    parent_rows = []
    for n, row in sorted(current_parent.items()):
        if n in parent_added and row['kind'] == 'file':
            raw = R.read(PARENT, n)
            assert len(raw) == row['bytes']
            saved['Parent/' + n] = raw
            parent_rows.append(dict(row, sha256=R.digest(raw)))
        else:
            parent_rows.append(known_parent.get(n, row))

    review_manifest = R.scan(REVIEW)
    for row in review_manifest['members']:
        if row['kind'] == 'file':
            saved['outcome-review/' + row['path']] = R.read(REVIEW, row['path'])
    root_names = ('SERIALIZED_PREDICTION_PARENT_LAUNCH01.stdout', 'SERIALIZED_PREDICTION_PARENT_LAUNCH01.stderr', 'SERIALIZED_PREDICTION_PARENT_LAUNCH01_ROOT_EXIT.json', 'SERIALIZED_PREDICTION_PARENT_PREFLIGHT01.stdout', 'SERIALIZED_PREDICTION_PARENT_PREFLIGHT01.stderr', 'SERIALIZED_PREDICTION_PARENT_PREFLIGHT01_ROOT_EXIT.json', 'SERIALIZED_PREDICTION_OUTCOME_CAPTURE01.py', 'SERIALIZED_PREDICTION_READONLY_INSPECTION_ERRORS01.json', 'REMOTE_CONFIRMATION82.json')
    phase_names = ('FINAL_DIRECT03_REMOTE_CHECK01.json', 'BOTH_FAILED_DIRECT_RECOVERY_CHECK01.json', 'FINAL_ENVELOPE_RECOVERY_PROOF01.json', 'ACTUAL_PREFLIGHT_CHECK01.json', 'NUMERICAL_ENTRY_RELEASE01.json', 'NUMERICAL_FRESH_ELIGIBILITY01.json')
    for n in root_names:
        saved['Root/' + n] = R.read(C, n)
    phase_pins = {}
    for n in phase_names:
        raw = R.read(V, n); saved['post-preparation-phase/' + n] = raw
        phase_pins[n] = R.digest(raw)
    assert sum(map(len, saved.values())) <= 8 * 1024**2 and time.monotonic() - begun < 120
    objects = git(CAP, ['cat-file', '--batch-all-objects', '--batch-check=%(objectname) %(objecttype) %(objectsize)']).decode().splitlines()
    assert objects == prior['Git_object_inventory'] and len(objects) == 473
    OUT.mkdir(mode=0o700)
    snapshot = OUT / 'snapshot'; snapshot.mkdir(mode=0o700)
    mapped = {}
    for index, (name, body) in enumerate(sorted(saved.items())):
        flat = 'body-%04d' % index
        with R.new_file(snapshot / flat) as fd:
            offset = 0
            while offset < len(body):
                written = os.write(fd, body[offset:]); assert written > 0; offset += written
            os.fsync(fd)
        assert R.read(snapshot, flat) == body
        mapped[name] = {'flat': flat, 'bytes': len(body), 'sha256': R.digest(body)}
    composition = {'schema_version': 1, 'kind': 'closed-serialized-prediction-byte-increment', 'identity': IDENTITY, 'source': SOURCE, 'basis': {'path': str(basis), 'sha256': '105330459532576a56dc3aee8b035ca411bd058385c2b441f15b705cb431da41'}, 'final_envelope_basis': {'path': str(envelope), 'sha256': 'aab3471c56911bf01aaffc9fdd6d13ab8e4fe8699e65409d38b8d151a13c89b7'}, 'capsule': dict(cap_before, members=cap_rows), 'Git': {'root': str(CAP / '.git'), 'manifest': dict(git_before, members=git_rows)}, 'Git_object_inventory': objects, 'Git_logical_objects': len(objects), 'Parent': {'root': str(PARENT), 'manifest': dict(parent_before, members=parent_rows)}, 'outcome_review': {'root': str(REVIEW), 'manifest': review_manifest}, 'post_preparation_phase': {'root': str(V), 'exact_files': phase_pins}, 'materialized': mapped, 'accepted_unchanged_CAP_regular_reused': 1188, 'accepted_unchanged_Parent_regular_reused': 13, 'accepted_unchanged_Git_regular_reused': git_reused, 'original_parent_exit': None, 'actual_Root_exit': 0, 'actual_child_exit': 0, 'native_PID_history_complete': False, 'optimizer_updates': 0, 'paper_financial_fits': 0, 'installed_runtime_body_recovery': False, 'POSIX_reconstruction': False, 'immutable_writer_exclusion': False, 'numerical_authority': False, 'qualification': 'Complete declared CAP/Git/Parent outcome byte scope through actual accepted current/final-envelope bases plus all25 new opaque CAP bodies, all new Parent attempt bodies, current mutable Git, new outcome review and specified post-preparation/Root increments. Old historical bodies inherited, not recopied or freshly hashed. Saved-model consistency only, no empirical accuracy or whole capacity claim.'}
    R.put(snapshot / 'COMPOSITION01.json', composition)
    manifest = R.scan(snapshot)
    R.put(OUT / 'archive-manifest.json', manifest)
    archive = R.pack(snapshot, manifest, OUT / 'increment.tar.gz')
    assert M.metadata(CAP, omit_git=True, allocation_cap=1024**3) == (cap_before, cap_allocated, cap_signatures)
    assert M.metadata(CAP / '.git', allocation_cap=1024**3) == (git_before, git_allocated, git_signatures)
    assert M.metadata(PARENT, allocation_cap=80 * 1024**2) == (parent_before, parent_allocated, parent_signatures)
    R.same(REVIEW, review_manifest); R.same(snapshot, manifest)
    assert all(R.digest(R.read(V, n)) == pin for n, pin in phase_pins.items())
    assert time.monotonic() - begun < 120 and shutil.disk_usage(CAP).free >= 10 * 1024**3
    result = {'schema_version': 1, 'status': 'ACTUAL_CLOSED_PREDICTION_INCREMENT_CAPTURED_ONCE', 'identity': IDENTITY, 'source': SOURCE, 'archive': archive, 'basis': composition['basis'], 'final_envelope_basis': composition['final_envelope_basis'], 'new_original_bodies': len(mapped), 'new_original_bytes': sum(v['bytes'] for v in mapped.values()), 'CAP_regular': 1213, 'CAP_typed': 1563, 'new_CAP_regular': 25, 'Parent_regular': sum(r['kind'] == 'file' for r in parent_rows), 'Git_logical_objects': len(objects), 'old_CAP_regular_reused': 1188, 'old_Parent_regular_reused': 13, 'old_Git_regular_reused': git_reused, 'paper_financial_fits': 0, 'external_recovery': False, 'launch_authority': False}
    R.put(OUT / 'CAPTURE01.json', result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
