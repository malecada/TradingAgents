"""Independent compact changed-gate checks; never calls execute or native tools."""
import ast, copy, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
MAIN=HERE.parents[3]
F=HERE.parent
SRC=F/'real-data-pilot-second-graph-preservation-continuation01-2026-10-06/retirement02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((SRC/'MANIFEST02.json').read_bytes())
for rel,pin in manifest.items():
    p=SRC/rel
    assert not p.is_symlink() and sha(p)==pin
source=SRC/'retire02.py'; text=source.read_text()
assert sha(source)=='61320cbea932dca635837c156f22e6a007d1d8f8bea857cd9884fb47d26888d8'
change=json.loads((SRC/'CHANGE02.json').read_bytes()); inverse=text
for e in reversed(change['literal_edits']):
    assert inverse.count(e['after'])==1
    inverse=inverse.replace(e['after'],e['before'])
assert inverse.encode()==(MAIN/change['before_path']).read_bytes()
installed=F/'real-data-pilot-second-graph-post-recovery-retirement02-2026-10-06/retire02.py'
assert sha(installed)==sha(source) and installed.resolve().parents[4]==MAIN
failed=F/'real-data-pilot-second-graph-storage-outcome-review01-2026-10-06/FAILED_REVIEW02.json'
assert sha(failed)=='7516cd31e3218d8d3ae22130db9968dc6a61175f0716fe3bf8893ae2ff69c687'
# Execute only the changed bounded metadata gate, without systemctl, module imports,
# selector, body validation, locks, writes, or unlink statements from execute().
fun=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
start=next(i for i,n in enumerate(fun.body) if isinstance(n,ast.FunctionDef) and n.name=='reviewed')
end=next(i for i,n in enumerate(fun.body) if i>start and isinstance(n,ast.If) and 'subprocess.check_output' in ast.unparse(n.test))
fn=ast.FunctionDef(name='gate',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(fun.body[start:end]),decorator_list=[])
code=compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'independent-changed-metadata-gate','exec')
ROOT=HERE/'synthetic';ROOT.mkdir()
BACKUP=ROOT/'old';UNION=ROOT/'new';UNION_ID='real-pilot-second-graph-preservation-metadata-20261006-01'
for p in [BACKUP/'guard01',UNION/'guard01']:p.mkdir(parents=True)
old={'phase':'failed','child_exit_code':None,'cleanup_verified':True,'cgroup':str(ROOT/'absent-old'),'monitor_pid':2**40}
new={**old,'phase':'complete','child_exit_code':0,'cgroup':str(ROOT/'absent-new')}
base={'old/guard01/final.json':old,'old/outer-exit01.json':{'entry_selected_exit_code':1,'guard_child_exit_code':None},'old/ROOT_TERMINAL01.json':{'actual_root_tool_exit_code':1,'separate_actual_worker_exit_code':-15},'new/guard01/final.json':new,'new/outer-exit01.json':{'entry_selected_exit_code':0,'guard_child_exit_code':0,'cleanup_verified':True},'failed.json':{'decision':'accepted-failed-parent-partial-byte-evidence','parent_status':'failed','authenticated_body_get_count':36}}
def put(name,value):
    p=ROOT/name;p.write_text(json.dumps(value,sort_keys=True));return {'path':name,'sha256':sha(p)}
def run(mutation=None):
    data=copy.deepcopy(base)
    if mutation:mutation(data)
    for name,value in data.items():put(name,value)
    union={'identity':UNION_ID,'parent':'old','parent_status':'FAILED','count':36,'files':[{'index':i} for i in range(36)],'fresh_body_transfers':0,'fresh_restoration_metadata_rows':[35],'parent_proof':{'review':{'path':'failed.json','sha256':sha(ROOT/'failed.json')}}}
    put('new/complete.json',union);put('new/recovered-complete.json',union)
    evidence={n:sha(ROOT/n) for n in [*data,'new/complete.json','new/recovered-complete.json']}
    outcome={'decision':'accepted','identity':UNION_ID,'full_scope_byte_recovery':True,'evidence':{n:v for n,v in evidence.items() if n.startswith('new/')}}
    ref=put('outcome.json',outcome);evidence['outcome.json']=ref['sha256']
    scope={'Path':Path,'hashlib':hashlib,'json':json,'ROOT':ROOT,'BACKUP':BACKUP,'UNION':UNION,'UNION_ID':UNION_ID,'review':{'evidence':evidence,'union_outcome_review':ref}}
    exec(code,scope);scope['gate']()
run()
refusals=[]
cases=[('old/guard01/final.json','phase','complete'),('old/guard01/final.json','child_exit_code',0),('old/guard01/final.json','cleanup_verified',False),('old/ROOT_TERMINAL01.json','actual_root_tool_exit_code',0),('old/ROOT_TERMINAL01.json','separate_actual_worker_exit_code',0),('old/outer-exit01.json','guard_child_exit_code',0),('new/guard01/final.json','phase','failed'),('new/guard01/final.json','child_exit_code',None),('new/guard01/final.json','cleanup_verified',False),('new/outer-exit01.json','entry_selected_exit_code',1),('new/outer-exit01.json','guard_child_exit_code',None),('failed.json','authenticated_body_get_count',35)]
for name,key,value in cases:
    try:run(lambda d:d[name].__setitem__(key,value))
    except ValueError as e:refusals.append({'path':name,'field':key,'value':value,'refusal':str(e)})
    else:raise AssertionError((name,key,value))
run()
result={'decision':'accepted-source-only','source_sha256':sha(source),'installed_source':str(installed.relative_to(MAIN)),'manifest_sha256':sha(SRC/'MANIFEST02.json'),'members_authenticated':len(manifest),'exact_five_edit_inverse':True,'failed_basis_sha256':sha(failed),'synthetic_valid_metadata_gate_passed':True,'independent_refusals':refusals,'retirement_execute_called':False,'payload_reads':0,'native_or_network_calls':0,'actual_union_outcome_tested':False,'retirement_release':False}
(HERE/'SOURCE_CHECK01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
