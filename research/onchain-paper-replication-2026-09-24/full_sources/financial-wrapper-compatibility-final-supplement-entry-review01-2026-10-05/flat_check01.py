from pathlib import Path
import ast,copy,hashlib,json,os,stat,sys
O=Path(__file__).resolve().parent;F=O.parent;ROOT=F.parents[2];D=F/'financial-wrapper-compatibility-final-supplement-flat-root02-2026-10-05';RE=F/'financial-wrapper-compatibility-final-supplement-root02-2026-10-05';A=F/'financial-wrapper-compatibility-final-supplement-transport-preparation02-2026-10-05';H=lambda b:hashlib.sha256(b).hexdigest();checks=[];seen={}
def ok(v,m):
 if not v:raise AssertionError(m)
 checks.append(m)
def sig(p):
 s=p.lstat();return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p,h=None):
 p=Path(p);s=p.lstat();pin=sig(p);ok(p.resolve()==p and stat.S_ISREG(s.st_mode)and s.st_nlink==1 and s.st_size<=4194304,'bounded regular '+p.name);b=p.read_bytes();ok(sig(p)==pin,'stable read')
 if h:ok(H(b)==h,'pin '+p.name)
 seen[str(p)]={'signature':pin,'sha256':H(b),'bytes':len(b)};return b
readyraw=read(D/'ROOT_REQUEST_FLAT_READY01.json','dd63d52e629a34eb2d7c0e5b0fc3e59315055985d4ff4fee943eaa2a1b0db108');q=json.loads(readyraw)
craw=read(D/'FLAT_CONTRACT_READY01.json','c4b76fd3ddfa9cfe6455886bd4f1e9b46c883e2146a95fc377cf7442477bb45f');c=json.loads(craw)
old=json.loads(read(RE/'ROOT_REQUEST_FINAL_SUPPLEMENT01.json','b18caea1a109acc7057af1d6d3254069b1f44f1d727419d4afec928c498defe8'))
ok({k for k in q if q[k]!=old[k]}=={'actual_remote_receipt','actual_selected_mode_profile'},'ready only fills genuine outcome/profile');ok(q['actual_restore_release'] is None and c['request'] is None and c['flat_release'] is None,'no premature release')
for n,h in c['helpers'].items():ok(read(D/n,h)==read(RE/n,h),'exact installed support '+n)
caller=read(D/'caller_flat01.py','661ca98c29d44e0dfb7946139f6285b888fe40f083ddab319ed3a67374edf5f6');ok(caller==read(A/'caller_flat01.py'),'exact reviewed flat caller')
sys.path[:0]=[str(D),str(D/'utilities')];import binding01 as B;import watch01 as W;import receipt01 as V
from cohort01 import VerifiedCohort
R=B.R;required=B.validate(q);selraw=read(RE/'SELECTED_BODIES01.json',c['selection']['sha256']);sel=json.loads(selraw);ok(read(D/'SELECTED_BODIES01.json')==selraw,'literal local selection copy')
remote_raw=read(RE/'REMOTE_RECOVERY01.json','674054ff030c3e3aa0b21d7b09f5a2267def78af45f8ff8da21ac56ba9f1a912');remote=json.loads(remote_raw);V.validate_remote(remote,sel,H(selraw),required);ok(remote['fresh_git_root']==str(RE/'fresh-compatibility-final-supplement02.git') and remote['status']=='fresh-actual-remote-compatibility-final-supplement02-supervised-recovered','actual fixed receiver')
ok(remote['expected_operations']==len(remote['operations'])==55,'actual55 operations');ok(all(o['actual_reaped_exit']==o['exit']==0 and o['cleanup_failures']==[] for o in remote['operations']),'all actual Git children0/cleanup')
outer=json.loads(read(RE/'ROOT_FINAL_SUPPLEMENT_REMOTE02_EXIT.json','0c4190bc17465a48d9da18a5a799b9ed0a8a7eab34e660fcd709956e292433a5'));tool=json.loads(read(RE/'ROOT_TOOL_EXIT_REMOTE01.json','9664d26a5f12d7a3b7e70e67c0568df7b6ea99115bf87a8ccb8fdd2638b43fde'))
ok(outer['child_exit']==tool['actual_root_exit']==0 and outer['cleanup_failures']==[] and outer['parent_failure_type'] is None and outer['actual_parent_exit'] is None,'distinct genuine Root0 and original null')
spawn=json.loads(read(RE/'ROOT_FINAL_SUPPLEMENT_REMOTE02_SPAWN.json'));intent=json.loads(read(RE/'ROOT_FINAL_SUPPLEMENT_REMOTE02_INTENT.json'));ok(intent['entry_release_sha256']==H(read(O/'REMOTE_ENTRY_RELEASE01.json')),'actual released invocation')
pids={spawn['pid'],intent['parent_pid']}|{o['pid']for o in remote['operations']};ok(all(not Path('/proc',str(p)).exists()for p in pids),'all original recorded PIDs absent')
profile=json.loads(read(RE/'SELECTED_MODE_PROFILE01.json','f8e560e0c46298fb803f45f036d039a25697d60bedabf0c2cf565e574feb608f'));selected=RE/'selected';m=profile['full_manifest'];ok(profile['actual_selected_root']==str(selected) and R.scan(selected)==m,'whole actual selected original modes')
files={r['path']:r for r in m['members']if r['kind']=='file'};dirs={'.':m['root_mode'],**{r['path']:r['mode']for r in m['members']if r['kind']=='directory'}};ok(set(files)==set(required) and all(r['mode']==0o600 for r in files.values()),'15private selected bodies')
cohort=VerifiedCohort();cohort.selected_profile={'actual_selected_root':str(selected),'expected_owner_uid':os.geteuid(),'directory_modes':dirs,'files':files}
for row in remote['selected_blobs']:
 n=row['path'];b=read(selected/n,required[n]['sha256']);ok(b==read(ROOT/n,required[n]['sha256']) and len(b)==row['bytes']==required[n]['bytes'],'actual remote selected literal body');ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'],'actual OID');cohort.read(selected,n)
cohort.tree(selected,set(files));cohort.check()
# Genuine inner and outer release candidates. Intended Root names are fixed;
# candidate files remain in this review directory for literal installation.
inner={'schema_version':1,'decision':'ACCEPTED_EXACT_FINAL_SUPPLEMENT_BUNDLE_FLAT','contract_sha256':H(R.encode({k:v for k,v in q.items()if k!='actual_restore_release'})),'remote_sha256':q['actual_remote_receipt']['sha256'],'source_sha256':c['helpers']['restore_bundle01.py']}
ok(inner['contract_sha256']=='aa0b9dfe8fffa3bbb66c0fd0fe4a3abe1508130f370ca7b66e724e51cbac02cf','exact inner contract')
ib=R.encode(inner);finalq=copy.deepcopy(q);finalq['actual_restore_release']={'path':(D/'INNER_FLAT_RELEASE01.json').relative_to(ROOT).as_posix(),'bytes':len(ib),'sha256':H(ib)};qb=R.encode(finalq)
fc=copy.deepcopy(c);fc['request']={'path':'ROOT_REQUEST_FLAT01.json','sha256':H(qb)};fc['flat_release']={'path':'INNER_FLAT_RELEASE01.json','sha256':H(ib)};cb=R.encode(fc)
release={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_FINAL_SUPPLEMENT_FLAT','contract_sha256':H(cb),'caller_sha256':H(caller),'numerical_authority':False};rb=R.encode(release)
ns={'Path':Path};tree=ast.parse(caller);nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in {'contract','local','evidence'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'caller_flat01.py','exec'),ns);ok(ns['contract'](fc)=='FLAT','actual final contract predicate');ok(ns['evidence'](fc['remote_receipt']['path'])==RE/'REMOTE_RECOVERY01.json','read-only old receiver mapping')
ok(H(R.encode({k:v for k,v in finalq.items()if k!='actual_restore_release'}))==inner['contract_sha256'],'finalq exact inner self exclusion')
for n in fc['fresh_names']+['ROOT_FINAL_SUPPLEMENT_FLAT02'+s for s in ('_INTENT.json','_SPAWN.json','.stdout','.stderr','_EXIT.json')]:ok(not os.path.lexists(D/n),'fresh '+n)
for p in Path('/proc').iterdir():
 if p.name.isdigit() and int(p.name)!=os.getpid():
  try:argv=(p/'cmdline').read_bytes().split(b'\0')
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  ok(str(D/'restore_bundle01.py').encode() not in argv and str(D/'caller_flat01.py').encode()not in argv,'no active exact flat process')
observation=W.census(D);old_observation=W.census(RE);ok(stat.S_IMODE(D.stat().st_mode)==0o700,'private fresh flat root')
cohort.check()
for name,row in seen.items():ok(sig(Path(name))==row['signature'],'terminal sampled input '+Path(name).name)
for n,b in [('INNER_FLAT_RELEASE01.json',ib),('ROOT_REQUEST_FLAT01.json',qb),('FLAT_CONTRACT01.json',cb),('OUTER_FLAT_RELEASE01.json',rb)]:
 with (O/n).open('xb')as f:f.write(b)
result={'checks':len(checks),'actual_remote_sha256':H(remote_raw),'actual_root_exit_sha256':H(read(RE/'ROOT_FINAL_SUPPLEMENT_REMOTE02_EXIT.json')),'actual_tool_exit_sha256':H(read(RE/'ROOT_TOOL_EXIT_REMOTE01.json')),'profile_sha256':q['actual_selected_mode_profile']['sha256'],'actual_git_operations':55,'actual_selected_bodies':15,'actual_selected_bytes':sum(r['bytes']for r in required.values()),'original_selected_directory_modes':dirs,'original_parent_exit':None,'actual_root_exit':0,'actual_child_exit':0,'actual_cleanup_failures':[],'actual_recorded_pids_absent':sorted(pids),'inner_contract_sha256':inner['contract_sha256'],'ready_request_sha256':H(readyraw),'ready_contract_sha256':H(craw),'caller_sha256':H(caller),'new_root_observation':observation,'completed_receiver_observation':old_observation,'candidate_destinations':{n:{'path':str(D/n),'sha256':H((O/n).read_bytes()),'bytes':(O/n).stat().st_size}for n in ('INNER_FLAT_RELEASE01.json','ROOT_REQUEST_FLAT01.json','FLAT_CONTRACT01.json','OUTER_FLAT_RELEASE01.json')},'actual_flat_outcome':None,'numerical_authority':False}
(O/'FLAT_CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(O/'FLAT_READ_SET01.json').write_text(json.dumps(seen,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(result,sort_keys=True))
