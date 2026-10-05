from pathlib import Path
import json,hashlib,shutil,os,datetime
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-increment-preservation-review01-2026-10-05';R=F/'held-consumer-canonical-current-remote01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';OUT=F/'held-consumer-canonical-current-flat01-2026-10-05'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def put(n,v):
 p=D/n;b=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,h(b))
r=load(R/'REMOTE_RECOVERY01.json');x=load(R/'ACTUAL_ROOT_EXIT01.json');s=load(R/'SELECTED_BODIES01.json');entry=load(D/'REMOTE_ENTRY_RELEASE01.json')
assert ref(R/'REMOTE_RECOVERY01.json')['sha256']==x['remote_receipt_sha256']=='5d314ac03e00c41c4a9a3d04c06145e0830a18d7bc04f1e3a1b704e088c5a07a'
assert ref(R/'ACTUAL_ROOT_EXIT01.json')['sha256']=='b18b422d8e893ae174cc4a4b547095ee3a66d66267ef4ece8f9869b21716bf63' and x['actual_root_exit_code']==0
for k in ('stdout','stderr'):assert h((R/('ROOT01.'+k)).read_bytes())==x[k+'_sha256']
assert r['selection_sha256']==x['selection_sha256']==entry['selection']['sha256']==ref(R/'SELECTED_BODIES01.json')['sha256']
assert r['remote_commit']==s['remote_commit']==entry['actual_remote_commit'] and r['selected_count']==r['unique_selected_objects']==8 and r['selected_logical_bytes']==807426
assert len(r['operations'])==r['expected_operations']==34
for op in r['operations']:
 assert op['exit']==op['actual_reaped_exit']==0 and op['cleanup_failures']==[] and op['original_error'] is None
 assert op['actual_child_limits']=={'pid':op['pid'],'fsize':[4194304,4194304]} and not Path('/proc',str(op['pid'])).exists()
rows={x['path']:x for x in r['selected_blobs']};assert len(rows)==8
for row in s['rows']:
 v=rows[row['path']];assert all(v[k]==row[k] for k in row)
 b=(R/'selected'/row['path']).read_bytes();assert b==(M/row['path']).read_bytes() and len(b)==row['bytes'] and h(b)==row['sha256']
 assert v['git_mode'] in ('100644','100755') and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==v['git_object']
assert not (R/'FAILED01.json').exists() and r['elapsed_seconds']<600 and r['free_bytes']>=10737418240
assert r['whole_tree_policy']=={'allocated':100663296,'depth':32,'file':4194304,'floor':10737418240,'logical':67108864,'members':32768,'sample_seconds':5,'samples':8192}
put('REMOTE_CHECK01.json',{'schema_version':1,'decision':'accepted-actual-eight-body-canonical-increment-remote-recovery','receipt':ref(R/'REMOTE_RECOVERY01.json'),'actual_root_exit':ref(R/'ACTUAL_ROOT_EXIT01.json'),'selection':ref(R/'SELECTED_BODIES01.json'),'actual_selected_body_Git_oid_mode_joins':8,'selected_bytes':807426,'operations_reaped_zero':34,'cleanup_failures':[],'known_recorded_PIDs_absent':True,'qualification':'All eight originals/remote bodies match exact pins and Git object framing. Raw inherited receipt status/qualification is historical text; proof scope is the canonical current increment selection only. No full composed recovery before actual135-body flat verification; no numerical authority.'})
source=C/'CANONICAL_CURRENT_FLAT01.py';assert ref(source)==load(D/'FLAT_SOURCE_CHECK01.json')['source']
assert not os.path.lexists(OUT);free=shutil.disk_usage(F).free;assert free>=10737418240
put('FLAT_ENTRY_RELEASE01.json',{'schema_version':1,'decision':'accepted-exact-once-canonical-current-flat-restoration','source':ref(source),'source_check':ref(D/'FLAT_SOURCE_CHECK01.json'),'actual_receiver_check':ref(D/'REMOTE_CHECK01.json'),'receipt':ref(R/'REMOTE_RECOVERY01.json'),'one_use':True,'cwd':str(M),'argv':[str(M/'.venv/bin/python'),'-B',str(source)],'fresh_output':str(OUT),'expected_regular_bodies':135,'free_bytes':free,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'numerical_authority':False,'qualification':'Root alone may perform this one fresh R4 flat restoration. Receiver must not rerun. Preserve actual result/failure; full composed byte baseline proof and final release remain pending.'})
