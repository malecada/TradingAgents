import numpy as np
import pytest
from tests.research.onchain_replication.test_subsets import fixture
from tradingagents.research.onchain_replication.graph_store import save_graph,load_graph
from tradingagents.research.onchain_replication.provenance import file_hash


def test_graph_checkpoint_roundtrip_and_corruption(tmp_path):
    g=fixture();path=save_graph(tmp_path/'g',g);loaded=load_graph(path,file_hash(path))
    assert g.node_ids==loaded.node_ids
    np.testing.assert_array_equal(g.edge_aggregates,loaded.edge_aggregates)
    with pytest.raises(FileExistsError):save_graph(tmp_path/'g',g)
    (path.parent/'edge_index.npy').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='member hash'):load_graph(path,file_hash(path))
