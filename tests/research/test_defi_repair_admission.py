"""Historical-as-of predicate and narrow route tests; invented metadata only."""
import pytest
from tradingagents.research_defi_repair.verify_amendment import earlier_claim
from tradingagents.research_defi_repair.admission import admit

@pytest.mark.parametrize('first,expected', [('2026-09-11T08:00:00+00:00',True),('2026-09-11T11:00:00+00:00',False)])
def test_earlier_and_later_claims_have_different_historical_roles(first,expected):
    assert earlier_claim({'started_at':first},{'started_at':'2026-09-11T09:00:00+00:00'}) is expected

@pytest.mark.parametrize('first',['2026-09-11T09:00:00+00:00','2026-09-11T08:00:00','2026-09-11T08:00:00+02:00'])
def test_ambiguous_or_non_utc_order_is_not_silently_excluded(first):
    with pytest.raises(ValueError):earlier_claim({'started_at':first},{'started_at':'2026-09-11T09:00:00+00:00'})

@pytest.mark.parametrize('experiment,registration',[('anything-else','research/defi-depth-2026-09-15/gates-r1-v2.json'),('defi-depth-r1-20260915','another.json')])
def test_runtime_cannot_admit_other_routes_before_any_git_or_input_access(experiment,registration):
    with pytest.raises(ValueError,match='only the exact DeFi R1'):
        admit(root='/invented/nonexistent',registration=registration,experiment=experiment,source='0'*40)


def test_historical_certificate_accepts_later_claims_but_not_omitted_prior_or_chain(monkeypatch):
    # Retained metadata/hashes only; no financial engine or outcome calculations.
    from pathlib import Path
    import copy
    from tradingagents.research_defi_repair import verify,verify_amendment
    root=Path(__file__).resolve().parents[2]
    directory=root/'research_runs/dated-book-amended-20260911'
    valid=verify.verify_claim(directory)
    assert valid['experiment_id']=='dated-book-amended-20260911'
    original=verify_amendment.original_claim
    prior='dated-archive-20260911'
    def omit_earlier(path):
        result=original(path)
        if result['experiment_id']==prior:
            result=copy.deepcopy(result);result['started_at']='2026-09-12T00:00:00+00:00'
        return result
    monkeypatch.setattr(verify_amendment,'original_claim',omit_earlier)
    with pytest.raises(ValueError,match='inventory or original budget'):
        verify.verify_claim(directory)
    def chain(path):
        result=original(path)
        if result['experiment_id']==prior:
            result=copy.deepcopy(result);result['experiment']['budget_amendment']={}
        return result
    monkeypatch.setattr(verify_amendment,'original_claim',chain)
    with pytest.raises(ValueError,match='chained or duplicate'):
        verify.verify_claim(directory)


def test_current_claim_enumeration_keeps_later_claims(tmp_path,monkeypatch):
    from tradingagents.research_defi_repair import admission,verify
    records={name:{'experiment_id':name,'started_at':time,'family':{'mechanism_id':'invented'}}
             for name,time in [('early','2026-01-01T00:00:00Z'),('later','2026-03-01T00:00:00Z')]}
    for name in records:
        d=tmp_path/'research_runs'/name;d.mkdir(parents=True);(d/'claim.json').write_text('{}')
    monkeypatch.setattr(verify,'verify_claim',lambda path:records[path.name])
    assert {r['experiment_id'] for r in admission.claims(tmp_path)}=={'early','later'}
