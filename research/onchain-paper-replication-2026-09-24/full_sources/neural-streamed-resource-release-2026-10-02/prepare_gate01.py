"""Exact prospective04 metadata assembly; no numerical import, claim or job."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PARENT = HERE.parent
IDENTITY = 'eth-paper-neural-resource-20261002-04'
PREDECESSOR = 'eth-paper-neural-resource-20261002-03'
BUDGET = PARENT / 'neural-streamed-budget-preparation-2026-10-02'
INTEGRATION = PARENT / 'neural-streamed-integration-2026-10-02'
PHASE = PARENT / 'neural-streamed-phase-identity-2026-10-02'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    for prefix in ('research_runs', 'research_artifacts/onchain-paper-replication-2026-09-24/runs',
                   'research_artifacts/onchain-paper-replication-2026-09-24/sources'):
        assert not os.path.lexists(ROOT / prefix / IDENTITY), 'identity already used'
    # All immutable prerequisite records must exist before any release output.
    refs = {
        'accepted_budget_allocation': BUDGET / 'allocation02.json',
        'accepted_budget_review_report': BUDGET / 'REVIEW_BUDGET01.md',
        'budget_extension': BUDGET / 'extension02.json',
        'budget_callback_review': BUDGET / 'review.accepted01.json',
        'budget_population': BUDGET / 'population03.json',
        'budget_planning_resource_amendment': BUDGET / 'resource-amendment01.json',
        'scheduling_preparation_review': HERE / 'REVIEW_PREPARATION01.md',
        'phase_identity_correction': PHASE / 'IMPLEMENTATION01.md',
        'phase_identity_manifest': PHASE / 'manifest01.json',
        'phase_identity_review': PHASE / 'REVIEW_PHASE_IDENTITY01.md',
        'accepted_production_source_review': INTEGRATION / 'REVIEW_SOURCE01.md',
        'production_integration_manifest': INTEGRATION / 'manifest01.json',
        'accepted_adapter_execution': INTEGRATION / 'execution-result02.json',
        'accepted_adapter_execution_review': INTEGRATION / 'REVIEW_ADAPTER_EXECUTION02.md',
        'accepted_adapter_release': INTEGRATION / 'adapter-release05.json',
        'accepted_adapter_release_review': INTEGRATION / 'REVIEW_ADAPTER_RELEASE05.md',
        'accepted_adapter_tree': INTEGRATION / 'retained-tree02.json',
        'accepted_adapter_archive': INTEGRATION / 'retained-tree02.tar.gz',
        'closed_adapter01_result': INTEGRATION / 'execution-result01.json',
        'closed_adapter01_review': INTEGRATION / 'REVIEW_ADAPTER_EXECUTION01.md',
        'closed_adapter01_child_receipt_addendum': INTEGRATION / 'CLOSURE_RECEIPT_ADDENDUM01.json',
        'fresh_joint_remote_recovery': INTEGRATION / 'JOINT_REMOTE_RECOVERY01.json',
        'fresh_joint_remote_recovery_review': INTEGRATION / 'REVIEW_JOINT_REMOTE_RECOVERY01.md',
    }
    candidate = PARENT / 'neural-streamed-gat-candidate-2026-10-02'
    diagnostic = PARENT / 'neural-streamed-gat-diagnosis-2026-10-02'
    cleanup = candidate / 'cleanup-smoke-preparation01'
    refs.update({
        'streamed_fixed_protocol': candidate / 'PROTOCOL02.md',
        'streamed_fixed_protocol_review': candidate / 'REVIEW_PROTOCOL02.md',
        'streamed_green02_result': candidate / 'green-execution-result02.json',
        'streamed_green02_review': candidate / 'REVIEW_GREEN_EXECUTION02.md',
        'streamed_green02_tree': candidate / 'green-retained-tree02.json',
        'streamed_green02_archive': candidate / 'green-retained-tree02.tar.gz',
        'streamed_causal_diagnostic': diagnostic / 'execution-result01.json',
        'streamed_causal_diagnostic_review': diagnostic / 'REVIEW_DIAGNOSTIC_EXECUTION01.md',
        'accepted_cleanup_owner_result': cleanup / 'execution-result01.json',
        'accepted_cleanup_owner_review': cleanup / 'REVIEW_CLEANUP_OWNER_EXECUTION01.md',
    })
    for path in refs.values():
        assert path.is_file() and path.resolve() == path, str(path)
    assert sha(refs['budget_extension']) == '72561ea7648e43c5ee81f1d99a00c52091d0664827df4a3ba970e3c9ec654fc8'
    assert sha(refs['accepted_budget_allocation']) == 'd238ffd07c4f183b447509ffd967c928944c4dea95e77c88d4d2a102250765a8'
    assert sha(refs['budget_callback_review']) == '0ff87a42b58659c8791eeac1673cf89997eaf268b344a2be8a33aee18a3189bc'
    assert sha(refs['scheduling_preparation_review']) == 'ea029c47cab097268b45f78b6be08ac03626baa9a4ed06c98cfc076e32b0f8e7'
    assert sha(refs['fresh_joint_remote_recovery_review']) == '049f8a3b96c78e47cb3caa5ac0a880a3d1bd3568f46a2ca164d9fe381a9bcf96'
    assert sha(refs['phase_identity_manifest']) == 'b9fba2c892e6340a23c3fbafc3b5dd40d41ec76425b4b5a6a5a030c609b26121'

    gate = copy.deepcopy(json.loads((PARENT / 'neural-pressure-successor-release-2026-10-02/gate.json').read_bytes()))
    # Frozen ancestor objects are taken from original claims, not reconstructed.
    parent_claim = json.loads((ROOT / 'research_runs' / PREDECESSOR / 'claim.json').read_bytes())
    assert gate['experiments'][PREDECESSOR] == parent_claim['experiment']
    selected = copy.deepcopy(parent_claim['experiment'])
    gate['experiments'][IDENTITY] = selected
    selected['parent'] = PREDECESSOR
    selected['question'] = ('Can exact candidate02 streamed-gat-mulsum-v1/block65536 complete the unchanged nine-cell '
        'synthetic neural resource denominator under the same3.75GiB cap and3GiB host reserve after closed03kernelOOM, '
        'with explicit schema2 execution provenance and separately reviewed6.75GiB scheduling minimum?')
    selected['charter'] = pin(HERE / 'CHARTER.md')
    selected['cumulative_budget_extension'] = {
        'extension': pin(refs['budget_extension']), 'review': pin(refs['budget_callback_review'])}
    # Historical source-composition inputs remain inspectable with clear labels.
    for name in ('final_phase_integration', 'final_source_manifest', 'final_source_release_review'):
        selected['inputs']['closed03_' + name] = selected['inputs'].pop(name)
    for name, path in refs.items():
        selected['inputs'][name] = {**pin(path), 'dataset': 'eth'}
    for name, filename in (('execution_job', 'execution-job.json'), ('launch_scheduling', 'launch_scheduling.json'),
                           ('neural_plan', 'neural-plan.json')):
        selected['inputs'][name] = {**pin(HERE / filename), 'dataset': 'eth'}
    assert selected['cells'] == parent_claim['experiment']['cells']
    assert selected['windows'] == parent_claim['experiment']['windows']
    assert len(selected['cells']) == len(selected['windows']) == 9
    assert selected['inputs']['model']['sha256'] == '20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d'
    assert sha(HERE / 'execution-job.json') == sha(PARENT / 'neural-pressure-successor-release-2026-10-02/execution-job.json')
    old_plan = json.loads((ROOT / parent_claim['experiment']['inputs']['neural_plan']['path']).read_bytes())
    new_plan = json.loads((HERE / 'neural-plan.json').read_bytes())
    expected_plan = {**old_plan, 'schema_version': 2,
        'model_execution': {'schema_version': 1, 'backend': 'streamed-gat-mulsum-v1', 'block_edges': 65536}}
    assert new_plan == expected_plan

    ancestry = []
    ancestor = selected['parent']
    while ancestor is not None:
        original = json.loads((ROOT / 'research_runs' / ancestor / 'claim.json').read_bytes())
        assert gate['experiments'][ancestor] == original['experiment'], ancestor
        assert (ROOT / 'research_runs' / ancestor / 'terminal.json').is_file(), ancestor
        ancestry.append(ancestor)
        ancestor = original['experiment']['parent']
    assert ancestry == [PREDECESSOR, 'eth-paper-neural-resource-20261002-02',
                        'eth-paper-resource-pilot-20260924-02', 'eth-paper-resource-pilot-20260924']

    resource = json.loads((BUDGET / 'resource-amendment01.json').read_bytes())
    resource['status'] = 'EXACT_RELEASE_INDEPENDENT_GATE_REVIEW_REQUIRED_NO_CLAIM'
    resource['selected_variant']['candidate_code_and_production_selection_not_yet_accepted'] = False
    resource['unchanged'].pop('schedule_available_bytes')
    resource['scheduling_amendment'] = {
        'supersedes_only': 'budget planning resource-amendment01 unchanged.schedule_available_bytes',
        'previous_minimum_available_bytes': 7516192768,
        'minimum_available_bytes': 7247757312,
        'removed_extra_margin_bytes': 268435456,
        'host_reserve_bytes_unchanged': 3221225472,
        'hard_startup_bytes_unchanged': 7247757312,
        'freshness_seconds': 1, 'observation_count': 16, 'interval_seconds': 2,
        'review': pin(refs['scheduling_preparation_review']),
        'qualification': 'Readiness does not reserve RAM; narrower setup margin can still cause refusal or pressure termination.'}
    resource['evidence'].extend(pin(path) for path in refs.values())
    resource['remaining_before_execution'] = ['independent exact final gate review',
        'committed externally verified release', 'actual currentHEAD admission',
        'fresh sustained readiness, exclusive namespace and actual native readback']
    resource['qualification'] += (' Selected exactCPU first-order implementation has finite numerical proof, '
        'but full-size capacity and financial multi-graph execution remain unproved. '
        'Legacy phase receipts stay schema1; selected execution phase receipts explicitly schema2.')
    save(HERE / 'resource-amendment.json', resource)
    selected['inputs']['resource_amendment'] = {**pin(HERE / 'resource-amendment.json'), 'dataset': 'eth'}

    production = sorted(list((ROOT / 'tradingagents/research/onchain_replication').glob('*.py'))
        + list((ROOT / 'tradingagents/research').glob('*.py')) + [ROOT / 'tradingagents/__init__.py'])
    assert len(production) == 134, 'required closure changed; fresh review required'
    dynamic = {str(path.relative_to(ROOT)): sha(path) for path in production}
    assert dynamic['tradingagents/research/onchain_replication/streamed_gat.py'] == 'e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f'
    assert dynamic['tradingagents/research/onchain_replication/neural_phases.py'] == '11af32f66fa1d9289c713da0304a5c7e0d6dd7a0623f783597bd0f9368988d71'
    runtime = {path.name: sha(path) for path in (ROOT / 'tradingagents/research').glob('*.py')}
    assert runtime == parent_claim['experiment']['runtime_hashes']
    selected['runtime_hashes'] = runtime
    extra = [HERE / name for name in ('CHARTER.md', 'resource-amendment.json', 'execution-job.json',
        'launch_scheduling.json', 'readiness.py', 'launch_once.py', 'prepare_gate01.py', 'test_readiness04.py',
        'readiness-red01.log', 'readiness-green01.log', 'readiness.original03.py', 'launch_scheduling.original03.json')]
    extra.extend(refs.values())
    # Scientific inputs already committed are source-bound; untracked graph manifests
    # keep their admitted input identities, without inventing Git availability.
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
    for item in selected['inputs'].values():
        path = ROOT / item['path']
        assert sha(path) == item['sha256'], item['path']
        if item['path'] in tracked:
            extra.append(path)
    manifest_refs = {str(path.relative_to(ROOT)): sha(path) for path in sorted(set(extra))}
    save(HERE / 'source-manifest01.json', {
        'schema_version': 1, 'status': 'EXACT_SOURCE_GATE_REVIEW_REQUIRED_NO_EXECUTION',
        'identity': IDENTITY, 'parent': PREDECESSOR, 'integration_base_commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'dynamic_python_count': len(production), 'dynamic_source_files': dynamic,
        'runtime_hashes': runtime, 'refs': manifest_refs,
        'science_changed': False, 'neural_plan_schema': 2,
        'backend': 'streamed-gat-mulsum-v1', 'block_edges': 65536,
        'phase_receipt_schema_selected': 2, 'phase_receipt_schema_legacy': 1,
        'empirical_namespaces_reserved': False,
        'qualification': 'Explicit computational execution and scheduling amendments only. No financial fit/real MCM/full-size capacity proof; exact original scientific configuration and all four claim ancestor objects retained.'})
    selected['inputs']['final_source_manifest'] = {**pin(HERE / 'source-manifest01.json'), 'dataset': 'eth'}
    selected['source_files'] = {**dynamic, **manifest_refs,
        str((HERE / 'source-manifest01.json').relative_to(ROOT)): sha(HERE / 'source-manifest01.json')}
    for name in ('extension02.json', 'allocation02.json', 'review.accepted01.json'):
        path = BUDGET / name
        assert selected['source_files'][str(path.relative_to(ROOT))] == sha(path)
    save(HERE / 'gate.json', gate)
    source = '0' * 40
    claim = {
        'schema_version': 1, 'program_id': gate['program_id'], 'experiment_id': IDENTITY,
        'started_at': '2026-10-02T23:59:59.123456+00:00', 'source': source,
        'registration': str((HERE / 'gate.json').relative_to(ROOT)),
        'registration_sha256': sha(HERE / 'gate.json'), 'design_source': source,
        'bindings': None, 'bindings_sha256': None, 'inputs': selected['inputs'],
        'family': gate['families'][selected['family']], 'experiment': selected,
        'effective_attempt_budget': 64,
        'windows': [{**window, 'identity': gate['datasets'][window['dataset']]['identity'], 'state': 'exposed'}
                    for window in selected['windows']],
        'prior_exposures': [{**exposure, 'identity': dataset['identity']}
                           for dataset in gate['datasets'].values() for exposure in dataset['exposures']]}
    encode = lambda value: (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    claim_bytes = len(encode(claim))
    rpc_bytes = len(encode({'anchor_sha256': '0' * 64, 'op': 'claim', 'value': claim}))
    assert max(claim_bytes, rpc_bytes) <= 262144
    save(HERE / 'preparation01.json', {
        'schema_version': 1, 'status': 'EXACT_GATE_REVIEW_REQUIRED_NOT_ADMITTED',
        'identity': IDENTITY, 'gate': pin(HERE / 'gate.json'), 'resource_amendment': pin(HERE / 'resource-amendment.json'),
        'source_manifest': pin(HERE / 'source-manifest01.json'), 'dynamic_python_count': len(production),
        'source_pin_count': len(selected['source_files']), 'input_count': len(selected['inputs']),
        'runtime_count': len(runtime), 'ancestry': ancestry, 'claim_preview_bytes': claim_bytes,
        'rpc_preview_bytes': rpc_bytes, 'json_limit_bytes': 262144,
        'proposed_effective_budget': 64, 'highest_adopted_budget': 63, 'spent': 35,
        'qualified_financial_fits_complete': 0,
        'qualification': 'Metadata-only assembly. Actual committedHEAD admission computes the authoritative claim/RPC shape. No namespace reservation, claim, numerical input or workload. Independent exact gate review and externally verified commit remain required.'})
    print(json.dumps({'gate_sha256': sha(HERE / 'gate.json'), 'dynamic_python_count': len(production),
        'source_pin_count': len(selected['source_files']), 'input_count': len(selected['inputs']),
        'claim_preview_bytes': claim_bytes, 'rpc_preview_bytes': rpc_bytes, 'empirical_execution': False}))


if __name__ == '__main__':
    main()
