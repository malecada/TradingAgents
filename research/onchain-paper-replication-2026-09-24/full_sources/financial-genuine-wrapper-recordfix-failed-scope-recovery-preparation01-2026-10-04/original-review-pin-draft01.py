"""Exact permanently failed Source/Parent/outer byte recovery. No execution authority."""
import argparse,hashlib,json,os,shutil,stat
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent
BASE=H.parent
REL='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-recordfix-failed-scope-capture01-2026-10-04'
SOURCE='649fb8a11089524aaef7843dffeeb90a3a55ca17'
IDENTITY='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'
CAPTURE_HASH='37c3f6b064b005398535c8b49636ef4e9190dd508d29200034c81823b699786c'
CAPTURE_REVIEW='a3aa7bd14e2e5afc6aa731980f9bcebedbbd160b61d1de1e01a2fb21e6aa277e19'
COUNTS={'source':(1011,730),'parent':(33,28),'outer':(5,5)}
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for n,pin in PINS.items():R.require(R.digest(R.read(H,n))==pin,'exact accepted primitive')
raw=R.read(H,'CAPTURE_PINS01.json');R.require(R.digest(raw)=='dbbbc25bb69cd5a4ec01ccc1270cd9980f8c995bdca77c5e004aa91a465eea68','fixed capture roles');EXPECTED=json.loads(raw)

def ref(v):
 R.require(type(v)is dict and set(v)=={'path','sha256'},'exact proof reference');p=Path(v['path']);raw=R.read(p.parent,p.name);R.require(R.digest(raw)==v['sha256'],'proof changed');return raw

def contract(q):return R.digest(R.encode({k:v for k,v in q.items() if k!='release'}))

def request(q):
 R.require(type(q)is dict and set(q)=={'schema_version','remote_root','remote_receipt_sha256','capture_review_manifest','review','release','output_root'} and type(q['schema_version'])is int and q['schema_version']==1,'exact failed-scope request')
 for k,v in q.items():R.require(v is not None,'draft-not-released '+k)
 remote=Path(q['remote_root']);out=Path(q['output_root']);R.require(remote.is_absolute() and remote.resolve()==remote,'actual remote root')
 R.require(out.parent==BASE and out.resolve()==out and out.name.startswith('financial-genuine-wrapper-recordfix-failed-scope-flat-') and not os.path.lexists(out),'fresh fixed output scope')
 R.require(not out.is_relative_to(remote) and not remote.is_relative_to(out),'remote/output overlap')
 R.require(q['capture_review_manifest']['sha256']==CAPTURE_REVIEW,'actual independent local capture acceptance pin');ref(q['capture_review_manifest'])
 review=ref(q['review']);release=json.loads(ref(q['release']))
 R.require(release=={'schema_version':1,'decision':'accepted-exact-one-use-recordfix-failed-scope-flat','contract_sha256':contract(q),'helper_sha256':R.digest(R.read(H,'restore01.py')),'review_sha256':R.digest(review),'capture_sha256':CAPTURE_HASH},'exact independent release')
 return remote,out

def remote_bodies(remote,pin):
 raw=R.read(remote,'REMOTE_RECOVERY01.json');R.require(R.digest(raw)==pin,'actual remote receipt');receipt=json.loads(raw)
 R.require(receipt['status']=='fresh-actual-remote-recordfix-source325-recovered' and receipt['genuine_run_or_native_started'] is False,'actual accepted transport status')
 rows=receipt['selected_blobs'];R.require(type(rows)is list and 1<=len(rows)<=506 and len({r['path'] for r in rows})==len(rows) and receipt['selected_count']==len(rows),'complete remote selected denominator');index={r['path']:r for r in rows};bodies={};bundle=remote/'selected'/REL
 for n,p in EXPECTED.items():
  row=index[REL+'/'+n];body=R.read(bundle,n);R.require(len(body)==row['bytes']==p['bytes'] and R.digest(body)==row['sha256']==p['sha256'] and row['git_mode'] in ('100644','100755'),'exact remote captured body')
  R.require(hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==row['git_object'],'actual remote Git blob OID');bodies[n]=body
 return bundle,bodies

def joins(bodies):
 R.require(R.digest(bodies['CAPTURE01.json'])==CAPTURE_HASH,'immutable actual capture');c=json.loads(bodies['CAPTURE01.json']);ms={}
 R.require(c['status']=='COMPLETE_FAILED_SCOPE_BYTES_ONLY' and c['source_commit']==SOURCE and c['identity']==IDENTITY and c['actual_native_exit']==1 and c['genuine_failed_spent_claims']==1 and c['highest_actual_budget']==18 and c['planned_checkpoint_present'] is False,'permanent actual failed/spent disposition')
 R.require(c['claim_sha256']=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128' and c['failed_sha256']=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','original claim/failure pins')
 R.require(set(c['archives'])==set(COUNTS),'exact three roles')
 for role,(typed,files) in COUNTS.items():
  raw=bodies[role+'-manifest.json'];m=json.loads(raw);R.validate(m);R.require(R.encode(m)==raw,'canonical role manifest');p=EXPECTED[role+'.tar.gz'];R.require(c['archives'][role]==dict(p,manifest_sha256=R.digest(raw)) and R.digest(raw)==EXPECTED[role+'-manifest.json']['sha256'],'actual archive/manifest lineage')
  R.require(len(m['members'])==c['typed_members'][role]==typed and sum(r['kind']=='file' for r in m['members'])==c['regular_members'][role]==files and sum(r.get('bytes',0) for r in m['members'])==c['logical_bytes'][role],'complete original role denominator');ms[role]=m
 R.require(sum(c['logical_bytes'].values())<=R.BASE,'finite combined logical baseline')
 return c,ms

def reserve(p):
 fd=None
 try:
  R.require(p.parent.resolve()==p.parent,'canonical output parent');fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);s=os.fstat(fd);key=(s.st_dev,s.st_ino,s.st_mode)
  def check():
   t=p.parent.lstat();R.require(p.parent.resolve()==p.parent and key==(t.st_dev,t.st_ino,t.st_mode),'output parent changed')
  check();os.mkdir(p.name,0o700,dir_fd=fd);check();R.require(p.resolve()==p and stat.S_IMODE(p.stat().st_mode)==0o700,'private fresh target');os.fsync(fd)
 finally:R._cleanup(() if fd is None else (lambda:os.close(fd),))

def recovered_metadata(root,result,m):
 value=json.loads(R.read(root,result['metadata_file']));R.require(R.digest(R.encode(value))==result['metadata_sha256'] and value['manifest']==m and set(value['flat_members'])=={r['path'] for r in m['members'] if r['kind']=='file'},'exact complete role recovery metadata');return value

def outcome_joins(out,results,ms,c):
 maps={r:recovered_metadata(out/('flat-'+r),results[r],ms[r])['flat_members'] for r in COUNTS}
 def body(role,n):return R.read(out/('flat-'+role),maps[role][n])
 base='research_runs/'+IDENTITY
 R.require(R.digest(body('source',base+'/claim.json'))==c['claim_sha256'] and R.digest(body('source',base+'/failed.json'))==c['failed_sha256'] and base+'/complete.json' not in maps['source'],'genuine failed claim preserved')
 parent=json.loads(body('parent','attempt/parent-terminal.json'));outer=json.loads(body('outer','ACTUAL_TERMINAL01.json'))
 R.require(parent['actual_parent_exit'] is None and parent['actual_child_exit']==1 and outer['actual_exit']==1 and outer['original_parent_self_exit'] is None and outer['genuine_claim_present'] is True and outer['planned_interrupt_checkpoint_achieved'] is False,'original null/separate actual failed exits')
 R.require(outer['claim_sha256']==c['claim_sha256'] and outer['failed_sha256']==c['failed_sha256'] and outer['spent_numerical_engineering_claims']==1 and outer['effective_budget']==18,'Root failed accounting retained')
 return {'typed_members':1049,'regular_bodies':763,'role_metadata_files':3,'original_parent_self_exit':None,'separate_actual_exit':1,'genuine_failed_spent_claims':1,'budget':18,'planned_checkpoint_present':False}

def run(q):
 remote,out=request(q);floors=[]
 def floor():
  n=shutil.disk_usage(BASE).free;R.require(n>=R.FLOOR,'10GiB floor');floors.append(n)
 floor();bundle,bodies=remote_bodies(remote,q['remote_receipt_sha256']);c,ms=joins(bodies);R.same(Path(c['source_roots']['source']),ms['source']);floor();reserve(out);primary=None;results={}
 try:
  R.put(out/'request.json',q);R.put(out/'INTENT01.json',{'pid':os.getpid(),'capture_sha256':CAPTURE_HASH,'remote_receipt_sha256':q['remote_receipt_sha256'],'roles':list(COUNTS),'numerical_authority':False})
  for role,m in ms.items():
   floor();dest=out/('flat-'+role);reserve(dest);results[role]=R.restore(bundle/(role+'.tar.gz'),c['archives'][role],m,dest);floor();recovered_metadata(dest,results[role],m)
  joined=outcome_joins(out,results,ms,c);R.same(Path(c['source_roots']['source']),ms['source']);R.require(remote_bodies(remote,q['remote_receipt_sha256'])[1]==bodies,'remote bundle changed');floor()
  R.put(out/'RECOVERY01.json',{'status':'COMPLETE_ACTUAL_FAILED_SCOPE_FLAT_BYTES','capture_sha256':CAPTURE_HASH,'remote_receipt_sha256':q['remote_receipt_sha256'],'actual':results,'outcome_metadata':joined,'observed_free_bytes':floors,'original_capture_boolean_qualification':'numerical_or_native_started false describes byte-capture operation; the preserved historical run genuinely claimed and FAILED','posix_instantiation':False,'runtime_or_empirical_recovery':False,'research_authority':False,'same_identity_retry':False})
 except BaseException as e:primary=e
 finally:
  def fail():
   if primary is not None:R.put(out/'FAILED01.json',{'status':'FAILED_RETAINED','error_type':type(primary).__name__,'partial_roles':results,'observed_free_bytes':floors})
  R._cleanup((fail,),primary=primary)
 if primary is not None:raise primary
 return results

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);a=p.parse_args();raw=R.read(a.request.parent.resolve(),a.request.name);R.require(R.digest(raw)==a.sha256,'explicit Root request pin');print(json.dumps(run(json.loads(raw)),sort_keys=True))
