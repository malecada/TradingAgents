"""Current source/selection joins only; no native launcher or study claim."""
import hashlib
from pathlib import Path
import pytest
from types import SimpleNamespace
from contextlib import nullcontext
import ast

from tradingagents.research.onchain_replication import compact_mcm_batched as batched
from tradingagents.research.onchain_replication import imported_authority_lease as lease
from tradingagents.research.onchain_replication import matching_numeric_policy as numeric
from tradingagents.research.onchain_replication import phase_timing


def test_numeric_selection_is_explicit_and_frozen():
    assert batched._numeric_policy({}) is None
    value=dict(numeric.POLICY)
    assert dict(batched._numeric_policy({'numeric_kernel_policy':value}))==value
    frozen=batched._numeric_policy({'numeric_kernel_policy':value})
    value['rtol']=1.
    assert dict(frozen)['rtol']==1e-6
    with pytest.raises(ValueError):batched._numeric_policy({'numeric_kernel_policy':value})


@pytest.mark.parametrize('value',[None,True,{},'bounded-numpy-agreement-c05-v1'])
def test_present_but_invalid_numeric_selection_refuses(value):
    with pytest.raises(ValueError):batched._numeric_policy({'numeric_kernel_policy':value})


def test_new_authored_adapter_and_timing_methods_are_source_authenticated():
    root=Path(lease.__file__).resolve().parents[3]
    modules=(numeric,phase_timing)
    sources={str(Path(m.__file__).resolve().relative_to(root)):
        hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules}
    loaded=lease._loaded(root,sources)
    labels={name:tuple(row[0] for row in value[2]) for name,value in loaded.items()}
    assert 'NumericAgreementAdapter.fill' in labels[numeric.__name__]
    assert 'PhaseTotals.add_count' in labels[phase_timing.__name__]
    assert 'PhaseTotals.measure.wrapped' in labels[phase_timing.__name__]
    lease._authenticate_loaded(loaded,sources,root)


def test_changed_adapter_code_refuses_source_authentication(monkeypatch):
    root=Path(lease.__file__).resolve().parents[3]
    path=Path(numeric.__file__).resolve()
    sources={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest()}
    original=numeric.NumericAgreementAdapter.fill
    def replacement(*args):return True
    monkeypatch.setattr(original,'__code__',replacement.__code__)
    with pytest.raises(ValueError,match='authenticated source'):
        lease._authenticate_loaded(lease._loaded(root,sources),sources,root)


@pytest.mark.parametrize('timed,selected',[(False,False),(True,False),(True,True)])
def test_complete_compute_retains_commits_and_joins_numeric_score_bodies(tmp_path,timed,selected):
    # The shared functional core is engineering-only. Metadata below does not
    # stand in for Target/Owner/Run; produce() requires those actual capabilities.
    from tests.research.onchain_replication.test_matching_reference import graph,config
    from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY
    from tradingagents.research.onchain_replication.array_neighborhoods import ArrayNeighborhoodIndex
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash
    from tradingagents.research.onchain_replication.matching_identity import graph_identity
    from tradingagents.research.onchain_replication.cache import cache_key
    g=graph([[0.],[1.],[2.]],[]);extraction={'hop_depth':0,'maximum_neighborhood_nodes':3}
    with ArrayNeighborhoodIndex(g,max_buffer_bytes=100000,edge_chunk=4) as index:
        motif=index.neighborhood(0,extraction)
    dictionary=SimpleNamespace(representatives=(motif,)*32,config=extraction,
        identity='c'*64,matching_config_hash='d'*64)
    schedule=dict(max_checkpoints=2,calls_per_checkpoint=10,operations_per_call=1024,
        max_total_checkpoints=10,max_total_checkpoint_bytes=4*1024**2)
    ad=SimpleNamespace(experiment={'source_files':{'invented-engine.py':'a'*64}})
    owner=SimpleNamespace(policy={'pair':POLICY,'schedule':schedule},matching=config()|{'max_iterations':1},
        bound=SimpleNamespace(_run=SimpleNamespace(admission=ad)))
    target=SimpleNamespace(owner=owner,dictionary=dictionary,execution=SimpleNamespace())
    scope=dict(graph=graph_hash(g),node_order=node_order_hash(g.node_ids),dictionary=dictionary.identity,
        ordered_motifs=cache_key([graph_identity(motif)]*32),matching='e'*64,workflow='f'*64)
    start=dict(rows=3,cells=96,graph_hash=scope['graph'],scope=scope)
    execution=dict(route='immutable-input-session+exact-byte-reuse-v1',max_entries=2,
        max_retained_bytes=4096,max_key_bytes=2048,max_origin_bytes=864,max_summary_bytes=25000)
    if selected:execution['numeric_kernel_policy']=dict(numeric.POLICY)
    b=dict(format=batched.FORMAT,authority_boundaries='entry-batch-checkpoint-final',batch_cells=32,
        max_journal_bytes=1024**2,max_body_bytes=8192,max_closure_token_bytes=4096,
        max_checkpoint_bytes=4*1024**2,retention='local-v2',max_spool_bytes=4096,
        max_offload_metadata_bytes=4096,max_offload_entries=100,max_offload_anchor_bytes=0,
        execution=execution,continuation={'format':'completed-prefix-v1','manifest_input':None,'max_commit_bytes':24576})
    policy=dict(schema_version=5,max_entries=96,max_workflow_metadata_bytes=8192,
        numeric=dict(max_buffer_bytes=100000,edge_chunk=4,extraction_limit=3),batched=b)
    modules=batched._modules(tmp_path)
    stage=SimpleNamespace(root=tmp_path,inode=tuple(batched.io._signature(tmp_path.lstat())[:2]))
    totals=phase_timing.PhaseTotals()
    with phase_timing.activate(totals) if timed else nullcontext():
        binding=batched._compute(target,stage,g,policy,start,modules,lambda:None)
    assert binding['batches']==3 and binding['cells']==96
    if selected:assert binding['numeric_execution']['numeric_kernel_policy']==numeric.POLICY
    if timed:
        assert totals.snapshot()['phases']['publication']['calls']>0
        assert b'phase_totals' in (tmp_path/'stream/numeric-batches/000000000000.json').read_bytes()
    assert binding['prefix_inventory']['files']==3 and binding['prefix_inventory']['legacy_counter_files']==0
    assert batched._prefix_inventory(tmp_path,binding,modules)==binding['prefix_inventory']
    marker=tmp_path/'matching/00000000.prefix.json'
    original=marker.read_bytes();marker.write_bytes(original[:-1]+b'!')
    with pytest.raises(ValueError):batched._prefix_inventory(tmp_path,binding,modules)


def test_continuation_requires_full_declared_commit_reservation():
    b={'batch_cells':32,'max_body_bytes':8192,'max_journal_bytes':1024**2,
       'continuation':{'format':'completed-prefix-v1','manifest_input':None,'max_commit_bytes':24576}}
    assert dict(batched._continuation_policy(b,3))['manifest_input'] is None
    b['continuation']['max_commit_bytes']=24575
    with pytest.raises(ValueError,match='reservation'):batched._continuation_policy(b,3)


def test_graph_specific_prefix_selection_is_finite_and_frozen():
    b={'batch_cells':32,'max_body_bytes':8192,'max_journal_bytes':1024**2,
       'continuation':{'format':'completed-prefix-v1','manifest_input':None,
         'graph_manifest_inputs':{'a'*64:'prior_graph_a'},'max_commit_bytes':24576}}
    frozen=batched._continuation_policy(b,3)
    b['continuation']['graph_manifest_inputs']['a'*64]='changed'
    assert dict(frozen)['graph_manifest_inputs']==(('a'*64,'prior_graph_a'),)
    b['continuation']['manifest_input']='ambiguous_global'
    with pytest.raises(ValueError,match='conflict'):batched._continuation_policy(b,3)


def test_real_caller_closes_entry_scopes_before_graph_batches_and_training():
    # A completed-batch snapshot requires no open timing frame. Inspect the
    # genuine caller's two preparation scopes, not a replacement caller fixture.
    from tradingagents.research.onchain_replication import real_pilot_import_caller
    tree=ast.parse(Path(real_pilot_import_caller.__file__).read_text())
    operation=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='operation')
    scopes=[node for node in ast.walk(operation) if isinstance(node,ast.With)
        and any(isinstance(item.context_expr,ast.Call) and item.context_expr.args
            and isinstance(item.context_expr.args[0],ast.Constant)
            and item.context_expr.args[0].value=='entry' for item in node.items)]
    assert len(scopes)==2
    for scope in scopes:
        calls=[node.func.attr for node in ast.walk(scope) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)]
        assert 'produce_imported' not in calls and 'run_one_update' not in calls
