"""Author handoff checks, explicitly NOT independent approval."""
import ast,copy,hashlib,importlib.util,json,os,stat
from pathlib import Path
import prepare_builder03_input01 as p
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
b=p.load('builder');draft=json.loads((HERE/'INPUT_DRAFT01.json').read_bytes())
results=[]
for week,item in draft['graphs'].items():
    if item is None:continue
    g=b.metadata(ROOT,item['manifest']);n=b.metadata(ROOT,item['node_count'])
    assert n['graph_manifest_sha256']==item['manifest']['sha256'] and n['node_features_sha256']==g['arrays']['node_features']['sha256']
    results.append({'predicate':'actual builder03 bounded metadata reader','week':week,'rows':n['rows']})
for label,fn,wanted in (
 ('actual builder03 seven-week gate',lambda:b.graphs(ROOT,{k:v for k,v in draft['graphs'].items() if v is not None}),'exact seven fixed weekly'),
 ('integrated missing-count refusal',lambda:p.prepare(ROOT,draft),'missing genuine graph/count'),
 ('integrated absent-protocol refusal',lambda:p.require_protocol(None),'missing exact selected protocol')):
    try:fn()
    except ValueError as e:
        assert wanted in str(e);results.append({'predicate':label,'result':'refused','reason':str(e)})
    else:raise AssertionError(label+' did not refuse')
# Compile unchanged real validator/environment AST bodies. No Admission, Owner,
# Run or numerical module is constructed. StorageWatch is the actual stdlib-only
# installed class and sees ONLY the new empty fixture subtree.
source=ROOT/'tradingagents/research/onchain_replication/real_pilot_storage.py'
raw=source.read_bytes();tree=ast.parse(raw)
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('validate','environment') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('KIND','EXPERIMENT') for t in n.targets)]
watchpath=ROOT/'tradingagents/research/onchain_replication/workflow_storage.py'
spec=importlib.util.spec_from_file_location('actual_metadata_watch',watchpath);watch=importlib.util.module_from_spec(spec);spec.loader.exec_module(watch)
ns={'Path':Path,'os':os,'stat':stat,'StorageWatch':watch.StorageWatch,'FIELDS':watch.FIELDS}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),ns)
r=HERE/'fixture';r.mkdir();(r/'research_artifacts').mkdir();(r/'research_runs').mkdir()
budget={'schema_version':2,'kind':ns['KIND'],'authority_root':str(r),'experiment':ns['EXPERIMENT'],'roots':[str(r/'research_artifacts'),str(r/'research_runs'/ns['EXPERIMENT'])],'shared_files':[str(r/'research_runs/.lock')],'limits':{'max_allocated_bytes':1000000,'max_logical_bytes':1000000,'max_entries':100,'max_depth':64,'max_scan_seconds':5}}
ns['validate'](budget,r)
env=ns['environment'](r,{})
paths=set(env.values());assert len(paths)==12 and all(Path(x).is_relative_to(r/'research_artifacts/real_pilot_runtime') for x in paths)
wrong=copy.deepcopy(budget);wrong['shared_files']=[]
try:ns['validate'](wrong,r)
except ValueError as e:assert 'writer roots' in str(e)
else:raise AssertionError('actual union validator admitted missing shared lock')
results.append({'predicate':'unchanged actual union validator/environment AST','valid_empty_fixture':True,'missing_shared_lock_refused':True,'runtime_paths':sorted(paths),'source_sha256':hashlib.sha256(raw).hexdigest(),'numerical_authority':False})
(HERE/'CHECKS01.json').write_text(json.dumps({'status':'AUTHOR_HANDOFF_CHECKS_PASSED_NOT_REVIEW_APPROVAL','results':results,'source_body_changes':False,'arrays_read':False,'empirical_admission':False},indent=2,sort_keys=True)+'\n')
print('PASS: four real compact metadata joins; three missing prerequisites refused; actual union validator/path routing checked without authority.')
