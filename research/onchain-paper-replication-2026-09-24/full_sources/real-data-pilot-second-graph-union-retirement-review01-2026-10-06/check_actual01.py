"""Finite metadata/stat review. Never opens selected original/get payloads."""
import ast, copy, hashlib, json, os, stat, subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parents[3];F=H.parent;B=F.parent
OLD=B/'storage/real-pilot-second-graph-preservation-20261006-01'
NEW=B/'storage/real-pilot-second-graph-preservation-metadata-20261006-01'
PRIOR=F/'real-data-pilot-second-graph-storage-outcome-review01-2026-10-06'
RET=F/'real-data-pilot-second-graph-post-recovery-retirement02-2026-10-06'
GET=F/'real-data-pilot-first-graph-get-duplicates-retirement01-2026-10-06'
E={}
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p,pin=None):
    assert p.resolve(strict=True)==p and not p.is_symlink()
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
    b=p.read_bytes();assert ident(s)==ident(p.lstat())
    h=hashlib.sha256(b).hexdigest();assert pin is None or pin==h
    E[str(p.relative_to(M))]=h;return b
def body(p,pin=None):return json.loads(raw(p,pin))
def ref(p):return {'path':str(p.relative_to(M)),'sha256':E[str(p.relative_to(M))]}
def dump(n,v):
    p=H/n;p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');raw(p);return ref(p)
def current(p,expected,mode):
    assert p.resolve(strict=True)==p and not p.is_symlink()
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
    assert ident(s)==expected and stat.S_IMODE(s.st_mode)==mode
    return {'path':str(p.relative_to(M)),'stat_identity':ident(s),'mode':mode,'nlink':s.st_nlink}
failed=body(PRIOR/'FAILED_REVIEW02.json','7516cd31e3218d8d3ae22130db9968dc6a61175f0716fe3bf8893ae2ff69c687')
meta=body(PRIOR/'FAILED_METADATA_CHECK02.json','e15485bb7b9f18c1454689a73e8fd0f115672b3277014761df99db20fb5b98fe')
body(PRIOR/'RECOVERED_PAYLOAD_HASH02.json','f1778a7c2b5d97e75ead703daf6ce76da0df2580aa4555ea2f4eed8aca5c86ab')
assert failed['decision']=='accepted-failed-parent-partial-byte-evidence' and failed['authenticated_body_get_count']==36
sel=body(OLD/'selection01.json','96f5605613d4d9c537d4d130917d3af04f9a8005cc385b5a0576c60cf673c43a')
cbytes=raw(NEW/'complete.json');assert cbytes==raw(NEW/'recovered-complete.json')==raw(NEW/'completion-candidate.json')
c=json.loads(cbytes)
assert c['identity']==NEW.name and c['parent']==OLD.name and c['parent_status']=='FAILED'
assert c['count']==len(c['files'])==len(meta['rows'])==36 and c['bytes_preserved']==sel['total_bytes']==4204068745
assert c['fresh_body_transfers']==0 and c['fresh_restoration_metadata_rows']==[35]
assert c['directories']==sel['directories'] and c['originals_retained'] is True and c['recoveries_retained'] is True
for k,r in c['parent_proof'].items():raw(M/r['path'],r['sha256'])
assert c['parent_proof']['review']==ref(PRIOR/'FAILED_REVIEW02.json')
observed=[]
for i,(r,h,u) in enumerate(zip(sel['files'],meta['rows'],c['files'])):
    assert i==h['index'] and r['path']==h['original_path'] and r['bytes']==h['bytes'] and r['sha256']==h['sha256']
    assert all(u[k]==v for k,v in r.items()) and h['body_get_complete'] is True
    observed.append(current(M/h['original_path'],h['original_stat_identity'],h['original_mode']))
    observed.append(current(M/h['recovered_path'],h['recovered_stat_identity'],h['recovered_mode']))
    if i<35:
        p=OLD/f'{i:02d}-kept.json';kept=body(p,meta['evidence'][str(p.relative_to(M))]);assert u==kept
        restore=raw(OLD/f'{i:02d}-restore.json',meta['evidence'][str((OLD/f'{i:02d}-restore.json').relative_to(M))])
        assert restore==raw(OLD/f'{i:02d}-recovered-restore.json',meta['evidence'][str((OLD/f'{i:02d}-recovered-restore.json').relative_to(M))])
    else:
        assert u==body(NEW/'35-kept.json')==body(NEW/'35-verified.json')==body(NEW/'35-restore.json')
        assert raw(NEW/'35-restore.json')==raw(NEW/'35-recovered-restore.json')
        assert u['remote_object'].endswith(OLD.name+'/35.bin') and u['remote_restore'].endswith(NEW.name+'/35-restore.json')
        assert u['body_recovery_origin']=='reviewed-parent-failed-historical-full-get'
        assert u['parent_body_proof']['sha256']==ref(PRIOR/'FAILED_METADATA_CHECK02.json')['sha256']
for d in c['directories']:
    p=M/d['path'];s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==d['mode']
oldf=body(OLD/'guard01/final.json',failed['evidence'][str((OLD/'guard01/final.json').relative_to(M))]);oldo=body(OLD/'outer-exit01.json');oldr=body(OLD/'ROOT_TERMINAL01.json')
assert oldf['phase']=='failed' and oldf['child_exit_code'] is None and oldf['cleanup_verified'] is True
assert oldo['entry_selected_exit_code']==1 and oldo['guard_child_exit_code'] is None
assert oldr['actual_root_tool_exit_code']==1 and oldr['separate_actual_worker_exit_code']==-15
for n in ['complete.json','failed.json','35-kept.json','35-verified.json','35-recovered-restore.json','recovered-complete.json']:
    assert not os.path.lexists(OLD/n)
nf=body(NEW/'guard01/final.json');no=body(NEW/'outer-exit01.json');nr=body(NEW/'ROOT_TERMINAL01.json');nc=body(NEW/'guard01/child_exit.json')
assert nf['phase']=='complete' and nf['child_exit_code']==0 and nf['cleanup_verified'] is True
assert no['entry_selected_exit_code']==0 and no['guard_child_exit_code']==0 and no['cleanup_verified'] is True
assert nr['actual_root_tool_exit_code']==0 and nc['exit_code']==0 and not os.path.lexists(NEW/'failed.json')
assert nr['identity']==NEW.name and nr['source_commit']=='dc46180f8494a2f7dea88e87791350d0d172504a'
pids=set(nr['selected_recorded_pids'])|{nc['workload_pid'],nf['monitor_pid'],oldf['monitor_pid']}
receipts=[]
for name in ['35-recovered-restore.json','recovered-complete.json']:
    t=body(NEW/(name+'.transport.json'));size=(NEW/name).stat().st_size
    assert t['status']=='complete' and t['returncode']==0 and t['error_type'] is None
    assert t['expected_bytes']==t['received_bytes']==size
    pids.add(t['pid']);receipts.append({'name':name,'bytes':size,'receipt':ref(NEW/(name+'.transport.json'))})
for pid in pids:assert not Path('/proc',str(pid)).exists()
for f in [oldf,nf]:assert not Path(f['cgroup']).exists()
unit=subprocess.run(['systemctl','--user','show',nf['unit'],'--property=MainPID,ActiveState,SubState,ControlGroup,Result'],text=True,capture_output=True)
assert unit.returncode==0
props=dict(line.split('=',1) for line in unit.stdout.splitlines() if '=' in line)
assert props['MainPID']=='0' and props['ActiveState']=='inactive' and props['SubState']=='dead' and props['ControlGroup']==''
active=subprocess.run(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True,capture_output=True)
assert active.returncode==0 and not active.stdout.strip()
# Ordinary source/receipt pins only. Never dereference the connection ref or runtime inventory.
env=body(NEW/'envelope01.json');rel=body(NEW/'RELEASE_REVIEW01.json')
assert rel['decision']=='accepted' and rel['envelope_sha256']==ref(NEW/'envelope01.json')['sha256']
for p,pin in env['source_files'].items():raw(M/p,pin)
raw(M/env['selection']['path'],env['selection']['sha256'])
body(NEW/'35-attempted.json');body(NEW/'launch-attempt01.json');body(NEW/'intent.json');body(NEW/'preflight01.json')
entry=RET/'retire02.py';raw(entry,'61320cbea932dca635837c156f22e6a007d1d8f8bea857cd9884fb47d26888d8')
raw(H/'SOURCE_CHECK01.json');raw(M/'research/onchain-paper-replication-2026-09-24/storage/cold-offload-2026-09-29-03/offload.py','0d507711644d962e494e659987ba0a6d479304af7092ba15315630d0b68e1a84')
raw(F/'real-data-pilot-incremental-graph-retention02-2026-10-05/select01.py','d9d63840c8f4510ac4e1b784ab31762d91f74c4de8d2258bdd7011823f921205')
for n in ['attempt01.json','complete01.json','failed01.json']:assert not os.path.lexists(RET/n)
q='Historical 36 full body gets plus newly completed restoration metadata/union full gets; current local identities/modes match the independently hashed bodies. No second payload hash, atomic writer exclusion, POSIX reconstruction, runtime reconstruction, current remote availability of inherited bodies, scientific completion or financial credit is inferred. Complete PID lifetime history remains unknown.'
detail={'decision':'accepted-actual-metadata-union','identity':NEW.name,'original_and_get_stat_observations':observed,'directory_descriptors':c['directories'],'fresh_metadata_gets':receipts,'old_parent_status':'FAILED','old_guard_child_exit_code':None,'old_worker_exit_code':-15,'old_root_exit_code':1,'new_root_exit_code':0,'new_guard_child_exit_code':0,'cleanup_verified':True,'known_recorded_pids_absent':sorted(pids),'unit_readback':unit.stdout,'active_native_units':active.stdout,'new_elapsed_seconds':nf['elapsed_seconds'],'last_unit_kernel_peak_bytes':nf['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'ancestor_peak_bytes':nf['optional_memory_telemetry']['user_ancestor']['kernel_peak_bytes'],'payload_read_bytes':0,'qualification':q}
detailref=dump('ACTUAL_UNION_CHECK01.json',detail)
outcome={'decision':'accepted','identity':NEW.name,'full_scope_byte_recovery':True,'body_count':36,'body_bytes':4204068745,'directory_count':8,'old_parent_status':'FAILED','actual_root_exit':0,'fresh_body_transfers':0,'fresh_metadata_get_count':2,'actual_check':detailref,'qualification':q,'evidence':dict(E)}
outref=dump('UNION_OUTCOME_REVIEW01.json',outcome)
retirement={'decision':'accepted','retirement_identity':'real-pilot-second-graph-ledger-retirement-20261006-01','entry_sha256':ref(entry)['sha256'],'entry_path':str(entry.relative_to(M)),'full_scope_byte_recovery':True,'retire_only_second_graph_ledger_and_successful_get':True,'union_outcome_review':outref,'payload_bytes_retired_if_successful':2*sel['files'][11]['bytes'],'evidence':dict(E),'qualification':'One-use ordinary retirement of the selected original May9 ledger and its historical successful get only; all arrays/other bodies retained. Entry must revalidate current source/evidence/stat/hash/consumer/native/locks and preserve partial failure. No numerical authority.'}
# Run only the compact actual gate from the installed source, never execute().
fun=next(n for n in ast.parse(entry.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
start=next(i for i,n in enumerate(fun.body) if isinstance(n,ast.FunctionDef) and n.name=='reviewed')
end=next(i for i,n in enumerate(fun.body) if i>start and isinstance(n,ast.If) and 'subprocess.check_output' in ast.unparse(n.test))
fn=ast.FunctionDef(name='actual_gate',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(fun.body[start:end]),decorator_list=[])
scope={'Path':Path,'hashlib':hashlib,'json':json,'ROOT':M,'BACKUP':OLD,'UNION':NEW,'UNION_ID':NEW.name,'review':retirement}
exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'exact-actual-metadata-gate','exec'),scope);scope['actual_gate']()
dump('RETIREMENT_RELEASE01.json',retirement)
# Separate first-five-get selection: hash-authenticated old full proof, stat-only currentness.
gs=body(GET/'selection01.json','e7dbfca702b36af25e60521b9de9ab3d83af7109436f3db74e5e6754b78d1a28')
draft=body(F/'real-data-pilot-first-graph-get-duplicates-retirement-preparation01-2026-10-06/SELECTION_DRAFT01.json')
assert {**draft,'status':'FROZEN_FOR_REVIEW'}==gs and gs['count']==5 and gs['retire_bytes']==509060512
getsource=raw(GET/'retire01.py','0ea52ac0db5f8f6fe726cd4298b6c4d79651380ccd98d673bacfc7a3c3cd32a6')
GE={}
for p,pin in gs['evidence'].items():raw(M/p,pin);GE[p]=pin
for r in gs['rows']:
    for k in ['original','recovered']:
        item=r[k];current(M/item['path'],item['stat_identity'],item['mode'])
assert [r['index'] for r in gs['rows']]==[21,22,23,25,26]
assert sum(r['recovered']['bytes'] for r in gs['rows'])==509060512
for n in ['attempt01.json','complete01.json','failed01.json']:assert not os.path.lexists(GET/n)
for p in gs['removed_ledger_paths']:assert not os.path.lexists(M/p)
# Invoke only source-defined read-only selection/inactivity predicates, not execute().
space={'__file__':str(GET/'retire01.py'),'__name__':'independent_metadata_selection_check'}
exec(compile(getsource,str(GET/'retire01.py'),'exec'),space)
space['inactive']();space['selected'](M,gs)
first=B/'storage/real-pilot-first-graph-preservation-20261006-01'
ff=body(first/'guard01/final.json');fo=body(first/'outer-exit01.json')
assert ff['phase']=='complete' and ff['child_exit_code']==0 and ff['cleanup_verified'] is True and fo['entry_selected_exit_code']==0
assert not Path(ff['cgroup']).exists() and not Path('/proc',str(ff['monitor_pid'])).exists()
for p in [GET/'selection01.json',GET/'retire01.py',H/'ACTUAL_UNION_CHECK01.json']:GE[str(p.relative_to(M))]=E[str(p.relative_to(M))]
gdetail=dump('FIRST_GET_CHECK01.json',{'decision':'accepted-exact-selection-current-stats','selection':ref(GET/'selection01.json'),'get_count':5,'bytes':509060512,'original_arrays_retained':True,'payload_read_bytes':0,'historical_recovery_basis':gs['evidence'],'qualification':'Existing full-byte proof plus all ten exact current stat/mode identities; no fresh remote body observation or writer exclusion.'})
GE[gdetail['path']]=gdetail['sha256']
dump('FIRST_GET_RETIREMENT_RELEASE01.json',{'decision':'accepted','retirement_identity':gs['identity'],'entry_sha256':ref(GET/'retire01.py')['sha256'],'retire_only_five_verified_array_get_duplicates':True,'selection':ref(GET/'selection01.json'),'evidence':GE,'retire_bytes':509060512,'qualification':'Separate one-use exact five successful May2 get duplicates only. Original arrays and every other recovery remain. Genuine entry must repeat current/active consumer/lock predicates; no numerical authority.'})
print(json.dumps({'actual_union':outref,'retirement_release':ref(H/'RETIREMENT_RELEASE01.json'),'first_get_release':ref(H/'FIRST_GET_RETIREMENT_RELEASE01.json'),'payload_read_bytes':0},sort_keys=True))
