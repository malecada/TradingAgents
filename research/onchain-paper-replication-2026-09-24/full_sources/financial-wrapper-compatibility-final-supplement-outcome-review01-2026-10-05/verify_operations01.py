"""Supplemental read-only exact original Git-operation output joins."""
from pathlib import Path
import json,hashlib,time,stat,os
H=Path(__file__).resolve().parent;B=H.parent;D=B/'financial-wrapper-compatibility-final-supplement-root02-2026-10-05';F=B/'financial-wrapper-compatibility-final-supplement-flat-root02-2026-10-05'
sha=lambda x:hashlib.sha256(x).hexdigest()
e=json.loads((H/'ACTUAL_PINS01.json').read_bytes());r=json.loads((Path(e['remote_receipt']['path'])).read_bytes());assert sha(Path(e['remote_receipt']['path']).read_bytes())==e['remote_receipt']['sha256']
checks=0
def check(v):
 global checks
 assert v;checks+=1
ops=r['operations'];records=r['selected_blobs'];main=r['remote_commit'];branch=r['branch']
def output(i,body):check(ops[i]['stdout_bytes']==len(body) and ops[i]['stdout_sha256']==sha(body))
output(0,(r['origin']+'\n').encode());head=(main+'\t'+branch+'\n').encode();output(1,head);output(-1,head);output(7,(main+'\n').encode())
tree=b''.join((x['git_mode']+' blob '+x['git_object']+'\t'+x['path']).encode()+b'\0' for x in records);output(8,tree)
start=9+r['unique_selected_objects']
for i,x in enumerate(records):
 b=(D/'selected'/x['path']).read_bytes();check(len(b)==x['bytes'] and sha(b)==x['sha256']);output(start+2*i,(str(len(b))+'\n').encode());output(start+2*i+1,b)
flat=json.loads(Path(e['flat_receipt']['path']).read_bytes());check(flat['source']=='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41')
for row in flat['observations']:check(row['logical_bytes']<=64*1024**2 and row['allocated_bytes']<=96*1024**2 and row['seconds']<5 and 1<=row['complete_attempts']<=3)
free=os.statvfs(F).f_bavail*os.statvfs(F).f_frsize;check(free>=10*1024**3)
result={'schema_version':1,'checks':checks,'recorded_remote_operations':len(ops),'first_final_HEAD_and_fetched_commit_output_joins':True,'all_selected_tree_mode_OID_and_size_body_output_joins':True,'current_disk_free_bytes':free,'remote_observations':len(r['whole_tree_observations']),'flat_inner_observations':len(flat['observations']),'remote_max_logical':max(x['logical_bytes'] for x in r['whole_tree_observations']),'remote_max_allocated':max(x['allocated_bytes'] for x in r['whole_tree_observations']),'flat_max_logical':max(x['logical_bytes'] for x in flat['observations']),'flat_max_allocated':max(x['allocated_bytes'] for x in flat['observations']),'qualified_sampled_not_continuous':True,'numerical_authority':False}
(H/'OPERATION_JOINS01.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(result))
