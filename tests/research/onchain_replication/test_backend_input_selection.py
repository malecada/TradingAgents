"""Synthetic bounded role bodies; no native loading or empirical authority."""
import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from tradingagents.research.onchain_replication import compact_mcm_batched as backend

SELECTION = 'source-checked-backend-role-bundle-v1'


@pytest.fixture
def roles(tmp_path, monkeypatch):
    bodies = {'environment': b'{"synthetic":true}', 'normal_source': b'source',
        'normal_library': b'library', 'edge_source': b'edge source',
        'edge_adapter': b'adapter', 'edge_library': b'L'*17072}
    sha = lambda b: hashlib.sha256(b).hexdigest()
    bodies['runtime'] = json.dumps({'format':'compiled-small-lse-runtime-reference-v1',
        'python':'3.13.13','numpy':'2.3.0','scipy':'1.17.1','platform':'linux',
        'machine':'x86_64','byteorder':'little','executable':'/synthetic/python',
        'runtime_inventory_sha256':sha(bodies['environment'])}).encode()
    bodies['abi'] = json.dumps({'format':'cpython-edge-abi-v1','implementation':'cpython',
        'cache_tag':'cpython-313','soabi':'cpython-313-x86_64-linux-gnu',
        'ext_suffix':'.cpython-313-x86_64-linux-gnu.so','pointer_bits':64}).encode()
    inputs = {}
    for role, body in bodies.items():
        relative = 'tradingagents/research/onchain_replication/edge_chunk_adapter.py' if role == 'edge_adapter' else role
        path = tmp_path/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
        inputs[role] = {'path':relative,'sha256':sha(body)}
    # Fixture-only allowed identities; actual policy schema, role/path/body/ABI
    # validation and bounded owned file readers remain real.
    for module, constants in [(backend.compiled_normalization_policy,
            {'SOURCE_SHA256':'normal_source','LIBRARY_SHA256':'normal_library'}),
            (backend.compiled_edge_owner, {'SOURCE':'edge_source','ADAPTER':'edge_adapter','LIBRARY':'edge_library'})]:
        for constant, role in constants.items(): monkeypatch.setattr(module, constant, sha(bodies[role]))
    normal_roles = {'source':'normal_source','library':'normal_library','runtime':'runtime'}
    edge_roles = {'source':'edge_source','adapter':'edge_adapter','library':'edge_library','runtime':'runtime','abi':'abi'}
    def policy(module, mapping):
        value = {'format':module.FORMAT}
        for kind, role in mapping.items():
            value[kind+'_path'] = str(tmp_path/inputs[role]['path'])
            value[kind+'_sha256'] = inputs[role]['sha256']
            if kind in ('runtime','abi'): value[kind+'_bytes'] = len(bodies[role])
        return value
    execution = {'compiled_normalization_policy':policy(backend.compiled_normalization_policy, normal_roles),
        'compiled_normalization_inputs':normal_roles,
        'compiled_edge_policy':policy(backend.compiled_edge_owner, edge_roles),
        'compiled_edge_inputs':edge_roles, 'backend_input_policy':SELECTION}
    singles, bundles = [], []
    def read_input(name):
        singles.append(name); return bodies[name]
    def read_inputs(names, **limits):
        bundles.append((names, limits)); return {name:bodies[name] for name in names}
    run = SimpleNamespace(admission=SimpleNamespace(root=tmp_path, inputs=inputs,
        experiment={'source_files':{inputs['edge_adapter']['path']:inputs['edge_adapter']['sha256']}}),
        read_input=read_input, read_inputs=read_inputs)
    return execution, run, bodies, singles, bundles


def test_bundle_deduplicates_shared_runtime_and_matches_legacy_policies(roles):
    execution, run, bodies, singles, bundles = roles
    legacy = {k:v for k,v in execution.items() if k != 'backend_input_policy'}
    expected = backend._compiled_inputs(legacy,run), backend._edge_inputs(legacy,run)
    assert len(singles) == 10
    singles.clear()
    assert backend._backend_inputs(execution,run) == expected
    assert singles == []
    assert bundles == [(tuple(sorted(bodies)), {'max_each_bytes':2*1024**2,'max_total_bytes':4*1024**2})]


@pytest.mark.parametrize('mutation', ['missing', 'extra', 'changed', 'mutable'])
def test_bundle_wrong_or_incomplete_bodies_refuse(roles, mutation):
    execution, run, bodies, singles, bundles = roles
    def wrong(names, **limits):
        result = {name:bodies[name] for name in names}
        if mutation == 'missing': del result['edge_adapter']
        elif mutation == 'extra': result['unregistered'] = b'extra'
        elif mutation == 'changed': result['edge_adapter'] = b'wrong'
        else: result['edge_adapter'] = bytearray(result['edge_adapter'])
        return result
    run.read_inputs = wrong
    with pytest.raises(ValueError): backend._backend_inputs(execution,run)
    assert singles == []


@pytest.mark.parametrize('change', ['unknown', 'none', 'missing_backend', 'duplicate_role', 'unregistered_role'])
def test_invalid_selection_or_roles_refuse(roles, change):
    execution, run, bodies, singles, bundles = roles
    if change == 'unknown': execution['backend_input_policy'] = 'unknown'
    elif change == 'none': execution['backend_input_policy'] = None
    elif change == 'missing_backend': execution = {'backend_input_policy':SELECTION}
    elif change == 'duplicate_role': execution['compiled_edge_inputs']['adapter'] = 'edge_source'
    else: execution['compiled_edge_inputs']['adapter'] = 'missing_role'
    with pytest.raises(ValueError): backend._backend_inputs(execution,run)


def test_selected_path_retains_adapter_source_and_disk_body_guards(roles):
    execution, run, bodies, singles, bundles = roles
    run.admission.experiment['source_files'].clear()
    with pytest.raises(ValueError, match='adapter input/source'): backend._backend_inputs(execution,run)
    info = run.admission.inputs['edge_adapter']
    run.admission.experiment['source_files'][info['path']] = info['sha256']
    (run.admission.root/info['path']).write_bytes(b'changed on disk')
    with pytest.raises(ValueError, match='body differs'): backend._backend_inputs(execution,run)


def test_policy_validator_accepts_only_explicit_bundle_selection(roles):
    execution, *_ = roles
    execution.update(route='immutable-input-session+exact-byte-reuse-v1',max_entries=32,
        max_retained_bytes=65536,max_key_bytes=4096,max_origin_bytes=4096,max_summary_bytes=8192)
    b = dict(format=backend.FORMAT,authority_boundaries='entry-batch-checkpoint-final',
        batch_cells=32,max_journal_bytes=1024**2,max_body_bytes=1024,
        max_closure_token_bytes=1024,max_checkpoint_bytes=4096,retention='local-v2',
        max_spool_bytes=4096,max_offload_metadata_bytes=4096,max_offload_entries=32,
        max_offload_anchor_bytes=0,execution=execution)
    policy = dict(schema_version=5,max_entries=32,max_workflow_metadata_bytes=4096,numeric={},batched=b)
    assert backend.validate(policy,32) is b
    bad = copy.deepcopy(policy); bad['batched']['execution']['backend_input_policy'] = False
    with pytest.raises(ValueError): backend.validate(bad,32)


def test_backend_timing_records_failure_without_changing_original_exception(roles):
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals, activate
    execution, run, *_ = roles
    original = RuntimeError('genuine bundle refused')
    def refuse(*args, **kwargs): raise original
    run.read_inputs = refuse
    totals = PhaseTotals()
    with activate(totals):
        with pytest.raises(RuntimeError) as caught: backend._backend_inputs(execution,run)
    assert caught.value is original
    row = totals.snapshot()['phases']['backend_setup']
    assert row['calls'] == 1 and row['failures'] == 1
