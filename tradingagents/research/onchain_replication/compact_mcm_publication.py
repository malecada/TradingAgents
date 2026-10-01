"""Current-owner publication and reads under an explicit registered output route.

This joins compact stage evidence to numeric output and a separate logical output
budget. It does not admit the dictionary's training samples, select the native
producer, append FeatureJournal events or close a representation. The caller
must derive the expected scientific scope from admitted inputs. Full registered
source/input checks run at boundaries; inner leases retain the frozen-input
contract. Failed publication consumes its namespace and poisons the owner.
"""
from contextlib import contextmanager
import json
import os

from . import compact_owner as owners, compact_policy, compact_stage, compact_mcm_output as output
from . import score_batches as io
from .cache import cache_key
from .matching_pair import BACKEND
from .provenance import durable_mkdir, thaw

require = io._require


@contextmanager
def _locked(owner):
    require(type(owner) is owners.Owner, 'actual compact owner required')
    require(owner._transition.acquire(blocking=False), 'concurrent compact output transition')
    try: yield
    finally: owner._transition.release()


def _prepare(owner, stage, output_input, expected_scope):
    owner.boundary()
    require(type(stage) is owners.Stage and stage.owner is owner and stage.closed
        and stage.kind == 'mcm' and stage.name in owner.required
        and owner.stages.get(stage.name) is stage and owner.active is None,
        'actual completed current-owner MCM stage required')
    stage.integrity(); owner._stage_bindings(stage)
    contract = thaw(stage.contract)
    require(contract['owner'] == owner.identity and contract['scope'] == thaw(stage.scope)
        and contract['pairs'] == stage.pairs and contract['policy'] == thaw(owner.policy)
        and contract['kind'] == 'mcm', 'completed stage contract differs from owner')
    compact_stage.verify(stage.root, expected_sha256=stage.reference, lease=lambda: None, **contract)
    run = owner.bound._run; record = owner.bound.record
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][record['representation']]
    plan = json.loads(run.read_input(selected['plan_input']))['producers'][record['producer']]
    require(type(output_input) is str and output_input in run.admission.inputs
        and selected.get('compact_mcm_output_input') == plan.get('compact_mcm_output_input') == output_input
        and selected.get('native_backend') == plan.get('native_backend') == compact_policy.BACKEND,
        'explicit compact MCM output route differs')
    policy = json.loads(run.read_input(output_input))
    require(set(policy) == {'schema_version', 'backend', 'max_artifact_bytes', 'max_workflow_output_bytes'}
        and type(policy['schema_version']) is int and policy['schema_version'] == 1
        and policy['backend'] == compact_policy.BACKEND, 'compact MCM output policy schema')
    compact_policy.positive((policy['max_artifact_bytes'], policy['max_workflow_output_bytes']))
    # Reserve every required graph's full artifact allowance plus receipt before
    # publishing any graph. This is separate from retained pair/score evidence.
    reserved = (len(owner.required) - 1) * (policy['max_artifact_bytes'] + io.META_LIMIT)
    require(reserved < 2**63 and reserved <= policy['max_workflow_output_bytes']
        and 4 * stage.pairs + io.META_LIMIT <= policy['max_artifact_bytes'],
        'compact workflow output reservation insufficient')
    scope = io._scope(expected_scope)
    require(scope['graph'] == stage.name[4:] and scope['workflow'] == contract['scope']['workflow']
        and scope['matching'] == cache_key({'config': thaw(owner.matching), 'backend': BACKEND}),
        'compact output required graph/workload/matching differs')
    attempt = (run.admission.root / 'research_artifacts/onchain_compact_outputs' /
        record['workflow_identity'] / record['experiment'] / stage.name)
    require(attempt.is_absolute() and attempt.resolve() == attempt, 'compact output path redirected')
    args = dict(stage_root=stage.root, stage_sha256=stage.reference, contract=contract,
        expected_scope=scope, max_output_bytes=policy['max_artifact_bytes'])
    # Includes dictionary/node/motif order before consuming a namespace.
    output._source(args)
    proof = {'schema_version': 1, 'kind': 'owned-compact-mcm-output', 'owner': owner.identity,
        'binding_sha256': cache_key(thaw(record)), 'claim_sha256': record['claim_sha256'],
        'stage': stage.name, 'stage_sha256': stage.reference,
        'policy_input': output_input, 'policy_sha256': run.admission.inputs[output_input]['sha256'],
        'workflow_reserved_output_bytes': reserved, 'representation_admitted': False}
    io._json(proof | {'artifact_sha256': '0' * 64})  # Preflight receipt before writes.
    pinned = (stage.reference, cache_key(contract), stage.inode)
    def lease():
        owner.lease(); stage.integrity()
        require(stage.owner is owner and owner.stages.get(stage.name) is stage
            and stage.closed and owner.active is None and
            (stage.reference, cache_key(thaw(stage.contract)), stage.inode) == pinned,
            'compact output stage authority changed')
        info = stage.root.lstat()
        require((info.st_dev, info.st_ino) == pinned[2], 'compact output stage directory changed')
        owners.exact(stage.root, 'intent.json', stage.intent)
    return attempt, args, proof, lease


def _verify(attempt, args, proof, lease, receipt_sha256):
    lease()
    saved, _ = compact_stage.read(attempt, 'receipt.json', receipt_sha256)
    require(set(saved) == set(proof) | {'artifact_sha256'}
        and saved == proof | {'artifact_sha256': saved['artifact_sha256']}, 'compact output receipt differs')
    output.verify(attempt / 'artifact', expected_sha256=saved['artifact_sha256'], **args, lease=lease)
    lease()
    # Callback-free final checks reject mutations from the last live callback.
    compact_stage.read(attempt, 'receipt.json', receipt_sha256)
    compact_stage.inventory(attempt, {'artifact', 'receipt.json'})
    output.verify(attempt / 'artifact', expected_sha256=saved['artifact_sha256'], **args, lease=lambda: None)
    return saved


def publish(owner, stage, *, output_input, expected_scope):
    with _locked(owner):
        attempt, args, proof, lease = _prepare(owner, stage, output_input, expected_scope)
        require(not owners.present(attempt), 'compact output namespace already claimed')
        lease(); durable_mkdir(attempt.parent)
        require(attempt.resolve() == attempt, 'compact output parent redirected')
        lease(); attempt.mkdir()
        try:
            parent, fd = io._open(attempt.parent)
            try: os.fsync(fd); io._root(parent, fd)
            finally: os.close(fd)
            artifact = output.publish(attempt / 'artifact', **args, lease=lease)
            owner.boundary(); lease()
            root, fd = io._open(attempt)
            try:
                ref = io._write(fd, 'receipt.json', io._json(proof | {'artifact_sha256': artifact}))
                _verify(attempt, args, proof, lease, ref); io._root(root, fd)
            finally: os.close(fd)
            return {'directory': str(attempt), 'receipt_sha256': ref, 'artifact_sha256': artifact}
        except BaseException:
            owner.poisoned = True; raise


def verify(owner, stage, *, output_input, expected_scope, receipt_sha256):
    with _locked(owner):
        attempt, args, proof, lease = _prepare(owner, stage, output_input, expected_scope)
        _verify(attempt, args, proof, lease, receipt_sha256)
        owner.boundary()
        return _verify(attempt, args, proof, lease, receipt_sha256)


@contextmanager
def open_verified(owner, stage, *, output_input, expected_scope, receipt_sha256):
    with _locked(owner):
        attempt, args, proof, lease = _prepare(owner, stage, output_input, expected_scope)
        saved = _verify(attempt, args, proof, lease, receipt_sha256)
        with output.open_verified(attempt / 'artifact', expected_sha256=saved['artifact_sha256'],
                                  **args, lease=lease) as matrix:
            yield matrix
            owner.boundary()
            _verify(attempt, args, proof, lease, receipt_sha256)
        # The nested reader performs live callbacks during its own exit. Join
        # wrapper evidence again after all of them, without invoking a callback.
        _verify(attempt, args, proof, lambda: None, receipt_sha256)
