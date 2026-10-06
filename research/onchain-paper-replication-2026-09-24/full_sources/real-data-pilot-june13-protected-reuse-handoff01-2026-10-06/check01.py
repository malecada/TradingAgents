from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys,types
R=Path.cwd();O=Path(__file__).resolve().parent;C=O/'candidate';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((O/'INVERSE01.json').read_bytes());base=R/v['baseline'];s=base.read_text();assert h(base)==v['before_sha256']
for e in v['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'])
assert s==(C/'real_pilot_import_caller.py').read_text();tree=ast.parse(s)
helpertree=ast.parse((C/'real_pilot_legacy_graph.py').read_text())
pkg=types.ModuleType('june13_metadata_checks');pkg.__path__=[];sys.modules[pkg.__name__]=pkg
def load(name,path):
 m=types.ModuleType(pkg.__name__+'.'+name);m.__package__=pkg.__name__;sys.modules[m.__name__]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
legacy=load('graph_legacy_coverage',R/'tradingagents/research/onchain_replication/graph_legacy_coverage.py');helper=load('adapter',C/'real_pilot_legacy_graph.py')
d=json.loads((O/'draft01/HANDOFF_DRAFT01.json').read_bytes());inputs=d['registered_input_templates'];mapping={helper.GRAPH_KEY:'graph_20220613'}
assert len(inputs)==21 and len(helper.registered(inputs,mapping))==20
refusals=0
for role in ('legacy_terminal','legacy_cell','legacy_graph_evidence'):
 x=copy.deepcopy(inputs);del x[role]
 try:helper.registered(x,mapping)
 except ValueError:refusals+=1
 else:raise AssertionError('missing original role admitted')
x=copy.deepcopy(inputs);x['legacy_terminal']['path']=x['legacy_terminal']['path'].replace('failed.json','complete.json')
try:helper.registered(x,mapping)
except ValueError:refusals+=1
else:raise AssertionError('failed parent relabel admitted')
x=copy.deepcopy(inputs);x['graph_20220613']['sha256']='0'*64
try:helper.registered(x,mapping)
except ValueError:refusals+=1
else:raise AssertionError('different graph admitted')
# Pure legacy metadata validator: authentic bodies and graph metadata only.
raws={role:(R/ref['path']).read_bytes() for role,ref in inputs.items()};manifest=json.loads(raws['legacy_graph_manifest']);carrier=types.SimpleNamespace(**manifest['metadata']);proof=json.loads(raws['legacy_graph_evidence'])
assert legacy.verify_legacy_coverage(proof,carrier,inputs['graph_20220613']['sha256'],raws.__getitem__)['parent_status']=='failed'
carrier.available_at='2022-06-13T00:00:00Z'
try:legacy.verify_legacy_coverage(proof,carrier,inputs['graph_20220613']['sha256'],raws.__getitem__)
except ValueError:refusals+=1
else:raise AssertionError('metadata availability substitution admitted')
assert all(v is None for v in d['future_root_bindings'].values()) and d['status']=='DRAFT_NOT_ADMITTED'
execute=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='execute');text=ast.unparse(execute)
assert text.index('verify(run, graph, role)')<text.index('resource_binding.open_first(')<text.index('original_import_stage.attach(')<text.index('Target(execution, g, k)')
verify=next(x for x in helpertree.body if isinstance(x,ast.FunctionDef) and x.name=='verify');text=ast.unparse(verify)
assert text.index('type(run) is ResearchRun')<text.index('run._active()')<text.index('verify_legacy_coverage(')
assert 'ResearchRun.start' not in text and 'Owner(' not in text and 'Binding(' not in text
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
print(json.dumps({'decision':'pass','caller_two_hunk_inverse':True,'actual_metadata_component_complete_parent_failed':True,'missing_substituted_refs_and_availability_refusals':refusals,'future_authority_null':True,'coverage_check_before_owner_birth':True,'genuine_runtime_type_guards_source_checked_not_executed':True,'payload_reads':0,'numeric_imports':0}))
