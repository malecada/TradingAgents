from pathlib import Path
import ast,hashlib,json
R=Path.cwd();O=Path(__file__).parent;v=json.loads((O/'INVERSE01.json').read_bytes());old=(R/v['baseline']).read_text();new=(O/'preflight01.py').read_text();assert new.replace(v['after'],v['before'])==old
rootpath=R/'research/onchain-paper-replication-2026-09-24/storage/real-pilot-third-graph-preservation-20261006-01/ROOT_TERMINAL01.json';root=json.loads(rootpath.read_bytes());assert 'selected_recorded_pids' not in root
try:root['selected_recorded_pids']
except KeyError:pass
else:raise AssertionError('old read unexpectedly available')
fn=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='preceding_storage');index=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pids' for t in n.targets));code=compile(ast.Module(body=fn.body[index:index+2],type_ignores=[]),'<exact changed read and original refusal>','exec');ns={'root':root,'Path':Path};exec(code,ns);assert len(ns['pids'])==76 and root['selected_recorded_pids_absent'] is True
for bad in ({}, {'actual_selected_recorded_pids':[]}, {'actual_selected_recorded_pids':[True]}):
 try:exec(code,{'root':bad,'Path':Path})
 except (ValueError,KeyError):pass
 else:raise AssertionError('bad metadata accepted')
print(json.dumps({'decision':'pass','original_key_red':True,'actual_key_green':True,'actual_pid_count':76,'actual_root_sha256':hashlib.sha256(rootpath.read_bytes()).hexdigest(),'exact_inverse':True,'missing_empty_bad_type_refused':True,'full_success_fixture_constructed':False}))
