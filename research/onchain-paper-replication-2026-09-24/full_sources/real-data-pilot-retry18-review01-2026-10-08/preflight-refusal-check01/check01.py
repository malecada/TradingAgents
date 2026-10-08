"""Metadata-only check of unclaimed Root entry refusal; no preflight replay."""
from pathlib import Path
import ast, datetime, hashlib, json, stat, subprocess
H=Path(__file__).resolve().parent;V=H.parent;F=V.parent;R=F.parents[2];D=F/'real-data-pilot-final18-2026-10-08'
NAME='eth-paper-real-data-end-to-end-resource-20261008-18';SOURCE='1773ca2897de86ba358e076537c8d814a788d103'
evidence={}
def raw(p):
    assert p.resolve(strict=True)==p and p.is_relative_to(F)
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<1024**2
    b=p.read_bytes();assert len(b)==s.st_size;z=p.lstat();assert (s.st_dev,s.st_ino,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_mtime_ns,z.st_ctime_ns)
    evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
refusal=read(D/'PREFLIGHT_REFUSAL01.json');release=read(V/'EXACT_LAUNCH_RELEASE01.json')
assert refusal['source']==SOURCE==subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
assert refusal['identity']==NAME and refusal['actual_entry_exit_code']==1 and refusal['actual_native_parent_exit'] is None
assert refusal['failed_check_memory_available_bytes'] is None and refusal['required_startup_bytes']==9126805504
assert refusal['error']=='ValueError: frozen startup RAM reserve unavailable'
assert refusal['root_io_capture_was_invoked'] is False
assert refusal['original_root_session']==14369 and refusal['original_terminal_chunk']=='4e0e97'
assert refusal['subsequent_observation']['memory_available_bytes']==9138245632
assert raw(D/'RELEASE_REVIEW01.json')==raw(V/'EXACT_LAUNCH_RELEASE01.json')
# Authenticate only actual entry source/release/gate at the launched commit, not417 refs.
for p in [D/'root_io.py',D/'preflight01.py',D/'RELEASE_REVIEW01.json',D/'gate01.json']:
    b=raw(p);rel=str(p.relative_to(R));committed=subprocess.check_output(['git','show',SOURCE+':'+rel],cwd=R)
    assert b==committed
    if p.name!='RELEASE_REVIEW01.json':assert evidence[rel]==release['evidence'][rel]
root=ast.parse(raw(D/'root_io.py'));main=root.body[-1]
assert isinstance(main,ast.If) and isinstance(main.body[1],ast.Assign) and ast.unparse(main.body[1].value)=='check()'
assert ast.unparse(main.body[2].value)=="launch_checked(args, preflight, Path(__file__).resolve().parent)"
preflight=raw(D/'preflight01.py').decode().splitlines()
assert preflight[247].strip()=="if available<job['resources']['start_reserve_bytes']:raise ValueError('frozen startup RAM reserve unavailable')"
assert preflight[246].strip()=="if free<startup:raise ValueError('full projected source/scratch plus disk floor unavailable')"
# Current metadata-only absence; no directory creation or native process action.
prefix=R/'research_artifacts/onchain-paper-replication-2026-09-24'
paths=[R/'research_runs'/NAME,prefix/'runs'/NAME,prefix/'sources'/NAME,prefix/'pilot-parent'/NAME,R/'research_artifacts/archive-dispatch-ethpilot-20261008-18']
paths += [D/n for n in ['launch-attempt01.json','outer-exit01.json','ROOT_IO_CLOSED01.json','ROOT_TERMINAL01.json','FINAL_STORAGE01.json','FINAL_STORAGE_UNAVAILABLE01.json']]
absent=[]
for p in paths:
    assert not p.exists() and not p.is_symlink(),str(p)
    absent.append(str(p.relative_to(R)))
representations=list((R/'research_artifacts/onchain_representations').glob('*/'+NAME));assert not representations
units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True);assert not units.strip()
# Reuse accepted budget accounting, without inspecting historical claim bodies.
budget=read(F/'real-data-pilot-seventeenth-resource-failed-review01-2026-10-08/budget89-review01/EXTENSION89_REVIEW01.json')
assert budget['decision']=='accepted'
raw(Path(__file__))
result={'schema_version':1,'decision':'accepted_unclaimed_preflight_refusal','identity':NAME,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':SOURCE,'evidence':dict(sorted(evidence.items())),
'root_receipt_original_session':14369,'root_receipt_original_terminal_chunk':'4e0e97','actual_entry_exit_code':1,'actual_native_parent_exit':None,
'failure_boundary':'Committed preflight01.py:248 raises in check(), before root_io.py main can call launch_checked or capture.','failed_check_memory_available_bytes':None,'required_startup_bytes':9126805504,
'subsequent_memory_available_bytes':9138245632,'subsequent_measurement_is_failure_sample':False,'absent_namespaces_and_lifecycle_records':absent,'representation_namespace_matches':0,'active_native_units':[],
'accounting':'No18 claim, native run or attempt namespace was created. Accepted prior accounting remains58closed33C25F/highestclaimed88 plus28pending/two closed preclaim reserves. The one unused18 allocation at effective89 is not spent by this metadata entry refusal.',
'future_eligibility':'Unused18 remains available for a later separately directed invocation only if the exact source/release and original full fresh preflight pass all current eligibility checks. This receipt does not schedule, replay or authorize a launch, relax9126805504 startup reserve, or establish durable headroom.',
'qualification':'Root original entry exit1 is distinct from a nonexistent native/guard/child exit. No ROOT_IO_CLOSED, guard cleanup, numerical FAILED disposition or spent18 is fabricated. Absence observations are current metadata facts, not writer exclusion.',
'not_tested':['Original tool-terminal bytes are not a repository artifact; original session/chunk/exit are attributed to Root PREFLIGHT_REFUSAL01, supported independently by committed code boundary and namespace absence.','No417-reference rehash, full preflight/admission replay, private/scientific body read, numerical import, future launch, or exact failure-time RAM reconstruction.']}
out=H/'PREFLIGHT_REFUSAL_REVIEW01.json'
with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':result['decision'],'path':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'absent_count':len(absent)}))
