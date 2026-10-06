import ast,copy,hashlib,importlib.util,json,sys,difflib
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;ROOT=H.parents[3]
def load(p,name):
    sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def need(v,m):
    if not v:raise ValueError(m)
def refused(fn):
    try:fn()
    except (ValueError,KeyError,TypeError) as e:return str(e)
    raise AssertionError('expected refusal')
def normalized(v):
    v=copy.deepcopy(v)
    for d in v['residual_domains'].values():d.pop('evidence_sha256')
    return v
old=load(F/'real-data-pilot-feature-residual-controls01-2026-10-06/residuals01.py','old_residual')
new=load(H/'residuals02.py','selected_residual');handoff=load(H/'prepare_builder03_input02.py','candidate_handoff')
draft=json.loads((H/'draft07/INPUT_DRAFT01.json').read_bytes());p=draft['protocol'];stage=json.loads((ROOT/p['references']['compact_policy']['path']).read_bytes())['stage_policy'];kw={'native_file_bytes':1024**3,'training_checkpoint_bytes':4*1024**2,'runtime_reservation':p['runtime_reservation']}
a=old.resolve(stage,**kw);b=new.resolve(stage,**kw);assert normalized(a)==normalized(b)
c=new.resolve(stage,**kw,lifecycle_reservation=p['lifecycle_reservation']);assert c['residual_domains']['training_and_lifecycle']['logical_bytes']==32*1024**2
for k in a['residual_domains']:
    if k!='training_and_lifecycle':assert normalized(a)['residual_domains'][k]==normalized(c)['residual_domains'][k]
reject=[]
for key,value in [('logical_bytes',False),('logical_bytes',1),('regular_files',67),('directories',15),('max_file_bytes',1025*1024**2),('max_file_bytes',1)]:
    bad=dict(p['lifecycle_reservation']);bad[key]=value;reject.append(refused(lambda:new.resolve(stage,**kw,lifecycle_reservation=bad)))
reject.append(refused(lambda:new.resolve(stage,**kw,lifecycle_reservation={})))
missing=refused(lambda:handoff.prepare(ROOT,draft));assert all(s in missing for s in ('2022-05-23','2022-05-30','2022-06-06'))
# Actual installed finite route predicate, no module/scientific import or guard.
source=ROOT/'tradingagents/research/onchain_replication/real_pilot_import_caller.py'
t=ast.parse(source.read_text());ns={'require':need,'Path':Path,'GIB':1024**3,'FILE_MAX':4*1024**2};nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('_finite_resources','_tiny_resources')];exec(compile(ast.Module(nodes,[]),str(source),'exec'),ns)
job=json.loads((ROOT/p['references']['execution_job']['path']).read_bytes());ns['_finite_resources'](job['resources']);tiny=refused(lambda:ns['_tiny_resources'](job['resources']))
# Real imported kernel's pure scalar policy predicate, not imported numerical module.
kpath=F/'original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py';tree=ast.parse(kpath.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy');ns={'require':need};exec(compile(ast.Module([node],[]),str(kpath),'exec'),ns)
counts=json.loads((H/'draft07/DIMENSIONS01.json').read_text())['known_counts'];entries=32*max(n for n in counts.values() if n is not None)
v={'schema_version':1,'edge_chunk':4096,'max_buffer_bytes':1048576,'max_output_bytes':4*entries,'max_numeric_bytes':4*entries+1048576};ns['validate_policy'](v,entries)
bad=dict(v,max_numeric_bytes=2*1024**2);numeric_refusal=refused(lambda:ns['validate_policy'](bad,entries))
# Literal edits retained; inverse reconstruction of both source candidates.
inverses={}
for before,after in [(F/'real-data-pilot-feature-residual-controls01-2026-10-06/residuals01.py',H/'residuals02.py'),(F/'real-data-pilot-feature-control-residual-review01-2026-10-06/prepare_builder03_input01.py',H/'prepare_builder03_input02.py')]:
    x,y=before.read_text(),after.read_text();changes=[]
    for op,a0,a1,b0,b1 in difflib.SequenceMatcher(None,x,y,autojunk=False).get_opcodes():
        if op!='equal':changes.append({'start':b0,'end':b1,'before':x[a0:a1],'after':y[b0:b1]})
    z=y
    for e in reversed(changes):assert z[e['start']:e['end']]==e['after'];z=z[:e['start']]+e['before']+z[e['end']:]
    assert z==x;inverses[after.name]={'baseline':str(before.relative_to(ROOT)),'baseline_sha256':hashlib.sha256(x.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(y.encode()).hexdigest(),'edits':changes}
(H/'EXACT_INVERSE01.json').write_text(json.dumps(inverses,indent=2,sort_keys=True)+'\n')
assert not {'numpy','torch','pandas'} & set(sys.modules)
result={'status':'passed-offline-metadata-only','default_parity':True,'opt_in_only_lifecycle_changed':True,'invalid_selections_refused':len(reject),'missing_real_counts_refused':missing,'schema2_finite_native_cap_passed':True,'tiny_route_still_refused':tiny,'actual_imported_kernel_scalar_check':True,'tiny_numeric_allowance_refused':numeric_refusal,'known_counts':counts,'selected_lifecycle_bytes':32*1024**2,'old64L_bytes':a['residual_domains']['training_and_lifecycle']['logical_bytes'],'no_payload_reads_or_native_admission':True,'source_pins':{str(q.relative_to(ROOT)):hashlib.sha256(q.read_bytes()).hexdigest() for q in [source,kpath,H/'residuals02.py',H/'prepare_builder03_input02.py',H/'prepare_selected01.py']}}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
