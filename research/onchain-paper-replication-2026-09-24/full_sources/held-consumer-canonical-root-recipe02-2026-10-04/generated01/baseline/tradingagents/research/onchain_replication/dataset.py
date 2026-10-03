"""Auditable daily example membership and training-only fitted price scaling."""
from dataclasses import dataclass,asdict
from datetime import timedelta
import numpy as np
from .calendar import eligible,expected_week,stamp
from .provenance import utc,canonical_bytes,digest,freeze
from .neighborhoods import graph_hash


@dataclass(frozen=True)
class Example:
    decision_at:str
    label_start:str
    label_end:str
    max_input_available_at:str
    input_dates:tuple[str,...]
    input_prices:tuple[float,...]
    graph_hashes:tuple[str,...]
    graph_available_at:tuple[str,...]
    target_price:float
    up:int


@dataclass(frozen=True)
class ExampleManifest:
    train:tuple[Example,...]
    test:tuple[Example,...]
    exclusions:tuple
    train_hash:str
    test_mask_hash:str
    source_hashes:tuple[str,...]
    fold_hash:str

    def require_test_mask(self,expected):
        if self.test_mask_hash!=expected:raise ValueError('common test mask mismatch')


@dataclass(frozen=True)
class Scaler:
    mean:float
    std:float
    dates:tuple[str,...]
    train_hash:str

    def transform(self,x):return (np.asarray(x)-self.mean)/self.std
    def inverse(self,x):return np.asarray(x)*self.std+self.mean


@dataclass(frozen=True)
class CalendarGraph:
    """Metadata only: identity must come from a separately admitted graph manifest."""
    asset:str
    start_utc:str
    end_utc:str
    available_at:str
    source_hashes:tuple[str,...]
    identity:str


def build_examples(graphs,prices,fold,config):
    metadata=(CalendarGraph(g.asset,g.start_utc,g.end_utc,g.available_at,
                            g.source_hashes,graph_hash(g)) for g in graphs)
    return build_examples_from_metadata(metadata,prices,fold,config)


def build_examples_from_metadata(graphs,prices,fold,config):
    if len(prices.dates)!=len(prices.closes) or len(set(prices.dates))!=len(prices.dates):raise ValueError('invalid price membership')
    lookup=dict(zip(prices.dates,prices.closes,strict=True))
    if not all(np.isfinite(v) and v>0 for v in lookup.values()):raise ValueError('invalid close')
    graph_map={};sources={prices.source_hash}
    for g in graphs:
        if prices.symbol!=g.asset+'-USD':raise ValueError('asset mismatch')
        key=stamp(g.start_utc)
        if key in graph_map:raise ValueError('duplicate weekly graph')
        if utc(g.start_utc).weekday()!=0 or utc(g.start_utc).time().isoformat()!='00:00:00' or utc(g.end_utc)-utc(g.start_utc)!=timedelta(days=7):raise ValueError('invalid complete week')
        if utc(g.available_at)<utc(g.end_utc)+timedelta(days=1):raise ValueError('graph availability precedes frozen lag')
        graph_map[key]=(g,g.identity);sources.update(g.source_hashes)
    train=[];test=[];excluded=[]
    decision=utc(fold.train_start)
    while decision<utc(fold.test_end):
        d=stamp(decision);label_end=stamp(decision+timedelta(days=1))
        is_train=decision<utc(fold.train_end)
        reason=None
        if is_train and utc(label_end)>=utc(fold.test_start):reason='purged_training_label'
        elif not is_train and decision<utc(fold.test_start):reason='outside_fold'
        elif not is_train and utc(label_end)>utc(fold.test_end):reason='test_label_boundary'
        dates=tuple((decision-timedelta(days=i)).date().isoformat() for i in range(config['lookback_days'],0,-1))
        target_date=decision.date().isoformat()
        if reason is None and (any(date not in lookup for date in dates) or target_date not in lookup):reason='warmup_or_missing_price'
        selected=[]
        if reason is None:
            for date in dates:
                step=stamp(utc(date+'T00:00:00Z')+timedelta(days=1))
                graph=graph_map.get(expected_week(step))
                if graph is None:reason='missing_expected_graph';break
                if not eligible(graph[0].available_at,step):reason='late_expected_graph';break
                selected.append(graph)
        if reason is not None:excluded.append(freeze({'decision_at':d,'reason':reason,'partition':'train' if is_train else 'test'}))
        else:
            available=tuple(stamp(g.available_at) for g,_ in selected)
            example=Example(d,d,label_end,max(d,*available),dates,tuple(lookup[x] for x in dates),tuple(h for _,h in selected),available,lookup[target_date],int(lookup[target_date]>lookup[dates[-1]]))
            (train if is_train else test).append(example)
        decision+=timedelta(days=1)
    return ExampleManifest(tuple(train),tuple(test),tuple(excluded),digest(canonical_bytes([asdict(x) for x in train])),digest(canonical_bytes([x.decision_at for x in test])),tuple(sorted(sources)),fold.member_hash)


def fit_scaler(examples,prices,fold):
    dates=tuple(sorted({d for x in examples.train for d in x.input_dates if utc(fold.train_start)<=utc(d+'T00:00:00Z')<utc(fold.train_end)}))
    if not dates:raise ValueError('empty scaler population')
    lookup=dict(zip(prices.dates,prices.closes,strict=True));values=np.array([lookup[d] for d in dates],dtype=np.float64)
    mean=float(values.mean());std=float(values.std(ddof=0))
    if not np.isfinite(mean) or not np.isfinite(std) or std<=0:raise ValueError('invalid scaler population')
    return Scaler(mean,std,dates,examples.train_hash)


def example_binding(examples,scaler):
    return {'train_hash':examples.train_hash,'test_mask_hash':examples.test_mask_hash,
            'test_examples_hash':digest(canonical_bytes([asdict(x) for x in examples.test])),
            'source_hashes':list(examples.source_hashes),'fold_hash':examples.fold_hash,'scaler':asdict(scaler)}
