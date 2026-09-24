from dataclasses import replace
from fractions import Fraction
import pytest
from tests.research.onchain_replication.test_btc_weekly import event,CONFIG,COVERAGE
from tradingagents.research.onchain_replication.btc_weekly import build_btc_weekly
from tradingagents.research.onchain_replication.btc_store import save_btc_graph,load_btc_graph,_write
from tradingagents.research.onchain_replication.provenance import file_hash


def test_exact_graph_and_whale_sidecar_survive_immutable_checkpoint(tmp_path):
    value=list(build_btc_weekly([event()],CONFIG,coverage=COVERAGE,scratch=tmp_path))[0]
    path=save_btc_graph(tmp_path/'saved',value);result=load_btc_graph(path,file_hash(path))
    assert result.edge_satoshis==value.edge_satoshis and result.incident_satoshis==value.incident_satoshis
    assert result.fee_satoshis==2 and result.graph.node_ids==value.graph.node_ids
    with pytest.raises(FileExistsError):save_btc_graph(tmp_path/'saved',value)
    (path.parent/'edge_satoshis.hex').write_text('1/1\n')
    with pytest.raises(ValueError,match='sidecar hash'):load_btc_graph(path,file_hash(path))


def test_inconsistent_exact_incident_values_cannot_be_published(tmp_path):
    value=list(build_btc_weekly([event()],CONFIG,coverage=COVERAGE,scratch=tmp_path))[0]
    with pytest.raises(ValueError,match='incident'):save_btc_graph(tmp_path/'bad',replace(value,incident_satoshis=(Fraction(0),)*len(value.graph.node_ids)))
    assert not (tmp_path/'bad').exists()


def test_large_exact_denominator_is_not_rounded_or_decimal_digit_limited(tmp_path):
    value=Fraction(2**20000+1,2**20000+3);path=tmp_path/'large.hex';_write(path,[value])
    a,b=path.read_text().strip().split('/')
    assert Fraction(int(a,16),int(b,16))==value


def test_whale_hash_supports_huge_exact_rationals_and_rejects_float_substitution(tmp_path):
    from tradingagents.research.onchain_replication.subsets import filter_graph
    value=list(build_btc_weekly([event()],CONFIG,coverage=COVERAGE,scratch=tmp_path))[0]
    small=Fraction(2**20000+1,2**20000+3)
    _,receipt=filter_graph(value.graph,'whale',exact_incident_volumes=(small,small,100*small))
    assert receipt['exact_incident_encoding']=='hex-rational-v1' and receipt['schema_version']==2
    with pytest.raises(ValueError,match='rational'):filter_graph(value.graph,'whale',exact_incident_volumes=[float(v) for v in value.incident_satoshis])
