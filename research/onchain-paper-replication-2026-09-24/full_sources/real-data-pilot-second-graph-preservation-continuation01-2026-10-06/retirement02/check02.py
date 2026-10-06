"""Only the changed compact union/failure gate. Never calls retirement execution."""
import ast,copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/'synthetic-root';ROOT.mkdir()
BACKUP=ROOT/'old';UNION=ROOT/'new';BACKUP.mkdir();UNION.mkdir();(BACKUP/'guard01').mkdir();(UNION/'guard01').mkdir();UNION_ID='real-pilot-second-graph-preservation-metadata-20261006-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v));return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
failed={'decision':'accepted-failed-parent-partial-byte-evidence','parent_status':'failed','authenticated_body_get_count':36};failed_ref=put(ROOT/'failed-review.json',failed)
u={'identity':UNION_ID,'parent':'old','parent_status':'FAILED','count':36,'files':[{'index':i} for i in range(36)],'fresh_body_transfers':0,'fresh_restoration_metadata_rows':[35],'parent_proof':{'review':failed_ref}}
put(UNION/'complete.json',u);put(UNION/'recovered-complete.json',u)
oldguard={'phase':'failed','child_exit_code':None,'cleanup_verified':True,'cgroup':str(ROOT/'absent-old-cgroup'),'monitor_pid':2**40};newguard={**oldguard,'phase':'complete','child_exit_code':0,'cgroup':str(ROOT/'absent-new-cgroup')}
put(BACKUP/'guard01/final.json',oldguard);put(UNION/'guard01/final.json',newguard)
put(BACKUP/'outer-exit01.json',{'entry_selected_exit_code':1,'guard_child_exit_code':None});put(BACKUP/'ROOT_TERMINAL01.json',{'actual_root_tool_exit_code':1,'separate_actual_worker_exit_code':-15});put(UNION/'outer-exit01.json',{'entry_selected_exit_code':0,'guard_child_exit_code':0,'cleanup_verified':True})
evidence={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*.json')};outcome={'decision':'accepted','identity':UNION_ID,'full_scope_byte_recovery':True,'evidence':{str((UNION/n).relative_to(ROOT)):evidence[str((UNION/n).relative_to(ROOT))] for n in ('complete.json','recovered-complete.json','guard01/final.json','outer-exit01.json')}}
outref=put(ROOT/'outcome.json',outcome);evidence[outref['path']]=outref['sha256'];review={'union_outcome_review':outref,'evidence':evidence}
tree=ast.parse((HERE/'retire02.py').read_text());execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute');start=next(i for i,n in enumerate(execute.body) if isinstance(n,ast.FunctionDef) and n.name=='reviewed');stop=next(i for i,n in enumerate(execute.body) if i>start and isinstance(n,ast.If) and 'subprocess.check_output' in ast.unparse(n.test));fn=ast.FunctionDef(name='check',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=execute.body[start:stop],decorator_list=[]);module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));space=globals();exec(compile(module,'changed-union-gate','exec'),space);check()
refusals=[]
def refuse(message):
 try:check()
 except ValueError as e:assert message in str(e);refusals.append(str(e))
 else:raise AssertionError(message)
put(BACKUP/'guard01/final.json',{**oldguard,'phase':'complete'});review['evidence']['old/guard01/final.json']=sha(BACKUP/'guard01/final.json');refuse('permanent FAILED');put(BACKUP/'guard01/final.json',oldguard);review['evidence']['old/guard01/final.json']=sha(BACKUP/'guard01/final.json')
put(UNION/'guard01/final.json',{**newguard,'child_exit_code':None});review['evidence']['new/guard01/final.json']=sha(UNION/'guard01/final.json');outcome['evidence']['new/guard01/final.json']=review['evidence']['new/guard01/final.json'];outref=put(ROOT/'outcome.json',outcome);review['union_outcome_review']=outref;review['evidence'][outref['path']]=outref['sha256'];refuse('actual NEW preservation union/native cleanup')
put(UNION/'guard01/final.json',newguard);review['evidence']['new/guard01/final.json']=sha(UNION/'guard01/final.json');del outcome['evidence']['new/guard01/final.json'];outref=put(ROOT/'outcome.json',outcome);review['union_outcome_review']=outref;review['evidence'][outref['path']]=outref['sha256'];refuse('independent union receipt join')
c=json.loads((HERE/'CHANGE02.json').read_bytes());b=(HERE/'retire02.py').read_text()
for e in reversed(c['literal_edits']):assert b.count(e['after'])==1;b=b.replace(e['after'],e['before'])
assert hashlib.sha256(b.encode()).hexdigest()==c['before_sha256']
result={'synthetic_changed_gate_pass':True,'refusals':refusals,'exact_inverse':True,'retirement_execution_called':False,'payload_opens':0,'qualification':'AST-extracted changed compact gate only; no real release, Run/Owner, native, network or unlink'};(HERE/'CHECK02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
