"""Read-only exact actual four-flat and inline-failure byte composition.
No restoration, checkpoint decoding, numerical import, source change or claim.
Run only after the four actual Root terminal receipts exist.
"""
from pathlib import Path
import sys,os,json,stat,ast,hashlib,importlib.util,time,base64
HERE=Path(__file__).resolve().parent;F=HERE.parent;V1=F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05';V2=F/'financial-wrapper-compatibility-complete100-recovery-outcome-review02-2026-10-05';sys.path[:0]=[str(V1),str(V2)]
from verify_capture01 import Reader,R,C,MAIN,D,verify_piece
from verify_failure_bundle01 import verify_inline
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation04-2026-10-05';sys.path[:0]=[str(P),str(P/'utilities')];spec=importlib.util.spec_from_file_location('accepted_outcome04',P/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)

def main():
 rd=Reader();capture_raw=rd.read(D/'CAPTURE01.json',O.CAPTURE);capture=O.context(capture_raw);entry=json.loads(rd.read(HERE/'FLAT_ENTRY_READBACK01.json'));remote_basis=json.loads(rd.read(HERE/'REMOTE_OUTCOME_AND_FLAT_CORE_READBACK01.json'));originals={};original_rows={}
 for role,scope in capture['originals'].items():
  root=Path(scope['root']);rd.tree(root,scope['manifest'],('.git',) if role=='capsule' else ())
  for row in scope['manifest']['members']:
   if row['kind']=='file':originals[role,row['path']]=root/row['path'];original_rows[role,row['path']]=(row['bytes'],row['sha256'])
 caproot=Path(capture['originals']['capsule']['root']);head=rd.read(caproot/'.git/HEAD').decode().strip();commit=rd.read(caproot/'.git'/head.removeprefix('ref: ')).decode().strip() if head.startswith('ref: ') else head;rd.need(commit==O.SOURCE,'actual original CAP source unchanged')
 seen={};lanes=[];proofs=[];pids=set();groups=set();inline_files=None
 for i in range(4):
  root=O.lane_root(i,'flat');receiver=O.lane_root(i,'remote');selected=receiver/'selected';e=entry['lanes'][i];basis=remote_basis['lanes'][i];prefix='ROOT_OUTCOME_LANE%02d_CANONICAL02_FLAT02'%(i+1)
  contract_raw=rd.read(root/'FLAT_CONTRACT02.json',e['contract_sha256']);contract=json.loads(contract_raw);qr=rd.read(root/'REQUEST_FLAT_FINAL01.json',e['request_sha256']);q=json.loads(qr);rd.need(O.request_core_sha256(q)==e['request_core_sha256'],'original released exact request core');rd.read(root/'caller01.py',e['caller_sha256']);ir=rd.read(root/'FLAT_RELEASE01.json',e['inner_release_sha256']);rd.need(ir==rd.read(HERE/('LANE%02d_INNER_FLAT_RELEASE01.json'%(i+1))),'genuine installed inner release unchanged')
  for name,h in contract['helpers'].items():rd.read(root/name,h)
  rr=rd.read(root/'LANE_RECOVERY01.json');receipt=json.loads(rr);rd.need(receipt=={'schema_version':1,'lane':i,'capture_sha256':O.CAPTURE,'request_sha256':R.digest(qr),'piece_ids':list(O.LANES[i]),'scopes':receipt['scopes'],'numerical_authority':False,'requires_cross_lane_original_review':True},'exact genuine completed lane receipt');rd.need(set(receipt['scopes'])=={'piece-%03d'%j for j in O.LANES[i]},'all exact disjoint pieces')
  outer_raw=rd.read(root/(prefix+'_EXIT.json'));outer=json.loads(outer_raw);actual_raw=rd.read(root/'ACTUAL_ROOT_EXIT01.json');actual=json.loads(actual_raw)
  rd.need(actual['actual_root_exit']==0 and actual['lane']==i,'actual separate Root flat exit0')
  rd.need(outer['child_exit']==0 and outer['actual_parent_exit'] is None and outer['parent_failure_type'] is None and outer['cleanup_failures']==[] and outer['parent_fsize_readback']==[R.FILE,R.FILE] and outer['numerical_authority'] is False and 0<=outer['elapsed_seconds']<210,'genuine actual child/cleanup/limits; original ParentNULL')
  # Actual Root receipt fields are joined literally, never filled by this review.
  rd.need(actual['receipt_sha256']==R.digest(rr) and actual['inner_exit_sha256']==R.digest(outer_raw) and actual['original_inner_actual_parent_exit'] is None,'Root/child/lane receipt literal join')
  rd.need(rd.read(root/(prefix+'.stderr'))==b'','actual child stderr empty');rd.read(root/(prefix+'.stdout'));intent=json.loads(rd.read(root/(prefix+'_INTENT.json')));spawn=json.loads(rd.read(root/(prefix+'_SPAWN.json')))
  outer_release=rd.read(HERE/('LANE%02d_OUTER_FLAT_RELEASE01.json'%(i+1)));rd.need(intent['contract_sha256']==e['contract_sha256'] and intent['entry_release_sha256']==R.digest(outer_release) and intent['claim_started'] is False and intent['argv']==spawn['argv'],'actual once-only released argv/intent');pids.update((intent['parent_pid'],spawn['pid']));groups.add(spawn['pid'])
  for n in ('BUNDLE_FLAT_FAILED01.json','FAILED01.json'):rd.need(not os.path.lexists(root/n),'no failed restoration disposition')
  for s in outer['observations']:rd.need(0<=s['logical_bytes']<=64*1024**2 and 0<=s['allocated_bytes']<=96*1024**2 and 1<=s['members']<=32768 and 0<=s['seconds']<5 and 1<=s['complete_attempts']<=3,'all actual finite sampled namespace observations')
  rd.tree(selected,basis['selected_manifest']);rd.read(receiver/'REMOTE_RECOVERY01.json',basis['actual_remote_receipt_sha256']);rd.read(receiver/'ACTUAL_ROOT_EXIT01.json',basis['actual_root_exit_sha256']);rd.need(rd.read(selected/O.CAPTURE_PATH,O.CAPTURE)==capture_raw,'actual remotely recovered capture metadata')
  required=O.selected_required(q,i,capture)
  for role,ref in q['proofs'].items():
   body=rd.read(selected/ref['path'],ref['sha256']);rd.need(len(body)==ref['bytes'],'literal selected actual proof extent')
   if role=='actual_capture_review':
    composite,failures=verify_inline(body);rd.need(R.digest(body)=='55539547260a1d8cbbd22bcbd2a60d27cd00a4392ea95f627efda965c1c0e2e0','actual full inline failure proof')
    if inline_files is None:
     inline_files=failures
     for name,b in failures.items():
      part,leaf=name.split('/',1);origin=C/leaf if part=='root_actual_outputs' else F/('financial-wrapper-compatibility-complete100-outcome-remote-'+part+'-2026-10-05')/leaf;rd.need(rd.read(origin,R.digest(b))==b,'all110 externally returned failed bodies equal originals')
    else:rd.need(failures==inline_files,'all four returned inline failure scopes identical')
  prefix_path=str(Path(O.CAPTURE_PATH).parent)+'/'
  for j in O.LANES[i]:
   piece=capture['pieces'][j];name='piece-%03d'%j;scope=receipt['scopes'][name];flat=root/('flat-'+name);meta_raw=rd.read(flat/scope['metadata_file'],scope['metadata_sha256']);meta=json.loads(meta_raw);m=json.loads(rd.read(selected/(prefix_path+piece['manifest']),piece['archive_pin']['manifest_sha256']));R.validate(m)
   rd.need(meta['manifest']==m and meta['archive']==piece['archive_pin'] and meta['schema_version']==1,'literal recovered original metadata and archive binding');mapping=meta['flat_members'];expected={b['member']:b for b in piece['bodies']}
   rd.need(set(mapping)==set(expected) and len(mapping)==len(set(mapping.values())) and set(mapping.values())=={'body-%05d.body'%k for k in range(len(mapping))},'complete unique actual flat mapping')
   rd.need(scope['archive_sha256']==piece['archive_pin']['sha256'] and scope['manifest_sha256']==piece['archive_pin']['manifest_sha256'] and scope['regular_bodies']==scope['members']==len(mapping) and scope['metadata_file']=='body-metadata.json' and scope['instantiated_posix_tree'] is False and scope['runtime_package_bodies_recovered'] is False and scope['research_authority'] is False,'honest exact output scope')
   fm={'schema_version':1,'root_mode':448,'members':[{'path':leaf,'kind':'file','mode':384,'bytes':expected[n]['bytes'],'sha256':expected[n]['sha256']} for n,leaf in mapping.items()]+[{'path':'body-metadata.json','kind':'file','mode':384,'bytes':len(meta_raw),'sha256':R.digest(meta_raw)}]};fm['members'].sort(key=lambda x:x['path']);rd.tree(flat,fm)
   # Independent TAR framing, body and original-byte reconstruction from actual remote archive.
   verify_piece(rd,selected/(prefix_path+piece['archive']),selected/(prefix_path+piece['manifest']),piece,originals)
   for b in piece['bodies']:
    k=b['role'],b['path'];rd.need(k not in seen,'no overlap or missing denominator');body=rd.read(flat/mapping[b['member']],b['sha256']);rd.need(len(body)==b['bytes'],'actual flat whole body extent');seen[k]=(len(body),R.digest(body))
  census=O.W.census(root);lanes.append({'lane':i,'root':str(root),'receipt':{'path':str(root/'LANE_RECOVERY01.json'),'sha256':R.digest(rr)},'actual_root_exit':{'path':str(root/'ACTUAL_ROOT_EXIT01.json'),'sha256':R.digest(actual_raw)},'original_inner_exit':{'path':str(root/(prefix+'_EXIT.json')),'sha256':R.digest(outer_raw)},'original_parent_exit':None,'actual_root_exit_code':0,'child_exit':0,'cleanup_failures':[],'pieces':list(O.LANES[i]),'elapsed_seconds':outer['elapsed_seconds'],'final_sampled_census':census})
 rd.need(seen==original_rows and len(seen)==845 and len(inline_files)==110,'complete independent original and failed-body reconstruction')
 for pid in pids:rd.need(type(pid)is int and pid>0 and not os.path.lexists(Path('/proc')/str(pid)),'all recorded actual flat PIDs absent')
 caller=rd.read(O.lane_root(0,'flat')/'caller01.py',entry['lanes'][0]['caller_sha256']);node=next(n for n in ast.parse(caller).body if isinstance(n,ast.FunctionDef) and n.name=='raw');ns={'os':os,'FILE':R.FILE};exec(compile(ast.Module(body=[node],type_ignores=[]),'<accepted bounded proc reader>','exec'),ns)
 for p in Path('/proc').iterdir():
  if p.name.isdigit():
   try:b=ns['raw'](p/'stat');rd.total+=len(b);rd.tick()
   except (FileNotFoundError,ProcessLookupError,PermissionError):continue
   rd.need(int(b.decode().rsplit(')',1)[1].split()[2]) not in groups,'recorded flat-owned process groups absent')
 outcome_path=F/'financial-wrapper-compatibility-complete100-outcome-review01-2026-10-05/MACHINE01.json';outcome_raw=rd.read(outcome_path,'27e29cab0b784748bdd0fef2ca484215b39b2b025784a469de443f619ae9b124');outcome=json.loads(outcome_raw)
 basispath=F/'financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05/BASELINE_FULL_RECOVERY_PROOF01.json';rd.read(basispath,'02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48')
 rd.finish()
 result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_COMPATIBILITY_COMPLETE100_BYTE_RECOVERY','source':commit,'identity':outcome['identity'],'capture_sha256':O.CAPTURE,'outcome_review_sha256':R.digest(outcome_raw),'claim_sha256':outcome['actual_claim_sha256'],'terminal_sha256':outcome['actual_terminal_sha256'],'checkpoint_sha256':outcome['actual_checkpoint_sha256'],'lanes':lanes,'pieces':26,'original_regular':845,'original_typed':1074,'original_bytes':77970429,'inline_failed_regular':110,'inline_failed_typed':119,'composite_sha256':'55539547260a1d8cbbd22bcbd2a60d27cd00a4392ea95f627efda965c1c0e2e0','Git407_basis':{'path':str(basispath),'sha256':'02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48'},'Git407_reconstructed_again':False,'all_original_modes_retained_as_metadata':True,'recorded_flat_PIDs_absent':sorted(pids),'recorded_flat_groups_absent':sorted(groups),'universal_process_history':None,'original_parent_exit':None,'checks':rd.checks,'read_bytes':rd.total,'elapsed_seconds':time.monotonic()-rd.start,'sampled_currentness_only':True,'POSIX_reconstruction':False,'installed_runtime_bodies_recovered':False,'whole_capacity':False,'new_claim_authority':False,'numerical_authority':False}
 R.put(HERE/'FINAL_RECOVERY_READBACK01.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('lanes','recorded_flat_PIDs_absent','recorded_flat_groups_absent')}))
if __name__=='__main__':main()
