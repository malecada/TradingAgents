"""Invented registered inputs and disposable Git claims; no study data."""
import hashlib
import json
import os
import subprocess

import pytest

from tradingagents.research import ResearchRun, runtime_hashes
from tradingagents.research.onchain_replication import imported_authority_interval as interval


@pytest.fixture
def bundle_run(tmp_path):
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=tmp_path, text=True).strip()
    git('init', '-q')
    (tmp_path/'engine.py').write_text('# invented engine\n')
    (tmp_path/'charter.md').write_text('Bounded synthetic input reads only.\n')
    digest = lambda p: hashlib.sha256((tmp_path/p).read_bytes()).hexdigest()
    inputs = {}
    for index in range(10):
        name = 'environment' if index==9 else f'role{index}'
        (tmp_path/f'{name}.json').write_bytes(f'{{"value":{index}}}'.encode())
        inputs[name] = {'path':f'{name}.json', 'sha256':digest(f'{name}.json'), 'dataset':'invented'}
    experiment = {'family':'fixture', 'parent':None, 'charter':{'path':'charter.md','sha256':digest('charter.md')},
        'question':'synthetic grouped read', 'stage':'development', 'reuse':'exploratory',
        'windows':[{'dataset':'invented','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],
        'inputs':inputs, 'source_files':{'engine.py':digest('engine.py')}, 'runtime_hashes':runtime_hashes(),
        'selection':None, 'cells':['fixture'], 'outputs':['result.json']}
    spec = {'schema_version':1,'program_id':'bundle-fixture',
        'families':{'fixture':{'mechanism_id':'invented','attempt_budget':1,'prior_attempts':0,'history_reference':'no empirical observations'}},
        'datasets':{'invented':{'identity':'invented-bundle','history_reference':'invented',
            'exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},
        'experiments':{'bundle':experiment}}
    (tmp_path/'registration.json').write_text(json.dumps(spec))
    git('add','engine.py','charter.md','registration.json')
    git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','fixture')
    run = ResearchRun.start(root=tmp_path, registration='registration.json', experiment='bundle', source=git('rev-parse','HEAD'))
    yield run
    if not (run.directory/'failed.json').exists():
        run.fail('synthetic fixture closed')


def read_bundle(run, names=None, **limits):
    return run.read_inputs(tuple(names or run.admission.inputs), max_each_bytes=limits.get('each',64), max_total_bytes=limits.get('total',1024))


def test_group_reads_real_bytes_with_two_fresh_admissions(bundle_run, monkeypatch):
    original = bundle_run._check_source
    calls = []
    def checked():
        original(); calls.append(True)
    monkeypatch.setattr(bundle_run, '_check_source', checked)
    result = read_bundle(bundle_run)
    assert result == {('environment' if i==9 else f'role{i}'):f'{{"value":{i}}}'.encode() for i in range(10)}
    assert len(calls) == 2


@pytest.mark.parametrize('names,limits', [
    (('role0','role0'),{}), (('unknown',),{}), (('role0',),{'each':4}),
    (('role0','role1'),{'total':15}), (('role0',),{'each':0}),
    (('role0',),{'total':4*1024**2+1}),
])
def test_invalid_or_over_capacity_bundle_refuses(bundle_run, names, limits):
    with pytest.raises(ValueError):read_bundle(bundle_run,names,**limits)


def test_source_mutation_at_exit_refuses_return(bundle_run, monkeypatch):
    original = bundle_run._check_source; calls = []
    def checked():
        calls.append(True)
        if len(calls) == 2:(bundle_run.admission.root/'engine.py').write_text('# changed\n')
        original()
    monkeypatch.setattr(bundle_run,'_check_source',checked)
    with pytest.raises(ValueError):read_bundle(bundle_run)
    assert len(calls)==2


def test_role_replaced_after_early_read_refuses(bundle_run, monkeypatch):
    from tradingagents.research.onchain_replication import original_dictionary
    original=original_dictionary._read_registered; calls=[]
    def changed(run,name,**kwargs):
        result=original(run,name,**kwargs); calls.append(name)
        if name=='role1':(run.admission.root/'role0.json').write_bytes(b'{"value":9}')
        return result
    monkeypatch.setattr(original_dictionary,'_read_registered',changed)
    with pytest.raises(ValueError):read_bundle(bundle_run)


@pytest.mark.parametrize('replacement',['symlink','hardlink'])
def test_redirect_or_linked_role_refuses(bundle_run,replacement):
    path=bundle_run.admission.root/'role0.json';other=path.with_name('other.json')
    other.write_bytes(path.read_bytes());path.unlink()
    if replacement=='symlink':path.symlink_to(other.name)
    else:os.link(other,path)
    with pytest.raises(ValueError):read_bundle(bundle_run)


def test_terminal_claim_cannot_read_bundle(bundle_run):
    bundle_run.fail('invented terminal')
    with pytest.raises(ValueError,match='terminal'):read_bundle(bundle_run)


def policy():
    return {'schema_version':1,'kind':interval.KIND,'live_interval_ms':1000,'fingerprint_interval_ms':2000,
        'full_interval_ms':3000,'max_stale_ms':60000,'max_calls_between_full':10000,'assumption':interval.ASSUMPTION}


def test_ten_slow_reads_expire_but_grouped_reads_fit(bundle_run,monkeypatch):
    now=[0.0]; original=bundle_run._check_source
    def checked():original();now[0]+=15.0
    monkeypatch.setattr(bundle_run,'_check_source',checked)
    lease=interval.Interval(policy(),clock=lambda:now[0]);lease.validate(lambda:None,lambda:None,lambda:None,boundary=True)
    for name in bundle_run.admission.inputs:bundle_run.read_input(name)
    with pytest.raises(ValueError,match='stale'):lease.validate(lambda:None,lambda:None,lambda:None,boundary=True)
    now[0]=0.;lease=interval.Interval(policy(),clock=lambda:now[0]);lease.validate(lambda:None,lambda:None,lambda:None,boundary=True)
    read_bundle(bundle_run)
    lease.validate(lambda:None,lambda:None,lambda:None,boundary=True)
    assert now[0]==30.0


def test_indivisible_over_deadline_validation_still_refuses():
    now=[0.0];lease=interval.Interval(policy(),clock=lambda:now[0])
    def slow():now[0]+=61.
    with pytest.raises(ValueError,match='stale'):lease.validate(slow,lambda:None,lambda:None,boundary=True)


def test_selected_backend_parsers_share_one_genuine_bundle(bundle_run,monkeypatch):
    from tradingagents.research.onchain_replication import compact_mcm_batched as backend
    monkeypatch.setattr(backend,'_compiled_policy',lambda execution:{})
    monkeypatch.setattr(backend,'_edge_policy',lambda execution:{})
    seen=[];original=bundle_run._check_source
    def checked():original();seen.append('source')
    monkeypatch.setattr(bundle_run,'_check_source',checked)
    def parse(execution,run,*,registered=None):
        assert registered is not None
        assert set(registered)=={'role0','role1','role2','role3','role4','role5','role6','role7','environment'}
        assert registered['role0']==b'{"value":0}'
        return tuple(sorted(registered))
    monkeypatch.setattr(backend,'_compiled_inputs',parse);monkeypatch.setattr(backend,'_edge_inputs',parse)
    execution={'backend_input_policy':'source-checked-backend-role-bundle-v1',
        'compiled_normalization_inputs':{'source':'role0','library':'role1','runtime':'role2'},
        'compiled_edge_inputs':{'source':'role3','adapter':'role4','library':'role5','runtime':'role6','abi':'role7'}}
    normalization,edge=backend._backend_inputs(execution,bundle_run)
    assert normalization==edge and len(seen)==2


def test_backend_bundle_absent_selection_preserves_legacy_calls(bundle_run,monkeypatch):
    from tradingagents.research.onchain_replication import compact_mcm_batched as backend
    calls=[]
    def legacy(execution,run):calls.append(execution);return 'legacy'
    monkeypatch.setattr(backend,'_compiled_inputs',legacy);monkeypatch.setattr(backend,'_edge_inputs',legacy)
    monkeypatch.setattr(bundle_run,'read_inputs',lambda *a,**k:pytest.fail('unselected bundle'))
    assert backend._backend_inputs({},bundle_run)==('legacy','legacy') and calls==[{},{}]
