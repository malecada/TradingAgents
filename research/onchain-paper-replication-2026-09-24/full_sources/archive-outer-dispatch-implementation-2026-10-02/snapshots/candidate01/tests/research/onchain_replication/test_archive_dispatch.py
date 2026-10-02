"""Tiny outer dispatch preparation and accounting; no SSH or empirical claims."""
import pytest


def test_rounded_capacity_counts_every_download_and_block_overhead():
    from tradingagents.research.onchain_replication.archive_dispatch import capacity
    value=capacity(max_events=4,chunk_events=2,record_bytes=16384,stages=3,reads=2)
    assert value=={'logical_bytes':3*65536*5,'rounded_bytes':3*(65536+4*2*65536),'commands':3*2*6,'chunks':6}


def test_capacity_cannot_refund_partial_last_chunk():
    from tradingagents.research.onchain_replication.archive_dispatch import capacity
    value=capacity(max_events=5,chunk_events=2,record_bytes=168,stages=2,reads=1)
    assert value['rounded_bytes']==2*(840+3*3*32768)
    assert value['commands']==2*3*5


@pytest.fixture
def synthetic(tmp_path,monkeypatch):
    import json
    from types import SimpleNamespace
    from tradingagents.research.lifecycle import ResearchRun
    from tradingagents.research.onchain_replication import archive_dispatch as d,compact_training
    from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,freeze
    run=object.__new__(ResearchRun);run._claim_sha256='c'*64
    connection={'host':'synthetic.invalid','user':'invented','port':23,'identity_file':'/unopened/key','known_hosts_file':'/unopened/hosts'}
    config={'schema_version':1,'format':d.FORMAT,'connection':connection,'rate_kbit':32768,'max_seconds':2,
        'max_payload_bytes':1000000,'max_commands':100,'max_diagnostic_bytes':20000000,'max_control_bytes':60000000,
        'namespace':'invented','receipt_output':'archive-start.json','terminal_output':'archive-terminal.json'}
    job={'operation':'produce','plan_input':'plan','producer':'proposed','compact_archive_input':'archive',d.KEY:'transport',
        'compact_policy_input':'compact','descriptor':{'required_graphs':['g']}}
    payload={'representation_jobs':{'proposed':job}}
    from tradingagents.research.onchain_replication import job as outer
    base=tmp_path/outer.PREFIX/'runs/invented';base.mkdir(parents=True)
    run.directory=tmp_path/'research_runs/invented';(run.directory/'outputs').mkdir(parents=True)
    launch={'experiment':'invented','source_commit':'a'*40,'supervisor_pid':1,'nonce':'invented'}
    (base/'launch.json').write_text(json.dumps(launch));(base/'owner.json').write_text(json.dumps({**launch,'monitor_pid':1,'monitor_start_ticks':'1'}))
    inputs={'transport':config,'archive':{'schema_version':1,'backend':'compact-archive-events-v1','transport_identity':d._connection(connection),'remote_namespace':'invented','max_stage_verifications':1,'local_free_floor_bytes':1,'max_writer_metadata_bytes':10000000,'max_read_metadata_bytes':10000000,'max_stage_bytes':100000000,'max_workflow_metadata_bytes':1000000000,'max_remote_payload_bytes':10000000,'max_decoded_transfer_bytes':10000000},
        'compact':{'stage_policy':{'log':{'max_events':4,'chunk_events':2}}},
        'plan':{'producers':{'proposed':dict(job)}},'execution_job':{'kind':'fit','payload':payload,'resources':{'disk_paths':[str(tmp_path)]}}}
    def refresh():
        run.admission=SimpleNamespace(root=tmp_path,source='a'*40,experiment_id='invented',
            inputs={n:{'sha256':digest(canonical_bytes(v))} for n,v in inputs.items()},
            experiment={'outputs':['archive-start.json','archive-terminal.json']})
    refresh();run._published_outputs={}
    monkeypatch.setattr(run,'_active',lambda:None);monkeypatch.setattr(run,'_check_source',lambda:None)
    monkeypatch.setattr(run,'read_input',lambda name:canonical_bytes(inputs[name]))
    def write(name,value):
        path=run.directory/'outputs'/name
        with path.open('xb') as f:f.write(canonical_bytes(value))
        run._published_outputs[name]=digest(path.read_bytes())
    monkeypatch.setattr(run,'write_json',write);monkeypatch.setattr(d.matching_owner,'_guard',lambda *args:None)
    monkeypatch.setattr(compact_training,'_archive_extension',lambda *args:{'synthetic':True})
    return d,run,inputs,payload,refresh


@pytest.mark.parametrize('mutation',['missing','mismatch','endpoint','budget','outputs'])
def test_preflight_refusals_allocate_nothing(synthetic,mutation):
    d,run,inputs,payload,refresh=synthetic
    if mutation=='missing':del payload['representation_jobs']['proposed'][d.KEY]
    if mutation=='mismatch':inputs['plan']['producers']['proposed'][d.KEY]='other'
    if mutation=='endpoint':inputs['archive']['transport_identity']='b'*64
    if mutation=='budget':inputs['transport']['max_payload_bytes']=1
    if mutation=='outputs':run.admission.experiment['outputs']=[]
    with pytest.raises(ValueError):d.preflight(run,payload,{'proposed':True})
    assert not list((run.admission.root/'research_artifacts').glob('archive-dispatch-*'))


def test_shared_capacity_is_not_reset_per_representation(synthetic):
    import copy
    d,run,inputs,payload,refresh=synthetic
    other=copy.deepcopy(payload['representation_jobs']['proposed']);other['compact_archive_input']='archive2';other['producer']='second'
    inputs['archive2']={**inputs['archive'],'remote_namespace':'other'}
    inputs['plan']['producers']['second']=copy.deepcopy(other);payload['representation_jobs']['second']=other
    refresh();plan=d.preflight(run,payload,{'proposed':True,'second':True})
    capacities=plan.record['representations']
    assert plan.record['capacity']['rounded_bytes']==sum(v['capacity']['rounded_bytes'] for v in capacities.values())
    inputs['transport']['max_payload_bytes']=plan.record['capacity']['rounded_bytes']-1
    with pytest.raises(ValueError,match='whole-job'):d.preflight(run,payload,{'proposed':True,'second':True})


def activate(context):
    from types import SimpleNamespace
    from threading import get_ident
    view=context.view('proposed')
    context._cap={'thread':get_ident(),'held':SimpleNamespace(check=lambda owner:None),'ledger':SimpleNamespace(owner=None,selection=SimpleNamespace(_transport=view)),
        'lease':lambda:None,'view':view,'claim_sha256':'d'*64,'remote_prefix':'invented'}
    return view


def test_direct_use_without_reserved_capability_refuses(synthetic):
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}))
    with pytest.raises(ValueError,match='outside live'):c.view('proposed').mkdir('invented-000000000000')
    assert c._spent['commands']==0
    c.close()


@pytest.mark.parametrize('field',['ssh','scp','budget','live','diagnostics','counter'])
def test_mutable_transport_configuration_refused(synthetic,field):
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));v=activate(c)
    original=getattr(c._transport,field)
    setattr(c._transport,field,[] if field in ('ssh','scp') else 1 if field=='counter' else None)
    with pytest.raises((ValueError,AttributeError)):v.mkdir('invented-000000000000')
    assert c._spent['commands']==0
    setattr(c._transport,field,original);c._cap=None;c.close()


def test_actual_local_child_transfers_keep_rounded_reservations(synthetic,monkeypatch,tmp_path):
    import sys
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));v=activate(c)
    receive=d.low.receive_diagnostic;remote=tmp_path/'synthetic-remote.bin';commands=[]
    def local(command,destination,**kwargs):
        commands.append(command)
        if command[0]=='scp':code='from pathlib import Path;Path('+repr(str(remote))+').write_bytes(Path('+repr(command[-2])+').read_bytes())'
        elif 'dd' in command:code='import sys;sys.stdout.buffer.write(open('+repr(str(remote))+',"rb").read())'
        else:code='pass'
        return receive([sys.executable,'-B','-c',code],destination,**kwargs)
    monkeypatch.setattr(d.low,'receive_diagnostic',local)
    source=tmp_path/'invented.bin';source.write_bytes(b'fixed artificial bytes')
    v.mkdir('invented-000000000000');v.put(source,'invented-000000000000/payload.bin');v.get('invented-000000000000/payload.bin',tmp_path/'copy.bin',expected_bytes=source.stat().st_size)
    assert (tmp_path/'copy.bin').read_bytes()==source.read_bytes()
    assert c._spent=={'logical_bytes':0,'rounded_bytes':source.stat().st_size+32768,'commands':3}
    assert len(commands)==3 and len(list(c.root.glob('reservation-*')))==2
    c._cap=None;c.close()
    with pytest.raises(ValueError,match='duplicate'):c.close()


def test_failed_child_spends_and_stops_context(synthetic,monkeypatch,tmp_path):
    import sys
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));v=activate(c)
    receive=d.low.receive_diagnostic
    monkeypatch.setattr(d.low,'receive_diagnostic',lambda command,destination,**kw:receive([sys.executable,'-B','-c','raise SystemExit(17)'],destination,**kw))
    with pytest.raises(RuntimeError):v.get('invented-000000000000/payload.bin',tmp_path/'copy.bin',expected_bytes=30)
    assert c._spent['rounded_bytes']==32768 and c._spent['commands']==1
    with pytest.raises(ValueError,match='failed context'):v.mkdir('invented-000000000000')
    assert c._spent['commands']==1
    c._cap=None;c.close()


def test_rejected_postclose_transport_cannot_poison_terminal(synthetic):
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));v=c.view('proposed');c.close()
    before={str(p):p.read_bytes() for p in c.root.rglob('*') if p.is_file()}
    with pytest.raises(ValueError,match='closed'):v.mkdir('invented-000000000000')
    assert {str(p):p.read_bytes() for p in c.root.rglob('*') if p.is_file()}==before


def test_wrong_thread_and_counter_refund_refuse_before_command(synthetic):
    import threading
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));v=activate(c);errors=[]
    def attempt():
        try:v.mkdir('invented-000000000000')
        except BaseException as e:errors.append(e)
    t=threading.Thread(target=attempt);t.start();t.join(2)
    assert not t.is_alive() and len(errors)==1 and c._spent['commands']==0
    c._spent['rounded_bytes']-=1
    with pytest.raises(ValueError,match='refund'):v.mkdir('invented-000000000000')


def test_counterfeit_operation_binding_refused(synthetic):
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}))
    with pytest.raises(ValueError,match='actual held'):
        with d.binding(c.view('proposed'),object(),object(),object(),object(),lambda:None):pass
    assert c._cap is None and c._spent['commands']==0


@pytest.mark.parametrize('kind',['short','oversized','deadline','diagnostic'])
def test_local_child_failure_modes_keep_spent_receipts(synthetic,monkeypatch,tmp_path,kind):
    import sys
    d,run,inputs,payload,refresh=synthetic
    if kind=='deadline':inputs['transport']['max_seconds']=1;refresh()
    c=d.Context(d.preflight(run,payload,{'proposed':True}));v=activate(c);receive=d.low.receive_diagnostic
    code={'short':'print("x",end="")','oversized':'print("x"*40,end="")','deadline':'import time;time.sleep(2)','diagnostic':'raise RuntimeError("synthetic failure")'}[kind]
    monkeypatch.setattr(d.low,'receive_diagnostic',lambda command,destination,**kw:receive([sys.executable,'-B','-c',code],destination,**kw))
    with pytest.raises((ValueError,RuntimeError,TimeoutError)):v.get('invented-000000000000/payload.bin',tmp_path/'copy.bin',expected_bytes=30)
    assert c._spent['rounded_bytes']==32768 and c._spent['commands']==1
    assert list(c.root.glob('command-failed-*')) and list((c.root/'diagnostics').glob('*.transport.json'))
    c._cap=None;c.close()


def test_terminal_preserves_original_fatal_when_publication_fails(synthetic,monkeypatch):
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));fatal=MemoryError('original fatal')
    monkeypatch.setattr(run,'write_json',lambda *a:(_ for _ in ()).throw(OSError('terminal receipt unavailable')))
    with pytest.raises(MemoryError) as caught:c.close(fatal)
    assert caught.value is fatal and fatal.__notes__ and (c.root/'terminal.json').exists()


def test_original_context_namespace_replacement_refuses(synthetic):
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));v=activate(c)
    original=c.root;original.rename(original.with_name(original.name+'-preserved'));original.mkdir()
    with pytest.raises(ValueError,match='namespace replaced'):v.mkdir('invented-000000000000')
    assert not list(original.iterdir())


def test_original_completed_diagnostic_cannot_be_replaced(synthetic,monkeypatch):
    import sys
    d,run,inputs,payload,refresh=synthetic;c=d.Context(d.preflight(run,payload,{'proposed':True}));v=activate(c);receive=d.low.receive_diagnostic
    monkeypatch.setattr(d.low,'receive_diagnostic',lambda command,destination,**kw:receive([sys.executable,'-B','-c','pass'],destination,**kw))
    v.mkdir('invented-000000000000')
    receipt=next((c.root/'diagnostics').glob('*.transport.json'));receipt.write_bytes(b'{}')
    with pytest.raises(ValueError,match='diagnostic'):v.mkdir('invented-000000000001')
    assert c._spent['commands']==1


def test_outer_wrapper_preflights_before_population_and_preserves_local_route(monkeypatch):
    from tradingagents.research.onchain_replication import job_payload,archive_dispatch,native_reuse,compact_native_producer
    calls=[];run=object();payload={'representation_jobs':{'x':{}}}
    monkeypatch.setattr(native_reuse,'selected',lambda *a:False)
    monkeypatch.setattr(compact_native_producer,'selected',lambda *a:False)
    def preflight(*args):calls.append('preflight');return None
    def local(*args,**kwargs):calls.append('population');assert kwargs=={'job_input':'execution_job'};return 'unchanged'
    monkeypatch.setattr(archive_dispatch,'preflight',preflight);monkeypatch.setattr(job_payload,'_execute_fit_payload',local)
    assert job_payload.execute_fit_payload(run,payload)=='unchanged' and calls==['preflight','population']


def test_outer_wrapper_closes_selected_context_with_original_failure(monkeypatch):
    from tradingagents.research.onchain_replication import job_payload,archive_dispatch,native_reuse,compact_native_producer
    calls=[];primary=MemoryError('fixed original population failure');run=object();payload={'representation_jobs':{'x':{}}}
    monkeypatch.setattr(native_reuse,'selected',lambda *a:False);monkeypatch.setattr(compact_native_producer,'selected',lambda *a:True)
    monkeypatch.setattr(archive_dispatch,'preflight',lambda *a:'selected')
    class Context:
        def __init__(self,plan):assert plan=='selected';calls.append('create')
        def close(self,error=None):assert error is primary;calls.append('close');raise error
    def fail(*args,**kwargs):assert isinstance(kwargs['archive_context'],Context);calls.append('population');raise primary
    monkeypatch.setattr(archive_dispatch,'Context',Context);monkeypatch.setattr(job_payload,'_execute_fit_payload',fail)
    with pytest.raises(MemoryError) as caught:job_payload.execute_fit_payload(run,payload)
    assert caught.value is primary and calls==['create','population','close']


def test_constructor_failure_preserves_claim_and_original_fatal(synthetic,monkeypatch):
    d,run,inputs,payload,refresh=synthetic;primary=MemoryError('transport construction failed')
    def fail(*args,**kwargs):raise primary
    monkeypatch.setattr(d,'_Transport',fail)
    with pytest.raises(MemoryError) as caught:d.Context(d.preflight(run,payload,{'proposed':True}))
    assert caught.value is primary
    root=run.admission.root/'research_artifacts/archive-dispatch-invented'
    assert (root/'intent.json').exists() and (root/'constructor-failed.json').exists()
    assert (run.directory/'outputs/archive-terminal.json').exists()
