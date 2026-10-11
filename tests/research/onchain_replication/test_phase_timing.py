"""Synthetic clocks; no numerical execution or wall-clock sleeps."""
import pytest


def test_nested_timings_are_exclusive_and_additive():
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals
    wall=[0.];cpu=[0.];totals=PhaseTotals(wall_clock=lambda:wall[0],cpu_clock=lambda:cpu[0])
    with totals.measure('entry'):
        wall[0]+=2;cpu[0]+=1
        with totals.measure('source_admission'):
            wall[0]+=3;cpu[0]+=2
        wall[0]+=4;cpu[0]+=1
    snapshot=totals.snapshot()
    assert snapshot['phases']['entry']=={'calls':1,'failures':0,'wall_seconds':6.,'cpu_seconds':2.,'bytes':0}
    assert snapshot['phases']['source_admission']=={'calls':1,'failures':0,'wall_seconds':3.,'cpu_seconds':2.,'bytes':0}
    assert sum(p['wall_seconds'] for p in snapshot['phases'].values())==9.


def test_failures_are_counted_without_replacing_primary():
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals
    now=[0.];totals=PhaseTotals(wall_clock=lambda:now[0],cpu_clock=lambda:now[0]);primary=RuntimeError('primary')
    with pytest.raises(RuntimeError) as found:
        with totals.measure('entry'):
            now[0]=1.;raise primary
    assert found.value is primary
    assert totals.snapshot()['phases']['entry']['failures']==1


def test_scope_restores_and_unselected_timing_is_noop():
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals, activate, measure
    now=[0.];totals=PhaseTotals(wall_clock=lambda:now[0],cpu_clock=lambda:now[0])
    with measure('entry'):now[0]+=10
    assert totals.snapshot()['phases']=={}
    with activate(totals):
        with measure('role_read'):now[0]+=2
    with measure('role_read'):now[0]+=10
    assert totals.snapshot()['phases']['role_read']['wall_seconds']==2.


def test_unknown_phase_and_active_snapshot_refuse():
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals
    totals=PhaseTotals()
    with pytest.raises(ValueError):
        with totals.measure('arbitrary-name'):pass
    with totals.measure('entry'):
        with pytest.raises(ValueError):totals.snapshot()


def test_backward_clock_refuses_and_primary_still_survives():
    from tradingagents.research.onchain_replication.phase_timing import PhaseTotals
    now=[1.];totals=PhaseTotals(wall_clock=lambda:now[0],cpu_clock=lambda:now[0])
    with pytest.raises(ValueError):
        with totals.measure('entry'):now[0]=0.
    assert totals.snapshot()['invalid_measurements']==1
    now[0]=1.;primary=MemoryError('primary')
    with pytest.raises(MemoryError) as found:
        with totals.measure('entry'):now[0]=0.;raise primary
    assert found.value is primary and totals.snapshot()['invalid_measurements']==2


def test_profile_publication_retains_primary_and_complete_snapshot():
    from tradingagents.research.onchain_replication.phase_timing import run_profiled,measure
    primary=RuntimeError('actual operation failed');seen=[]
    def operation():
        with measure('backend_setup'):raise primary
    def publish(value):
        seen.append(value);raise OSError('publication failed')
    with pytest.raises(RuntimeError) as found:run_profiled(operation,publish)
    assert found.value is primary
    assert seen[0]['phases']['backend_setup']['failures']==1
    assert any('OSError' in note for note in primary.__notes__)


def test_successful_profile_retains_result_and_refuses_missing_publication():
    from tradingagents.research.onchain_replication.phase_timing import run_profiled,measure
    sentinel=object();seen=[]
    def operation():
        with measure('entry'):pass
        return sentinel
    assert run_profiled(operation,seen.append) is sentinel
    assert seen[0]['authority'] is False
    with pytest.raises(OSError):run_profiled(operation,lambda value:(_ for _ in ()).throw(OSError('disk')))
