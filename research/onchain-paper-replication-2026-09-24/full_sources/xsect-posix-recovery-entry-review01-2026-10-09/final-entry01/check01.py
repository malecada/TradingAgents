import hashlib,json,os,resource,time
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[4];F=P.parent.parent;A=F/'xsect-posix-recovery-entry01-2026-10-09';B=F/'real-data-pilot-xsect-preservation03-2026-10-08'
os.nice(10);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(50,50));began=time.monotonic();evidence={}
def pin(p):
 raw=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return raw
def load(p):return json.loads(pin(p))
c=load(A/'CONTRACT_FINAL01.json');source=pin(A/'restore.py');assert hashlib.sha256(source).hexdigest()=='f3b1f132a9474c8e3f5df7eb30e885b465bd75e65930a063bfbd634d0da49dad';assert hashlib.sha256(pin(A/'bind.py')).hexdigest()=='48ab44cdbc4dce983c8fc7112cd6cf14578f4cd4056863b577a6249da1ba815b'
ns={'__file__':str(A/'restore.py'),'__name__':'read_only_final_review'};exec(compile(source,str(A/'restore.py'),'exec'),ns)
for ref in c['source_refs'].values():assert len(pin(R/ref['path']))==ref['bytes'] and evidence[ref['path']]==ref['sha256']
for key in ['backup_contract_ref','backup_complete_ref','backup_terminal_ref','native_terminal_ref','native_final_ref','legacy_transport_ref','owned_transport_ref','recovery_ref']:
 ref=c[key];assert len(pin(R/ref['path']))==ref['bytes'] and evidence[ref['path']]==ref['sha256']
rows,dirs,selection=ns['validate_selection'](c);assert len(rows)==3783 and len(dirs)==14 and len(selection)==29 and sum(x['bytes'] for x in rows)==6915716585
for selected in c['selection']:
 for key in ['receipt_ref','manifest_ref']:pin(R/selected[key]['path'])
bc=load(R/c['backup_contract_ref']['path']);selected=[B/name for name in bc['root_metadata_files']]+[R/ref['path'] for ref in bc['input_refs'].values()]+[R/bc['owned_transport_path']];assert len(selected)==8
for original in selected:
 assert pin(original)==pin(B/'returned-metadata'/original.name),original
receipts=list(B.glob('transport-run-*.json'))+list((B/'returned-metadata').glob('*.transport.json'))+list((B/'batches').glob('batch-*/*.transport.json'));assert len(receipts)==221
for path in receipts:
 q=load(path);assert q['status']=='complete' and q['error_type'] is None and q['returncode']==0
 cl=q['owned_cleanup'];assert cl['direct_child_reaped'] is True and cl['owned_group_absent'] is True
 assert len(q['stderr_tail'].encode())<=16384 and q['elapsed_seconds']<=1810
 if q['expected_bytes'] is not None:assert q['received_bytes']==q['expected_bytes']
 else:assert q['stdout_bytes']==q['received_bytes']<=65536
 assert not Path('/proc',str(q['pid'])).exists()
 try:os.killpg(q['pid'],0)
 except ProcessLookupError:pass
 else:raise AssertionError('original transport group remains')
 for child in cl['adopted_children_reaped']:assert not Path('/proc',str(child['pid'])).exists()
for batch,receipt,manifest in selection:
 base=B/'batches'/f"batch-{batch['index']:04d}";cl=load(base/'cleanup.json');assert cl=={'bundle.tar':'removed verified temporary copy','recovered.tar':'removed verified temporary copy'};assert not (base/'bundle.tar').exists() and not (base/'recovered.tar').exists()
terminal=load(R/c['backup_terminal_ref']['path']);assert terminal['actual_root_exit_code']==0 and terminal['session_id']==37092 and terminal['tool_chunk_id']=='3dc30f' and terminal['actual_transport_receipts']==221 and terminal['complete_sha256']==c['backup_complete_ref']['sha256'];assert terminal['original_driver_pid']==c['backup_driver_pid'] and terminal['original_driver_absent'] and terminal['original_owned_groups_absent']
native=load(R/c['native_terminal_ref']['path']);assert native['session_id']==83120 and native['actual_root_exit_code']==1 and native['registered_planned_stop'] is True
io=load(F/'real-data-pilot-final22-2026-10-08/ROOT_IO_CLOSED01.json');assert io==native['original_root_io_closed'] and io['supervisor_reaped'] and io['outer_log_handles_closed'] and io['actual_parent_exit_code']==1
# Existing actual read-only eligibility: genuine closure refs, /proc/cgroup absence,
# same device/4096 block, disk floor and host-memory checks. No launch/imported graphs.
observed=ns['eligibility'](c,c['restore_allocation_bound_bytes']);assert observed['required_free_bytes']==17998811136
assert c['status']=='READY' and c['identity']=='xsect-posix-recovery-20261009-01' and c['deletion_authorized'] is False
assert not Path(c['target_root']).exists() and not Path(c['target_root']).is_symlink()
for name in ['INTENT01.json','downloads','ROOT_PIN01.json','COMPLETE01.json','FAILED01.json']:assert not (A/name).exists() and not (A/name).is_symlink()
prior=load(P.parent/'SOURCE_REVIEW02.json');assert prior['decision']=='accepted_source_only' and prior['restore_sha256']==hashlib.sha256(source).hexdigest()
result={'status':'PASS_ACTUAL_FINAL_INPUT_REVIEW','files':len(rows),'directories':len(dirs),'batches':len(selection),'returned_root_metadata':len(selected),'bounded_transport_receipts':len(receipts),'actual_eligibility':observed,'native_terminal_exit':1,'backup_terminal_exit':0,'target_and_intent_unused':True,'actual_affinity':sorted(os.sched_getaffinity(0)),'elapsed_seconds':time.monotonic()-began,'qualification':'Actual metadata/hash/closure/headroom review only. No external fetch, original raw body, real reconstruction or scientific claim.'};(P/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n')
release={'decision':'accepted','identity':c['identity'],'contract_sha256':hashlib.sha256((A/'CONTRACT_FINAL01.json').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source).hexdigest(),'evidence':dict(sorted(evidence.items())),'qualifications':['Exact final contract and source only; Root must copy release unchanged and rerun actual entry eligibility.','All29 original backup metadata/receipt joins and8 returned root bodies checked;221 original bounded transport receipts show actual cleanup and original processes/groups now absent.','Native22 FAILED planned1024 remains spent; no scientific completion implied.','No original raw bodies or network accessed in this review; no real restore executed; no writer exclusion or deletion authority.','Root owns remaining prerequisite preservation and actual restore launch.']};(P/'RELEASE01.json').write_text(json.dumps(release,sort_keys=True,indent=2)+'\n');print(json.dumps(result));print('release_sha256',hashlib.sha256((P/'RELEASE01.json').read_bytes()).hexdigest())
