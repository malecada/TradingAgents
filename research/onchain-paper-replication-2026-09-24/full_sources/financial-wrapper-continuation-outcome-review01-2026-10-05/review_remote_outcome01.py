"""Actual returned receiver bytes and cleanup; never a network invocation."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys
H=Path(__file__).resolve().parent;F=H.parent;MAIN=F.parents[2];D=F/'financial-wrapper-continuation-refused-outcome-remote01-2026-10-05'
spec=importlib.util.spec_from_file_location('accepted_bounded_reader',F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05/verify_capture01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);Reader,R=m.Reader,m.R
rd=Reader();rr=rd.read(D/'REMOTE_RECOVERY01.json','df1b7eba17016ddb7419ea5c7cff9e65fca1de056f08cac1dfa4a1a013b6af33');r=json.loads(rr);ar=rd.read(D/'ACTUAL_ROOT_EXIT01.json','ced2cba7a6c5ce7d303c22df8dad18258b45adee2afc2288f6c29ce575605f28');a=json.loads(ar);release=json.loads(rd.read(H/'REMOTE_ENTRY_RELEASE01.json','382eba41377a65ce321c920e0696cd215514c9a07b5b9ce26bbb26fb8e7bb02a'));source=json.loads(rd.read(H/'REMOTE_SOURCE_READBACK01.json'));sr=rd.read(D/'SELECTED_BODIES01.json',release['selection_sha256']);sel=json.loads(sr)
rd.need(a['actual_root_exit_code']==0 and a['actual_root_session']==97450 and a['terminal_chunk']=='fd5b3e' and a['actual_receiver_receipt_sha256']==R.digest(rr) and a['original_financial_parent_exit_unmodified'],'actual distinct Root exit and preserved original financialParentnull')
stdout=json.loads(rd.read(D/'ROOT.stdout'));rd.need(rd.read(D/'ROOT.stderr')==b'' and all(stdout[k]==r[k] for k in stdout),'actual receiver output')
rd.need(r['remote_commit']==sel['remote_commit']==release['commit'] and r['selection_sha256']==release['selection_sha256'] and r['selected_count']==len(r['selected_blobs'])==8 and r['selected_logical_bytes']==267420 and r['expected_operations']==len(r['operations'])==34 and r['unique_selected_objects']==8 and not r['genuine_run_or_native_started'] and r['elapsed_seconds']<600,'exact actual released population/operation denominator')
rd.need([{k:row[k] for k in ('path','bytes','sha256')} for row in r['selected_blobs']]==sel['rows'],'all eight source/receipt rows')
for row in r['selected_blobs']:
 p=D/'selected'/row['path'];body=rd.read(p,row['sha256']);o=source['selection_objects'][row['path']];rd.need(len(body)==row['bytes'] and row['git_mode']==o['mode'] and row['git_object']==o['oid']==hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest() and rd.read(MAIN/row['path'],row['sha256'])==body,'actual remote/original/OID byte join')
rd.need(r['whole_tree_policy']==release['whole_tree_policy'] and r['free_bytes']>=10737418240,'actual unchanged policy/floor');pids=set()
for op in r['operations']:
 pids.add(op['pid']);rd.need(op['exit']==op['actual_reaped_exit']==0 and op['cleanup_failures']==[] and op['actual_child_limits']=={'pid':op['pid'],'fsize':[4194304,4194304]} and op['stdout_bytes']<=4194304 and op['stderr_bytes']<=65536 and op['seconds']<65,'every actual child reaped, file limit readback and bounded streams')
for obs in r['whole_tree_observations']:
 rd.need(0<=obs['logical_bytes']<=67108864 and 0<=obs['allocated_bytes']<=100663296 and 1<=obs['members']<=32768 and obs['seconds']<5 and obs['complete_attempts']<=3,'actual whole-tree finite samples')
rd.need(len(r['whole_tree_observations'])<=8192 and r['initial_owned_allocation']==r['whole_tree_observations'][0],'initial whole baseline retained')
for pid in pids:rd.need(not os.path.lexists(Path('/proc')/str(pid)),'actual recorded Git PID absent')
rc=rd.read(F/'financial-wrapper-continuation-canonical-remote01-2026-10-05/caller01.py','159d99cee4623d4d7c5ad86f5019be6f686f842725f3a12ae4359eec1df28b12');node=next(n for n in ast.parse(rc).body if isinstance(n,ast.FunctionDef) and n.name=='raw');ns={'os':os,'FILE':4194304};exec(compile(ast.Module(body=[node],type_ignores=[]),'<accepted bounded proc reader>','exec'),ns)
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:b=ns['raw'](p/'stat');rd.total+=len(b);rd.tick()
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  rd.need(int(b.decode().rsplit(')',1)[1].split()[2]) not in pids,'actual recorded Git groups absent')
profile=R.scan(D/'selected');rd.tree(D/'selected',profile);rd.need(sum(row['kind']=='file' for row in profile['members'])==8,'complete selected namespace original modes')
for n,h in [('recover01.py',release['receiver_sha256']),('watch01.py',release['watch_sha256']),('utilities/owned_io.py',release['owned_io_sha256'])]:rd.read(D/n,h)
rd.need(not os.path.lexists(D/'FAILED01.json'),'no receiver failure disposition');rd.finish();result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_EIGHT_BODY_REMOTE_BYTE_RETURN_ONLY','remote_receipt_sha256':R.digest(rr),'actual_Root_exit_sha256':R.digest(ar),'release_sha256':'382eba41377a65ce321c920e0696cd215514c9a07b5b9ce26bbb26fb8e7bb02a','commit':r['remote_commit'],'selected_count':8,'selected_bytes':267420,'actual_successful_reaped_operations':34,'recorded_Git_PIDs_and_groups_absent':sorted(pids),'actual_root_exit':0,'original_financial_Parent_exit':None,'universal_process_history':None,'physical_encrypted_wire_bytes':None,'elapsed_seconds':r['elapsed_seconds'],'selected_mode_manifest':profile,'flat_recovery':None,'no_numerical_authority':True,'checks':rd.checks,'read_bytes':rd.total};R.put(H/'REMOTE_OUTCOME_READBACK01.json',result);print(json.dumps({'decision':result['decision'],'sha256':R.digest(R.encode(result)),'checks':rd.checks}))
