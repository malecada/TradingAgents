from pathlib import Path
import json,hashlib,tarfile,stat,ast
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;C=F/'heartbeat-root-checkpoint10-2026-10-04';Q=F/'financial-wrapper-serialized-prediction-failed-direct-capture02-2026-10-05';O=F/'financial-wrapper-serialized-prediction-final-direct01-2026-10-05';R=F/'financial-wrapper-serialized-prediction-final-direct02-2026-10-05';sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def save(n,x):
 p=D/n
 with p.open('x') as h:h.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')
 p.chmod(0o444);return ref(p)
cp=ref(D/'FAILED_DIRECT_CAPTURE_CHECK02.json')
# Complete36 original/archive join completed in tool81f3d3 before later selection-alias assertion.
old=(O/'recover02.py').read_text();new=(R/'recover01.py').read_text();assert sha(new.encode())=='afee6b3234f29518542a29d9bbf8611e048348d472614274e8d19b75512f8be2'
def ass(t):return [x for x in ast.parse(t).body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='REQUIRED'][-1]
x=ass(old);y=ass(new);required=ast.literal_eval(y.value);lines=new.splitlines(True);lines[y.lineno-1:y.end_lineno]=old.splitlines(True)[x.lineno-1:x.end_lineno];inverse=''.join(lines).replace('FINAL_POPULATION_COUNT = 36','FINAL_POPULATION_COUNT = 23').replace('fresh-serialized-prediction-final-direct02.git','fresh-serialized-prediction-final-direct01.git').replace('fresh-actual-serialized-prediction-final-direct02-recovered','fresh-actual-serialized-prediction-final-direct01-recovered');assert inverse==old
for n in ['watch01.py','utilities/owned_io.py']:assert (R/n).read_bytes()==(O/n).read_bytes()
s=json.loads((R/'SELECTED_BODIES_DRAFT01.json').read_bytes());assert s['remote_commit'] is None and len(s['rows'])==36 and sum(x['bytes'] for x in s['rows'])==3360961;assert required=={x['path']:{k:v for k,v in x.items() if k!='path'} for x in s['rows']}
for row in s['rows']:
 b=(M/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
oldrows=json.loads((O/'SELECTED_BODIES01.json').read_bytes())['rows'];assert all(x in s['rows'] for x in oldrows if not x['path'].endswith('/FINAL_TYPED_SCOPE02.json'));assert (R/'FINAL_TYPED_SCOPE01.json').read_bytes()==(O/'FINAL_TYPED_SCOPE02.json').read_bytes()
scope=json.loads((R/'FINAL_TYPED_SCOPE01.json').read_bytes());print('scopekeys',list(scope));print('scope_nonrows',{k:v for k,v in scope.items() if k not in ('original_regular_files','selected_original_files')})
sc=save('FINAL_DIRECT_SUCCESSOR_SOURCE_CHECK01.json',{'schema_version':1,'decision':'accepted-exact-final-direct02-source-and-fixed-draft','source':ref(R/'recover01.py'),'baseline_source':ref(O/'recover02.py'),'selection_draft':ref(R/'SELECTED_BODIES_DRAFT01.json'),'typed_scope':ref(R/'FINAL_TYPED_SCOPE01.json'),'literal_inverse_exact':True,'unchanged_watch':ref(R/'watch01.py'),'unchanged_owned_io':ref(R/'utilities/owned_io.py'),'selected_count':36,'selected_bytes':3360961,'original22_content_rows_retained':True,'identical_typed_scope_relocated':True,'expected_operations':10+len(set(x['sha256'] for x in s['rows']))+72,'failed_capture_check':cp,'prior_final_scope_check':ref(D/'FINAL_DIRECT_SOURCE_CHECK02.json'),'qualification':'Source and locally authentic fixed content only. Actual committed selected-tree membership/mode/blob-OID and push/readback required before entry. Actual recovery and failed archive restoration required before final-envelope/preflight acceptance. Original failed namespace never reused.','numerical_authority':False})
print(json.dumps({'capturecheck':cp,'sourcecheck':sc}))
