"""One exact Source339 flat recovery, solely from an authenticated remote recovery."""
import argparse,hashlib,json,os,shutil,stat,sys,time
from pathlib import Path
import recovery04 as R
from git_objects01 import tree_join,claim_join
H=Path(__file__).resolve().parent
SOURCE='0a2e7639b42b9423b90743feadcda4078aa21816'
REL='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04'
GATE='fixture_inputs/financial_wrapper_claimedrun01/gates.json'
GATEHASH='3a20293832fa7ecc5e2821fb27dc940d1a997ab7f2ad373bc28f73e893e8781a'
IDENTITY='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
PINS['git_objects01.py']='c364269be9c112dbc9501a41c8f9cf21def9a95b33cf2b9054f4384ae3888a4a'
for n,pin in PINS.items():R.require(R.digest(R.read(H,n))==pin,'exact R4 primitive')
_pins=R.read(H,'CAPTURE_PINS01.json');R.require(R.digest(_pins)=='355a876341a21e6d4fa97ad11371805d6e93acd2ef4766e7f547d6c8c9f1fba1','fixed actual capture pins');EXPECTED=json.loads(_pins)

def ref(value):
 R.require(type(value)is dict and set(value)=={'path','sha256'},'exact external proof');p=Path(value['path']);raw=R.read(p.parent,p.name);R.require(R.digest(raw)==value['sha256'],'proof changed');return raw

def validate_request(q):
 R.require(type(q)is dict and set(q)=={'schema_version','source','remote_root','remote_receipt_sha256','review','release'},'request schema')
 R.require(type(q['schema_version'])is int and q['schema_version']==1 and q['source']==SOURCE,'fixed Source339')
 for k in ('remote_root','remote_receipt_sha256','review','release'):R.require(q[k] is not None,'unreleased '+k)
 root=Path(q['remote_root']);R.require(root.is_absolute() and root.resolve()==root,'actual remote root canonical')
 review=ref(q['review']);release=json.loads(ref(q['release']))
 R.require(release=={'decision':'accepted-exact-claimedrun-source339-flat-recovery','source':SOURCE,'helper_sha256':R.digest(R.read(H,'restore01.py')),'request_sha256':R.digest(R.encode({k:v for k,v in q.items() if k!='release'})),'review_sha256':R.digest(review)},'exact independent release')
 return root

def remote_bodies(root,pin):
 raw=R.read(root,'REMOTE_RECOVERY01.json');R.require(R.digest(raw)==pin,'actual remote receipt pin');receipt=json.loads(raw)
 R.require(receipt['status']=='fresh-actual-remote-recordfix-source325-recovered' and receipt['genuine_run_or_native_started'] is False,'corrected byte-only remote recovery')
 rows=receipt['selected_blobs'];R.require(type(rows)is list and 1<=len(rows)<=506 and len({r['path'] for r in rows})==len(rows),'finite remote denominator')
 selected={r['path']:r for r in rows};bundle=root/'selected'/REL;body={}
 for n,pin in EXPECTED.items():
  row=selected[REL+'/'+n];raw=R.read(bundle,n);R.require(len(raw)==row['bytes']==pin['bytes'] and R.digest(raw)==row['sha256']==pin['sha256'] and row['git_mode'] in ('100644','100755'),'actual remote body/size/mode joins')
  R.require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_object'],'actual remote Git blob OID');body[n]=raw
 return bundle,body,receipt

def joins(body):
 m=json.loads(body['source-manifest.json']);R.validate(m);t=json.loads(body['CAPTURE01.json'])
 R.require(R.encode(m)==body['source-manifest.json'] and len(m['members'])==1029 and sum(r['kind']=='file' for r in m['members'])==747 and sum(r.get('bytes',0) for r in m['members'])==9692681,'whole actual Source339 denominator')
 R.require(t['status']=='ACTUAL_COMPLETE_SOURCE339_BYTE_CAPTURE_NOT_EXTERNAL_OR_RELEASE' and t['current_equals_design']==SOURCE and t['tracked']==339 and t['registered_pins']==338 and t['input_roles']==8 and t['original_spent_claims']==1 and t['new_claim_started'] is False and t['parent_or_final_review_captured'] is False,'actual capture qualification')
 R.require(t['archive']==dict(EXPECTED['source.tar.gz'],manifest_sha256=EXPECTED['source-manifest.json']['sha256']) and t['disk_free_after_bytes']>=R.FLOOR,'actual archive/floor')
 return m,None,t

def flat_source_joins(destination,result,m,a):
 metadata=json.loads(R.read(destination,result['metadata_file']));R.require(R.digest(R.encode(metadata))==result['metadata_sha256'] and metadata['manifest']==m,'complete flat metadata')
 mapping=metadata['flat_members'];R.require(len(mapping)==747 and set(mapping)=={r['path'] for r in m['members'] if r['kind']=='file'},'all747 recovered bodies')
 def raw(n):return R.read(destination,mapping[n])
 modes={r['path']:r['mode'] for r in m['members'] if r['kind']=='file'}
 repo,tracked=tree_join(raw,set(mapping),SOURCE,339,manifest_modes=modes)
 head=raw('.git/HEAD').decode('ascii').strip()
 if head.startswith('ref: '):
  refname=head[5:];R.require(refname.startswith('refs/heads/') and all(part not in ('','.','..') for part in refname.split('/')),'canonical archived HEAD ref')
  path='.git/'+refname
  if path in mapping:head=raw(path).decode('ascii').strip()
  else:
   refs={}
   for line in raw('.git/packed-refs').decode('ascii').splitlines():
    if not line or line.startswith(('#','^')):continue
    oid,name=line.split(' ',1);R.require(name not in refs,'duplicate packed ref');refs[name]=oid
   head=refs[refname]
 R.require(head==SOURCE,'actual recovered source HEAD')
 gate=raw(GATE);R.require(R.digest(gate)==GATEHASH,'actual gate');reg=json.loads(gate);exp=reg['experiments'][IDENTITY];pins=exp['source_files']
 R.require(len(pins)==338 and set(pins)|{GATE}==set(tracked),'complete source339/338')
 for n,pin in pins.items():R.require(R.digest(raw(n))==pin,'selected body')
 R.require(len(exp['inputs'])==8,'eight roles')
 for ref in exp['inputs'].values():R.require(R.digest(raw(ref['path']))==ref['sha256'],'input hash')
 closure=json.loads(raw(exp['inputs']['source_closure']['path']));R.require(len(closure['installed'])==194 and sum(n.startswith('tradingagents/') for n in closure['installed'])==149,'194/149 implementation')
 for n,pin in closure['installed'].items():R.require(pins[n]==pin,'implementation pin')
 R.require(closure['installed']['tradingagents/research/onchain_replication/financial_wrapper_fixture.py']=='f4ea651b4677c83f8e16c316d17f704d44d9ec86ff78a4bf7c4b895e92e1a16e','claimed-run correction')
 runtime=json.loads(raw(exp['inputs']['runtime_mapping']['path']));R.require(len(runtime['distribution_records'])==251,'runtime metadata only')
 old='research_runs/financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01/'
 for name,pin in {'claim.json':'4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','failed.json':'35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450'}.items():R.require(R.digest(raw(old+name))==pin,'original failed history')
 R.require(old+'complete.json' not in mapping and 'research_runs/'+IDENTITY+'/claim.json' not in mapping,'no replacement or new claim')
 historical=claim_join(repo,json.loads(raw(old+'claim.json')))
 return {'recovered_commit_ancestry_count':len(repo.commits),'historical_claim_source_joins':historical,'tracked_git_commit_tree_blob_joins':339,'selected_body_joins':338,'inputs':8,'recovered_regular_bodies':747,'private_flat_files_with_metadata':748,'posix_tree_instantiated':False,'historical_failed_claims':1,'new_claims':0,'parent_or_final_review_recovered':False}

def reserve(p):
 fd=None
 try:
  R.require(p.parent.resolve()==p.parent,'canonical output parent');fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);s=os.fstat(fd);key=(s.st_dev,s.st_ino,s.st_mode)
  def check():
   t=p.parent.lstat();R.require(p.parent.resolve()==p.parent and key==(t.st_dev,t.st_ino,t.st_mode),'output parent changed')
  check();os.mkdir(p.name,0o700,dir_fd=fd);check();R.require(p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==0o700,'private fresh target');os.fsync(fd)
 finally:R._cleanup(() if fd is None else (lambda:os.close(fd),))

def run(q):
 R.require(H.name=='financial-genuine-wrapper-claimedrun-source339-flat-20261004-01','fixed Root-installed fresh flat scope');root=validate_request(q);R.require(not any(os.path.lexists(H/n) for n in ['INTENT01.json','flat-source01','RECOVERY01.json','FAILED01.json']),'one-use flat namespace');floors=[]
 def floor():
  free=shutil.disk_usage(H).free;R.require(free>=R.FLOOR,'10GiB floor');floors.append(free)
 floor();bundle,body,receipt=remote_bodies(root,q['remote_receipt_sha256']);m,a,t=joins(body)
 R.put(H/'INTENT01.json',{'pid':os.getpid(),'source':SOURCE,'remote_receipt_sha256':q['remote_receipt_sha256'],'native_started':False});primary=None;result=None;begun=time.monotonic()
 try:
  floor();destination=H/'flat-source01';reserve(destination);result=R.restore(bundle/'source.tar.gz',t['archive'],m,destination);floor();source_joins=flat_source_joins(destination,result,m,a);floor()
  R.put(H/'RECOVERY01.json',{'status':'actual-claimedrun-source339-fresh-flat-recovered','source':SOURCE,'actual':result,'joins':source_joins,'remote_receipt_sha256':q['remote_receipt_sha256'],'disk_floor_observations':floors,'elapsed_seconds':time.monotonic()-begun,'original_capture_pid_observed':False,'runtime_bodies':False,'empirical_stores':False,'numerical_credit':0,'release_of_numerical_work':False})
 except BaseException as e:primary=e
 finally:
  def failure():
   if primary is not None:R.put(H/'FAILED01.json',{'status':'FAILED_RETAINED','error_type':type(primary).__name__,'source':SOURCE,'partial_restore':result,'disk_floor_observations':floors})
  R._cleanup((failure,),primary=primary)
 if primary is not None:raise primary
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);n=p.parse_args();raw=R.read(n.request.parent.resolve(),n.request.name);R.require(R.digest(raw)==n.sha256,'exact request');print(json.dumps(run(json.loads(raw)),sort_keys=True))
