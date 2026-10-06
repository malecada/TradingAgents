from pathlib import Path
import ast,hashlib,json
R=Path.cwd();O=Path(__file__).parent;F=O.parent;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,v in json.loads((O/'INVERSE01.json').read_bytes()).items():
 s=(R/v['baseline']).read_text();assert h(R/v['baseline'])==v['before_sha256']
 for e in v['literal_edits']:assert e['before'] in s;s=s.replace(e['before'],e['after'])
 assert s==(O/name).read_text() and h(O/name)==v['after_sha256'];ast.parse(s)
# Compile only new stdlib metadata predicate; no lifecycle/native imports or authority construction.
fn=next(n for n in ast.parse((O/'preflight01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='preceding_storage');ns={'Path':Path,'ROOT':R,'json':json,'file_hash':h};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<candidate predicate>','exec'),ns)
review=F/'real-data-pilot-second-graph-union-retirement-review01-2026-10-06/UNION_OUTCOME_REVIEW01.json';ref={'path':str(review.relative_to(R)),'sha256':h(review)};checks=[]
for label,inputs in [('missing',{}),('corrupt_actual_hash',{'storage_closure_review':{**ref,'sha256':'0'*64}}),('wrong_genuine_backup',{'storage_closure_review':ref})]:
 try:ns['preceding_storage'](inputs)
 except (ValueError,KeyError) as exc:checks.append({'case':label,'refused':type(exc).__name__,'message':str(exc)})
 else:raise AssertionError(label)
old=ast.parse((R/json.loads((O/'INVERSE01.json').read_bytes())['preflight01.py']['baseline']).read_text());new=ast.parse((O/'preflight01.py').read_text());oldcheck=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='check');newcheck=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='check')
# The exact declared text edits above are the sole differences; no execution is attempted.
result={'decision':'pass','literal_inverses':2,'syntax':2,'launch_byte_identical':True,'actual_metadata_refusals':checks,'future_success_path_unexecuted':True,'payload_reads':0,'native_calls':0,'numerical_imports':False};(O/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
