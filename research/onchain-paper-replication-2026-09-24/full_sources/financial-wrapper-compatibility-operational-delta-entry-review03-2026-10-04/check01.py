from pathlib import Path
import json,hashlib,stat,os,subprocess,sys,importlib.util
D=Path(__file__).resolve().parent;B=D.parent;MAIN=B.parents[2];I=B/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';C=B/'heartbeat-root-checkpoint10-2026-10-04';H=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def ck(n,v,**kw):
 assert v,n;rows.append(dict(name=n,**kw));(D/'CHECKS01.json').write_text(json.dumps(rows,indent=2)+'\n')
head='4d0dbef40c978788ec9ddd9a5e4f4c2d18c52714';draft_raw=(I/'ROOT_INSTALLATION_DRAFT01.json').read_bytes();draft=json.loads(draft_raw);selection_raw=(I/'SELECTED_BODIES01.json').read_bytes();selection=json.loads(selection_raw)
ck('genuine current installation draft exact',H(draft_raw)=='4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d');ck('genuine selected exact and commit',H(selection_raw)=='d2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b' and selection['remote_commit']==head);ck('caller exact',H((C/'root_operational_remote03.py').read_bytes())=='91b1bc524b614fe6b84cfc1df74d887e94c267b91509b679b563e21f304b83c7')
for n,pin in draft['helpers_and_selection'].items():
 p=I/n;s=p.lstat();ck('actual installed helper/selection:'+n,p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==pin['bytes'] and H(p.read_bytes())==pin['sha256'])
ck('actual fixed helper and owned root',draft['helpers_and_selection']['recover01.py']['sha256']=='ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf' and draft['owned_root']==str(I) and draft['source_main_commit']==head)
# Local read-only Git metadata only: no fetch/remote/entry/child receiver.
def git(args):
 p=subprocess.run(['git',*args],cwd=MAIN,capture_output=True,check=True,timeout=15);assert len(p.stdout)<=4194304 and len(p.stderr)<=65536;return p.stdout
ck('actual Main HEAD',git(['rev-parse','HEAD']).decode().strip()==head);rawtree=git(['ls-tree','-r','-z',head,'--',*[r['path'] for r in selection['rows']]]);(D/'COMMITTED_SELECTED_TREE01.bin').write_bytes(rawtree);tree={}
for item in rawtree.split(b'\0')[:-1]:
 left,path=item.split(b'\t',1);mode,kind,oid=left.decode().split();tree[path.decode()]=(mode,kind,oid)
ck('committed complete selected15 namespace',len(tree)==len(selection['rows'])==15 and set(tree)=={r['path'] for r in selection['rows']});oids=[]
for r in selection['rows']:
 p=MAIN/r['path'];s=p.lstat();b=p.read_bytes();oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();mode,kind,committed_oid=tree[r['path']];ck('actual Main/committed selected body:'+r['path'],stat.S_ISREG(s.st_mode) and s.st_nlink==1 and len(b)==r['bytes'] and H(b)==r['sha256'] and mode in ('100644','100755') and kind=='blob' and oid==committed_oid);oids.append(oid)
ck('literal selection denominator55',sum(r['bytes'] for r in selection['rows'])==507946 and len(set(oids))==15 and draft['expected_operations']==10+len(set(oids))+2*len(selection['rows'])==55)
confirmation=json.loads((C/'REMOTE_CONFIRMATION46_COMPLETE01.json').read_bytes());ck('actual complete confirmation source receipt',confirmation['main_commit']==confirmation['actual_remote_head']==head and confirmation['commit']['exit']==confirmation['commit_push']['exit']==confirmation['actual_lsremote']['exit']==0 and confirmation['actual_lsremote']['final_chunk']=='47f374' and H((C/'REMOTE_CONFIRMATION46.json').read_bytes())==confirmation['preserved_incomplete_working_receipt_sha256']);ck('actual latest complete receipt copied',(D/'REMOTE_CONFIRMATION46_COMPLETE01.json').read_bytes()==(C/'REMOTE_CONFIRMATION46_COMPLETE01.json').read_bytes())
# Authenticate complete previously accepted source and different-author watcher review evidence.
for dirname,pin,decision,machinepin in [('financial-wrapper-compatibility-operational-delta-remote-review02-2026-10-04','7b2a32464feaf8a95467dad2274d14b13154bd3f09fca447c72b952ff58e8714','ACCEPTED_SOURCE_ONLY_COMPLETE15_REMOTE_SUCCESSOR','bd33dac061d5a7dba3f7f9e1dd38f194770f66f6f37c487ba76d2e1eeefd5b02'),('financial-wrapper-operational-forensic-watch-review04-2026-10-04','7a94ef046588cb9a10a978d63865302e0b12a25e60db98190aea9927ecc59f47','ACCEPTED_NARROW_SOURCE_ONLY_FIXED_PUBLICATION_RETRY_SCHEDULE','aed1248d003fbe19ccbd5f0f57b6801e6cf08713bb01d6d9fa56a145e172bb57')]:
 root=B/dirname;manifest_raw=(root/'MANIFEST01.json').read_bytes();manifest=json.loads(manifest_raw);machine_raw=(root/'MACHINE01.json').read_bytes();machine=json.loads(machine_raw);ck('exact accepted source review:'+dirname,H(manifest_raw)==pin and H(machine_raw)==machinepin and machine['decision']==decision)
 for r in manifest['members']:
  p=root/r['path'];s=p.lstat();valid=stat.S_IMODE(s.st_mode)==r['mode']
  if r['kind']=='file':valid=valid and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256']
  elif r['kind']=='directory':valid=valid and stat.S_ISDIR(s.st_mode)
  elif r['kind']=='symlink':valid=valid and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
  else:valid=False
  ck('review current member:'+dirname+':'+r['path'],valid)
 for n in ('MACHINE01.json','MANIFEST01.json','REPORT01.md'):(D/(('WATCH_' if 'watch' in dirname else 'SOURCE_')+n)).write_bytes((root/n).read_bytes())
for name in ['ROOT_REMOTE03_INTENT01.json','ROOT_REMOTE03_SPAWN01.json','ROOT_REMOTE03_EXIT01.json','fresh-operational-source-policy02.git','selected','flat-operational-delta01','flat-failed-remote02-01','REMOTE_RECOVERY01.json','FAILED01.json','ROOT_REMOTE03.stdout','ROOT_REMOTE03.stderr','restore01.py']:
 ck('actual absent fresh namespace:'+name,not os.path.lexists(I/name))
ck('flat and entry authority not installed',draft['flat_helper_installed'] is False and draft['exact_installed_entry_review'] is None and draft['actual_recovery'] is None)
targets={str(I/'recover01.py').encode(),str(I/'restore01.py').encode(),str(C/'root_operational_remote03.py').encode()};matches=[];scanned=0
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:
  # Only command-line argv is inspected for exact task executable paths; never environments.
  with (p/'cmdline').open('rb') as f:argv=f.read(32768).split(b'\0')
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 scanned+=1
 if targets.intersection(argv):matches.append({'pid':int(p.name),'matched_paths':[x.decode() for x in targets.intersection(argv)]})
ck('no actual matching receiver/flat/outer process',matches==[],processes_scanned=scanned)
# Read-only installed exact watch dependency for current actual baseline, not self-review.
sys.path.insert(0,str(I));spec=importlib.util.spec_from_file_location('installed_watch_baseline',I/'watch01.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);baseline=w.census(I);ck('actual current complete resource baseline',baseline['logical_bytes']<=67108864 and baseline['allocated_bytes']<=100663296 and baseline['members']<=32768);(D/'BASELINE01.json').write_text(json.dumps({'owned_root':str(I),'sample':baseline,'disk_free_bytes':w.shutil.disk_usage(I).free,'qualified_by_peer_watch_acceptance':True,'watch_independently_reviewed_here':False},indent=2)+'\n');ck('actual10GiBfloor',w.shutil.disk_usage(I).free>=10737418240)
failedroot=Path(draft['prior_consumed_failure']['root']);failed_raw=(failedroot/'FAILED01.json').read_bytes();failed=json.loads(failed_raw);ck('old Root02 still failed/nulls',H(failed_raw)==draft['prior_consumed_failure']['failed_sha256']=='7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a' and failed['operations'][2]['exit'] is None and failed['operations'][2]['actual_reaped_exit']==0 and not (failedroot/'REMOTE_RECOVERY01.json').exists());(D/'HISTORICAL_FAILED01.json').write_bytes(failed_raw)
ck('all actual installed control bytes unchanged at end',H((I/'ROOT_INSTALLATION_DRAFT01.json').read_bytes())=='4ac66420883fe2605db005152c4492e0597aaab1593ebc9976d1857b0ff6a96d' and H((I/'recover01.py').read_bytes())=='ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf')
print(json.dumps({'checks':len(rows),'current_preconditions_passed':True,'entry_decision':'WITHHELD_ACTUAL_DRAFT_BODY_NOT_AUTHENTICATED_BY_CALLER','no_network_or_entry':True}))
