"""Engineering control parsing/refusal; no genuine entry completion claim."""
import ast
import inspect
import pytest
from tradingagents.research.onchain_replication import compact_mcm_batched as m


def selection():
    return {'schema_version':6,'entry_qualification':{
        'format':'genuine-mcm-entry-preparation-only-v1',
        'experiment_id':'eth-paper-real-data-end-to-end-resource-20261011-36',
        'graph_hash':'a'*64},'batched':{'execution':{'compiled_normalization_policy':{}}}}


def test_absent_stop_does_not_borrow_any_target_or_authority():
    assert m._entry_qualification({}) is None
    m._stop_after_entry(object(),{})


@pytest.mark.parametrize('field,value',[('format','success'),('experiment_id','financial-fit'),
    ('graph_hash','a'*63),('extra',True)])
def test_stop_selection_rejects_changed_fields(field,value):
    value_policy=selection();value_policy['entry_qualification'][field]=value
    with pytest.raises(ValueError):m._entry_qualification(value_policy)


def test_stop_policy_is_frozen_and_requires_selected_serial_backend():
    policy=selection();value=m._entry_qualification(policy)
    policy['entry_qualification']['graph_hash']='b'*64
    assert dict(value)['graph_hash']=='a'*64
    policy=selection();policy['batched']['execution']={}
    with pytest.raises(ValueError):m._entry_qualification(policy)


def test_selected_stop_refuses_fabricated_target_without_completion():
    with pytest.raises(ValueError,match='genuine'):
        m._stop_after_entry(object(),selection())


@pytest.mark.parametrize('batched',[None,[],{'execution':None}])
def test_malformed_execution_refuses_without_borrowing_authority(batched):
    policy=selection();policy['batched']=batched
    with pytest.raises(ValueError):m._entry_qualification(policy)


def test_stop_follows_closed_entry_and_precedes_producer_stage_creation():
    function=ast.parse(inspect.getsource(m.produce)).body[0]
    statements=function.body[-1].body
    entry=next(n for n in statements if isinstance(n,ast.With))
    stop=next(n for n in statements if isinstance(n,ast.Expr)
        and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)
        and n.value.func.id=='_stop_after_entry')
    stage=next(n for n in statements if isinstance(n,ast.Assign)
        and any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute)
            and c.func.attr=='directory' for c in ast.walk(n)))
    assert entry.end_lineno<stop.lineno<stage.lineno
    assert sum(isinstance(c,ast.Call) and isinstance(c.func,ast.Name)
        and c.func.id=='_entry_lease' for c in ast.walk(entry))==3
