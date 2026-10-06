from pathlib import Path
import ast,hashlib,json,os,stat,subprocess,sys
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';O=Path(__file__).resolve().parent
T=F/'real-data-pilot-may30-ledger-relocation01-2026-10-06';A=F/'real-data-pilot-may30-ledger-relocation-retire-disposition02-2026-10-06'
evidence={}
def raw(p,pin=None):
 p=Path(p);assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_size<4*1024**2
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if pin:assert h==pin,(str(p),h,pin)
 evidence[str(p.relative_to(R))]=h;return b
def obj(p,pin=None):return json.loads(raw(p,pin))
def sig(p):
 assert p.resolve(strict=True)==p
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
e=obj(T/'copy-envelope01.json','d18a382896fe9e2b57a001e373ae173c9a5c25e25e3be7fcf58dd574fbc48d5a')
for p,h in e['source_files'].items():raw(R/p,h)
for ref in e['evidence']+[e['environment'],e['selection']]:raw(R/ref['path'],ref['sha256'])
from tradingagents.research.onchain_replication.environment import inventory
assert inventory(R)==obj(R/e['environment']['path'])
c=obj(T/'SELECTION01.json');q=obj(T/'copy-complete01.json','e7b9573bae1eec99303aee490eeb2086514c560082f860336eb52c3959576924');g=obj(T/'copy-guard01/final.json','0cfa7891775ef35484647da52113af5c4df4cc6e9287469d3e0ca93ce4720c79');r=obj(T/'copy-ROOT_TERMINAL01.json','b52a5efe2f77b5d0eb7fbdba842063b2834051b233545a84b8c59d7a041c679c');x=obj(T/'copy-outer-exit01.json');p=obj(T/'copy-preflight01.json');remote=obj(T/'REMOTE_CONFIRMATION01.json')
raw(T/'copy-RELEASE_REVIEW01.json','e52d2e7ad48ec6f6999ae0c104d6da2faa609c7c16886c7ed334c424c8e917d1')
for n in ['copy-attempt01.json','copy-launch-attempt01.json']:obj(T/n)
assert q['identity']==e['identity']==c['identity']==r['identity']==x['identity']
assert g['phase']=='complete' and g['child_exit_code']==0 and g['cleanup_verified'] is True
assert r['actual_root_tool_exit_code']==r['actual_parent_exit_code']==x['entry_selected_exit_code']==0
assert r['complete_sha256']==evidence[str((T/'copy-complete01.json').relative_to(R))] and r['guard_final_sha256']==evidence[str((T/'copy-guard01/final.json').relative_to(R))]
assert r['source_commit']==p['head']==remote['actual_commit']==remote['actual_remote_head']=='a40bad971581fc245be8322b36b50488f8795394'
assert remote['actual_push_exit_code']==remote['actual_remote_readback_exit_code']==0 and remote['matches'] is True
assert r['native_seconds']==g['elapsed_seconds'] and r['original_cleanup_stop_returncode']==g['cleanup_stop_returncode']==5 and r['lifetime_pid_history_complete'] is False
assert q['copy_readback_verified'] is q['external_byte_recovery_verified'] is q['typed_name_mode_verified'] is True
assert q['source_retired'] is q['original_retired'] is False and q['two_partial_arrays_retained'] is True
assert q['original']==c['recovery_selection']['rows'][0]['original']
observations=[]
for row in c['recovery_selection']['rows']:
 a=row['original'];v=sig(R/a['path']);assert [v[i] for i in [0,1,3,4,5]]==a['stat_identity'] and v[6]==a['mode'] and v[3]==a['bytes'];observations.append({'path':a['path'],'stat_identity7':v,'sha256_inherited':a['sha256']})
dst=Path(q['target']['path']);v=sig(dst);assert v==q['target']['stat_identity'] and {k:q['target'][k] for k in c['target']}==c['target'] and v[6]==q['original']['mode']
assert sorted(z.name for z in dst.parent.iterdir())==['ledger.sqlite']
assert v[0]==66307 and observations[0]['stat_identity7'][0]==66310
assert not Path(g['cgroup']).exists() and all(not Path('/proc',str(pid)).exists() for pid in r['actual_selected_recorded_pids'])
unit=subprocess.run(['systemctl','--user','show',g['unit'],'--property=ActiveState,SubState,MainPID,ControlGroup'],capture_output=True,text=True,check=True).stdout
props=dict(line.split('=',1) for line in unit.splitlines());assert props=={'MainPID':'0','ControlGroup':'','ActiveState':'inactive','SubState':'dead'},props
assert g['memory_max_bytes']==256*1024**2 and g['memory_high_bytes']==192*1024**2 and g['memory_swap_max_bytes']==0 and g['wall_seconds']==14400
assert g['disk_floor_bytes']==10*1024**3 and set(g['disk_paths'])=={str(R),'/home/malecada/Data'} and all(n>=g['disk_floor_bytes'] for n in g['minimum_sampled_disk_free_bytes'].values())
assert all(g['memory_events'][k]==0 for k in ['max','oom','oom_kill'])
assert not any((T/n).exists() for n in ['copy-failed01.json','retire-attempt01.json','retire-complete01.json','relocation-receipt01.json'])
# Immutable correction and exact inverse. Reuse sealed fault outputs, not their asserted conclusion.
man=obj(A/'MANIFEST01.json','7f6e13a4efe47a6383098d653f8b579252ca45f988efa8dda71ae8930eedf490')
for n,d in man['files'].items():assert len(raw(A/n,d['sha256']))==d['bytes']
inv=obj(A/'INVERSE01.json');new=raw(A/'relocate01.py').decode();back=new
for edit in reversed(inv['edits']):assert back.count(edit['after'])==1;back=back.replace(edit['after'],edit['before'],1)
assert back==raw(R/inv['baseline']).decode()
filtered=lambda s:[ast.dump(n) for n in ast.parse(s).body if not isinstance(n,ast.FunctionDef) or n.name!='retire']
assert filtered(back)==filtered(new)
put('CHECK01.json',{'decision':'pass','source_files':len(e['source_files']),'evidence_inputs':len(e['evidence']),'runtime_inventory_equal':True,'original_stat_joins':observations,'destination_stat_identity7':v,'destination_sole_leaf':True,'current_unit':props,'recorded_pids_absent':r['actual_selected_recorded_pids'],'real_payload_reads':0,'copy_native_seconds':g['elapsed_seconds'],'memory_high_events':g['memory_events']['high'],'cleanup_stop_returncode':5,'lifetime_pid_history_complete':False,'retire_inverse_edits':len(inv['edits']),'outside_retire_AST_unchanged':True})
put('EVIDENCE01.json',evidence)
print(json.dumps({'decision':'pass','real_payload_reads':0,'source_files':len(e['source_files']),'originals':3,'destination':1,'retire_inverse_edits':len(inv['edits'])}))
