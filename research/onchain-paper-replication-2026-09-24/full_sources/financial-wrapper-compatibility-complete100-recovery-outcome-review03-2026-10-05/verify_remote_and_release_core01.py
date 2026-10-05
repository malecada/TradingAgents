"""Actual four receiver outcomes and exact dependent flat cores; no recovery entry."""
from pathlib import Path
import sys,os,json,stat,ast,hashlib,importlib.util,math
HERE=Path(__file__).resolve().parent;F=HERE.parent;REVIEW1=F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05';REVIEW2=F/'financial-wrapper-compatibility-complete100-recovery-outcome-review02-2026-10-05';sys.path[:0]=[str(REVIEW1),str(REVIEW2)];from verify_capture01 import Reader,R,C,MAIN,D
from verify_failure_bundle01 import verify_inline
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation04-2026-10-05';sys.path[:0]=[str(P),str(P/'utilities')];spec=importlib.util.spec_from_file_location('review_outcome04',P/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
rd=Reader();entry=json.loads(rd.read(REVIEW2/'REMOTE_ENTRY_CHECKS01.json'));summary_raw=rd.read(C/'CANONICAL02_FOUR_REMOTE_ACTUAL_EXITS01.json');summary=json.loads(summary_raw);draft_raw=rd.read(C/'CANONICAL02_FOUR_FLAT_ACTUAL_DRAFT01.json');drafts=json.loads(draft_raw);capture=O.context(rd.read(D/'CAPTURE01.json',O.CAPTURE));results=[];releases=[];pids=set();groups=set();inline_verified=False
rd.need(len(summary['lanes'])==len(drafts['lanes'])==4 and summary['all_actual_root_exit_zero'] is True,'all four genuine actual endpoints')
for i,(basis,record,draft) in enumerate(zip(entry['lanes'],summary['lanes'],drafts['lanes'])):
 root=O.lane_root(i,'remote');flat=O.lane_root(i,'flat');selected=root/'selected';prefix='ROOT_OUTCOME_LANE%02d_CANONICAL02_REMOTE02'%(i+1)
 rd.need(basis['root']==record['root']==str(root) and draft['root']==str(flat) and record['lane']==draft['lane']==i,'fixed actual distinct scopes')
 qraw=rd.read(Path(draft['request_path']),draft['draft_request_sha256']);q=json.loads(qraw);core=O.request_core_sha256(q);rd.need(core==draft['request_core_sha256'] and q['release'] is None,'actual unsigned flat core')
 original_q=json.loads(rd.read(root/'ROOT_REQUEST01.json',basis['request_sha256']));rd.need({k:v for k,v in q.items() if k not in ('remote','profile')}=={k:v for k,v in original_q.items() if k not in ('remote','profile')},'flat fills only actual remote/profile refs')
 required=O.selected_required(q,i,capture);sr=rd.read(root/'SELECTED_BODIES01.json',basis['selection_sha256']);selection=json.loads(sr);rd.need(sr==O.selection_encode(selection),'actual remote exact canonical selector')
 rr=rd.read(root/'REMOTE_RECOVERY01.json',record['receipt_sha256']);remote=json.loads(rr);rp=Path(MAIN/q['remote']['path']);rd.need(rp==root/'REMOTE_RECOVERY01.json' and q['remote']['sha256']==draft['remote_receipt_sha256']==record['receipt_sha256'] and q['remote']['bytes']==len(rr),'exact real remote reference')
 rs=importlib.util.spec_from_file_location('actual_receipt_lane%d'%i,root/'receipt01.py');RM=importlib.util.module_from_spec(rs);rs.loader.exec_module(RM);rd.read(root/'receipt01.py',basis['helpers']['receipt01.py']);records=RM.validate_remote(remote,selection,R.digest(sr),required)
 rd.need(remote['fresh_git_root']==str(root/('fresh-compatibility-complete100-outcome-lane%02d-canonical02.git'%(i+1))) and remote['expected_operations']==basis['expected_git_operations'] and record['operations']==len(remote['operations']),'actual operation denominator and fresh Git root')
 er=rd.read(root/'ACTUAL_ROOT_EXIT01.json',record['root_exit_sha256']);actual=json.loads(er);outerraw=rd.read(root/(prefix+'_EXIT.json'),actual['inner_exit_sha256']);outer=json.loads(outerraw)
 rd.need(actual['actual_root_exit']==0 and actual['original_inner_actual_parent_exit'] is None and actual['lane']==i and actual['receipt_sha256']==R.digest(rr) and actual['receipt_file']==str(root/'REMOTE_RECOVERY01.json') and actual['inner_exit_file']==str(root/(prefix+'_EXIT.json')),'separate actual Root exit0 and unchanged null')
 rd.need(outer['child_exit']==0 and outer['actual_parent_exit'] is None and outer['parent_failure_type'] is None and outer['cleanup_failures']==[] and outer['parent_fsize_readback']==[R.FILE,R.FILE] and outer['numerical_authority'] is False and 0<=outer['elapsed_seconds']<630,'actual clean bounded caller terminal')
 rd.need(not os.path.lexists(root/'FAILED01.json') and rd.read(root/(prefix+'.stderr'))==b'','no failed receipt and no child stderr')
 rd.read(root/(prefix+'.stdout'));spawn=json.loads(rd.read(root/(prefix+'_SPAWN.json')));intent=json.loads(rd.read(root/(prefix+'_INTENT.json')));rd.need(intent['contract_sha256']==basis['contract_sha256'] and spawn['argv']==intent['argv'] and intent['claim_started'] is False,'actual attempted caller/source binding');pids.update((spawn['pid'],intent['parent_pid']));groups.add(spawn['pid'])
 for op in remote['operations']:pids.add(op['pid']);groups.add(op['pid'])
 for sample in outer['observations']:
  rd.need(type(sample['logical_bytes'])is int and 0<=sample['logical_bytes']<=64*1024**2 and type(sample['allocated_bytes'])is int and 0<=sample['allocated_bytes']<=96*1024**2 and 1<=sample['members']<=32768 and 0<=sample['seconds']<5 and 1<=sample['complete_attempts']<=3,'actual finite outer census record')
 profraw=rd.read(MAIN/q['profile']['path'],q['profile']['sha256']);profile=json.loads(profraw);rd.need(q['profile']['sha256']==draft['profile_sha256'] and q['profile']['bytes']==len(profraw) and profile['actual_selected_root']==str(selected),'actual profile exact body/root');m=profile['full_manifest'];R.validate(m);rd.tree(selected,m);files={r['path']:r for r in m['members'] if r['kind']=='file'};rd.need(set(files)==set(required),'complete actual selected membership')
 for row in records:
  raw=rd.read(selected/row['path'],row['sha256']);rd.need(len(raw)==row['bytes'] and files[row['path']]['sha256']==row['sha256'] and files[row['path']]['bytes']==len(raw) and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_object'],'actual remote selected bytes and Git OID')
  if row['path']==q['proofs']['actual_capture_review']['path']:
   rd.need(R.digest(raw)=='55539547260a1d8cbbd22bcbd2a60d27cd00a4392ea95f627efda965c1c0e2e0','real remotely recovered composite')
   if not inline_verified:
    composite,bodies=verify_inline(raw)
    for name,b in bodies.items():
     part,leaf=name.split('/',1)
     original=(C/leaf) if part=='root_actual_outputs' else F/('financial-wrapper-compatibility-complete100-outcome-remote-'+part+'-2026-10-05')/leaf
     rd.need(rd.read(original,R.digest(b))==b,'all110 actual externally returned failure bodies join originals')
    inline_verified=True
 rd.need(R.digest(rd.read(flat/'outcome01.py'))==draft['source_sha256']=='bea06f690e6e69783a2f3aa905a4e3f53beba9466059a3d8babdd6e7f397af8e','accepted flat source04')
 for n,h in basis['helpers'].items():rd.read(flat/n,h)
 fresh=['LANE_RECOVERY01.json']+['flat-piece-%03d'%j for j in O.LANES[i]]
 for n in fresh:rd.need(not os.path.lexists(flat/n),'fresh fixed flat outputs')
 census=O.W.census(flat);O.W.census(root)
 release={'schema_version':1,'decision':'ACCEPTED_EXACT_OUTCOME_LANE_FLAT','lane':i,'request_core_sha256':core,'source_sha256':draft['source_sha256'],'numerical_authority':False};releases.append(release)
 results.append({'lane':i,'remote_root':str(root),'flat_root':str(flat),'actual_remote_receipt_sha256':R.digest(rr),'actual_root_exit_sha256':R.digest(er),'inner_exit_sha256':R.digest(outerraw),'original_parent_exit':None,'actual_root_exit':0,'child_exit':0,'cleanup_failures':[],'actual_Git_operations':len(remote['operations']),'selected_files':len(records),'selected_bytes':sum(x['bytes'] for x in records),'elapsed_seconds':remote['elapsed_seconds'],'selected_manifest':m,'draft_request_sha256':R.digest(qraw),'request_core_sha256':core,'source_sha256':draft['source_sha256'],'profile_sha256':R.digest(profraw),'flat_initial_census':census})
for pid in pids:rd.need(type(pid)is int and pid>0 and not os.path.lexists(Path('/proc')/str(pid)),'recorded owned metadata process absent')
# One bounded read of current process groups, scoped to recorded metadata children.
caller=rd.read(O.lane_root(0,'remote')/'caller01.py',entry['lanes'][0]['caller_sha256']);node=next(n for n in ast.parse(caller).body if isinstance(n,ast.FunctionDef) and n.name=='raw');ns={'os':os,'FILE':R.FILE};exec(compile(ast.Module(body=[node],type_ignores=[]),'<accepted bounded proc reader>','exec'),ns)
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:b=ns['raw'](p/'stat');rd.total+=len(b);rd.tick()
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  rd.need(int(b.decode().rsplit(')',1)[1].split()[2]) not in groups,'recorded owned metadata process group absent')
rd.need(inline_verified,'actual full inline failure scope verified');rd.finish()
for i,r in enumerate(releases):R.put(HERE/('LANE%02d_INNER_FLAT_RELEASE01.json'%(i+1)),r)
result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_FOUR_CANONICAL02_REMOTE_BYTE_OUTCOMES_AND_EXACT_FLAT_CORES_ONLY','actual_summary_sha256':R.digest(summary_raw),'draft_binding_sha256':R.digest(draft_raw),'lanes':results,'all_recorded_processes_absent':len(pids),'recorded_owned_groups_absent':len(groups),'universal_process_history':None,'inline_failure_bodies_actual_remote_verified':110,'inline_failure_typed':119,'full845_flat_recovery_accepted':False,'caller_flat_entry_released':False,'numerical_authority':False,'checks':rd.checks,'read_bytes':rd.total,'release_files':[{'path':'LANE%02d_INNER_FLAT_RELEASE01.json'%(i+1),'sha256':R.digest(R.encode(r))} for i,r in enumerate(releases)]}
(HERE/'REMOTE_OUTCOME_AND_FLAT_CORE_READBACK01.json').write_bytes(R.encode(result));print(json.dumps({k:v for k,v in result.items() if k!='lanes'}))
