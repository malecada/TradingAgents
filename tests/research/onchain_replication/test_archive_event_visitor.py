import pytest
from tests.research.onchain_replication.test_archive_pair_reader import fixture


def test_verified_event_visitor_is_ordered_and_receives_immutable_frames(tmp_path):
    module,transport,log,contract = fixture(tmp_path); frames=[]
    result=module.verify(**contract,on_event=frames.append)
    assert [f[0] for f in frames] == list(range(5))
    assert [f[1] for f in frames] == [0,3,1,0,2]
    assert all(type(f) is tuple for f in frames)
    assert result['replay']['completed_pairs'] == 2


def test_visitor_error_retains_failed_read_attempt(tmp_path):
    module,transport,log,contract=fixture(tmp_path)
    def visit(frame):raise RuntimeError('visitor failure')
    with pytest.raises(RuntimeError,match='visitor failure'):module.verify(**contract,on_event=visit)
    assert (contract['attempt']/'failed.json').exists()
    assert not (log.root/'failed.json').exists()
