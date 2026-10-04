"""Fixed-source opaque preservation preparation. No empirical authority."""
import argparse,json,os,stat,shutil
from pathlib import Path
import recovery04 as R
from bounded_git01 import git
H=Path(__file__).resolve().parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source')
SCOPE=CAP.parent.parent
SOURCE='649fb8a11089524aaef7843dffeeb90a3a55ca17'
GATE='fixture_inputs/financial_wrapper_recordfix01/gates.json'
GATEHASH='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a'
ADOPTION='c08c065d3366441e94ae237cceab3fc35a1e83981f87e63a2e7085eab8523dc6'
ORIGINAL='81f48355e3ea73ab085f14488656ab21d78a535c30914e3d36860c7266728108'
IDENTITY='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'
require=R.require

def floor(root):
 free=shutil.disk_usage(root).free;require(free>=R.FLOOR,'10GiB disk floor');return free

def reference(ref):
 require(type(ref)is dict and set(ref)=={'path','sha256'},'exact proof reference');p=Path(ref['path']);require(p.is_absolute() and p.resolve()==p,'proof canonical');raw=R.read(p.parent,p.name);require(R.digest(raw)==ref['sha256'],'proof bytes changed');return raw

def contract(q):return R.digest(R.encode({k:v for k,v in q.items() if k!='release'}))

def validate_request(q):
 require(type(q)is dict and set(q)=={'schema_version','source','capsule_root','output_root','manifest','manifest_sha256','source_review','review_manifest','release'},'capture request schema')
 require(type(q['schema_version'])is int and q['schema_version']==1 and q['source']==SOURCE and q['capsule_root']==str(CAP),'fixed actual source')
 for k in ('output_root','manifest','manifest_sha256','source_review','review_manifest','release'):require(q[k] is not None,'unreleased '+k)
 R.validate(q['manifest']);require(R.digest(R.encode(q['manifest']))==q['manifest_sha256'],'manifest pin')
 out=Path(q['output_root']);require(out.parent==SCOPE and out.resolve()==out and out.name.startswith('financial-recordfix-source-capture-') and not os.path.lexists(out),'fresh disjoint capture identity')
 require(q['source_review']['sha256']=='905e757c255b63c52358b4edac05456117f24ea89b1e21cbe0233b4fd2152202' and q['review_manifest']['sha256']=='4f39700328879e71749e31e230b7d273b36ad29783a601e483ff8a26ccd9c72f','exact actual independent source review pins')
 body=reference(q['source_review']);mr=reference(q['review_manifest']);m=json.loads(mr)
 review=json.loads(body);require(review['decision']=='ACCEPTED_ACTUAL_CORRECTED_SOURCE_AND_READONLY_ADMISSION_ONLY' and review['source']==review['design_source']==SOURCE and review['actual_ready'] is True and review['adoption_sha256']==ADOPTION,'actual independent source/admission acceptance')
 # Actual review schema is authenticated by final release; its body must be a
 # member of its actual complete independent manifest, not a synthetic receipt.
 rows=m['members'];name=Path(q['source_review']['path']).name
 require(sum(r.get('path')==name and r.get('sha256')==R.digest(body) and r.get('bytes')==len(body) and r.get('kind')=='file' for r in rows)==1,'independent review body membership')
 release=json.loads(reference(q['release']))
 require(release=={'schema_version':1,'decision':'accepted-exact-recordfix-source-capture','contract_sha256':contract(q),'source':SOURCE,'source_review_sha256':R.digest(body),'review_manifest_sha256':R.digest(mr),'helper_sha256':R.digest(R.read(H,'capture01.py'))},'independent exact preservation release')
 return out

def authenticate():
 raw=R.read(H,'SOURCE_ADOPTION01.json');require(R.digest(raw)==ADOPTION,'adoption pin');ad=json.loads(raw)
 require(ad['root']==str(CAP) and ad['source']==ad['design_source']==SOURCE and ad['implementation']==194 and ad['package']==149 and ad['implementation_changed']==1 and ad['implementation_unchanged']==193,'actual source adoption')
 require(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'source HEAD changed')
 gate=R.read(CAP,GATE);require(R.digest(gate)==GATEHASH==ad['registration_sha256'],'current gate');g=json.loads(gate);exp=g['experiments'][IDENTITY];pins=exp['source_files']
 require(pins==ad['source_files'] and len(pins)==324 and GATE not in pins,'actual324 source pins')
 tree=git(CAP,['ls-tree','-rz',SOURCE]);entries={}
 for item in tree.split(b'\0'):
  if not item:continue
  meta,path=item.split(b'\t');mode,kind,oid=meta.decode().split();path=path.decode();R.path_name(path);require(kind=='blob' and mode in ('100644','100755') and path not in entries,'Git type/mode/path');entries[path]=(mode,oid)
 require(set(entries)==set(pins)|{GATE} and len(entries)==325,'actual complete325 tracked')
 # Batch exact committed body/OID framing and verify current mode/body.
 ordered=sorted(entries)
 for start in range(0,len(ordered),32):
  names=ordered[start:start+32];raw=git(CAP,['cat-file','--batch'],''.join(SOURCE+':'+n+'\n' for n in names).encode());offset=0
  for n in names:
   end=raw.index(b'\n',offset);oid,kind,size=raw[offset:end].decode().split();size=int(size);require(0<=size<=R.FILE and kind=='blob' and oid==entries[n][1],'Git object framing');body=raw[end+1:end+1+size];require(raw[end+1+size:end+2+size]==b'\n','Git body tail');offset=end+2+size
   current=R.read(CAP,n);require(body==current and R.digest(body)==(GATEHASH if n==GATE else pins[n]),'committed/current source pin');require(bool((CAP/n).stat().st_mode&0o111)==(entries[n][0]=='100755'),'current Git executable mode')
  require(offset==len(raw),'Git batch tail')
 raw=R.read(H,'MODE_QUALIFICATION02.json');require(R.digest(raw)=='45d00d1534d772cf6759690e60071a8aa0127aca1ef9cc71bf765c098f2a65cb','actual mode qualification pin');modes=json.loads(raw)['rows']
 require(len(modes)==325 and len({r['path'] for r in modes})==325 and {r['path'] for r in modes}==set(entries),'complete mode qualification')
 for row in modes:
  n=row['path'];require(stat.S_IMODE((CAP/n).lstat().st_mode)==row['actual_posix_mode'] and entries[n][0]==row['git_mode'] and row['sha256']==(GATEHASH if n==GATE else pins[n]),'actual POSIX/Git mode qualification')
 require(len(exp['inputs'])==8,'eight roles')
 for ref in exp['inputs'].values():require(ad['role_hashes'][ref['path']]==ref['sha256']==R.digest(R.read(CAP,ref['path'])),'exact role body')
 def role(n):return json.loads(R.read(CAP,exp['inputs'][n]['path']))
 closure=role('source_closure')['installed'];raw=R.read(H,'ORIGINAL_CLOSURE01.json');require(R.digest(raw)==ORIGINAL,'original194 closure pin');old=json.loads(raw)['installed'];changed=[n for n in old if old[n]!=closure.get(n)]
 require(set(old)==set(closure) and len(old)==194 and sum(n.startswith('tradingagents/') for n in closure)==149 and changed==['tradingagents/research/onchain_replication/financial_wrapper_fixture.py'],'exact194/149/one change')
 require(all(pins[n]==v for n,v in closure.items()),'implementation pins')
 runtime=role('runtime_mapping');require(len(runtime['distribution_records'])==251,'251 runtime metadata pins')
 return {'source':SOURCE,'tracked':325,'selected':324,'implementation':194,'package':149,'changed':changed,'runtime_record_metadata_count':251,'role_hashes':ad['role_hashes'],'git_entries':entries,'runtime_bodies_captured':False}

def reserve(out):
 fd=None
 try:
  parent=out.parent;require(parent.resolve()==parent,'output parent canonical');fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);s=os.fstat(fd)
  require((s.st_dev,s.st_ino)==(parent.lstat().st_dev,parent.lstat().st_ino) and parent.resolve()==parent,'output parent changed before creation')
  os.mkdir(out.name,0o700,dir_fd=fd)
  require(out.resolve()==out and (s.st_dev,s.st_ino)==(parent.lstat().st_dev,parent.lstat().st_ino),'output parent changed');os.fsync(fd)
 finally:R._cleanup(() if fd is None else (lambda:os.close(fd),))

def capture(q):
 out=validate_request(q);floors=[floor(CAP)];auth=authenticate();R.same(CAP,q['manifest']);floors.append(floor(CAP));reserve(out);primary=None;archive=None
 try:
  R.put(out/'request.json',q);R.put(out/'source-manifest.json',q['manifest']);R.put(out/'source-authentication.json',auth)
  floors.append(floor(CAP));archive=R.pack(CAP,q['manifest'],out/'source.tar.gz');floors.append(floor(CAP));require(authenticate()==auth,'source authentication changed');R.same(CAP,q['manifest'])
 except BaseException as e:primary=e
 finally:
  def terminal():R.put(out/'terminal.json',{'status':'FAILED' if primary else 'COMPLETE_BYTES_ONLY','error_type':None if primary is None else type(primary).__name__,'source':SOURCE,'archive':archive,'observed_free_bytes':floors,'external_recovery':False,'runtime_bodies':False,'scientific_credit':0})
  R._cleanup((terminal,),primary=primary)
 if primary is not None:raise primary
 return archive

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--request',type=Path,required=True);a.add_argument('--sha256',required=True);ns=a.parse_args();raw=R.read(ns.request.parent.resolve(),ns.request.name);require(R.digest(raw)==ns.sha256,'request changed');print(json.dumps(capture(json.loads(raw)),sort_keys=True))
