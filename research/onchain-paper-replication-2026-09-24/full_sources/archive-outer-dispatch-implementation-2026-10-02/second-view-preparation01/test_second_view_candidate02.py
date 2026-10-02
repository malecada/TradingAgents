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
from copy import deepcopy

import pytest

from tests.research.onchain_replication import test_archive_producer_integration as upstream
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash


@pytest.fixture
def released(request):
    reference=os.environ.get('ARCHIVE_OUTER_SECOND_VIEW_RELEASE')
    if not reference:pytest.skip('unexecuted proposal; coordinator source/fixture release required')
    path=Path(reference)
    expected=os.environ.get('ARCHIVE_OUTER_SECOND_VIEW_RELEASE_SHA256')
    assert expected is not None and file_hash(path)==expected
    spec=json.loads(path.read_bytes())
    assert spec['status']=='released_single_isolated_synthetic_attempt'
    assert spec['identity']=='archive-outer-two-view-20261002-01'
    source=Path(__file__).resolve().parents[3]
    assert source==Path(spec['isolated_source_root']).resolve(strict=True)
    assert spec['source_files'] and all(file_hash(source/name)==sha for name,sha in spec['source_files'].items())
    case=request.param
    assert case in spec['cases']==['success','second_view_failure']
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
        'rate_kbit':32768,'max_seconds':5,'max_payload_bytes':64*1024**2,'max_commands':512,
        'max_diagnostic_bytes':128*1024**2,'max_control_bytes':272*1024**2,
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
                archived['remote_namespace']={'success':'sv1-ok','second_view_failure':'sv1-fail'}[case]
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
            # r2 has independent scientific/cache identity, outputs and remote
            # namespace, but exactly the same registered transport input.
            second_item=deepcopy(t.item);second_job=deepcopy(job)
            second_policy=json.loads((t.root/'archive_policy.json').read_bytes())
            second_policy['remote_namespace']={'success':'sv2-ok','second_view_failure':'sv2-fail'}[case]
            t.input('archive_policy_r2',second_policy)
            for item in (second_item,second_job):
                item['compact_archive_input']='archive_policy_r2'
                item['descriptor']['compact_archive_execution']['policy_sha256']=t.exp['inputs']['archive_policy_r2']['sha256']
                item['descriptor']['seed']=13
            for item in (second_item,second_job):
                item['binding_output']='r2-binding.json'
                item['journal_output']='r2-journal.json'
            second_job['producer']='p2'
            t.plan['producers']['p2']=second_item
            t.execution['payload']['representation_jobs']['r2']=second_job
            t.exp['outputs']+=['r2-binding.json','r2-journal.json','r2-failure.json']
            batch['representations']['r2']={'output':'r2-binding.json','failure_output':'r2-failure.json'}
            second_cell=deepcopy(batch['cells'][0]);second_cell['representation']='r2'
            second_cell['cell'].update(id='sum-r2',seed=13)
            batch['cells'].append(second_cell)
            t.input('outer_batch_plan',batch)

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


@pytest.mark.parametrize('released',['success','second_view_failure'],indirect=True)
def test_actual_two_views_share_original_job_accounting(admitted,monkeypatch):
    from tradingagents.research.onchain_replication import archive_dispatch as dispatch,archive_transport
    from tradingagents.research.onchain_replication import job_payload,run as batch,compact_native_producer
    case,attempt,t,job,graphs,examples=admitted
    from tradingagents.research.lifecycle import _immutable
    held={};contexts=[];commands=[];ledgers={};after_terminal=[]
    remote=attempt/'remote-child-harness';remote.mkdir()
    original_init=dispatch.Context.__init__;original_outer=dispatch.Context._outer
    def initialized(context,*args,**kwargs):
        original_init(context,*args,**kwargs);contexts.append(context)
    def observed_outer(context):
        value=original_outer(context)  # Original joins still execute.
        if 'outer-terminal.json' in context._run._published_outputs:
            after_terminal.append({'intent_sha256':file_hash(context.root/'intent.json'),
                'output_sha256':file_hash(context._run.directory/'outputs/outer-terminal.json')})
        return value
    monkeypatch.setattr(dispatch.Context,'__init__',initialized)
    monkeypatch.setattr(dispatch.Context,'_outer',observed_outer)
    receive=archive_transport.receive_diagnostic
    def local(command,destination,**kwargs):
        assert len(contexts)==1 and not held.get('postclose')
        context=contexts[0];cap=context._cap;assert cap is not None
        name=cap['view']._name;ledger=cap['ledger'];ledgers[name]=ledger
        assert cap['view'] is context.view(name)
        stage=ledger.owner.active
        kind='upload' if command[0]=='scp' else 'mkdir' if 'mkdir' in command else 'download'
        commands.append({'view':name,'kind':kind,'stage_kind':stage.kind,
            'rounded_before':context._spent['rounded_bytes'],'commands_reserved':context._spent['commands']})
        if name=='r2' and 'first_view_closed' not in held:
            first=ledgers['r'];assert first.owner.closed and first._closed and not first._poisoned
            held['first_view_closed']={str(p):p.read_bytes() for p in first.root.rglob('*') if p.is_file()}
            first_job=payload['representation_jobs']['r']
            first_item=json.loads(t.run.read_input(first_job['plan_input']))['producers'][first_job['producer']]
            publication_paths=[first.owner.root/'complete.json',first.owner.root.parent/'complete.json',
                t.run.directory/'outputs'/first_item['binding_output'],
                t.run.directory/'outputs'/first_item['journal_output']]
            marker=json.loads((first.owner.root.parent/'complete.json').read_bytes())
            publication_paths.append(Path(marker['publication']['path']))
            held['first_publications']={str(p):p.read_bytes() for p in publication_paths}
            held['first_reserved']=dict(first.reserved)
            held['first_commands']=len([x for x in commands if x['view']=='r'])
            held['rounded_at_second_view']=context._spent['rounded_bytes']
            assert held['rounded_at_second_view']>0
            _immutable(attempt/'first-view-carry-forward.json',{
                'first_representation':'r','next_representation':'r2',
                'first_ledger_path':str(first.root.relative_to(t.root)),
                'ledger_files':{str(Path(p).relative_to(t.root)):digest(raw) for p,raw in held['first_view_closed'].items()},
                'publication_files':{str(Path(p).relative_to(t.root)):digest(raw) for p,raw in held['first_publications'].items()},
                'first_ledger_reserved':held['first_reserved'],'first_commands_completed':held['first_commands'],
                'original_context_spent_at_first_r2_dispatch':dict(context._spent),
                'boundary_note':'Current r2 command and operation reservations are already included; no r2 local child has dispatched yet.',
                'intent_sha256':file_hash(context.root/'intent.json')})
        if case=='second_view_failure' and name=='r2' and kind=='download' and not held.get('injected'):
            held.update(injected=True,failure_spent=dict(context._spent),second_reserved=dict(ledger.reserved))
            vector=[sys.executable,'-B','-c','raise SystemExit(19)']
        elif kind=='upload':
            member=command[-1].split(':',1)[1]
            vector=[sys.executable,'-B','-c','from pathlib import Path;p=Path('+repr(str(remote/member))+');p.open("xb").write(Path('+repr(command[-2])+').read_bytes())']
        elif kind=='mkdir':
            vector=[sys.executable,'-B','-c','from pathlib import Path;Path('+repr(str(remote/command[-1]))+').mkdir()']
        else:
            assert 'dd' in command
            member=next(x[3:] for x in command if x.startswith('if='))
            vector=[sys.executable,'-B','-c','import sys;sys.stdout.buffer.write(open('+repr(str(remote/member))+',"rb").read())']
        return receive(vector,destination,**kwargs)
    monkeypatch.setattr(archive_transport,'receive_diagnostic',local)
    def preflight(run,populations,**kwargs):
        assert run is t.run and kwargs['plan_input']=='outer_batch_plan'
        assert set(populations)=={'whole'} and len(populations['whole'][0].train)==2 and len(populations['whole'][0].test)==2
    def no_fit(run,populations,prepared,**kwargs):
        assert run is t.run and set(prepared)=={'r','r2'}
        held.update(prepared=prepared,postclose=True)
        return {'synthetic_only':True,'financial_fit_count':0}
    monkeypatch.setattr(batch,'preflight_batch',preflight)
    monkeypatch.setattr(batch,'execute_batch',no_fit)
    payload=json.loads(t.run.read_input('execution_job'))['payload']
    if case=='second_view_failure':
        with pytest.raises(compact_native_producer.CompactProducerError):job_payload.execute_fit_payload(t.run,payload)
        assert held['injected'] and 'prepared' not in held
        assert ledgers['r2']._closed and ledgers['r2']._poisoned
        assert not (ledgers['r2'].owner.root/'complete.json').exists()
    else:
        assert job_payload.execute_fit_payload(t.run,payload)=={'synthetic_only':True,'financial_fit_count':0}
        for name,prepared in held['prepared'].items():
            terminal=prepared.features._terminal;owner=terminal._owner
            assert owner is ledgers[name].owner and owner.closed
            assert owner.stages['dictionary'].contract['pairs']==20
            assert all(s.contract['pairs']==6 for n,s in owner.stages.items() if n!='dictionary')
            terminal.check();compact_native_producer.finalize(prepared)
    assert len(contexts)==1 and set(ledgers)=={'r','r2'}
    context=contexts[0];assert context._closed and context.view('r') is not context.view('r2')
    assert context.view('r')._context is context.view('r2')._context is context
    assert {str(p) for p in ledgers['r'].root.rglob('*') if p.is_file()}==set(held['first_view_closed'])
    assert all(Path(p).read_bytes()==raw for p,raw in held['first_view_closed'].items())
    assert all(Path(p).read_bytes()==raw for p,raw in held['first_publications'].items())
    assert dict(ledgers['r'].reserved)==held['first_reserved']
    terminal=json.loads((t.run.directory/'outputs/outer-terminal.json').read_bytes())
    start=json.loads((t.run.directory/'outputs/outer-start.json').read_bytes())
    assert set(start['representations'])=={'r','r2'} and after_terminal
    assert start['intent_sha256']==terminal['intent_sha256']==file_hash(context.root/'intent.json')
    assert all(x['intent_sha256']==terminal['intent_sha256'] for x in after_terminal)
    assert all(x['output_sha256']==file_hash(t.run.directory/'outputs/outer-terminal.json') for x in after_terminal)
    assert terminal['spent']['logical_bytes']==sum(x.reserved['decoded_transfer_bytes'] for x in ledgers.values())
    reservations=[json.loads(p.read_bytes()) for p in context.root.glob('reservation-*.json')]
    command_records=[json.loads(p.read_bytes()) for p in context.root.glob('command-[0-9]*.json')]
    assert terminal['spent']['rounded_bytes']==sum(x['bytes'] for x in reservations)>held['rounded_at_second_view']
    assert terminal['spent']['commands']==len(command_records)==len(commands)>held['first_commands']
    assert [x['commands_reserved'] for x in commands]==list(range(1,len(commands)+1))
    assert [x['rounded_before'] for x in commands]==sorted(x['rounded_before'] for x in commands)
    assert terminal['status']==('failed' if case=='second_view_failure' else 'complete')
    if case=='second_view_failure':
        assert all(terminal['spent'][k]>=v for k,v in held['failure_spent'].items())
        assert all(ledgers['r2'].reserved[k]>=v for k,v in held['second_reserved'].items())
    before={str(p):p.read_bytes() for p in context.root.rglob('*') if p.is_file()}
    for name in ('r','r2'):
        with pytest.raises(ValueError):context.view(name).mkdir('postclose')
    assert before=={str(p):p.read_bytes() for p in context.root.rglob('*') if p.is_file()}
    (attempt/'second-view-observations.json').write_bytes(canonical_bytes({'case':case,'commands':commands,
        'after_terminal_original_joins':after_terminal,'financial_fit_count':0,'raw_fixture_root':str(t.root),
        'mock_guard':True,'ssh_interoperability_proven':False,'views':['r','r2']}))
