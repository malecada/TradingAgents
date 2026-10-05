from pathlib import Path
import json,hashlib,tarfile,stat,ast
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;C=F/'heartbeat-root-checkpoint10-2026-10-04';Q=F/'financial-wrapper-serialized-prediction-failed-direct-capture02-2026-10-05';O=F/'financial-wrapper-serialized-prediction-final-direct01-2026-10-05';R=F/'financial-wrapper-serialized-prediction-final-direct02-2026-10-05';sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def save(n,x):
 p=D/n
 with p.open('x') as h:h.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')
 p.chmod(0o444);return ref(p)
a=Q/'failed-increment.tar.gz';assert ref(a)['sha256']=='dd7959b74bb47929ad70f0a90ab532191f80a5ac80dd8a9bda06c29ebe91ac03' and a.stat().st_size==2755736
mb=(Q/'archive-manifest.json').read_bytes();assert sha(mb)=='4ed334ae95d4013dde2d9964fb28bd6389db31cb08e6417fcfded0732da99b14';m=json.loads(mb);rows={x['path']:x for x in m['members']};assert len(rows)==47 and sum(x['kind']=='file' for x in rows.values())==36
assert stat.S_IMODE(O.stat().st_mode)==m['root_mode'];assert {str(p.relative_to(O)) for p in O.rglob('*')}==set(rows)
with tarfile.open(a,'r:gz') as t:
 members=t.getmembers();assert {x.name.rstrip('/') for x in members}==set(rows)
 for ti in members:
  n=ti.name.rstrip('/');row=rows[n];p=O/n;st=p.lstat();assert stat.S_IMODE(st.st_mode)==row['mode']==ti.mode
  if row['kind']=='file':
   assert ti.isfile() and stat.S_ISREG(st.st_mode) and st.st_nlink==1;body=t.extractfile(ti).read();assert len(body)==row['bytes'] and sha(body)==row['sha256'] and body==p.read_bytes()
  else:assert ti.isdir() and stat.S_ISDIR(st.st_mode)
root=json.loads((C/'SERIALIZED_PREDICTION_FAILED_DIRECT_CAPTURE02_ROOT_EXIT.json').read_bytes());assert root['actual_root_exit_code']==0 and root['claim_or_num_started'] is False and root['capture_sha256']==ref(Q/'CAPTURE01.json')['sha256'];assert root['stderr_sha256']==sha((C/'SERIALIZED_PREDICTION_FAILED_DIRECT_CAPTURE02.stderr').read_bytes())==sha(b'');assert root['stdout_sha256']==ref(C/'SERIALIZED_PREDICTION_FAILED_DIRECT_CAPTURE02.stdout')['sha256']
cp=save('FAILED_DIRECT_CAPTURE_CHECK02.json',{'schema_version':1,'decision':'accepted-actual-complete-failed-receiver-tree-capture','capture':ref(Q/'CAPTURE01.json'),'archive':ref(a),'manifest':ref(Q/'archive-manifest.json'),'source':ref(C/'SERIALIZED_PREDICTION_FAILED_DIRECT_CAPTURE02.py'),'entry':ref(D/'FAILED_DIRECT_CAPTURE_ENTRY02.json'),'actual_root_exit':ref(C/'SERIALIZED_PREDICTION_FAILED_DIRECT_CAPTURE02_ROOT_EXIT.json'),'regular_bodies':36,'typed_members':47,'original_bytes':sum(x.get('bytes',0) for x in rows.values()),'original_archive_bytes_modes_membership_joined':True,'partial_Git_included':True,'receiver_original_failure_preserved':True,'actual_external_recovery_pending':True,'numerical_authority':False})
old=(O/'recover02.py').read_text();new=(R/'recover01.py').read_text();assert sha(new.encode())=='afee6b3234f29518542a29d9bbf8611e048348d472614274e8d19b75512f8be2'
def ass(t):return [x for x in ast.parse(t).body if isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='REQUIRED'][-1]
x=ass(old);y=ass(new);required=ast.literal_eval(y.value);lines=new.splitlines(True);lines[y.lineno-1:y.end_lineno]=old.splitlines(True)[x.lineno-1:x.end_lineno];inverse=''.join(lines).replace('FINAL_POPULATION_COUNT = 36','FINAL_POPULATION_COUNT = 23').replace('fresh-serialized-prediction-final-direct02.git','fresh-serialized-prediction-final-direct01.git').replace('fresh-actual-serialized-prediction-final-direct02-recovered','fresh-actual-serialized-prediction-final-direct01-recovered');assert inverse==old
for n in ['watch01.py','utilities/owned_io.py']:assert (R/n).read_bytes()==(O/n).read_bytes()
s=json.loads((R/'SELECTED_BODIES_DRAFT01.json').read_bytes());assert s['remote_commit'] is None and len(s['rows'])==36 and sum(x['bytes'] for x in s['rows'])==3360961;assert required=={x['path']:{k:v for k,v in x.items() if k!='path'} for x in s['rows']}
for row in s['rows']:
 b=(M/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
oldrows=json.loads((O/'SELECTED_BODIES01.json').read_bytes())['rows'];assert all(x in s['rows'] for x in oldrows)
scope=json.loads((R/'FINAL_TYPED_SCOPE01.json').read_bytes());print('scopekeys',list(scope));print('scope_nonrows',{k:v for k,v in scope.items() if k not in ('original_regular_files','selected_original_files')})
sc=save('FINAL_DIRECT_SUCCESSOR_SOURCE_CHECK01.json',{'schema_version':1,'decision':'accepted-exact-final-direct02-source-and-fixed-draft','source':ref(R/'recover01.py'),'baseline_source':ref(O/'recover02.py'),'selection_draft':ref(R/'SELECTED_BODIES_DRAFT01.json'),'typed_scope':ref(R/'FINAL_TYPED_SCOPE01.json'),'literal_inverse_exact':True,'unchanged_watch':ref(R/'watch01.py'),'unchanged_owned_io':ref(R/'utilities/owned_io.py'),'selected_count':36,'selected_bytes':3360961,'original23_rows_retained':True,'expected_operations':10+len(set(x['sha256'] for x in s['rows']))+72,'failed_capture_check':cp,'prior_final_scope_check':ref(D/'FINAL_DIRECT_SOURCE_CHECK02.json'),'qualification':'Source and locally authentic fixed content only. Actual committed selected-tree membership/mode/blob-OID and push/readback required before entry. Actual recovery and failed archive restoration required before final-envelope/preflight acceptance. Original failed namespace never reused.','numerical_authority':False})
print(json.dumps({'capturecheck':cp,'sourcecheck':sc}))
