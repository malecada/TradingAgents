"""Invented graphs only; actual event codec and unchanged matching engine."""
import json
import pytest
from tests.research.onchain_replication import test_compact_matcher as tiny
from tests.research.onchain_replication.test_archive_pair_writer import fixture as archive_fixture
from tradingagents.research.onchain_replication import compact_matcher as matcher_module
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.matching_reference import match_reference


def retention_policy():
    return {'schema_version':1,'format':'archived-restart-retention-v1',
        'max_stores':20,'max_generations':100,'max_control_bytes':32*1024**2,
        'max_cumulative_bytes':64*1024**2,'max_live_bytes':40*1024**2,
        'max_replay_bytes':2*1024**2,'max_input_bytes':128*1024,'max_replays':2}


def fixture(tmp_path, *, progress):
    writer,transport,kwargs=archive_fixture(tmp_path)
    a=tiny.graph([[0.],[.3]],[(0,1,.1)]);b=tiny.graph([[.2],[.7]],[(1,0,.4)])
    from tradingagents.research.onchain_replication.contracts import AttributedGraph
    a,b=(AttributedGraph(g.node_ids,g.node_features,g.edge_index,g.edge_features,'a'*64,g.node_ids[0]) for g in (a,b))
    config=tiny.config()|{'beta_final':1.}
    schedule=tiny.SCHEDULE|({'operations_per_call':1,'calls_per_checkpoint':1,'max_checkpoints':3} if progress else {})
    kwargs['scope']=matcher_module.scope(config,tiny.CONTEXT,tiny.POLICY,'f'*64,schedule)
    kwargs['max_iterations']=config['max_iterations']
    kwargs['limits']={'chunk_events':2,'max_events':32,'max_pairs':4,'max_logical_bytes':100000}
    kwargs['archive_policy'].update(max_chunks=16,max_metadata_bytes=2000000)
    log=writer.ArchivePairLog(**kwargs)
    purpose={'schema_version':1,'kind':'mcm','workload_sha256':'f'*64,
        'typed_graphs':[graph_identity(a),graph_identity(b)],'center_index':0,'motif_index':0}
    selection={'kind':'mcm','population':{'nodes':1,'motifs':1},'members':[[0,0]]}
    try:
        matcher=matcher_module.CompactMatcher(log,config=config,context=tiny.CONTEXT,
            policy=tiny.POLICY,workload_sha256='f'*64,schedule=schedule,lease=lambda:None,
            retention={'policy':retention_policy(),'selection':selection,'stage':'e'*64})
    except BaseException:
        log.close();raise
    return matcher,log,a,b,config,purpose,transport


def test_three_scheduled_snapshots_retire_only_superseded_arrays_and_copy_first(tmp_path):
    # Removing retirement or copying FIRST only at completion breaks this test.
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=True)
    try:
        with pytest.raises(matcher_module.CheckpointStop):matcher(purpose,a,b)
        stores=list((tmp_path/'checkpoints/stores').iterdir())
        assert len(stores)==1
        store=stores[0]
        for i in (0,1):
            assert not list((store/f'generation-{i:020d}').rglob('*.npy'))
            assert (store/f'generation-{i:020d}/state/manifest.json').is_file()
        assert len(list((store/'generation-00000000000000000002').rglob('*.npy')))==3
        assert len(list((store/'replay-00000000000000000000').rglob('*.npy')))==3
        assert log.state['progress_events']==3 and log.state['completed_pairs']==0
        assert matcher.retention.spent['generations']==3
        assert len(list((tmp_path/'checkpoints/bridges').glob('progress-*.json')))==3
        assert not (tmp_path/'checkpoints/seal.json').exists()
    finally:log.fail('synthetic bounded cadence stop')


def test_completion_before_cadence_keeps_selected_inputs_without_pair_store(tmp_path):
    # Eager stores for all comparisons or forced snapshots break this test.
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=False)
    try:
        result=matcher(purpose,a,b)
        assert result['score']==match_reference(a,b,config).score
        reference=matcher.retention.finish_stage()
        assert reference and log.state['progress_events']==0
        assert list((tmp_path/'checkpoints/stores').iterdir())==[]
        selected=json.loads((tmp_path/'checkpoints/selected-000000000000.json').read_bytes())
        assert selected['disposition']=='completed_before_first_scheduled_checkpoint'
        assert len(list((tmp_path/'checkpoints/inputs').rglob('*.npy')))==6
        assert matcher.retention.spent['generations']==0
    finally:log.close()


def test_actual_binary_read_anchors_no_checkpoint_selection_and_rejects_rehashed_seal(tmp_path):
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=False)
    try:
        matcher(purpose,a,b);reference=matcher.retention.finish_stage();terminal=log.finish()
        from tradingagents.research.onchain_replication import stage_retention_reader as reader
        from tradingagents.research.onchain_replication import archive_pair_reader
        from tradingagents.research.onchain_replication.provenance import thaw
        visitor=reader.Visitor(tmp_path/'checkpoints',policy=retention_policy(),
            selection=thaw(matcher.retention.selection),expected_sha256=reference,start_sha256=log.start_sha)
        complete=tmp_path/'log/archive-complete.json'
        import hashlib
        archive_pair_reader.verify(tmp_path/'log',expected_sha256=hashlib.sha256(complete.read_bytes()).hexdigest(),
            owner=log.start['owner'],scope=log.start['scope'],archive_policy=log.policy,
            attempt=tmp_path/'read',transport=transport,lease=lambda:None,max_read_metadata_bytes=1000000,
            on_event=visitor.visit)
        visitor.finish()
        result=reader.check(tmp_path/'checkpoints',policy=retention_policy(),
            selection=thaw(matcher.retention.selection),expected_sha256=reference,
            start_sha256=log.start_sha)
        assert result['completed_pairs']==1 and result['progress_events']==0
        seal=tmp_path/'checkpoints/seal.json';value=json.loads(seal.read_bytes());value['completed_pairs']=2
        seal.write_text(json.dumps(value))
        with pytest.raises(ValueError):reader.check(tmp_path/'checkpoints',policy=retention_policy(),
            selection=thaw(matcher.retention.selection),expected_sha256=reference,start_sha256=log.start_sha)
    finally:log.close()


@pytest.mark.parametrize('target',['refund','limits','route'])
def test_late_callback_cannot_refund_expand_or_disable_stage_retention(tmp_path,target):
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=True)
    controller=matcher.retention
    def mutate():
        if log.state['progress_events']==1:
            if target=='refund':controller.spent['generations']=0
            elif target=='limits':controller.policy=dict(controller.policy)|{'max_generations':999}
            else:matcher.retention=None
    matcher.lease=mutate
    try:
        with pytest.raises(ValueError):matcher(purpose,a,b)
        failure=json.loads((tmp_path/'checkpoints/failed.json').read_bytes())
        assert failure['spent']['generations']==1
        assert log.state['completed_pairs']==0
        assert len(list((tmp_path/'checkpoints/stores').glob('*/generation-*')))==1
        assert not (tmp_path/'checkpoints/seal.json').exists()
    finally:log.fail('synthetic revoked retention')


def test_late_progress_view_mutation_preserves_both_generations_and_spending(tmp_path,monkeypatch):
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=True)
    original=log.progress
    def changed(artifact):
        result=original(artifact)
        if log.state['progress_events']==2:
            path=tmp_path/'checkpoints/events'/f'progress-{log.events-1:012d}.json'
            path.write_bytes(b'{}')
        return result
    monkeypatch.setattr(log,'progress',changed)
    try:
        with pytest.raises(ValueError):matcher(purpose,a,b)
        assert matcher.retention.spent['generations']==2 and log.state['completed_pairs']==0
        root=next((tmp_path/'checkpoints/stores').iterdir())
        assert all(len(list((root/f'generation-{i:020d}').rglob('*.npy')))==3 for i in (0,1))
        assert len(list((root/'replay-00000000000000000000').rglob('*.npy')))==3
        assert (root/'failure.json').exists() and (tmp_path/'checkpoints/failed.json').exists()
    finally:log.fail('synthetic late progress mutation')


def test_retirement_failure_keeps_first_replay_no_completion_and_full_reservations(tmp_path,monkeypatch):
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=True)
    from tradingagents.research.onchain_replication import restart_retention
    original=restart_retention.os.unlink
    def fail(path,*args,**kwargs):
        if str(path).endswith('.npy'):raise OSError('synthetic unlink refusal')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(restart_retention.os,'unlink',fail)
    try:
        with pytest.raises(OSError):matcher(purpose,a,b)
        root=next((tmp_path/'checkpoints/stores').iterdir())
        assert matcher.retention.spent['generations']==2 and log.state['progress_events']==2
        assert log.state['completed_pairs']==0
        assert (root/'retire-00000000000000000000-intent.json').exists()
        assert not (root/'retire-00000000000000000000-complete.json').exists()
        assert len(list(root.rglob('*.npy')))==9
        assert json.loads((tmp_path/'checkpoints/failed.json').read_bytes())['spent']==matcher.retention.spent
    finally:log.fail('synthetic retirement failure')


def test_final_callback_cannot_replace_new_stage_seal(tmp_path):
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=False)
    try:
        matcher(purpose,a,b)
        path=tmp_path/'checkpoints/seal.json'
        def mutate():
            if path.exists():path.write_bytes(b'{}')
        matcher.lease=mutate
        with pytest.raises(ValueError):matcher.retention.finish_stage()
    finally:log.close()


def test_foreign_active_stage_member_refuses_before_further_reservation(tmp_path):
    matcher,log,a,b,config,purpose,transport=fixture(tmp_path,progress=True)
    path=tmp_path/'checkpoints/foreign'
    def mutate():
        if log.state['progress_events']==1:path.touch()
    matcher.lease=mutate
    try:
        with pytest.raises(ValueError):matcher(purpose,a,b)
        assert matcher.retention.spent['generations']==1
        assert json.loads((tmp_path/'checkpoints/failed.json').read_bytes())['spent']['generations']==1
    finally:log.fail('synthetic foreign active member')


@pytest.mark.parametrize('entry',['inspect','seal','verify'])
def test_old_stage_format_refuses_new_retention_policy_before_any_io(tmp_path,entry):
    from tradingagents.research.onchain_replication import compact_stage
    from tests.research.onchain_replication.test_compact_policy import candidate
    policy=candidate();policy['restart_retention']=retention_policy();policy['max_retained_logical_bytes']=100000000
    kwargs=dict(owner='a'*64,scope={k:'b'*64 for k in ('workflow','config','policy','context','numerical_source')},
        policy=policy,kind='dictionary',pairs=0,log_terminal_sha256='c'*64,stream_terminal_sha256=None)
    def forbidden():raise AssertionError('old format lease called for new format')
    if entry!='inspect':kwargs['lease']=forbidden
    if entry=='verify':kwargs['expected_sha256']='d'*64
    with pytest.raises(ValueError,match='old stage format'):
        getattr(compact_stage,entry)(tmp_path/'absent',**kwargs)
    assert not (tmp_path/'absent').exists()
