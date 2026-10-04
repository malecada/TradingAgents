"""One read-only actual capture population/canonical-byte verification."""
from pathlib import Path
import ast,hashlib,json,os,stat,io,gzip,tarfile,time,subprocess
H=Path(__file__).resolve().parent;B=H.parent;C=B/'heartbeat-root-checkpoint10-2026-10-04';D=B/'financial-wrapper-compatibility-preclaim-baseline-capture01-2026-10-05';S=D/'snapshot'
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');PARENT=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
EXPECTED={'bridge':'financial-wrapper-compatibility-final-source-runtime-bridge02-2026-10-04','capture-review':'financial-wrapper-compatibility-source-parent-capture-review04-2026-10-04','coalesced':'financial-wrapper-compatibility-coalesced-evidence-root03-2026-10-04','coalesced-review':'financial-wrapper-compatibility-coalesced-evidence-outcome-review04-2026-10-04','delta04':'financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04','failed03':'financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04','postinstall':'financial-wrapper-compatibility-coalesced-postinstall-review04-2026-10-04','root-copy':'financial-wrapper-compatibility-coalesced-evidence-root-launch04-2026-10-04'}
ROOTFILES=['COALESCED_CANDIDATES_INSTALL04_INTENT01.json','COALESCED_CANDIDATES_INSTALL04_OBSERVED01.json','COALESCED_CANDIDATES_INSTALL04_ACTUAL_TOOL_EXIT01.json'];CURRENT='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
start=time.monotonic();checks=0;cache={};sigs={};trees={};total=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,msg):
 global checks
 if not v:raise AssertionError(msg)
 checks+=1
sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p,pin=None):
 global total
 p=Path(p);s=p.lstat();ok(time.monotonic()-start<120 and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'finite canonical regular')
 if p not in cache:
  with p.open('rb') as f:b=f.read(4194305)
  ok(sig(p.lstat())==sig(s) and len(b)==s.st_size,'stable body');cache[p]=b;sigs[p]=sig(s);total+=len(b);ok(total<=64*1024**2,'64MiB total audit read')
 else:ok(sigs[p]==sig(s),'cached body remains exact');b=cache[p]
 ok(pin is None or sha(b)==pin,'actual pin');return b
def j(p,pin=None):return json.loads(read(p,pin))
def census(root,exclude=()):
 out={};pending=[root]
 while pending:
  p=pending.pop()
  with os.scandir(p) as it:
   for e in it:
    if p==root and e.name in exclude:continue
    st=e.stat(follow_symlinks=False);n=str(Path(e.path).relative_to(root));ok(stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode),'actual type');out[n]=sig(st)
    if stat.S_ISDIR(st.st_mode):pending.append(Path(e.path))
 ok(len(out)<4096,'finite population');old=trees.get(root);ok(old is None or old==(tuple(exclude),out),'complete namespace unchanged');trees[root]=(tuple(exclude),out);return out
source=read(C/'root_preclaim_baseline_capture01.py','64c969a7d4f3558466633ba3eb027def12b10318e9d2c9e0c618efac50fdc078');old=read(C/'root_source_parent_capture04.py','f55ce818ef7999195c88d872c983a568861d5d45d2970af61b539979faf27cdf');ok(source.split(b'import subprocess,datetime,resource')[0]==old.split(b'import subprocess,datetime,resource')[0]+b'\n' and ast.dump(ast.parse(source.split(b'import subprocess,datetime,resource')[0]))==ast.dump(ast.parse(old.split(b'import subprocess,datetime,resource')[0])),'exact accepted Reader/IO prefix reused')
cap=j(D/'CAPTURE01.json','27f7929e32708c013dfa56b00f4092ce46076baef5f8ee0135cbfd4621ac828c');man=j(D/'MANIFEST01.json','6048eadcb4841a816a884eebe16b66fa5d3c4e50ff61ee80df55e43ec44957f9');ar=read(D/'baseline01.tar.gz','b47c7201a023e8b08fd90e8f8fc228751608b30cf6d25077373e7f797db1178c');terminal=j(C/'PRECLAIM_BASELINE_CAPTURE01_ACTUAL_TOOL_EXIT01.json')
ok(terminal['actual_tool_exit']==0 and terminal['actual_tool_chunk']=='aaaeda' and terminal['pid_history'] is None and terminal['capture']['sha256']==sha(read(D/'CAPTURE01.json')) and terminal['source']['sha256']==sha(source),'genuine separate Root terminal/unknown PID')
ok(cap['scopes']=={k:str(B/v) for k,v in EXPECTED.items()} and cap['source']==CURRENT,'exact eight fixed scopes/currentsource')
rows={x['path']:x for x in man['members']};ok(len(rows)==len(man['members'])==303 and list(rows)==sorted(rows),'sorted unique303typed');ok(set(census(S))==set(rows) and stat.S_IMODE(S.stat().st_mode)==man['root_mode']==0o700,'complete private snapshot')
payload={}
for n,x in rows.items():
 st=(S/n).lstat();ok(stat.S_IMODE(st.st_mode)==x['mode']==(0o700 if x['kind']=='directory' else 0o600),'snapshot literal mode')
 if x['kind']=='file':b=read(S/n,x['sha256']);ok(len(b)==x['bytes'],'snapshot extent');payload[n]=b
ok(len(payload)==cap['payload_files']==262 and sum(map(len,payload.values()))==cap['payload_bytes']==10739552,'fullpayload count/bytes')
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as tar:
 for x in man['members']:
  ti=tarfile.TarInfo(x['path']+('/' if x['kind']=='directory' else ''));ti.mode=x['mode'];ti.uid=ti.gid=ti.mtime=0;ti.uname=ti.gname=''
  if x['kind']=='directory':ti.type=tarfile.DIRTYPE;tar.addfile(ti)
  else:ti.size=x['bytes'];tar.addfile(ti,io.BytesIO(payload[x['path']]))
ok(gzip.compress(buf.getvalue(),mtime=0)==ar and len(ar)==cap['archive_bytes']==3052678,'fullcanonical USTAR order/header/mode/body/padding/footer/gzip')
with tarfile.open(fileobj=io.BytesIO(ar),mode='r:gz') as tar:
 for ti,x in zip(tar.getmembers(),man['members'],strict=True):
  ok(ti.name==x['path'] and ti.mode==x['mode'] and ti.uid==ti.gid==ti.mtime==0 and ti.uname==ti.gname=='' and not ti.pax_headers,'independent parsed canonical header')
  ok(ti.isdir() if x['kind']=='directory' else ti.isfile() and tar.extractfile(ti).read()==payload[x['path']],'independent parsed body/type')
scopes=json.loads(payload['ORIGINAL_SCOPES01.json']);origins=json.loads(payload['ORIGINAL_ORIGINS01.json']);ok(sha(payload['ORIGINAL_SCOPES01.json'])==cap['original_scopes_sha256'] and sha(payload['ORIGINAL_ORIGINS01.json'])==cap['origins_sha256'],'origin metadata pins');ok(set(scopes)==set(EXPECTED),'all eight originalscopes metadata')
original_files={};scope_stats={};empty=[]
for alias,dirname in EXPECTED.items():
 root=B/dirname;x=scopes[alias];rr={z['path']:z for z in x['members']};actual=census(root);ok(str(root)==x['root'] and set(actual)==set(rr) and stat.S_IMODE(root.stat().st_mode)==x['original_root_mode'],'full original scope/rootmode '+alias)
 for n,z in rr.items():
  st=(root/n).lstat();ok(stat.S_IMODE(st.st_mode)==z['mode'],'every original literal mode')
  if z['kind']=='file':b=read(root/n,z['sha256']);ok(len(b)==z['bytes'] and payload[alias+'/'+n]==b,'original exact body');original_files[alias+'/'+n]={'original_path':str(root/n),'original_mode':z['mode'],'bytes':len(b),'sha256':sha(b)}
  elif not any(k.startswith(n+'/') for k in rr):empty.append(alias+'/'+n)
 scope_stats[alias]={'typed':len(rr),'files':sum(z['kind']=='file' for z in rr.values()),'root_mode':x['original_root_mode']}
for n in ROOTFILES:
 p=C/n;b=read(p);key='root-install/'+n;ok(payload[key]==b,'all three literal Root installer bodies');original_files[key]={'original_path':str(p),'original_mode':stat.S_IMODE(p.stat().st_mode),'bytes':len(b),'sha256':sha(b)}
ok(len(origins)==len(original_files)==260 and len({x['archive_path'] for x in origins})==260,'all260 originalfile mappings plus2metadata')
for x in origins:ok({k:v for k,v in x.items() if k!='archive_path'}==original_files[x['archive_path']],'full original row/path/mode/hash equality')
# Reuse prior exact independently accepted body basis, never relabel as new recovery.
critical={'bridge/SOURCE_INPUT_RUNTIME_PROOF01.json':'ac1ed8a157d7ec113ebe1a8e2eb71a917f46572d0cc8b035c1ee850d9b10730c','bridge/MANIFEST01.json':'e581f20cb295639283e33ca7bdbe9da811baa4eb14637a656d816eb5ddfe3f1b','postinstall/MANIFEST01.json':'7e82b8c9b70e6dd2582282443894c479d30f965ed0b004395b9ec5d206b3a016','coalesced-review/MANIFEST01.json':'2eb451cc119963749bc6ac3a2edaf089590b900de810625a888216bfe3f14b95','capture-review/MANIFEST01.json':'4a21d4a7853e8386e72b700bca5243415caef1d4c0914c008547977e835ded84','coalesced/MANIFEST01.json':'f6326fbf10f76c378f4070d7be91c2c4013d58dc2a0c64ca7e0da11cade56d6d','coalesced/ORIGINAL_RECOVERY_PROOF01.json':'c5cf38d2a54682e9b36c0d4462cc07a611fb047cc422803b23d590552511b7a5','failed03/FAILED_LOCAL_CAPTURE01.json':'07838977e0d6ec5e2e88c35cdd860d8c478c581ba09ccc9772470b5a618829d0'}
for n,pin in critical.items():ok(sha(payload[n])==pin,'immutable independently accepted or failed artifact '+n)
master=json.loads(payload['delta04/snapshot/CAPSULE_MASTER605.json']);ok(sha(payload['delta04/snapshot/CAPSULE_MASTER605.json'])=='ce012a88a8623faea1c95f0165344932e109ab1e4355551dfd80230214f530b9','accepted current605 master');cm={x['path']:x for x in master['members']};ok(len(cm)==605 and set(census(CAP,('.git',)))==set(cm),'complete current605 namespace')
for n,x in cm.items():
 p=CAP/n;ok(stat.S_IMODE(p.lstat().st_mode)==x['mode'],'current original mode')
 if x['kind']=='file':ok(len(read(p,x['sha256']))==x['bytes'],'full current opaque body')
idx=json.loads(payload['delta04/snapshot/SOURCE_GIT407_METADATA01.json']);ok(sha(payload['delta04/snapshot/SOURCE_GIT407_METADATA01.json'])=='ce48d2c2c54f0beea47617b8da113020fe64e6b0fc86e6eb35a067bd558dc8e3','exact accepted407 index');old394=[x for x in idx['objects'] if x['body_basis']=='accepted-original394-composition'];new13=[x for x in idx['objects'] if x not in old394];ok(len(old394)==394 and len(new13)==13,'unchanged394 plus13 object denominator')
for x in new13:
 b=payload['delta04/snapshot/'+x['body_basis']];ok(sha(b)==x['sha256'] and len(b)==x['bytes'] and hashlib.sha1(x['type'].encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['oid'],'each new13 raw type/framing/OID')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='')
def git(*args):return subprocess.run(['git',*args],cwd=CAP,env=env,check=True,capture_output=True,timeout=15).stdout
ok(git('rev-parse','HEAD').decode().strip()==CURRENT,'actual source HEAD');ok({x.split()[0].decode() for x in git('rev-list','--objects',CURRENT).splitlines()}=={x['oid'] for x in idx['objects']},'actual exact407 reachable set')
q=json.loads(payload['delta04/snapshot/parent/REQUEST_DRAFT01.json']);gate=j(CAP/q['registration'],q['registration_sha256']);e=gate['experiments'][q['identity']];ok(len(e['source_files'])==354 and len(e['inputs'])==11 and set(git('ls-tree','-r','--name-only',CURRENT).decode().splitlines())==set(e['source_files'])|{q['registration']},'355tracked354pins11inputs')
for n,pin in e['source_files'].items():ok(sha(read(CAP/n))==pin,'current registered source pin')
for z in e['inputs'].values():read(CAP/z['path'],z['sha256'])
parentfiles={n.removeprefix('delta04/snapshot/parent/'):b for n,b in payload.items() if n.startswith('delta04/snapshot/parent/')};ok(len(parentfiles)==10 and set(census(PARENT))==set(parentfiles),'complete actual10 Parentdraft')
for n,b in parentfiles.items():ok(read(PARENT/n)==b,'actual exact Parent draft body')
ok(q['status']=='DRAFT_NOT_RELEASED' and q['proofs']['full_recovery'] is None and q['proofs']['independent_source_input_runtime'] is None and q['final_review'] is None and not (PARENT/'REQUEST_FINAL01.json').exists() and not (PARENT/'attempt').exists(),'baseline excludes actual missingfinalauthority')
failed=json.loads(payload['failed03/FAILED_LOCAL_CAPTURE01.json']);ok(failed['actual_exit']==1 and 'failed03/CAPTURE01.json' not in payload,'originalfailed03 remainsfailed');mismatch=[]
oldman=json.loads(payload['failed03/MANIFEST01.json']);fm={x['path']:x for x in scopes['failed03']['members']}
for x in oldman['members']:
 if fm['snapshot/'+x['path']]['mode']!=x['mode']:mismatch.append(x['path']);ok(fm['snapshot/'+x['path']]['mode']==0o775 and x['mode']==0o700,'original775 mismatch literalmetadata')
ok(mismatch==['reviews','source-inputs','source-inputs/fixture_inputs'],'all3 genuine failed modes retained')
for root,(exc,_) in list(trees.items()):census(root,exc)
for p,s in sigs.items():ok(sig(p.lstat())==s,'final complete read fingerprint')
out={'schema_version':1,'status':'INDEPENDENT_ACTUAL_BASELINE_POPULATION_VERIFIED','checks':checks,'distinct_files':len(cache),'bytes_read':total,'elapsed_seconds':time.monotonic()-start,'archive_bytes':len(ar),'snapshot_files':262,'snapshot_typed':303,'snapshot_logical_bytes':10739552,'original_file_origins':260,'scope_stats':scope_stats,'empty_original_directories_retained_as_metadata':empty,'current605':605,'current_files':sum(x['kind']=='file' for x in cm.values()),'reachable_git407':407,'old394_basis_reused_exactly':True,'new13_framing_checked':True,'source':CURRENT,'tracked':355,'source_pins':354,'inputs':11,'parent_files':10,'failed03_mode_mismatches':mismatch,'actual_root_terminal':terminal,'actual_external_recovery':None,'numerical_authority':False}
(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['scope_stats','actual_root_terminal','empty_original_directories_retained_as_metadata']}))
