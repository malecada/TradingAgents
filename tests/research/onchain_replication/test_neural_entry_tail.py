"""Fresh tiny authority proves entry refusal still leaves closure headroom."""
import pytest
from tradingagents.research.onchain_replication import neural_physical as physical


def test_active_entry_refusal_retains_all_seventeen_closure_publications(tmp_path):
    policy={'schema_version':1,'max_file_bytes':65536,'max_json_bytes':8192,
        'max_allocated_bytes':2*1024**2,'max_logical_bytes':1024**2,
        'max_entries':128,'tail_reserve_bytes':131072}
    base=tmp_path/physical.PREFIX/'runs'/'invented-entry-tail';base.mkdir(parents=True)
    (tmp_path/'research_runs').mkdir();(tmp_path/physical.PREFIX/'sources').mkdir()
    scope=physical.Scope.create(tmp_path,'invented-entry-tail','a'*40,policy,{'synthetic':True})
    try:
        before=scope.check()
        for index in range(110-before['entries']):(base/f'padding-{index:03d}').touch()
        assert scope.check()['entries']==110
        with pytest.raises(ValueError,match='entry'):
            scope.immutable(base/'ordinary.json',{'value':'must refuse before write'})
        assert not (base/'ordinary.json').exists()
        with scope.terminal_tail():
            for index in range(16):scope.immutable(base/f'closure-{index:02d}.json',{'status':'failed','synthetic':True})
            final=scope.finish()
        assert final['entries']==127
        assert all((base/f'closure-{index:02d}.json').is_file() for index in range(16))
        assert (base/'physical-final.json').is_file()
        assert len(list(base.glob('padding-*')))==110-before['entries']
        assert not list(base.glob('.physical-pending-*'))
    finally:
        scope.close_authority()
