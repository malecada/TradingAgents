"""Preclaim refusal of retained compact MCM output namespaces."""
import pytest
from tests.research.onchain_replication.test_compact_native_producer import admitted, api
from tradingagents.research.onchain_replication.cache import cache_key


@pytest.mark.parametrize('form',['directory','dangling_link'])
def test_existing_mcm_output_namespace_refused_before_owner(admitted,monkeypatch,form):
    t,job,graphs,examples=admitted;m=api()
    path=t.root/'research_artifacts/onchain_compact_outputs'/cache_key(job['descriptor'])
    path.parent.mkdir(parents=True,exist_ok=True)
    if form=='directory':path.mkdir()
    else:path.symlink_to(path.parent/'absent',target_is_directory=True)
    monkeypatch.setattr(m.matching_owner,'open_first',lambda *args,**kw:pytest.fail('existing output reached owner claim'))
    with pytest.raises(ValueError,match='reserved|redirected'):m.selected(t.run,'r',job)
    assert not t.directory.exists()
