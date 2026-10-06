"""Only identity/inverse and new metadata gate; never retirement/native execution."""
import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parents[3]
source=(H/'retire01.py').read_text();delta=json.loads((H/'INVERSE01.json').read_bytes());before=source
for e in reversed(delta['literal_edits']):
    assert before.count(e['after'])==1;before=before.replace(e['after'],e['before'])
assert before.encode()==(M/delta['baseline']).read_bytes()
s={'__file__':str(H/'retire01.py'),'__name__':'offline_source_check'};exec(compile(source,str(H/'retire01.py'),'exec'),s)
t=H/'RELEASE_TEMPLATE01.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
try:s['execute'](t,sha(t))
except ValueError as e:assert 'exact outcome/retirement release' in str(e)
else:raise AssertionError('null template admitted')
assert not any((H/n).exists() for n in ['attempt01.json','complete01.json','failed01.json'])
root=H/'synthetic';root.mkdir();backup=root/'real-pilot-third-graph-preservation-20261006-01';(backup/'guard01').mkdir(parents=True)
def put(p,v):p.write_text(json.dumps(v,sort_keys=True));return {'path':str(p.relative_to(root)),'sha256':sha(p)}
base={'complete.json':{'identity':backup.name,'count':36,'files':[{'index':i} for i in range(36)],'originals_retained':True,'recoveries_retained':True},'guard01/final.json':{'phase':'complete','child_exit_code':0,'cleanup_verified':True,'cgroup':str(root/'absent-cgroup'),'monitor_pid':2**40},'outer-exit01.json':{'entry_selected_exit_code':0,'guard_child_exit_code':0,'cleanup_verified':True},'ROOT_TERMINAL01.json':{'identity':backup.name,'actual_root_tool_exit_code':0}}
fun=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
start=next(i for i,n in enumerate(fun.body) if isinstance(n,ast.FunctionDef) and n.name=='reviewed')
stop=next(i for i,n in enumerate(fun.body) if i>start and isinstance(n,ast.If) and 'subprocess.check_output' in ast.unparse(n.test))
fn=ast.FunctionDef(name='check_gate',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(fun.body[start:stop]),decorator_list=[])
code=compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'changed-recovery-gate','exec')
def check(mut=None):
    data=copy.deepcopy(base)
    if mut:mut(data)
    data['recovered-complete.json']=copy.deepcopy(data['complete.json'])
    evidence={}
    for n,v in data.items():r=put(backup/n,v);evidence[r['path']]=r['sha256']
    outcome={'decision':'accepted','identity':backup.name,'full_scope_byte_recovery':True,'evidence':dict(evidence)}
    r=put(root/'outcome.json',outcome);evidence[r['path']]=r['sha256']
    env={'Path':Path,'json':json,'hashlib':hashlib,'ROOT':root,'BACKUP':backup,'review':{'backup_outcome_review':r,'evidence':evidence}}
    exec(code,env);env['check_gate']()
check();refusals=[]
for n,k,v in [('ROOT_TERMINAL01.json','actual_root_tool_exit_code',1),('guard01/final.json','child_exit_code',None),('guard01/final.json','cleanup_verified',False),('complete.json','count',35)]:
    try:check(lambda d:d[n].__setitem__(k,v))
    except ValueError as e:refusals.append({'path':n,'field':k,'value':v,'refusal':str(e)})
    else:raise AssertionError((n,k,v))
check()
denominator=next(n.test for n in fun.body if isinstance(n,ast.If) and "row['bytes'] != 3310923776" in ast.unparse(n.test))
predicate=compile(ast.Expression(denominator),'exact-ledger-denominator','eval')
env={'n':11,'union':{'files':[{} for _ in range(36)]},'kept':{},'row':{'bytes':3310923776}}
assert eval(predicate,env) is False
env['row']['bytes']-=1;assert eval(predicate,env) is True
result={'decision':'pass-source-only','literal_inverse_edits':len(delta['literal_edits']),'null_release_template_refused_before_attempt':True,'synthetic_valid_gate':True,'refusals':refusals,'exact_ledger_byte_predicate':3310923776,'pair_bytes':6621847552,'actual_backup_outcome_read':False,'payload_reads':0,'native_network_deletion_calls':0,'qualification':'Synthetic metadata only; no actual recovery/retirement authority and no active-backup files inspected.'}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
