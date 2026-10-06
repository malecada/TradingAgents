"""Actual admitted function prefix; explicit synthetic admission, no numeric import."""
import ast,hashlib,json,tempfile,types,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];P=ROOT/'tradingagents/research/onchain_replication'
identity=ast.parse((P/'imported_mcm_identity.py').read_text());constants={n.targets[0].id:ast.literal_eval(n.value) for n in identity.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'KERNEL','HELPER'}}
helpers=set(constants.values());package='tradingagents/research/onchain_replication/fixture_source.py'
def require(v,m):
    if not v:raise ValueError(m)
def load(path):
    tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admitted');stop=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='own')
    fn.body=fn.body[:stop]+[ast.Return(value=ast.Constant(value='source_boundary_passed'))]
    tree=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));ns={'__package__':'closure_fixture','Path':Path,'require':require,'schema':lambda j:None,'validate_plan':lambda p:p,'_read':lambda ad,role:ad.plan,'_bind_resources':lambda *a:None,'_source_authority_root':lambda a:True}
    exec(compile(tree,str(path),'exec'),ns);return ns['admitted']
module=types.ModuleType('closure_fixture.job');module.required_sources=lambda:{package};sys.modules[module.__name__]=module
module=types.ModuleType('closure_fixture.provenance');module.file_hash=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();sys.modules[module.__name__]=module
functions=[load(P/'real_pilot_import_caller.py'),load(HERE/'candidate/real_pilot_import_caller.py')]
# Guard's literal helper closure must equal the actual Target.sources constants.
tree=ast.parse((HERE/'candidate/real_pilot_import_caller.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admitted');added=next(n.value.right for n in fn.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='required');assert ast.literal_eval(added)==helpers
rows=[]
with tempfile.TemporaryDirectory(prefix='source-closure-fixture-') as directory:
    root=Path(directory);pins={}
    for i,name in enumerate(sorted({package}|helpers)):
        q=root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(f'# inert source fixture{i}\n');pins[name]=hashlib.sha256(q.read_bytes()).hexdigest()
    def run(fn,sourcepins):
        ad=types.SimpleNamespace(root=root,experiment={'source_files':sourcepins,'cells':['one']},family={'mechanism_id':'celik-sefer-transaction-graph-full-neural-replication'},plan={'schema_version':1,'cell_id':'one'})
        job={'payload':{'representation_jobs':{'one':{'real_pilot_input':'pilot'}}},'resources':{'storage_budget':{'root':str(root)}}}
        try:return {'status':'pass','value':fn(ad,job)}
        except ValueError as e:return {'status':'refuse','reason':str(e)}
    for name in sorted(helpers):
        omitted={k:v for k,v in pins.items() if k!=name};a,b=[run(fn,omitted) for fn in functions];assert a['status']=='pass' and b['status']=='refuse';rows.append({'case':'missing helper','helper':name,'original':a,'candidate':b})
        q=root/name;raw=q.read_bytes();q.write_bytes(raw+b'# changed\n');a,b=[run(fn,pins) for fn in functions];assert a['status']=='pass' and b['status']=='refuse';rows.append({'case':'changed helper','helper':name,'original':a,'candidate':b});q.write_bytes(raw)
    a,b=[run(fn,pins) for fn in functions];assert a['status']==b['status']=='pass';rows.append({'case':'complete exact closure','original':a,'candidate':b})
    q=root/package;raw=q.read_bytes();q.write_bytes(raw+b'# changed\n');assert run(functions[1],pins)['status']=='refuse';q.write_bytes(raw);rows.append({'case':'changed required package source','candidate':'refuse'})
old="    require(required_sources() <= set(ad.experiment['source_files']), 'complete current package closure required')\n";assert (HERE/'candidate/real_pilot_import_caller.py').read_text().replace((HERE/'REPLACEMENT01.txt').read_text(),old)==(P/'real_pilot_import_caller.py').read_text()
assert not any(k=='numpy' or k.startswith('torch') for k in sys.modules)
result={'status':'PASS','checks':rows,'helper_set_equals_actual_Target_constants':True,'exact_inverse':True,'qualification':'Actual admitted prefix through source boundary, earlier metadata functions and admission are explicit stubs. No full admission/claim/Owner/scientific arrays or numerical helpers imported. This proves missing/changed closure refusal before downstream work, not numerical capacity.'};(HERE/'CHECK_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','cases':len(rows),'exact_inverse':True}))
