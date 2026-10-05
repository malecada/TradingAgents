from pathlib import Path
import json,hashlib,stat,sys
M=Path.cwd();F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;H=lambda b:hashlib.sha256(b).hexdigest();j=lambda p:json.loads(p.read_bytes());ref=lambda p:{'path':str(p),'sha256':H(p.read_bytes())}
lane=int(sys.argv[1]);session=int(sys.argv[2]);chunk=sys.argv[3];assert lane in (1,2,3)
e=j(D/'REMOTE_LANES_ENTRY_RELEASE01.json');entry=e['entries'][lane-1];R=Path(entry['owned_root']);r=j(R/'REMOTE_RECOVERY01.json');root=j(R/'ACTUAL_ROOT_EXIT01.json');s=j(R/'SELECTED_BODIES01.json');assert root['actual_root_exit']==0 and root['session']==session and root['final_chunk']==chunk and root['entry_sha256']==ref(D/'REMOTE_LANES_ENTRY_RELEASE01.json')['sha256']
assert s['remote_commit']==r['remote_commit']==e['commit'] and ref(R/'SELECTED_BODIES01.json')['sha256']==r['selection_sha256']==entry['selection_sha256'];assert r['selected_count']==len(r['selected_blobs'])==entry['count'] and r['selected_logical_bytes']==entry['bytes'] and r['unique_selected_objects']==entry['count']
wanted={v['path']:v for v in s['rows']}
for v in r['selected_blobs']:
 p=R/'selected'/v['path'];b=p.read_bytes();assert H(b)==v['sha256']==wanted[v['path']]['sha256'] and len(b)==v['bytes']==wanted[v['path']]['bytes'];assert v['git_mode']=='100644' and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==v['git_object'];assert stat.S_ISREG(p.lstat().st_mode) and p.stat().st_nlink==1
assert {str(p.relative_to(R/'selected')) for p in (R/'selected').rglob('*') if p.is_file()}==set(wanted)
ops=r['operations'];count=entry['count'];assert len(ops)==r['expected_operations']==entry['expected_operations'] and [o['operation'] for o in ops]==['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree']+['fetch']*count+['cat-file']*(2*count)+['ls-remote']
for o in ops:assert o['exit']==o['actual_reaped_exit']==0 and o['cleanup_failures']==[] and o['actual_child_limits']=={'pid':o['pid'],'fsize':[4194304,4194304]} and o['seconds']<60 and o['stdout_bytes']<=4194304 and o['stderr_bytes']<=65536
head=(r['remote_commit']+'\t'+r['branch']+'\n').encode()
for o in (ops[1],ops[-1]):assert o['stdout_sha256']==H(head) and o['stdout_bytes']==len(head)
assert r['elapsed_seconds']<600 and r['free_bytes']>=10737418240 and r['genuine_run_or_native_started'] is False
for v in r['whole_tree_observations']:assert v['logical_bytes']<=67108864 and v['allocated_bytes']<=100663296 and v['members']<=32768 and v['seconds']<5 and 1<=v['complete_attempts']<=3
logical=allocated=members=0
for p in [R]+list(R.rglob('*')):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode);allocated+=st.st_blocks*512
 if p!=R:members+=1
 if stat.S_ISREG(st.st_mode):logical+=st.st_size;assert st.st_nlink==1 and st.st_size<=4194304
assert logical<67108864 and allocated<100663296 and members<32768
x={'schema_version':1,'decision':'accepted-actual-single-outcome-receiver-lane','lane':lane,'receipt':ref(R/'REMOTE_RECOVERY01.json'),'actual_root_exit':ref(R/'ACTUAL_ROOT_EXIT01.json'),'selection':ref(R/'SELECTED_BODIES01.json'),'commit':r['remote_commit'],'selected_count':count,'selected_bytes':entry['bytes'],'actual_operations':len(ops),'all_selected_SHA_size_OID_mode_membership_joins':True,'all_exits_reaped_zero':True,'cleanup_failures':[],'head_readbacks_exact':True,'actual_child_file_limit':4194304,'current_whole_tree':{'logical_bytes':logical,'allocated_bytes':allocated,'members':members},'full_outcome_recovery':False,'numerical_authority':False};p=D/f'REMOTE_LANE{lane:02d}_CHECK01.json';assert not p.exists();p.write_text(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n');p.chmod(0o444);print(ref(p))
