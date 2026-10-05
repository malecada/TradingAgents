from pathlib import Path
import hashlib,importlib.util,json,os,stat,time
O=Path(__file__).resolve().parent;F=O.parent;D=F/'financial-wrapper-compatibility-complete100-outcome-capture-preparation03-2026-10-05';H=lambda b:hashlib.sha256(b).hexdigest();raw=(D/'MANIFEST01.json').read_bytes();assert H(raw)=='cc45dd81c5ffca746ea32983ea4325ae0c5ae9c8322c9c017169a2ca2381e44c';manifest=json.loads(raw)
for row in manifest['members']:
 p=D/row['path'];s=p.lstat();assert p.resolve()==p and stat.S_IMODE(s.st_mode)==row['mode']
 if row['kind']=='file':assert stat.S_ISREG(s.st_mode)and s.st_nlink==1 and s.st_size==row['bytes'] and H(p.read_bytes())==row['sha256']
 else:assert stat.S_ISDIR(s.st_mode)
assert {p.relative_to(D).as_posix()for p in D.rglob('*')}=={r['path']for r in manifest['members']}|{'MANIFEST01.json'}
spec=importlib.util.spec_from_file_location('actual_capture03',D/'capture01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);R=M.R;start=time.monotonic();pins={}
for name,pin in {'capture01.py':'d8b61b8bc45e69da0df50bfa4694c0c0d103aaa5dce6668fccd0686c275958bb','utilities/owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','utilities/recovery_pax01.py':'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2','utilities/bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}.items():M.pinned_read(D,name,pins,pin)
assert Path(R.__file__).resolve()==D/'utilities/recovery_pax01.py' and Path(R._cleanup.__code__.co_filename).resolve()==D/'utilities/owned_io.py' and Path(R.git.__code__.co_filename).resolve()==D/'utilities/bounded_git01.py'
qp=F/'heartbeat-root-checkpoint10-2026-10-04/COMPATIBLE100_CAPTURE_REQUEST01.json';qhash='c1d0c90db757e80e4dbcb66491575435f21022445344f98ec6bb02103c7642d7';q=json.loads(M.ref_read({'path':str(qp),'sha256':qhash},pins));evidence={}
for role,ref in q['evidence'].items():evidence[role]=json.loads(M.ref_read(ref,pins))
parent=json.loads(M.ref_read(q['parent_request'],pins));assert q['roots']=={'capsule':str(M.CAP),'parent':str(M.PARENT)} and q['identity']==M.IDENTITY and q['source']==M.SOURCE
assert evidence['terminal']['actual_parent_exit'] is None and evidence['terminal']['actual_child_exit']==0 and evidence['root_exit']['actual_root_exit']==0
assert evidence['independent_disposition']['decision']=='ACCEPTED_ACTUAL_SYNTHETIC_ENGINEERING_COMPLETE100' and evidence['independent_disposition']['cleanup_proof_sha256']==q['evidence']['cleanup']['sha256']
cleanup=evidence['cleanup'];assert cleanup['native_pid_history_complete'] is False;assert len(q['owned_pids'])==7 and set(q['owned_pids'])==set(map(int,cleanup['owned_pid_start_records']))|{1199600,1199602,1199603};assert q['cgroup_paths']==[cleanup['cgroup']]
assert all(not Path('/proc',str(pid)).exists()for pid in q['owned_pids']) and all(not os.path.lexists(cg)for cg in q['cgroup_paths'])
assert 'only recorded owned PIDs' in q['process_scope_qualification'] and 'native_pid_history_complete=false' in q['process_scope_qualification']
for n,h in parent['source_files'].items():M.pinned_read(M.CAP,n,pins,h)
head=M.pinned_read(M.CAP,'.git/HEAD',pins).decode().strip()
if head.startswith('ref: '):head=M.pinned_read(M.CAP,'.git/'+R.path_name(head[5:]),pins).decode().strip()
assert head==M.SOURCE
scopes={role:M.inventory(Path(path),role=='capsule')for role,path in q['roots'].items()}
for role,path in q['roots'].items():
 current=M.signatures(Path(path),scopes[role]);assert all(k not in pins or pins[k]==v for k,v in current.items());pins.update(current)
groups=M.plan(scopes);rawbytes=sum(x['bytes']for g in groups for x in g);members=sum(len(m['members'])for m in scopes.values());assert members<=M.MEMBERS
output=F/'financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05';assert not os.path.lexists(output)
M.boundary(start,M.RAW*2);M.unchanged(pins)
result={'source_sha256':H((D/'capture01.py').read_bytes()),'author_manifest_sha256':H(raw),'request_sha256':qhash,'source_files':len(parent['source_files']),'actual_scopes':{k:{'typed_members':len(v['members']),'regular_files':sum(r['kind']=='file'for r in v['members']),'logical_bytes':sum(r.get('bytes',0)for r in v['members'])}for k,v in scopes.items()},'raw_bytes':rawbytes,'planned_pieces':len(groups),'max_piece_raw_bytes':max(sum(r['bytes']for r in g)for g in groups),'max_body_bytes':max(r['bytes']for g in groups for r in g),'combined_members':members,'free_output_path':str(output),'recorded_owned_pids_absent':q['owned_pids'],'authenticated_cgroup_paths_absent':q['cgroup_paths'],'native_pid_history_complete':False,'disk_reserve_checked':M.RAW*2,'deadline_seconds':120,'elapsed_seconds':time.monotonic()-start,'actual_capture_executed':False,'numerical_authority':False}
(O/'ENTRY_CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
release={'schema_version':1,'decision':'ACCEPTED_EXACT_TERMINAL_OUTCOME_BYTE_CAPTURE','request_sha256':qhash,'source_sha256':result['source_sha256'],'evidence':q['evidence'],'terminal_and_root_exit_authenticated':True,'all_owned_processes_and_cgroup_absent':True,'independent_disposition_authenticated':True,'numerical_authority':False}
(O/'CAPTURE_ENTRY_RELEASE01.json').write_bytes(R.encode(release));print(json.dumps(result,sort_keys=True));print('RELEASE_SHA256',H((O/'CAPTURE_ENTRY_RELEASE01.json').read_bytes()))
