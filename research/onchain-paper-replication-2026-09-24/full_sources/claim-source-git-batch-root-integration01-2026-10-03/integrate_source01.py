"""Root-only, one-use accepted source integration; no research package imports."""
import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASE = HERE.parent
OLD = Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-01/source')
NEW = Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source')
OLD_A = '6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e'
BASELINE = 'a520a756ec3fa126f56ec1c694851b6f46416e462228eb51a6954385b449f439'
ACCEPTED = '3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'

def sha(body):
    return hashlib.sha256(body).hexdigest()

def write(name, data):
    with (HERE / name).open('x') as stream:
        stream.write(json.dumps(data, indent=2, sort_keys=True) + '\n')

def git(root, *args):
    return subprocess.check_output(['git', '-c', 'protocol.allow=never', *args], cwd=root,
        env={**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'GIT_CONFIG_NOSYSTEM': '1'}, timeout=15).decode().strip()

def main():
    assert not (HERE / 'INTEGRATION01.json').exists()
    assert not (HERE / 'WITHDRAWAL_SOURCE_A01.json').exists()
    target = REPO / 'tradingagents/research/verify.py'
    candidate = BASE / 'claim-source-git-batch-candidate01-2026-10-03/candidate01.py'
    review = BASE / 'claim-source-git-batch-review01-2026-10-03/REVIEW_BATCH01.md'
    manifest = BASE / 'claim-source-git-batch-candidate01-2026-10-03/MANIFEST01.json'
    extents = BASE / 'claim-source-git-batch-selected-extents-investigation01-2026-10-03/REPORT01.md'
    assert sha(target.read_bytes()) == BASELINE
    assert sha(candidate.read_bytes()) == ACCEPTED
    assert sha(review.read_bytes()) == '847f7f8552948ae19a1966d3f6176c8b67bd417924369754ba47600cd56d6c5f'
    assert sha(manifest.read_bytes()) == 'c048da8c0c5242dab43b1e72a985b76565d8dd1a52f993c7277d18eac12ced03'
    assert sha(extents.read_bytes()) == '54b1b806d487fecf30793d1daf1e266549c7a31006bc07ea7d1afdef96ae2484'
    for row in json.loads(manifest.read_bytes())['files']:
        body = (manifest.parent / row['path']).read_bytes()
        assert len(body) == row['bytes'] and sha(body) == row['sha256']
    assert git(REPO, 'branch', '--show-current') == 'research/onchain-paper-replication-2026-09-24'
    assert git(REPO, 'status', '--short', '--untracked-files=no') == ''
    before = git(REPO, 'rev-parse', 'HEAD')
    assert before == 'c079195b1ec9e0c4a665fb76fd455642d16f9291'
    assert git(OLD, 'rev-parse', 'HEAD') == OLD_A
    assert git(OLD, 'status', '--short', '--untracked-files=no') == ''
    inv = json.loads((OLD / 'cold_prep/source_inventory.json').read_bytes())
    for row in inv['source_inventory']:
        body = (OLD / row['target']).read_bytes()
        assert len(body) == row['bytes'] and sha(body) == row['sha256']
    assert len(inv['source_inventory']) == 195 and inv['package_count'] == 147
    assert sha((OLD / 'tradingagents/research/verify.py').read_bytes()) == BASELINE
    ids = ('compact-cold-inputs-20261003-01', 'compact-cold-comparison-20261003-01')
    roots = ('research_runs', 'proof_outer', 'proof_supervise',
        'research_artifacts/compact-cold-engineering-20261003',
        'research_artifacts/onchain-paper-replication-2026-09-24/runs')
    absent = []
    for identity in ids:
        for base in roots:
            path = OLD / base / identity
            assert not path.exists() and not path.is_symlink()
            absent.append(str(path))
    assert not NEW.exists() and not NEW.is_symlink()
    pids = (2413150, 2413154, 2413318, 2414328, 2415326, 2415330, 2417343, 2418034, 2418042, 3273614)
    assert all(not Path('/proc', str(pid)).exists() for pid in pids)
    cgroup = Path('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/onchain-replication-e624afdb7518476db19811f2cfcb8aed.service')
    assert not cgroup.exists()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write('WITHDRAWAL_SOURCE_A01.json', {
        'schema_version': 1, 'status': 'withdrawn-unattempted-root-selection', 'observed_at': timestamp,
        'old_root': str(OLD), 'old_source': OLD_A,
        'old_capsule_mutated': False, 'old_proposed_release_status': 'draft',
        'old_full_recovery_review': '98e10689af473c969f7fdb639357e6115aeed001999cefc28923759fd205f214',
        'unclaimed_paths_absent': absent, 'successor_root': str(NEW), 'successor_root_absent': True,
        'family_attempt_budget': 2, 'family_prior_attempts': 0, 'exposures': [],
        'reason': 'Exact independently accepted verify.py changes source and numerical-anchor bindings; fresh coherent source/input/registration preparation is required.',
        'release_required': ['independent zero-claim withdrawal review', 'fresh source S2/T2/A2 and exact 147-file anchor',
            'nine inputs and native path mapping', 'actual full external recovery and review', 'exact released envelope and one-use launcher',
            'fresh cross-root identity/runtime/native eligibility'],
        'qualification': 'No claim, reservation, terminal, refund, budget increase, empirical success or authority is created.'})
    # The old capsule is intentionally untouched. Only the accepted live source changes.
    target.write_bytes(candidate.read_bytes())
    assert sha(target.read_bytes()) == ACCEPTED
    assert git(OLD, 'rev-parse', 'HEAD') == OLD_A
    write('INTEGRATION01.json', {
        'schema_version': 1, 'status': 'accepted-source-integrated-no-execution-release', 'observed_at': timestamp,
        'main_previous_head': before, 'target': str(target.relative_to(REPO)), 'old_sha256': BASELINE,
        'new_sha256': ACCEPTED, 'candidate_manifest': sha(manifest.read_bytes()), 'independent_review': sha(review.read_bytes()),
        'selected_extent_report': sha(extents.read_bytes()),
        'old_capsule_unchanged': True, 'old_pids_absent': list(pids), 'old_cgroup_absent': str(cgroup),
        'numeric_jobs_started': 0, 'paper_closed': 36, 'paper_complete': 27, 'paper_failed': 9, 'paper_highest_adopted': 64,
        'engineering_failed_closed': 4, 'engineering_highest_adopted': 5,
        'method_or_scientific_configuration_changed': False,
        'qualification': 'Fresh bounded batching retains every historical/current source/hash/charter verification. Stricter group transport limits and error-order qualifications follow the exact independent review. Source integration is not resource capacity, measured speedup, scientific completion, or empirical release.'})
    print(json.dumps({'status': 'source-integrated-old-A-withdrawn-unattempted', 'sha256': ACCEPTED,
        'old_head': OLD_A, 'unclaimed_paths_absent': len(absent), 'numeric_jobs_started': 0}, sort_keys=True))

if __name__ == '__main__':
    main()
