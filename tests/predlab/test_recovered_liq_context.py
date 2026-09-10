import json

import pandas as pd
import pytest

from scripts import audit_recovered_liq_2026_09_10 as replay
from scripts import audit_reeval_common as common


@pytest.fixture
def gate(tmp_path, monkeypatch):
    source = tmp_path/'original'
    recovery = tmp_path/'recovery'
    source.mkdir(); recovery.mkdir()
    original = source/'TEST.parquet'
    snapshot = recovery/'TEST.parquet'
    clock = pd.date_range('2025-03-30', periods=3, freq='D', tz='UTC', name='ts')
    pd.DataFrame({'close':[10.,999.]},index=clock[[0,2]]).to_parquet(original)
    pd.DataFrame({'close':[10.,11.,999.]},index=clock).to_parquet(snapshot)
    # Documentary evidence is pinned explicitly, outside market-source roots.
    metadata = tmp_path/'receipt.json'; metadata.write_text('{}')
    g = {'families':{'liq_fade':{'cells':[{'id':'a'}]}},
         'source_roots':[str(source),str(recovery)],
         'original_input_sha256':{str(original):replay.sha256(original)},
         'pinned_auxiliary_inputs':{str(metadata):replay.sha256(metadata)},
         'input_overrides':{str(original):{'source_sha256':replay.sha256(original),
                'snapshot':str(snapshot),'snapshot_sha256':replay.sha256(snapshot)}}}
    monkeypatch.setattr(common.registry,'get_experiment',lambda key:g)
    monkeypatch.setattr(common.registry,'preflight',lambda *args:{'git_commit':'test'})
    monkeypatch.setattr(common.registry,'log_trial',lambda **kwargs:None)
    return tmp_path,g,original,snapshot,metadata


def test_exact_overlay_records_both_sources_and_filters_holdout(gate):
    root,g,original,snapshot,_ = gate
    ctx = replay.RecoveredRunContext(root=root)
    frame = ctx.read_market(original,start='2025-03-30')
    assert frame.close.tolist()==[10.,11.]
    assert str(original) in ctx.hashes and str(snapshot) in ctx.hashes
    assert pd.read_parquet(original).close.tolist()==[10.,999.]
    with pytest.raises(ValueError,match='registered source roots'):
        ctx.read_market(root/'receipt.json')
    ctx.finish({},[{'id':'a','config':{},'metrics':{'status':'blocked'}}])
    result=json.loads((ctx.output_dir/'result.json').read_text())
    assert result['experiment']==replay.KEY and len(result['cells'])==1


@pytest.mark.parametrize('which',['original','snapshot','receipt'])
def test_tampered_pinned_input_refused_before_output_creation(gate,which):
    root,g,original,snapshot,metadata=gate
    {'original':original,'snapshot':snapshot,'receipt':metadata}[which].write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash mismatch'):
        replay.RecoveredRunContext(root=root)
    assert not (root/'data/predlab'/replay.KEY).exists()


def test_overlay_cannot_change_its_pinned_original_identity(gate):
    root,g,original,_,_=gate
    g['input_overrides'][str(original)]['source_sha256']='different'
    with pytest.raises(ValueError,match='not pinned'):
        replay.RecoveredRunContext(root=root)


def test_auxiliary_pin_cannot_replace_an_original_hash(gate):
    root,g,original,_,_=gate
    g['pinned_auxiliary_inputs'][str(original)]='contradictory'
    with pytest.raises(ValueError,match='contradictory'):
        replay.RecoveredRunContext(root=root)


def test_replacement_changed_after_start_cannot_be_consumed(gate):
    root,g,original,snapshot,_=gate
    ctx=replay.RecoveredRunContext(root=root)
    snapshot.write_bytes(b'changed')
    with pytest.raises(RuntimeError,match='changed during run'):
        ctx.read_market(original)


def test_default_command_never_consumes_inputs(monkeypatch,capsys):
    monkeypatch.setattr(replay,'RecoveredRunContext',lambda **kwargs:pytest.fail('dry run consumed inputs'))
    assert replay.main([])==0
    assert 'Dry run' in capsys.readouterr().out
