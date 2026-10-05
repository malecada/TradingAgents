from pathlib import Path
import json,hashlib,shutil,os,datetime
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-serialized-prediction-outcome-preservation-review01-2026-10-05';R=F/'financial-wrapper-serialized-prediction-outcome-remote01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';OUT=F/'financial-wrapper-serialized-prediction-outcome-flat01-2026-10-05'
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def load(p):return json.loads(p.read_bytes())
def put(n,v):
 p=D/n;b=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,h(b))
r=load(R/'REMOTE_RECOVERY01.json');x=load(R/'ACTUAL_ROOT_EXIT01.json');s=load(R/'SELECTED_BODIES01.json')
assert ref(R/'REMOTE_RECOVERY01.json')['sha256']=='be5c162d95e7899531b89caf800d2327b3ec4ef38ecdf58595e512c9b83ba667'==x['remote_receipt_sha256']
assert ref(R/'ACTUAL_ROOT_EXIT01.json')['sha256']=='a4174d8cbeba982fae7affbbd238964e174b05a3f9fdef9b919b3ec28c6fc249' and x['actual_root_exit_code']==0
for k in ('stdout','stderr'):assert h((R/('ACTUAL_ROOT01.'+k)).read_bytes())==x[k+'_sha256']
assert r['selection_sha256']==ref(R/'SELECTED_BODIES01.json')['sha256'] and r['remote_commit']==s['remote_commit']=='e260b040baba493449e89d3e91cab3d89ae4a55e'
assert r['selected_count']==r['unique_selected_objects']==8 and r['selected_logical_bytes']==1252014
assert len(r['operations'])==r['expected_operations']==34
for o in r['operations']:
 assert o['exit']==o['actual_reaped_exit']==0 and o['cleanup_failures']==[] and o['original_error'] is None
 assert o['actual_child_limits']=={'pid':o['pid'],'fsize':[4194304,4194304]}
 assert not Path('/proc',str(o['pid'])).exists()
rows={x['path']:x for x in r['selected_blobs']};assert len(rows)==8
for p in s['rows']:
 v=rows[p['path']];assert all(v[k]==p[k] for k in p)
 raw=(R/'selected'/p['path']).read_bytes();assert raw==(M/p['path']).read_bytes() and len(raw)==p['bytes'] and h(raw)==p['sha256']
 assert v['git_mode'] in ('100644','100755') and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==v['git_object']
assert r['whole_tree_policy']=={'allocated':100663296,'depth':32,'file':4194304,'floor':10737418240,'logical':67108864,'members':32768,'sample_seconds':5,'samples':8192}
assert r['elapsed_seconds']<600 and r['free_bytes']>=10737418240
put('REMOTE_CHECK01.json',{'schema_version':1,'decision':'accepted-actual-prediction-outcome-selected-byte-recovery','receipt':ref(R/'REMOTE_RECOVERY01.json'),'actual_root_exit':ref(R/'ACTUAL_ROOT_EXIT01.json'),'selection':ref(R/'SELECTED_BODIES01.json'),'selected_count':8,'selected_bytes':1252014,'actual_reaped_operations':34,'known_operation_PIDs_absent':True,'cleanup_failures':[],'qualification':'Eight original/received bytes and Git OIDs/modes joined independently. Inherited helper status/qualification text describes its historical caller, not the new outcome scope. This proof is restricted to these eight selected bodies; full86-body restore and inherited composition remain pending. No numerical authority.'})
source=C/'SERIALIZED_PREDICTION_OUTCOME_FLAT01.py';prior=load(D/'FLAT_SOURCE_CHECK01.json');assert ref(source)==prior['source']
assert not os.path.lexists(OUT);free=shutil.disk_usage(F).free;assert free>=10737418240
put('FLAT_ENTRY_RELEASE01.json',{'schema_version':1,'decision':'accepted-exact-once-prediction-outcome-flat-restoration','one_use':True,'source':ref(source),'source_check':ref(D/'FLAT_SOURCE_CHECK01.json'),'receiver_check':ref(D/'REMOTE_CHECK01.json'),'receiver_receipt':ref(R/'REMOTE_RECOVERY01.json'),'actual_receiver_root_exit':ref(R/'ACTUAL_ROOT_EXIT01.json'),'cwd':str(M),'argv':[str(M/'.venv/bin/python'),'-B',str(source)],'fresh_output':str(OUT),'free_bytes':free,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_regular_bodies':86,'numerical_authority':False,'qualification':'Root alone may perform the one fresh unchanged-R4 restoration. Preserve actual result or failure. No receiver rerun; full current outcome composition acceptance remains pending actual restored bytes.'})
