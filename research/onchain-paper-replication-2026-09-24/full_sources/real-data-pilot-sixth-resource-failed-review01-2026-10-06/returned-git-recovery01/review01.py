"""One tiny returned archive read and offline bare-Git object authentication."""
from pathlib import Path
import hashlib,io,json,os,stat,subprocess,tarfile
R=Path.cwd();F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
P=F/'real-data-pilot-sixth-resource-failed-review01-2026-10-06';H=P/'returned-git-recovery01'
CAP=F/'real-data-pilot-sixth-resource-failed-increment01-2026-10-06'
N='eth-paper-real-data-end-to-end-resource-20261006-06'
SOURCE='137bb3110862e04653cd17fccf2c6913b878fcb5'
ORIGINAL=CAP/'failed-increment01.tar';RETURNED=CAP/'fresh-git-recovered-increment01.tar'
cache={};counts={}
def raw(p):
 p=Path(p);assert p!=ORIGINAL
 if p not in cache:
  q=R/p;s=q.lstat();assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=q.read_bytes();z=q.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);cache[p]=b;counts[str(p)]=counts.get(str(p),0)+1
 return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(n,v):
 p=H/n
 with p.open('x') as f:f.write(json.dumps(v,sort_keys=True,indent=2)+'\n')
 return p
assert sha(P/'INCREMENT_SELECTION01.json')=='cc6773445c65f2d243687313c701c53a3e35e6182fc3231785e86cc59973718e'
assert sha(P/'OUTCOME_REVIEW01.json')=='756f4761d1d8e053088abd085b805083dab9defe8aa2a42c77d9e6c372a9b6c7'
selection=read(P/'INCREMENT_SELECTION01.json');capture=read(CAP/'CAPTURE01.json');fresh=read(CAP/'FRESH_GIT_RECOVERY01.json')
assert selection['decision']=='accepted' and selection['regular_count']==23 and selection['directory_count']==5 and selection['original_regular_bytes']==149774
assert capture['selection']==ref(P/'INCREMENT_SELECTION01.json') and capture['regular_file_count']==23 and capture['directory_count']==5 and capture['typed_member_count']==28
assert capture['archive']==fresh['archive'] and fresh['archive']['path']==str(ORIGINAL)
assert fresh['source']==fresh['actual_remote_head']==SOURCE and fresh['push_exit']==0 and fresh['push_session']==99555 and fresh['push_terminal_chunk']=='063c72'
assert fresh['selected_regular_files']==23 and fresh['selected_directories']==5 and fresh['selected_regular_bytes']==149774
assert fresh['recovered_archive']['path']==str(RETURNED) and fresh['recovered_archive']['bytes']==fresh['archive']['bytes']==204800
bare=Path(fresh['fresh_bare_repository'])
assert bare==Path('/home/malecada/master_thesis/onchain-pilot-recovery/real-pilot-sixth-resource-failed-20261006-01.git') and bare.resolve(strict=True)==bare
assert not (bare/'objects/info/alternates').exists() and not (bare/'objects/info/http-alternates').exists()
ops=fresh['operations'];assert len(ops)==7 and all(o['returncode']==0 for o in ops)
assert ops[0]['command']==['git','ls-remote','git@github.com:malecada/TradingAgents.git','refs/heads/research/onchain-paper-replication-2026-09-24']
ops=ops[1:]
assert ops[0]['command']==['git','init','--bare',str(bare)]
assert ops[1]['command']==['git','-C',str(bare),'remote','add','origin','git@github.com:malecada/TradingAgents.git']
assert ops[4]['command']==['git','-C',str(bare),'fetch','--depth=1','--filter=blob:none','origin',SOURCE]
assert ops[5]['command']==['git','-C',str(bare),'cat-file','blob',SOURCE+':'+str(ORIGINAL)] and ops[5]['stdout_bytes']==204800
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
env.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_TERMINAL_PROMPT='0')
git_checks=[]
def git(*args):
 r=subprocess.run(['git','--git-dir='+str(bare),*args],env=env,check=True,capture_output=True)
 git_checks.append({'args':list(args),'returncode':r.returncode,'stdout':r.stdout.decode().strip()})
 return r.stdout
assert git('rev-parse','--is-bare-repository').strip()==b'true'
assert git('rev-parse','FETCH_HEAD').strip().decode()==SOURCE
assert git('config','--get','remote.origin.url').strip()==b'git@github.com:malecada/TradingAgents.git'
tree=git('ls-tree','-z',SOURCE,'--',str(ORIGINAL)).rstrip(b'\0')
header,path=tree.split(b'\t');mode,kind,oid=header.split()
assert path.decode()==str(ORIGINAL) and kind==b'blob' and mode in (b'100644',b'100755')
assert git('cat-file','-t',oid.decode()).strip()==b'blob' and git('cat-file','-s',oid.decode()).strip()==b'204800'
b=raw(RETURNED)
assert len(b)==204800 and hashlib.sha256(b).hexdigest()==fresh['recovered_archive']['sha256']==fresh['archive']['sha256']=='e836983bd3e8432cce448e87c8c8b2e32c3ccb25f2fc600f7c99792426a406d9'
assert len(oid)==40 and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode()
expected={v['path']:v for v in selection['files']+selection['directories']};assert len(expected)==28
for v in selection['files']:
 p=Path(v['path']);s=p.lstat();assert (R/p).resolve(strict=True)==R/p and stat.S_ISREG(s.st_mode) and s.st_nlink==v['nlink']==1
 assert stat.S_IMODE(s.st_mode)==v['mode'] and v['stat_identity']==[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for v in selection['directories']:
 p=Path(v['path']);s=p.lstat();assert (R/p).resolve(strict=True)==R/p and stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==v['mode']
members=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:') as tf:
 seen=set()
 for m in tf.getmembers():
  p=m.name.rstrip('/');assert p in expected and p not in seen and not Path(p).is_absolute() and '..' not in Path(p).parts;seen.add(p);v=expected[p];assert m.mode==v['mode']
  if v['kind']=='directory':assert m.isdir() and m.size==0;members.append({'path':p,'kind':'directory','mode':m.mode})
  else:
   assert m.isfile() and not m.issym() and not m.islnk() and m.size==v['bytes']
   with tf.extractfile(m) as stream:body=stream.read(m.size+1)
   digest=hashlib.sha256(body).hexdigest();assert len(body)==m.size and digest==v['sha256']
   members.append({'path':p,'kind':'regular','mode':m.mode,'bytes':m.size,'sha256':digest})
 assert seen==set(expected)
assert sum(v.get('bytes',0) for v in members)==149774 and counts[str(RETURNED)]==1 and str(ORIGINAL) not in counts
mp=write('RECOVERED_MEMBERS01.json',{'schema_version':1,'decision':'accepted','identity':N,'returned_archive':ref(RETURNED),'source':SOURCE,'bare_git_blob_oid':oid.decode(),'regular_count':23,'directory_count':5,'total_names':28,'unpacked_regular_bytes':149774,'returned_archive_streams':1,'original_archive_streams':0,'members':members})
evidence={str(p):hashlib.sha256(v).hexdigest() for p,v in cache.items()};evidence[str(mp)]=sha(mp)
rp=write('RECOVERY_REVIEW01.json',{'schema_version':1,'decision':'accepted','identity':N,'recovery_source_commit':SOURCE,'evidence':dict(sorted(evidence.items())),
 'scope':'Complete public06 failed-resource increment BYTE recovery via fresh external Git fetch and recovered archive;23 regular files totaling 149774 bytes plus 5 typed directories, 28 names in204800-byte tar.',
 'fresh_fetch_evidence':ref(CAP/'FRESH_GIT_RECOVERY01.json'),'bare_repository':str(bare),'current_alternates_absent':True,'offline_git_checks':git_checks,'git_lazy_fetch_disabled':True,
 'archive':{'sha256':sha(RETURNED),'bytes':204800,'git_blob_oid':oid.decode(),'tree_source_commit':SOURCE,'returned_path':str(RETURNED),'returned_archive_streams':1,'original_archive_streams':0,'members_review':ref(mp)},
 'original_selected_stat_identities_currently_unchanged':True,'actual_external_recovery_accepted':True,
 'external_provenance_basis':'Recorded successful fresh bare init/external SSH Git fetch/blob recovery and remote HEAD equality; independently confirmed present bare object/tree identity without network or lazy fetch. Returned archive Git object SHA1 and SHA256 computed from its sole body read.',
 'original_outcome':ref(P/'OUTCOME_REVIEW01.json'),'originals_retained':True,'recovered_archive_retained':True,'deletion_authorized':False,
 'qualification':'BYTE/member/name/mode acceptance covers only this exact public failed-resource increment. No POSIX ownership/timestamps/xattrs reconstruction, installed runtime/raw/graph/private/unrelated-store recovery, future remote availability or scientific credit. Original06 genuine claim77 remains permanently FAILED/spent; all original nulls and unavailable cells retained. Existing02 namespace remains untouched.',
 'not_tested':['No transport/native/network replay, fresh fetch, historical body stream, original tar read, extraction or deletion.','No numerical/scientific/raw/runtime/private body read or financial correctness/capacity claim.','External origin history relies on preserved actual fetch record; current offline bare state does not reconstruct historical process lifetime.']})
manifest=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':N,'files':[ref(H/'review01.py'),ref(mp),ref(rp)]})
print(json.dumps({'review':ref(rp),'manifest':ref(manifest),'members':ref(mp),'decision':'accepted','blob_oid':oid.decode()},sort_keys=True))
