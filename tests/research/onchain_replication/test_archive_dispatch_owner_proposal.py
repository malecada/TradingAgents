"""Prepared-only outer owner fixture; explicit coordinator release is mandatory.

Reuses accepted actual-owner fixture contracts. Guard and final fitting are
synthetic boundaries; registered source/input/journal/owner admission is real.
No SSH vector is executed. No empirical/model fit is permitted by this file.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

import pytest

from tests.research.onchain_replication import test_archive_producer_integration as upstream
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash


@pytest.fixture
def released(request):
    reference=os.environ.get('ARCHIVE_OUTER_FIXTURE_RELEASE')
    if not reference:pytest.skip('unexecuted proposal; coordinator source/fixture release required')
    path=Path(reference)
    expected=os.environ.get('ARCHIVE_OUTER_FIXTURE_RELEASE_SHA256')
    assert expected is not None and file_hash(path)==expected
    spec=json.loads(path.read_bytes())
    assert spec['status']=='released_single_isolated_synthetic_attempt'
    source=Path(__file__).resolve().parents[3]
    assert source==Path(spec['isolated_source_root']).resolve(strict=True)
    assert spec['source_files'] and all(file_hash(source/name)==sha for name,sha in spec['source_files'].items())
    case=request.param
    assert case in spec['cases']==['success','late_failure','local']
    root=Path(spec['attempt_root'])/case
    assert root.parent.resolve(strict=True)==root.parent and not os.path.lexists(root)
    root.mkdir()  # A repeated invocation is refused; no historical fixture reopened.
    return case,root


@pytest.fixture
def admitted(released,monkeypatch):
    from tradingagents.research.onchain_replication import archive_dispatch as dispatch
    from tradingagents.research.onchain_replication.dataset import Scaler
    from tradingagents.research.onchain_replication.graph_store import save_graph
    from tradingagents.research.onchain_replication.job_payload import population_record
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash
    case,attempt=released
    training=upstream.native.upstream.upstream.upstream.upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    config={'schema_version':1,'format':dispatch.FORMAT,
        'connection':{'host':'synthetic.invalid','user':'invented','port':23,
            'identity_file':'/unopened/synthetic/key','known_hosts_file':'/unopened/synthetic/hosts'},
        'rate_kbit':32768,'max_seconds':5,'max_payload_bytes':32*1024**2,'max_commands':256,
        'max_diagnostic_bytes':64*1024**2,'max_control_bytes':136*1024**2,
        'namespace':'outer-'+case,'receipt_output':'outer-start.json','terminal_output':'outer-terminal.json'}
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            graphs,fold,examples=upstream.native.dates.population()
            scaler=Scaler(0.,1.,tuple(x.decision_at for x in examples.train),examples.train_hash)
            t.input('outer_population',population_record(examples,scaler))
            refs={}
            for i,g in enumerate(graphs):
                metadata=save_graph(t.root/'outer-graphs'/str(i),g);name='outer_graph_'+str(i)
                t.exp['inputs'][name]={'path':str(metadata.relative_to(t.root)),'sha256':file_hash(metadata),'dataset':'sample'}
                refs[graph_hash(g)]={'input':name}
            job=t.execution['payload']['representation_jobs']['r']
            for item in (t.item,job):
                item.update(graphs=refs,population='whole')
                if case=='local':
                    item.pop('compact_archive_input',None)
                    item['descriptor'].pop('compact_archive_execution',None)
                else:item[dispatch.KEY]='outer_transport'
            if case!='local':
                archived=json.loads((t.root/'archive_policy.json').read_bytes())
                archived['transport_identity']=dispatch._connection(config['connection'])
                archived['remote_namespace']='outer-'+case
                t.input('archive_policy',archived);t.input('outer_transport',config)
                for item in (t.item,job):
                    item['descriptor']['compact_archive_execution']['policy_sha256']=t.exp['inputs']['archive_policy']['sha256']
                t.exp['outputs']+=['outer-start.json','outer-terminal.json']
            batch={'populations':{'whole':{}},'representations':{'r':{'output':t.item['binding_output'],'failure_output':'outer-representation.json'}},
                'cells':[{'status':'ready','population':'whole','representation':'r',
                    'cell':{'id':'sum','arm':'proposed','seed':job['descriptor']['seed'],'fold':fold.id}}]}
            t.input('outer_batch_plan',batch)
            t.exp['outputs'].append('outer-representation.json')
            t.execution['payload'].update(population_inputs={'whole':'outer_population'},batch_plan_input='outer_batch_plan')
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    # Accepted helpers normally delete temporary fixture roots. Preserve every
    # raw run and failed setup under this fresh released case directory instead.
    make=tempfile.mkdtemp
    class RetainedTemporaryDirectory:
        def __init__(self,*args,**kwargs):self.name=make(prefix='registered-',dir=attempt)
        def cleanup(self):pass
        def __enter__(self):return self.name
        def __exit__(self,*args):pass
    with monkeypatch.context() as scoped:
        scoped.setattr(tempfile,'TemporaryDirectory',RetainedTemporaryDirectory)
        gen=upstream.admitted.__wrapped__(monkeypatch,attempt,SimpleNamespace(param='capacity'))
        values=next(gen)
    t,job,graphs,examples,unused_local_transport=values
    (attempt/'run-reference.json').write_bytes(canonical_bytes({'root':str(t.root),'source_commit':t.source,
        'experiment_id':t.run.admission.experiment_id,'scope':'fresh isolated synthetic fixture; no historical study identity',
        'case':case,'mocked_boundaries':['kernel guard','financial batch preflight/execution']}))
    try:yield case,attempt,t,job,graphs,examples
    finally:gen.close()


@pytest.mark.parametrize('released',['success','late_failure','local'],indirect=True)
def test_actual_outer_archive_dispatch_route_proposal(admitted,monkeypatch):
    from tradingagents.research.onchain_replication import archive_dispatch as dispatch,archive_transport
    from tradingagents.research.onchain_replication import job_payload,run as batch,compact_native_producer
    case,attempt,t,job,graphs,examples=admitted
    retained={};contexts=[];commands=[];remote=attempt/'remote-child-harness';remote.mkdir()
    original_init=dispatch.Context.__init__
    def initialized(context,*args,**kwargs):
        original_init(context,*args,**kwargs);contexts.append(context)
    monkeypatch.setattr(dispatch.Context,'__init__',initialized)
    receive=archive_transport.receive_diagnostic
    def local(command,destination,**kwargs):
        assert contexts and not retained.get('postclose')
        c=contexts[-1];cap=c._cap;assert cap is not None
        ledger=cap['ledger'];stage=ledger.owner.active
        commands.append({'command_kind':'upload' if command[0]=='scp' else command[-1] if 'mkdir' in command else 'download',
            'stage':stage.name,'kind':stage.kind,'rounded_before':c._spent['rounded_bytes']})
        if case=='late_failure' and stage.kind=='mcm' and 'dd' in command and not retained.get('injected'):
            retained.update(injected=True,ledger=ledger,prior_spent=dict(ledger.reserved),
                prior_dictionary={str(p):p.read_bytes() for op in ledger._operations.values()
                    if op._stage.kind=='dictionary' for p in op.root.glob('*.json')})
            vector=[sys.executable,'-B','-c','raise SystemExit(19)']
        elif command[0]=='scp':
            member=command[-1].split(':',1)[1]
            vector=[sys.executable,'-B','-c',
                'from pathlib import Path; p=Path('+repr(str(remote/member))+'); p.open("xb").write(Path('+repr(command[-2])+').read_bytes())']
        elif 'mkdir' in command:
            vector=[sys.executable,'-B','-c','from pathlib import Path;Path('+repr(str(remote/command[-1]))+').mkdir()']
        else:
            assert 'dd' in command
            member=next(x[3:] for x in command if x.startswith('if='))
            vector=[sys.executable,'-B','-c','import sys;sys.stdout.buffer.write(open('+repr(str(remote/member))+',"rb").read())']
        assert vector[0]==sys.executable
        return receive(vector,destination,**kwargs)
    monkeypatch.setattr(archive_transport,'receive_diagnostic',local)
    def preflight(run,populations,**kwargs):
        assert run is t.run and kwargs['plan_input']=='outer_batch_plan'
        assert set(populations)=={'whole'} and len(populations['whole'][0].train)==2 and len(populations['whole'][0].test)==2
    def no_fit(run,populations,prepared,**kwargs):
        assert run is t.run and set(prepared)=={'r'}
        retained.update(prepared=prepared['r'],postclose=True)
        return {'synthetic_only':True,'financial_fit_count':0}
    monkeypatch.setattr(batch,'preflight_batch',preflight);monkeypatch.setattr(batch,'execute_batch',no_fit)
    payload=json.loads(t.run.read_input('execution_job'))['payload']
    if case=='late_failure':
        with pytest.raises(compact_native_producer.CompactProducerError):job_payload.execute_fit_payload(t.run,payload)
        assert retained['injected'] and len(contexts)==1
        ledger=retained['ledger'];assert ledger._closed and ledger._poisoned
        assert all(Path(p).read_bytes()==raw for p,raw in retained['prior_dictionary'].items())
        assert all(ledger.reserved[k]>=v for k,v in retained['prior_spent'].items())
        assert json.loads((t.run.directory/'outputs/outer-terminal.json').read_bytes())['status']=='failed'
        assert not (ledger.owner.root/'complete.json').exists()
    else:
        result=job_payload.execute_fit_payload(t.run,payload)
        assert result=={'synthetic_only':True,'financial_fit_count':0}
        prepared=retained['prepared'];terminal=prepared.features._terminal;owner=terminal._owner
        assert owner.closed and owner.stages['dictionary'].contract['pairs']==20
        assert all(s.contract['pairs']==6 for n,s in owner.stages.items() if n!='dictionary')
        terminal.check();compact_native_producer.finalize(prepared)
        if case=='local':
            assert not contexts and not commands and not hasattr(owner,'_archive_operations')
            assert not list((t.root/'research_artifacts').glob('archive-dispatch-*'))
        else:
            assert len(contexts)==1;context=contexts[0];ledger=owner._archive_operations
            assert context._closed and ledger._closed and not ledger._poisoned
            assert {c['kind'] for c in commands}=={'dictionary','mcm'}
            assert [x['rounded_before'] for x in commands]==sorted(x['rounded_before'] for x in commands)
            start=json.loads((t.run.directory/'outputs/outer-start.json').read_bytes())
            completed=json.loads((t.run.directory/'outputs/outer-terminal.json').read_bytes())
            assert start['intent_sha256']==file_hash(context.root/'intent.json')==completed['intent_sha256']
            assert completed['status']=='complete' and completed['spent']['logical_bytes']==ledger.reserved['decoded_transfer_bytes']
            records=[json.loads(p.read_bytes()) for p in context.root.glob('reservation-*.json')]
            assert sum(x['bytes'] for x in records)==completed['spent']['rounded_bytes']>0
            before={str(p):p.read_bytes() for p in context.root.rglob('*') if p.is_file()}
            with pytest.raises(ValueError):context.view('r').mkdir('postclose')
            assert before=={str(p):p.read_bytes() for p in context.root.rglob('*') if p.is_file()}
    (attempt/'fixture-observations.json').write_bytes(canonical_bytes({'case':case,'commands':commands,
        'financial_fit_count':0,'raw_fixture_root':str(t.root),'mock_guard':True,'ssh_interoperability_proven':False}))
