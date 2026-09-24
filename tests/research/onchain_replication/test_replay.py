import json
from pathlib import Path
import pytest
from tradingagents.research.onchain_replication.replay import make_synthetic_fixture,replay


def test_bounded_full_model_checkpoint_replay_and_corruption(tmp_path):
    config=json.loads((Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/model.json').read_bytes())
    directory=tmp_path/'example';make_synthetic_fixture(directory,config,'a'*40)
    result=replay(directory)
    assert result['status']=='passed' and result['max_absolute_difference']==0 and result['predictions']==2
    (directory/'expected.json').write_text('[[0,0],[0,0]]')
    with pytest.raises(ValueError,match='fixture bytes'):replay(directory)
