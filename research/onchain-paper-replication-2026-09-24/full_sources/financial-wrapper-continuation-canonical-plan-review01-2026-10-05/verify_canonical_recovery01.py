"""Actual returned canonical delta + unchanged accepted recovery composition.
No restoration, numerical modules, checkpoint decoding or lifecycle calls.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,stat,subprocess,sys
H=Path(__file__).resolve().parent;F=H.parent;T=F/'financial-wrapper-continuation-canonical-transport-bound01-2026-10-05';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
sys.path[:0]=[str(T),str(T/'utilities')];spec=importlib.util.spec_from_file_location('canonical_transport',T/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
rd=Reader();root=O.lane_root(0,'flat');remote=O.lane_root(0,'remote');prefix='ROOT_CONTINUATION_CANONICAL_FLAT02';entry=json.loads(rd.read(H/'FLAT_ENTRY_READBACK01.json'));rr=rd.read(root/'LANE_RECOVERY01.json');receipt=json.loads(rr);er=rd.read(root/(prefix+'_EXIT.json'));outer=json.loads(er);ar=rd.read(root/'ACTUAL_ROOT_EXIT01.json');actual=json.loads(ar)
rd.need(actual['actual_tool_exit_code']==0 and actual['original_outer_parent_exit'] is None,'actual separate Root tool0 with original unknown parent preserved')
rd.need(outer['child_exit']==0 and outer['actual_parent_exit'] is None and outer['parent_failure_type'] is None and outer['cleanup_failures']==[] and outer['parent_fsize_readback']==[R.FILE,R.FILE] and not outer['numerical_authority'] and outer['elapsed_seconds']<210,'actual child/reap/cleanup/caps')
qr=rd.read(root/'REQUEST_FLAT01.json',entry['request_sha256']);q=json.loads(qr);contract=json.loads(rd.read(root/'FLAT_CONTRACT01.json',entry['contract_sha256']));rd.need(O.request_core_sha256(q)==entry['request_core_sha256'],'actual released request core')
for n,h in contract['helpers'].items():rd.read(root/n,h)
intent=json.loads(rd.read(root/(prefix+'_INTENT.json')));spawn=json.loads(rd.read(root/(prefix+'_SPAWN.json')));rd.need(intent['contract_sha256']==entry['contract_sha256'] and intent['entry_release_sha256']==entry['release_sha256'] and intent['argv']==spawn['argv'] and not intent['claim_started'],'genuine one-use source/caller/argv')
rd.need(rd.read(root/(prefix+'.stderr'))==b'' and not os.path.lexists(root/'BUNDLE_FLAT_FAILED01.json'),'no failed restoration/stderr');rd.read(root/(prefix+'.stdout'))
for s in outer['observations']:rd.need(0<=s['logical_bytes']<=64*1024**2 and 0<=s['allocated_bytes']<=96*1024**2 and 1<=s['members']<=32768 and 0<=s['seconds']<5 and 1<=s['complete_attempts']<=3,'actual unchanged finite sample limits')
remote_basis=json.loads(rd.read(H/'REMOTE_OUTCOME_READBACK01.json'));rd.read(remote/'REMOTE_RECOVERY01.json',remote_basis['remote_receipt_sha256']);rd.read(remote/'ACTUAL_ROOT_EXIT01.json',remote_basis['actual_root_exit_sha256']);profile=json.loads(rd.read(remote/'ACTUAL_SELECTED_MODE_PROFILE01.json','b31cd3180381c78890d2638486dd21cdfebeca8bf8eed31ca70c1a97bffdd6c9'));selected=remote/'selected';rd.tree(selected,profile['full_manifest'])
capture_raw=rd.read(selected/O.CAPTURE_PATH,O.CAPTURE);capture=O.context(capture_raw);pre=str(Path(O.CAPTURE_PATH).parent)+'/';mr=rd.read(selected/(pre+capture['manifest']),capture['archive_pin']['manifest_sha256']);m=json.loads(mr);R.validate(m);archive=rd.read(selected/(pre+capture['archive']),capture['archive_pin']['sha256']);local=json.loads(rd.read(H/'DELTA_CAPTURE_READBACK01.json','741b8aa1b54c36853a59d44b842aa4c720f2e6f51c701564681a206db0dbad6e'));rd.need(R.digest(capture_raw)==local['capture_sha256'] and R.digest(archive)==local['archive_sha256'] and R.digest(mr)==local['archive_manifest_sha256'],'actual remote bytes equal independently accepted capture')
rd.need(receipt=={'schema_version':1,'lane':0,'capture_sha256':O.CAPTURE,'request_sha256':R.digest(qr),'scope':'current-increment','scopes':receipt['scopes'],'numerical_authority':False,'requires_actual_composition_review':True} and set(receipt['scopes'])=={'current-increment'},'exact complete actual restoration receipt')
scope=receipt['scopes']['current-increment'];flat=root/'flat-current-increment';metaraw=rd.read(flat/scope['metadata_file'],scope['metadata_sha256']);meta=json.loads(metaraw);rd.need(meta['manifest']==m and meta['archive']==capture['archive_pin'] and meta['schema_version']==1,'entire original typed metadata retained');mapping=meta['flat_members'];expected={r['path']:r for r in m['members']};rd.need(len(expected)==112 and set(mapping)==set(expected) and len(set(mapping.values()))==112 and scope['members']==scope['regular_bodies']==112 and scope['archive_sha256']==R.digest(archive) and scope['manifest_sha256']==R.digest(mr) and not scope['instantiated_posix_tree'] and not scope['runtime_package_bodies_recovered'],'actual complete112 opaque bodies, honest exclusions')
fm={'schema_version':1,'root_mode':448,'members':sorted([{'path':mapping[n],'kind':'file','mode':384,'bytes':r['bytes'],'sha256':r['sha256']} for n,r in expected.items()]+[{'path':scope['metadata_file'],'kind':'file','mode':384,'bytes':len(metaraw),'sha256':R.digest(metaraw)}],key=lambda r:r['path'])};rd.tree(flat,fm);bodies={n:rd.read(flat/mapping[n],r['sha256']) for n,r in expected.items()}
it=R.framed_members(archive);seen=set();primary=None
try:
 for n,t,b in it:
  rd.need(n in expected and n not in seen,'complete nonduplicate external PAX denominator');seen.add(n);row=expected[n];rd.need(t.isfile() and t.mode==row['mode']==384 and t.uid==t.gid==0 and t.mtime==0 and t.uname==t.gname=='' and t.size==len(b)==row['bytes'] and b==bodies[n],'every actual external archive and flat body equals')
except BaseException as error:primary=error
R._cleanup((it.close,),primary=primary)
if primary is not None:raise primary
rd.need(seen==set(expected),'all112 returned PAX bodies');comp=json.loads(bodies['COMPOSITION01.json']);rd.need(R.digest(bodies['COMPOSITION01.json'])==local['composition_sha256'],'exact independently accepted complete composition returned');material=comp['materialized'];rd.need(len(material)==111 and {v['flat'] for v in material.values()}==set(bodies)-{'COMPOSITION01.json'},'all111 actual originals plus composition')
origins={};newcap={'fixture_inputs/financial_wrapper_continuation01/prior.json','fixture_inputs/financial_wrapper_continuation01/gates.json'}
for n in newcap:origins['cap/'+n]=CAP/n
for role,value in comp['origins'].items():
 origin=Path(value['root']);om=value['manifest']
 if role=='parent':prefixkey='parent/';parent=origin;rd.tree(parent,om)
 else:prefixkey='dependencies/%02d/'%int(role.removeprefix('dependency-'))
 for row in om['members']:
  p=origin/row['path'];s=p.lstat();rd.need(stat.S_IMODE(s.st_mode)==row['mode'],'original mode history remains literal')
  if row['kind']=='file':rd.need(stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'],'original regular type/extent');origins[prefixkey+row['path']]=p
  else:rd.need(row['kind']=='directory' and stat.S_ISDIR(s.st_mode),'original typed directory')
for row in comp['Git']['new_objects']:origins['git/'+row['name']]=F/'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_PLAN_GIT_TAIL01'/row['name']
rd.need(set(origins)==set(material),'exact complete current original scope')
for key,p in origins.items():
 row=material[key];body=bodies[row['flat']];rd.need(len(body)==row['bytes'] and R.digest(body)==row['sha256'] and rd.read(p,row['sha256'])==body,'each actual returned original-body join')
prior=json.loads(rd.read(F/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05/CURRENT_COMPOSITION02.json','65ee768ba3a6569b125920bbc61f01d64487a90a5ced608df31b505cd008f370'));basisraw=rd.read(Path(comp['basis']['path']),comp['basis']['sha256']);rd.need(comp['basis']['sha256']=='97faaa53f2bcc1cdfd08756480e89632ae6ca6fc4a3f966ace53de3a59cdf19d','accepted prior current823/1049/416 recovery');basis=json.loads(basisraw);rd.read(Path(basis['review']['path']),basis['review']['sha256'])
oldrows={r['path']:r for r in prior['capsule']['members']};current={r['path']:r for r in comp['capsule']['members']};rd.need(set(oldrows)==set(current) and len(current)==1049 and sum(r['kind']=='file' for r in current.values())==823 and {n for n in current if current[n]!=oldrows[n]}==newcap,'entire original821 rows reused plus exact two changed bodies');rd.tree(CAP,comp['capsule'],('.git',))
oldset=set(prior['git']['current416']);newset=set()
for row in comp['Git']['new_objects']:
 body=bodies[material['git/'+row['name']]['flat']];rd.need(hashlib.sha1(row['type'].encode()+b' '+str(len(body)).encode()+b'\0'+body).hexdigest()==row['oid'],'every returned new Git object exact type/OID');newset.add(row['oid'])
rd.need(len(oldset)==416 and len(newset)==6 and not oldset&newset and comp['Git']['complete']==422,'accepted416 plus actual6 exact closure')
p=subprocess.run(['git','--no-optional-locks','-C',str(CAP),'rev-list','--objects',O.SOURCE],capture_output=True,timeout=10,check=True);rd.need(not p.stderr and len(p.stdout)<1024*1024 and {s.split()[0] for s in p.stdout.decode().splitlines()}==oldset|newset,'actual current full422 Git closure')
head=rd.read(CAP/'.git/HEAD').decode().strip();commit=rd.read(CAP/'.git'/head[5:]).decode().strip() if head.startswith('ref: ') else head;rd.need(commit==comp['source']==O.SOURCE,'actual current d4c source');draftbody=bodies[material['parent/REQUEST_SOURCE_BOUND_DRAFT01.json']['flat']];draft=json.loads(draftbody);rd.need(R.digest(draftbody)=='0ea7cf3d34ccf9d67a1be6d836e130de275475bd6bb9d0284405cf141c6d18d6' and draft['source']==draft['design_source']==commit and draft['status']=='DRAFT_NOT_RELEASED' and draft['proofs']['full_recovery'] is draft['final_review'] is None,'actual recovered honest source-bound draft');rd.need(not os.path.lexists(parent/'attempt') and not os.path.lexists(CAP/'research_runs'/draft['identity']),'no new numerical attempt')
pids={intent['parent_pid'],spawn['pid']};groups={spawn['pid']}
for pid in pids:rd.need(not os.path.lexists(Path('/proc')/str(pid)),'recorded flat PID absent')
caller=rd.read(root/'caller01.py',entry['caller_sha256']);node=next(n for n in ast.parse(caller).body if isinstance(n,ast.FunctionDef) and n.name=='raw');ns={'os':os,'FILE':R.FILE};exec(compile(ast.Module(body=[node],type_ignores=[]),'<accepted bounded proc reader>','exec'),ns)
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:b=ns['raw'](p/'stat');rd.total+=len(b);rd.tick()
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  rd.need(int(b.decode().rsplit(')',1)[1].split()[2]) not in groups,'recorded flat process group absent')
sample=O.W.census(root);rd.finish();result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_CANONICAL_CURRENT_SOURCE_BOUND_DRAFT_BYTE_RECOVERY','source':commit,'design_source':commit,'identity':draft['identity'],'capsule_root':str(CAP),'parent_root':str(parent),'capture_sha256':O.CAPTURE,'archive_sha256':R.digest(archive),'flat_receipt_sha256':R.digest(rr),'actual_Root_exit_sha256':R.digest(ar),'original_outer_exit_sha256':R.digest(er),'actual_Root_exit':0,'actual_child_exit':0,'original_parent_exit':None,'cleanup_failures':[],'recorded_flat_PIDs_absent':sorted(pids),'recorded_flat_groups_absent':sorted(groups),'universal_process_history':None,'saved_original_bodies':111,'archive_regular':112,'archive_typed':112,'archive_logical_bytes':1990361,'current_CAP_regular':823,'current_CAP_typed':1049,'Parent_source_bound_draft_files':11,'source_bound_draft_sha256':R.digest(draftbody),'tracked':360,'source_pins':359,'input_roles':29,'current_Git_logical_objects':422,'Git416_basis_and_old821_CAP_hashes_reused':True,'changed_CAP_bodies':2,'new_Git_objects':6,'prior_current_recovery':comp['basis'],'sampled_currentness_only':True,'POSIX_reconstruction':False,'installed_runtime_body_recovery':False,'whole_capacity':False,'numerical_authority':False,'checks':rd.checks,'read_bytes':rd.total,'elapsed_seconds':__import__('time').monotonic()-rd.start,'final_sample':sample};R.put(H/'CANONICAL_RECOVERY_READBACK01.json',result);print(json.dumps(result))
