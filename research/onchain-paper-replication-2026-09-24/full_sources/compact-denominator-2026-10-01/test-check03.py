"""Actual compact Training joined to its complete registered daily calendar."""
from dataclasses import asdict,replace
from types import SimpleNamespace
import shutil
import pytest
import numpy as np
from tests.research.test_lifecycle import git
from tests.research.onchain_replication import test_compact_training as training
from tradingagents.research.onchain_replication.calendar import build_folds
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,PricePanel
from tradingagents.research.onchain_replication.dataset import build_examples
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,file_hash

ROOT=training.first.ROOT if hasattr(training.first,'ROOT') else __import__('pathlib').Path(__file__).resolve().parents[3]
VALIDATOR='research/onchain-paper-replication-2026-09-24/full_sources/representation-denominator-2026-10-01/denominator.py'
def stamp(day):return day+'T00:00:00Z'
COVERAGE={'source_hashes':['a'*64]}
CALENDAR={'lookback_days':2,'folds':[{'id':'tiny','train_start':stamp('2024-01-15'),
    'train_end':stamp('2024-02-01'),'test_start':stamp('2024-02-02'),'test_end':stamp('2024-02-04'),
    'validation_start':None,'validation_end':None}]}

def population():
    graphs=[]
    for start,end,available in [('2024-01-15','2024-01-22','2024-01-23'),('2024-01-22','2024-01-29','2024-01-30')]:
        graphs.append(GraphSnapshot('ETH',stamp(start),stamp(end),stamp(available),('a'*64,),'a'*64,
            ('a','b'),np.ones((2,4)),np.array([[0],[1]],dtype=np.int64),np.ones((1,2)),1,1,{}))
    dates=('2024-01-28','2024-01-29','2024-01-30','2024-01-31','2024-02-01','2024-02-02','2024-02-03')
    prices=PricePanel('ETH-USD',dates,tuple(100.+i for i in range(7)),(),'b'*64,stamp('2026-01-01'))
    fold=build_folds(CALENDAR,COVERAGE)[0]
    return graphs,fold,build_examples(graphs,prices,fold,CALENDAR)

@pytest.fixture
def admitted(request,monkeypatch):
    option=getattr(request,'param','valid');original=training.first.Tests.fixture
    def chosen_population():
        graphs,fold,examples=population()
        if option=='truncated':
            rows=examples.test[:1]
            examples=replace(examples,test=rows,test_mask_hash=digest(canonical_bytes([r.decision_at for r in rows])))
        return graphs,fold,examples
    monkeypatch.setattr(training,'population',chosen_population)
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            t.input('denominator_calendar',CALENDAR | ({'lookback_days':500000} if option=='lookback' else {}))
            t.input('denominator_coverage',COVERAGE if option!='coverage' else {'source_hashes':['c'*64]})
            t.input('compact_denominator',{'schema_version':1,'calendar_input':'denominator_calendar',
                'coverage_input':'denominator_coverage','max_calendar_days':4 if option=='cap' else 64})
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item['compact_denominator_input']='compact_denominator'
            path=t.root/VALIDATOR;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/VALIDATOR,path);git(t.root,'add','--',VALIDATOR)
            t.exp['source_files'][VALIDATOR]=file_hash(path)
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=training.admitted.__wrapped__(SimpleNamespace(param='valid'));owner,args,t=next(gen)
    try:yield training.admit(owner,args),t
    finally:
        try:next(gen)
        except StopIteration:pass

def api():
    from tradingagents.research.onchain_replication import compact_denominator
    return compact_denominator


def test_actual_complete_calendar_without_sampling(admitted):
    route,t=admitted;m=api();result=m.admit(route,input_name='compact_denominator');result.check()
    d=result.record['denominator']
    assert d['calendar_days']==20 and d['train_rows']==2 and d['test_rows']==2
    assert sum(d['excluded_by_reason'].values())==16
    assert d['price_exclusions_revalidated'] is False
    assert result.record['graph_completion_validated'] is False and not route.owner.stages


@pytest.mark.parametrize('admitted',['truncated','coverage','cap'],indirect=True)
def test_registered_but_incomplete_or_inconsistent_calendar_refused(admitted):
    route,t=admitted
    with pytest.raises(ValueError):api().admit(route,input_name='compact_denominator')
    assert not route.owner.stages


def test_original_population_rechecked_after_callback(admitted,monkeypatch):
    route,t=admitted;m=api();result=m.admit(route,input_name='compact_denominator');lease=route.lease
    def changed():
        lease();route.graphs[0].node_features.setflags(write=True);route.graphs[0].node_features[0,0] += 1
    monkeypatch.setattr(type(route),'lease',lambda self:changed())
    with pytest.raises(ValueError):result.check()


@pytest.mark.parametrize('admitted',['lookback'],indirect=True)
def test_lookback_mismatch_refused_before_calendar_allocation(admitted,monkeypatch):
    route,t=admitted;m=api();validator=m._validator();calls=[]
    def refused(*args,**kwargs):
        calls.append(1);raise AssertionError('calendar allocation reached despite actual row mismatch')
    monkeypatch.setattr(validator,'validate',refused);monkeypatch.setattr(m,'_validator',lambda:validator)
    with pytest.raises(ValueError,match='lookback'):m.admit(route,input_name='compact_denominator')
    assert not calls


def test_final_receipt_callback_cannot_hide_original_graph_mutation(admitted,monkeypatch):
    route,t=admitted;m=api();result=m.admit(route,input_name='compact_denominator')
    source=m._sources;lease=type(route).lease;ready=[]
    def sources(value):
        answer=source(value);ready.append(True);return answer
    def changed(self):
        lease(self)
        if ready:
            self.graphs[0].node_features.setflags(write=True)
            self.graphs[0].node_features[0,0] += 1
    monkeypatch.setattr(m,'_sources',sources);monkeypatch.setattr(type(route),'lease',changed)
    with pytest.raises(ValueError,match='original graphs'):result.check()
