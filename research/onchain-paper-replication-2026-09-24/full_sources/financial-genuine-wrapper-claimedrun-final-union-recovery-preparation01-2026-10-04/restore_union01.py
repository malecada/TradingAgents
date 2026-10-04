"""Final union ordinary-byte flat restore. Literal links are never interpreted."""
import argparse,hashlib,json,os,re,shutil,stat
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent
BASE=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources')
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for n,pin in PINS.items():R.require(R.digest(R.read(H,n))==pin,'unchanged accepted primitive')

def hashed(v):R.require(type(v)is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'exact SHA256');return v

def reference(ref):
 R.require(type(ref)is dict and set(ref)=={'path','sha256'},'exact proof reference');p=Path(ref['path']);raw=R.read(p.parent,p.name);R.require(R.digest(raw)==hashed(ref['sha256']),'proof changed');return raw

def contract(q):return R.digest(R.encode({k:v for k,v in q.items() if k!='release'}))

def request(q):
 fields={'schema_version','remote_root','remote_receipt_sha256','remote_commit','archive','manifest','union_auth','expected_members','expected_files','expected_logical_bytes','output_root','review','release'}
 R.require(type(q)is dict and set(q)==fields and type(q['schema_version'])is int and q['schema_version']==1,'exact final union request')
 for n in fields-{'schema_version'}:R.require(q[n] is not None,'unreleased '+n)
 remote=Path(q['remote_root']);out=Path(q['output_root']);R.require(remote.is_absolute() and remote.resolve()==remote,'remote canonical')
 R.require(out.parent==BASE and out.resolve()==out and out.name=='financial-genuine-wrapper-claimedrun-final-union-flat-20261004-01' and not os.path.lexists(out),'fresh fixed-scope Root flat namespace')
 R.require(not out.is_relative_to(remote) and not remote.is_relative_to(out),'remote/output overlap')
 hashed(q['remote_receipt_sha256']);R.require(type(q['remote_commit'])is str and re.fullmatch('[0-9a-f]{40}',q['remote_commit']) is not None,'actual remote commit')
 for role in ('archive','manifest','union_auth'):
  x=q[role];R.require(type(x)is dict and set(x)=={'path','sha256','bytes'},'exact selected role');R.path_name(x['path']);R.require(x['path'].startswith('research/'),'selected research scope');hashed(x['sha256']);R.require(type(x['bytes'])is int and 0<=x['bytes']<=R.FILE,'bounded role size')
 R.require(len({q[k]['path'] for k in ('archive','manifest','union_auth')})==3,'distinct archive/manifest/auth roles')
 R.require(type(q['expected_members'])is int and 0<q['expected_members']<=32768 and type(q['expected_files'])is int and 0<q['expected_files']<=q['expected_members'] and type(q['expected_logical_bytes'])is int and 0<=q['expected_logical_bytes']<=R.BASE,'finite exact union denominator')
 review=reference(q['review']);release=json.loads(reference(q['release']))
 R.require(release=={'schema_version':1,'decision':'accepted-exact-one-use-final-union-flat','contract_sha256':contract(q),'helper_sha256':R.digest(R.read(H,'restore_union01.py')),'review_sha256':R.digest(review)},'genuine exact independent one-use release')
 return remote,out

def selected(remote,q):
 raw=R.read(remote,'REMOTE_RECOVERY01.json');R.require(R.digest(raw)==q['remote_receipt_sha256'],'actual remote receipt');receipt=json.loads(raw)
 R.require(receipt['status']=='fresh-actual-remote-recordfix-source325-recovered' and receipt['genuine_run_or_native_started'] is False and receipt['remote_commit']==q['remote_commit'],'actual accepted transport scope/commit')
 rows=receipt['selected_blobs'];R.require(type(rows)is list and 1<=len(rows)<=506 and len({r['path'] for r in rows})==len(rows) and receipt['selected_count']==len(rows),'complete remote selection denominator')
 entries={r['path']:r for r in rows};raws={}
 for role in ('archive','manifest','union_auth'):
  pin=q[role];row=entries[pin['path']];body=R.read(remote/'selected',pin['path']);R.require(row['sha256']==pin['sha256']==R.digest(body) and row['bytes']==pin['bytes']==len(body) and row['git_mode'] in ('100644','100755'),'actual selected union body')
  R.require(row['git_object']==hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest(),'selected Git OID');raws[role]=body
 return raws

def manifest_join(q,raw):
 m=json.loads(raw);R.validate(m);R.require(R.encode(m)==raw,'canonical ordinary union manifest')
 R.require(len(m['members'])==q['expected_members'] and sum(r['kind']=='file' for r in m['members'])==q['expected_files'] and sum(r.get('bytes',0) for r in m['members'])==q['expected_logical_bytes'],'exact complete union denominator')
 return m

EXPECTED_ORIGINALS_SHA256='40b4002ee1b0edf1d2d4e4202cf3d5c98834eb9656b02558caedf40d7261dc30'

def validate_expected_trees(trees):
 raw=R.read(H,'EXPECTED_ORIGINALS01.json');R.require(R.digest(raw)==EXPECTED_ORIGINALS_SHA256,'exact complete original census pin');expected=json.loads(raw)
 R.require(type(trees)is list and len(trees)==20 and trees==expected['scope_trees'],'complete exact twenty original roots/membership/body/modes/literal links')
 # Explicit anchors independently prevent substitution of stale caller/source contexts.
 by={t['scope']:{r['path']:r for r in t['members']} for t in trees}
 anchors={
  ('actual-parent','parent01.py'):'5d5cbdae455c62c3e66b53208b0f79e6e5bbc7ce05d3ded77126da5e0692deda',
  ('actual-parent','REQUEST_FINAL03.json'):'529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8',
  ('actual-parent','proofs/FINAL_REVIEW01.json'):'95dadb68b74693212dece8b363156ddc5d98c4b4726a9c50577d2655bb8f3c38',
  ('actual-parent','proofs/CUMULATIVE19_REVIEW01.json'):'3268b76971e4e721222707d16d25dfe84e94104779931e647fb4d7a2bf01202e',
  ('actual-parent','proofs/INDEPENDENT_SOURCE_INPUT_RUNTIME01.json'):'059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c',
  ('actual-parent','proofs/FULL_SOURCE_RECOVERY01.json'):'468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825',
  ('root-verifier-binding','generated-claimedrun01/verifier01.py'):'14089451a225aa541eb6faf30c78cb31c79b1380d7ef54d77e895575e3ce250c',
  ('root-verifier-binding','generated-claimedrun01/BINDING01.json'):'57e3b72754668f3be5d1611475b9c29be3fabd91ffe71c5cad60792fa4881989',
  ('actual-verifier-review','MANIFEST01.json'):'0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2',
 }
 for (scope,path),pin in anchors.items():R.require(by[scope][path]['kind']=='file' and by[scope][path]['sha256']==pin,'genuine fixed actual caller/verifier proof '+scope+'/'+path)
 return expected

def authenticate_union(q,m,auth_raw,metadata_raw):
 auth=json.loads(auth_raw);mapping=json.loads(metadata_raw)
 fields={'schema_version','status','archive','union_mapping_sha256','ordinary_members','original_trees','original_typed_members','original_regular_members','original_lexical_links','source_capture_reused_unchanged','genuine_native_or_numerical_started','elapsed_seconds','free_bytes','qualification'}
 R.require(type(auth)is dict and set(auth)==fields and type(auth['schema_version'])is int and auth['schema_version']==1 and auth['status']=='complete-final-caller-review-byte-capture','actual union auth schema/status')
 R.require(auth['archive']=={'bytes':q['archive']['bytes'],'sha256':q['archive']['sha256'],'manifest_sha256':q['manifest']['sha256']} and auth['union_mapping_sha256']==R.digest(metadata_raw),'actual archive/mapping joins')
 R.require(auth['source_capture_reused_unchanged'] is True and auth['genuine_native_or_numerical_started'] is False and type(auth['free_bytes'])is int and auth['free_bytes']>=R.FLOOR,'actual capture qualification')
 mf={'schema_version','scope','source_manifest_sha256','source_archive_sha256','source_full_recovery_readback_sha256','source_commit','scope_trees','original_regular_logical_bytes','runtime_bodies_or_empirical_stores_recovered','links_followed_or_extracted','native_or_numerical_started'}
 R.require(type(mapping)is dict and set(mapping)==mf and type(mapping['schema_version'])is int and mapping['schema_version']==1,'original trees schema')
 R.require(mapping['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816' and mapping['source_manifest_sha256']=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8' and mapping['source_archive_sha256']=='b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24' and mapping['source_full_recovery_readback_sha256']=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825','separate original Source recovery pins')
 R.require(all(mapping[k] is False for k in ('runtime_bodies_or_empirical_stores_recovered','links_followed_or_extracted','native_or_numerical_started')),'byte-only mapping scope')
 trees=mapping['scope_trees'];validate_expected_trees(trees)
 ordinary={r['path']:r for r in m['members']};expected={'ORIGINAL_TREES01.json'};typed=regular=links=logical=0
 R.require(ordinary['ORIGINAL_TREES01.json']['kind']=='file' and ordinary['ORIGINAL_TREES01.json']['sha256']==R.digest(metadata_raw) and ordinary['ORIGINAL_TREES01.json']['bytes']==len(metadata_raw),'ordinary metadata body binding')
 for tree in trees:
  R.require(set(tree)=={'scope','original_root','members'} and type(tree['original_root'])is str and Path(tree['original_root']).is_absolute(),'original root metadata')
  scope=tree['scope'];rows=tree['members'];R.require(type(rows)is list and 0<len(rows)<=32768 and [r['path'] for r in rows]==sorted({r['path'] for r in rows}),'complete sorted original names');by={r['path']:r for r in rows}
  R.require(by.get('.',{}).get('kind')=='directory','original root directory')
  for row in rows:
   typed+=1;n=row['path'];kind=row['kind'];R.require(type(row['mode'])is int and 0<=row['mode']<=0o7777,'literal original mode')
   if n!='.':R.path_name(n);parent=str(Path(n).parent);R.require(by.get(parent,{}).get('kind')=='directory','original parent membership')
   target=scope if n=='.' else scope+'/'+n
   if kind=='lexical-symlink':
    R.require(set(row)=={'path','mode','kind','target'} and type(row['target'])is str and n!='.' and target not in ordinary,'lexical link literal only');links+=1;continue
   expected.add(target);R.require(target in ordinary and ordinary[target]['kind']==kind,'ordinary tree membership')
   if kind=='directory':R.require(set(row)=={'path','mode','kind'},'original directory fields')
   else:
    R.require(kind=='file' and set(row)=={'path','mode','kind','bytes','sha256','union_path'} and row['union_path']==target and row['bytes']==ordinary[target]['bytes'] and row['sha256']==ordinary[target]['sha256'],'complete original regular body mapping');regular+=1;logical+=row['bytes']
 R.require(expected==set(ordinary),'no missing/extra ordinary union members')
 for k,v in {'ordinary_members':len(ordinary),'original_trees':len(trees),'original_typed_members':typed,'original_regular_members':regular,'original_lexical_links':links}.items():R.require(type(auth[k])is int and auth[k]==v,'union auth denominator '+k)
 R.require(type(mapping['original_regular_logical_bytes'])is int and mapping['original_regular_logical_bytes']==logical<=64*1024**2,'complete original logical denominator')
 return {'original_trees':len(trees),'original_typed_members':typed,'original_regular_members':regular,'original_lexical_links':links,'ordinary_members':len(ordinary),'links_followed':False}

def reserve(out):
 fd=None
 try:
  R.require(out.parent.resolve()==out.parent,'parent canonical');fd=os.open(out.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);s=os.fstat(fd);pin=(s.st_dev,s.st_ino,s.st_mode)
  def stable():
   t=out.parent.lstat();R.require(out.parent.resolve()==out.parent and (t.st_dev,t.st_ino,t.st_mode)==pin,'parent changed')
  stable();os.mkdir(out.name,0o700,dir_fd=fd);stable();R.require(out.resolve()==out and stat.S_IMODE(out.stat().st_mode)==0o700,'fresh private output');os.fsync(fd)
 finally:R._cleanup(() if fd is None else (lambda:os.close(fd),))

def restore_ordinary(archive,info,m,destination):
 # Only ordinary members pass R.validate; link descriptions are opaque file bytes.
 R.validate(m);result=R.restore(archive,info,m,destination)
 metadata=json.loads(R.read(destination,result['metadata_file']));R.require(R.digest(R.encode(metadata))==result['metadata_sha256'] and metadata['manifest']==m,'actual flat manifest mapping')
 names={r['path'] for r in m['members'] if r['kind']=='file'};R.require(set(metadata['flat_members'])==names and result['regular_bodies']==len(names),'every regular union body recovered')
 return result

def run(q):
 remote,out=request(q);floors=[]
 def floor():
  n=shutil.disk_usage(BASE).free;R.require(n>=R.FLOOR,'observed10GiB floor');floors.append(n)
 floor();bodies=selected(remote,q);m=manifest_join(q,bodies['manifest']);floor();reserve(out);primary=None;result=None
 try:
  R.put(out/'request.json',q);R.put(out/'intent.json',{'pid':os.getpid(),'contract_sha256':contract(q),'remote_receipt_sha256':q['remote_receipt_sha256'],'lexical_links_interpreted':False})
  floor();dest=out/'flat';reserve(dest)
  info={'bytes':q['archive']['bytes'],'sha256':q['archive']['sha256'],'manifest_sha256':q['manifest']['sha256']}
  result=restore_ordinary(remote/'selected'/q['archive']['path'],info,m,dest);floor()
  flat_metadata=json.loads(R.read(dest,result['metadata_file']));mapping_raw=R.read(dest,flat_metadata['flat_members']['ORIGINAL_TREES01.json']);union=authenticate_union(q,m,bodies['union_auth'],mapping_raw)
  R.require(selected(remote,q)==bodies,'remote bytes changed during recovery')
  R.put(out/'RECOVERY01.json',{'status':'COMPLETE_FINAL_UNION_ORDINARY_FLAT_BYTES','archive':q['archive'],'manifest':q['manifest'],'union_auth':q['union_auth'],'remote_receipt_sha256':q['remote_receipt_sha256'],'actual':result,'union_semantic_joins':union,'observed_free_bytes':floors,'lexical_links_followed':False,'posix_tree_instantiated':False,'runtime_or_empirical_stores':False,'research_authority':False,'union_auth_semantics':'actual complete twenty-original mapping/body/mode/link-count joins; no link followed or POSIX tree instantiated'})
 except BaseException as e:primary=e
 finally:
  def failed():
   if primary is not None:R.put(out/'FAILED01.json',{'status':'FAILED_RETAINED','error_type':type(primary).__name__,'partial_recovery':result,'observed_free_bytes':floors})
  R._cleanup((failed,),primary=primary)
 if primary is not None:raise primary
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);a=p.parse_args();raw=R.read(a.request.parent.resolve(),a.request.name);R.require(R.digest(raw)==hashed(a.sha256),'actual Root request pin');print(json.dumps(run(json.loads(raw)),sort_keys=True))
