from fractions import Fraction
import json
from pathlib import Path
import numpy as np
import pytest
from tradingagents.research.onchain_replication.btc_weekly import build_btc_weekly

CONFIG=json.loads((Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/graph.json').read_text())
COVERAGE=[('2024-01-01T00:00:00Z','2024-01-08T00:00:00Z')]

def event(identity='a',day='01',previous='b'):
    return {'transaction':{'id':identity*64,'coinbase':False,
        'inputs':[{'txid':previous*64,'vout':0},{'txid':previous*64,'vout':1}],
        'outputs':[{'address':'z','satoshis':5},{'address':'a','satoshis':2}]},
        'prevouts':{(previous*64,0):{'address':'a','satoshis':4},(previous*64,1):{'address':'b','satoshis':5}},
        'timestamp':f'2024-01-{day}T12:00:00Z','source_hash':'f'*64}

def test_exact_weekly_projection_and_incident_sidecar(tmp_path):
    other=event('c',previous='d')
    excluded=event('e',previous='9');excluded['transaction']['coinbase']=True
    result=list(build_btc_weekly([event(),other,excluded],CONFIG,coverage=COVERAGE,scratch=tmp_path))[0]
    graph=result.graph
    assert (graph.raw_count,graph.admitted_count,dict(graph.exclusion_counts))==(3,2,{'excluded_coinbase':1})
    assert graph.node_ids==('a','b','z')
    assert result.edge_satoshis==(Fraction(16,9),Fraction(40,9),Fraction(20,9),Fraction(50,9))
    assert result.incident_satoshis==(Fraction(92,9),Fraction(70,9),Fraction(10))
    assert result.fee_satoshis==4
    np.testing.assert_allclose(graph.edge_aggregates[:,1],[float(x/100000000) for x in result.edge_satoshis])
    assert list(graph.edge_aggregates[:,0])==[2,2,2,2]

@pytest.mark.parametrize('mutation,reason',[
    ('duplicate_transaction','transaction'),('double_spend','spent prevout'),
    ('missing_prevout','unavailable prevout'),('conflicting_prevout','spent prevout')])
def test_rejects_unavailable_or_duplicate_ledger_before_yield(tmp_path,mutation,reason):
    first=event();second=event('c',previous='d')
    if mutation=='duplicate_transaction':second['transaction']['id']=first['transaction']['id']
    if mutation in ('double_spend','conflicting_prevout'):
        second=event('c')
        if mutation=='conflicting_prevout':second['prevouts'][('b'*64,0)]['satoshis']=8
    if mutation=='missing_prevout':second['prevouts'].clear()
    with pytest.raises(ValueError,match=reason):list(build_btc_weekly([first,second],CONFIG,coverage=COVERAGE,scratch=tmp_path))

def test_cross_week_double_spend_is_rejected_and_partial_coverage_is_rejected(tmp_path):
    with pytest.raises(ValueError,match='spent prevout'):
        list(build_btc_weekly([event(),event('c',day='08')],CONFIG,
             coverage=[('2024-01-01T00:00:00Z','2024-01-15T00:00:00Z')],scratch=tmp_path))
    with pytest.raises(ValueError,match='complete week'):
        list(build_btc_weekly([event()],CONFIG,coverage=[('2024-01-01T00:00:00Z','2024-01-07T00:00:00Z')],scratch=tmp_path))

def test_empty_expected_week_is_not_fabricated(tmp_path):
    with pytest.raises(ValueError,match='empty expected week'):
        list(build_btc_weekly([event()],CONFIG,coverage=[('2024-01-01T00:00:00Z','2024-01-15T00:00:00Z')],scratch=tmp_path))


@pytest.mark.parametrize('reverse',[False,True])
def test_observed_creator_cannot_have_phantom_prevout(tmp_path,reverse):
    creator=event();creator['transaction']['coinbase']=True
    spender=event('c',previous='a')
    spender['transaction']['inputs'][0]['vout']=9
    spender['prevouts'][('a'*64,9)]=spender['prevouts'].pop(('a'*64,0))
    # vout1 must agree with the observed creator; vout9 does not exist at all.
    spender['prevouts'][('a'*64,1)]={'address':'a','satoshis':2}
    spender['transaction']['outputs']=[{'address':'z','satoshis':1}]
    events=[creator,spender]
    with pytest.raises(ValueError,match='absent from observed creator'):
        list(build_btc_weekly(events[::-1] if reverse else events,CONFIG,coverage=COVERAGE,scratch=tmp_path))


def test_observed_creator_values_must_agree_with_source_resolution(tmp_path):
    creator=event();creator['transaction']['coinbase']=True
    spender=event('c',previous='a')
    with pytest.raises(ValueError,match='conflicting observed prevout'):
        list(build_btc_weekly([creator,spender],CONFIG,coverage=COVERAGE,scratch=tmp_path))


@pytest.mark.parametrize('mutation,reason',[('future','precedes'),('duplicate_position','duplicate observed'),('block_hash','conflicting block'),('mixed','mixed chain'),('immature','immature')])
def test_observed_chain_consistency_uses_position_not_timestamp(tmp_path,mutation,reason):
    creator=event();spender=event('c',previous='a')
    creator.update(chain_position=(100,1),block_hash='1'*64)
    spender.update(chain_position=(101,1),block_hash='2'*64)
    spender['prevouts']={('a'*64,0):{'address':'z','satoshis':5},('a'*64,1):{'address':'a','satoshis':2}}
    if mutation=='future':spender['chain_position']=(99,1)
    if mutation=='duplicate_position':spender.update(chain_position=(100,1),block_hash='1'*64)
    if mutation=='block_hash':spender['chain_position']=(100,2)
    if mutation=='mixed':del spender['chain_position']
    if mutation=='immature':creator['transaction']['coinbase']=True
    with pytest.raises(ValueError,match=reason):list(build_btc_weekly([spender,creator],CONFIG,coverage=COVERAGE,scratch=tmp_path))


def test_nonmonotone_block_timestamp_does_not_invent_invalid_chain(tmp_path):
    creator=event(day='02');spender=event('c',previous='a',day='01')
    creator.update(chain_position=(100,1),block_hash='1'*64)
    spender.update(chain_position=(101,1),block_hash='2'*64)
    spender['prevouts']={('a'*64,0):{'address':'z','satoshis':5},('a'*64,1):{'address':'a','satoshis':2}}
    result=list(build_btc_weekly([spender,creator],CONFIG,coverage=COVERAGE,scratch=tmp_path))[0]
    assert result.observed_chain_order_checked


@pytest.mark.parametrize('mutation,reason',[('reused_hash','multiple heights'),('block_timestamp','timestamp within')])
def test_block_identity_and_timestamp_are_consistent_within_observed_source(tmp_path,mutation,reason):
    first=event();second=event('c',previous='d')
    first.update(chain_position=(100,1),block_hash='1'*64)
    second.update(chain_position=(101,1),block_hash='1'*64)
    if mutation=='block_timestamp':second.update(chain_position=(100,2),timestamp='2024-01-02T12:00:00Z')
    with pytest.raises(ValueError,match=reason):list(build_btc_weekly([first,second],CONFIG,coverage=COVERAGE,scratch=tmp_path))
