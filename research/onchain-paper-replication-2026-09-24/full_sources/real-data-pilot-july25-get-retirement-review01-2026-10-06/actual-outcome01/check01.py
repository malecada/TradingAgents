"""Actual outcome metadata and stat review only; never opens retired/retained payloads."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,sys,types
HERE=Path(__file__).resolve().parent;REVIEW=HERE.parent;F=REVIEW.parent;ROOT=F.parents[2];D=F/'real-data-pilot-july25-get-retirement01-2026-10-06'
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));assert p.suffix not in ('.bin','.sqlite','.npy','.npz') and p.name!='connection.json','payload/private read forbidden'
 if event=='subprocess.Popen':assert args[1][:5]==['systemctl','--user','list-units','--state=active,activating','--no-legend'],'only inactivity query permitted'
 if event in ('os.remove','os.rename','os.rmdir','socket.connect'):raise AssertionError('mutation/network forbidden')
sys.addaudithook(audit)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'retire01.py')=='05512665226937ca46ab9bdaf5578de9de53e46b5778e859b885854d48ea5f8e'
assert sha(D/'complete01.json')=='4a917f95ff5a5539ce53be7210a383d1b24aa417865ec9de03478382ae303586'
assert sha(D/'ROOT_TERMINAL01.json')=='e1c1519b9dd5f6f6b0a7b04f66c33a87305e3009be85bf693417c5dfd48586ba'
assert sha(D/'RELEASE_REVIEW01.json')==sha(REVIEW/'entry01/RELEASE_REVIEW01.json')=='9c76329462b1f63ae966ba2b96f3f1c9b156bee178281b30c863868e501d806a'
assert sha(D/'selection01.json')=='6245d372684be982a283a87f6bac224d50e9161c2a4e3f55187f207a41907297'
r=types.ModuleType('exact_completed_get');r.__file__=str(D/'retire01.py');exec(compile((D/'retire01.py').read_bytes(),r.__file__,'exec'),vars(r));m,cold=r.sources()
read=lambda p:json.loads(p.read_bytes())
c=read(D/'selection01.json');complete=read(D/'complete01.json');attempt=read(D/'attempt01.json');terminal=read(D/'ROOT_TERMINAL01.json');release=read(D/'RELEASE_REVIEW01.json');before=read(REVIEW/'entry01/CHECK01.json')
for p,h in release['evidence'].items():m.metadata(ROOT,p,h)
assert attempt=={'identity':r.ID,'selection_sha256':sha(D/'selection01.json'),'no_retry':True}
get=c['recovery_selection']['rows'][0]['recovered']['path']
assert complete['identity']==terminal['identity']==r.ID
assert complete['unlink_attempted']==complete['removed']==[get] and complete['ambiguous_attempts']==[]
assert complete['get_retired'] is True and complete['payload_bytes_retired']==r.SIZE and complete['no_retry'] is True
assert complete['original_parent_status']=='failed' and complete['all_other_recoveries_retained'] is True and complete['data_retained'] is True
assert terminal['actual_root_tool_exit_code']==0 and terminal['native_child_exit_code'] is None and terminal['native_cleanup_verified'] is None
assert terminal['complete']=={'path':str((D/'complete01.json').relative_to(ROOT)),'sha256':sha(D/'complete01.json')}
assert terminal['get_absent'] is True and terminal['data_retained'] is True
assert terminal['root_session_id']==4875 and terminal['terminal_chunk']=='93cbab'
assert not os.path.lexists(D/'failed01.json') and not os.path.lexists(ROOT/get) and not os.path.lexists(ROOT/m.ORIGINAL)
assert sorted(p.name for p in D.glob('attempt*.json'))==['attempt01.json']
bridge_ref=c['relocation']['relocation_receipt'];bridge=json.loads(m.metadata(ROOT,bridge_ref['path'],bridge_ref['sha256']))
assert bridge['identity']==r.RELOCATION and complete['retained_target']==bridge['target']==before['retained_data'];r.retained(complete['retained_target']);r.inactive(m)
failed_path=ROOT/'research_runs'/m.GRAPH/'failed.json';assert sha(failed_path)==m.FAILED_SHA and read(failed_path)['status']=='failed'
assert not os.path.lexists(failed_path.with_name('complete.json'))
assert sha(D/'ROOT_BINDING_FAILURE01.json')==before['prior_binding_failure_sha256']
free={str(p):shutil.disk_usage(p).free for p in (ROOT,Path('/home/malecada/Data'))};assert all(n>=10*1024**3 for n in free.values())
observation={'decision':'PASS','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':r.ID,'exact_single_attempt':True,'complete_sha256':sha(D/'complete01.json'),'root_terminal_sha256':sha(D/'ROOT_TERMINAL01.json'),'release_sha256':sha(D/'RELEASE_REVIEW01.json'),'source_sha256':sha(D/'retire01.py'),'get_absent':True,'original_absent':True,'retained_data_current_stat':r.sig(r.TARGET.lstat()),'no_failed_receipt':True,'native_and_registered_consumers_inactive':True,'root_exit_code':0,'native_child_exit_code':None,'native_cleanup_verified':None,'logical_payload_bytes_retired':r.SIZE,'pre_entry_sampled_get_allocated_bytes':before['get_allocated_bytes'],'root_free_bytes_before':before['disk_free_bytes'][str(ROOT)],'root_terminal_free_bytes':terminal['root_free_bytes'],'root_terminal_free_delta_bytes':terminal['root_free_bytes']-before['disk_free_bytes'][str(ROOT)],'current_disk_free_bytes':free,'payload_reads':False,'qualification':'Exact accepted-source complete publication follows returned sole unlink, parent fsync, current retained Data checks and held descriptor closes. No new global descriptor or writer exclusion audit. Pre-entry st_blocks*512 is allocation associated with this file, not an isolated statvfs reclamation measurement; intervening writes/shared allocator behavior can change free space. Ordinary retirement has no native child.'}
(HERE/'CHECK01.json').write_text(json.dumps(observation,indent=2)+'\n');print(json.dumps({k:observation[k] for k in ('decision','logical_payload_bytes_retired','pre_entry_sampled_get_allocated_bytes','root_terminal_free_delta_bytes','current_disk_free_bytes')}))
