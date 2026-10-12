"""Real _prepare control flow with synthetic borrowed boundary objects only.

No genuine authority is created; execution stops at kernel selection, before
numeric execution, reservation, publication, or an entry-completion claim.
"""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from tradingagents.research.onchain_replication import compact_mcm as live
from tradingagents.research.onchain_replication import compact_mcm_batched as batched
HERE=Path(__file__).resolve().parent
PAIRS=56584576
class KernelReached(Exception):pass

def actual():return json.loads((HERE/'ACTUAL36_POLICY.json').read_text())

def path(policy,tmp_path,*,candidate=True,required=8,wrong_route=False):
    source=HERE/('compact_mcm.py' if candidate else 'ORIGINAL_compact_mcm.py')
    tree=ast.parse(source.read_text());function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_prepare')
    ns=dict(vars(live));calls=[]
    selected={'plan_input':'plan','compact_mcm_input':'mcm','real_pilot_input':'pilot'}
    bodies={'execution_job':{'payload':{'representation_jobs':{'r':selected}}},'plan':{'producers':{'p':{'compact_mcm_input':'wrong' if wrong_route else 'mcm'}}},'mcm':policy,'pilot':{'schema_version':2,'population_scope':'resource_pilot_subset'}}
    def read(role):calls.append(('read',role));return json.dumps(bodies[role]).encode()
    run=NS(read_input=read,admission=NS(inputs={'mcm':{},'out':{}},root=tmp_path))
    owner=NS(bound=NS(_run=run,record={'representation':'r','producer':'p'}),required=tuple(range(required)))
    graph=NS(node_ids=range(1768268));dictionary=NS(representatives=range(32))
    scope={'synthetic_scope':'policy-control-only'}
    target=NS(dictionary=dictionary,scope=scope)
    target.check=lambda:calls.append(('boundary','synthetic'))
    target._prepare_sources=lambda:[];target._prepare_graph=lambda key:graph;target.derive_scope=lambda:dict(scope)
    ns['_imported']=lambda value:True;ns['_owner']=lambda value:owner
    def kernel(value):raise KernelReached('policy predicates accepted; no numerical/authority execution')
    ns['_kernel']=kernel
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),ns)
    return ns['_prepare'](target,'a'*64,'mcm','out')

def test_actual36_red_exact_original_message(tmp_path):
    p=actual();batched.validate(p,PAIRS)
    with pytest.raises(ValueError,match='^compact MCM policy/cell/metadata allowance differs$'):
        path(p,tmp_path,candidate=False)

def test_actual36_candidate_reaches_next_kernel_boundary(tmp_path):
    with pytest.raises(KernelReached):path(actual(),tmp_path)

@pytest.mark.parametrize('schema',[1,2,5,6])
def test_absent_qualifier_legacy_durability_batched_routes(tmp_path,schema):
    p=actual();p.pop('entry_qualification');p['schema_version']=schema
    if schema in (1,2):p.pop('batched')
    if schema==2:p['durability']={'schema_version':1,'scope':'resource-pilot-only','pair_records':1,'tail_records':1,'max_interval_ms':1}
    if schema==5:
        p['batched'].pop('group_batches');p['batched']['retention']='local-v2';p['batched']['execution'].pop('binding_timing')
    for candidate in (False,True):
        with pytest.raises(KernelReached):path(p,tmp_path,candidate=candidate)

@pytest.mark.parametrize('mutation', ['schema','nonserial','case','graph_length','graph_case','extra','identity','arbitrary_top_key'])
def test_actual_validator_rejects_invalid_qualifier(tmp_path,mutation):
    p=actual();q=p['entry_qualification']
    if mutation=='schema':p['schema_version']=5
    if mutation=='nonserial':p['batched']['execution'].pop('compiled_normalization_policy')
    if mutation=='case':q['format']=q['format'].upper()
    if mutation=='graph_length':q['graph_hash']='a'*63
    if mutation=='graph_case':q['graph_hash']='A'*64
    if mutation=='extra':q['extra']=True
    if mutation=='identity':q['experiment_id']='eth-paper-real-data-end-to-end-resource-20261012-other'
    if mutation=='arbitrary_top_key':p['unregistered']=True
    with pytest.raises(ValueError):path(p,tmp_path)

@pytest.mark.parametrize('mutation',['cells','metadata','schema_bool','metadata_bool','route'])
def test_other_branch_scalar_checks_preserved(tmp_path,mutation):
    p=actual()
    if mutation=='cells':p['max_entries']=PAIRS-1
    if mutation=='metadata':p['max_workflow_metadata_bytes']=172031
    if mutation=='schema_bool':p['schema_version']=True
    if mutation=='metadata_bool':p['max_workflow_metadata_bytes']=True
    with pytest.raises(ValueError):path(p,tmp_path,wrong_route=mutation=='route')

def test_qualification_not_permitted_on_legacy_or_durability(tmp_path):
    for schema in (1,2):
        p=actual();p['schema_version']=schema;p.pop('batched')
        if schema==2:p['durability']={'schema_version':1,'scope':'resource-pilot-only','pair_records':1,'tail_records':1,'max_interval_ms':1}
        with pytest.raises(ValueError):path(p,tmp_path)

def test_valid_other_graph_is_not_a_false_target_binding_claim(tmp_path):
    p=actual();p['entry_qualification']['graph_hash']='b'*64
    # Parser validates shape, not the eventual genuine target identity.
    with pytest.raises(KernelReached):path(p,tmp_path)
    with pytest.raises(ValueError,match='genuine'):batched._stop_after_entry(object(),p)

if __name__=='__main__':
    # Standalone finite engineering fixture; repository pytest profile unchanged.
    import tempfile,unittest,sys
    cases=[(test_actual36_red_exact_original_message,()),(test_actual36_candidate_reaches_next_kernel_boundary,())]
    cases += [(test_absent_qualifier_legacy_durability_batched_routes,(x,)) for x in (1,2,5,6)]
    cases += [(test_actual_validator_rejects_invalid_qualifier,(x,)) for x in ('schema','nonserial','case','graph_length','graph_case','extra','identity','arbitrary_top_key')]
    cases += [(test_other_branch_scalar_checks_preserved,(x,)) for x in ('cells','metadata','schema_bool','metadata_bool','route')]
    cases += [(test_qualification_not_permitted_on_legacy_or_durability,()),(test_valid_other_graph_is_not_a_false_target_binding_claim,())]
    def run(function,args):
        with tempfile.TemporaryDirectory() as tmp:function(Path(tmp),*args)
    suite=unittest.TestSuite(unittest.FunctionTestCase(lambda f=f,args=args:run(f,args),description=f.__name__+str(args)) for f,args in cases)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
