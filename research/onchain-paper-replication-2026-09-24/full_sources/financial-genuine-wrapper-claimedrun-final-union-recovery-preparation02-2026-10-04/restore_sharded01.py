"""Final union ordinary-byte flat restore. Literal links are never interpreted."""
import argparse,hashlib,json,os,re,shutil,stat
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent
BASE=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources')
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for n,pin in PINS.items():R.require(R.digest(R.read(H,n))==pin,'unchanged accepted primitive')

import time
from pathlib import PurePosixPath
R.require(R.digest(R.read(H,'shards01.py'))=='9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba','exact shard planner source')
import shards01 as PLAN
R.require(Path(PLAN.__file__).resolve()==H/'shards01.py','actual pinned planner module origin')

def hashed(v):R.require(type(v)is str and re.fullmatch('[0-9a-f]{64}',v) is not None,'exact SHA256');return v

def reference(ref):
 R.require(type(ref)is dict and set(ref)=={'path','sha256'},'exact proof reference');p=Path(ref['path']);raw=R.read(p.parent,p.name);R.require(R.digest(raw)==hashed(ref['sha256']),'proof changed');return raw

def contract(q):return R.digest(R.encode({k:v for k,v in q.items() if k!='release'}))

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

def request(q):
 fields={'schema_version','remote_root','remote_receipt_sha256','remote_commit','manifest','shard_index','union_auth','expected_members','expected_files','expected_logical_bytes','expected_shards','output_root','review','release'}
 R.require(type(q)is dict and set(q)==fields and type(q['schema_version'])is int and q['schema_version']==1,'exact sharded request')
 for n in fields-{'schema_version'}:R.require(q[n] is not None,'unreleased '+n)
 remote=Path(q['remote_root']);out=Path(q['output_root']);R.require(remote.is_absolute() and remote.resolve()==remote,'remote canonical')
 R.require(out.parent==BASE and out.resolve()==out and out.name=='financial-genuine-wrapper-claimedrun-final-union-sharded-flat-20261004-01' and not os.path.lexists(out),'fresh exact sharded output')
 R.require(not out.is_relative_to(remote) and not remote.is_relative_to(out),'remote output disjoint')
 hashed(q['remote_receipt_sha256']);R.require(type(q['remote_commit'])is str and re.fullmatch('[0-9a-f]{40}',q['remote_commit']) is not None,'actual remote commit')
 for role in ('manifest','shard_index','union_auth'):selected_reference(q[role])
 R.require(len({q[k]['path'] for k in ('manifest','shard_index','union_auth')})==3,'distinct actual selected roles')
 R.require(type(q['expected_members'])is int and 0<q['expected_members']<=32768 and type(q['expected_files'])is int and 0<q['expected_files']<=q['expected_members'],'complete virtual count')
 R.require(type(q['expected_logical_bytes'])is int and 0<q['expected_logical_bytes']<=64*1024**2 and type(q['expected_shards'])is int and 0<q['expected_shards']<=251,'bounded actual logical/shard counts')
 review=reference(q['review']);release=json.loads(reference(q['release']))
 R.require(release=={'schema_version':1,'decision':'accepted-exact-one-use-final-union-sharded-flat','contract_sha256':contract(q),'helper_sha256':R.digest(R.read(H,'restore_sharded01.py')),'review_sha256':R.digest(review)},'genuine exact independent sharded release')
 return remote,out

def selected_reference(ref):
 R.require(type(ref)is dict and set(ref)=={'path','bytes','sha256'},'exact selected body reference');R.path_name(ref['path']);R.require(ref['path'].startswith('research/'),'selected research scope');hashed(ref['sha256']);R.require(type(ref['bytes'])is int and 0<=ref['bytes']<=R.FILE,'selected body bounded');return ref

def selected(remote,q,refs):
 raw=R.read(remote,'REMOTE_RECOVERY01.json');R.require(R.digest(raw)==q['remote_receipt_sha256'],'actual remote receipt pin');receipt=json.loads(raw)
 R.require(receipt['status']=='fresh-actual-remote-recordfix-source325-recovered' and receipt['genuine_run_or_native_started'] is False and receipt['remote_commit']==q['remote_commit'],'actual transport status/commit')
 rows=receipt['selected_blobs'];R.require(type(rows)is list and 1<=len(rows)<=506 and receipt['selected_count']==len(rows) and len({r['path'] for r in rows})==len(rows),'finite complete remote selection');entries={r['path']:r for r in rows}
 R.require(1<=len(refs)<=506 and len({r['path'] for r in refs})==len(refs) and sum(r['bytes'] for r in refs)<=64*1024**2,'finite unique selected shard bytes');result={}
 for ref in refs:
  selected_reference(ref);row=entries[ref['path']];body=R.read(remote/'selected',ref['path']);R.require(row['sha256']==ref['sha256']==R.digest(body) and row['bytes']==ref['bytes']==len(body) and row['git_mode'] in ('100644','100755'),'actual selected shard body')
  R.require(row['git_object']==hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest(),'actual selected Git blob');result[ref['path']]=body
 return result

def manifest_join(q,raw):
 m=json.loads(raw);R.validate(m);R.require(R.encode(m)==raw,'canonical complete virtual manifest')
 R.require(len(m['members'])==q['expected_members'] and sum(r['kind']=='file' for r in m['members'])==q['expected_files'] and sum(r.get('bytes',0) for r in m['members'])==q['expected_logical_bytes']<=64*1024**2,'actual complete virtual denominator');return m

def validate_index(q,m,raw):
 index=json.loads(raw);R.require(R.encode(index)==raw,'canonical sharded index')
 fields={'schema_version','kind','virtual_manifest','limits','regular_bodies','shards'}
 R.require(type(index)is dict and set(index)==fields and type(index['schema_version'])is int and index['schema_version']==1 and index['kind']=='complete-final-union-shards-v1','exact sharded index schema')
 R.require(index['limits']=={'logical_bytes':2097152,'typed_members':256,'archive_bytes':4194304},'unchanged shard limits')
 R.require(type(index['regular_bodies'])is int and index['regular_bodies']==q['expected_files'],'index regular denominator')
 prefix=str(PurePosixPath(q['shard_index']['path']).parent);virtual=index['virtual_manifest'];R.require(type(virtual)is dict and set(virtual)=={'path','bytes','sha256'} and virtual=={'path':'union-manifest.json','bytes':q['manifest']['bytes'],'sha256':q['manifest']['sha256']} and q['manifest']['path']==prefix+'/'+virtual['path'],'actual virtual manifest binding')
 plans=PLAN.partition(m);shards=index['shards'];R.require(type(shards)is list and len(shards)==len(plans)==q['expected_shards'] and 1<=len(shards)<=251,'exact deterministic shard count');refs=[]
 for i,(row,plan) in enumerate(zip(shards,plans)):
  fields={'id','regular_paths','manifest','archive','members','regular_bodies','logical_bytes','tar_bytes_bound'}
  R.require(type(row)is dict and set(row)==fields and row['id']=='shard-'+str(i).zfill(4),'ordered canonical shard id')
  R.require(row['regular_paths']==plan['regular_paths'] and row['members']==len(plan['manifest']['members']) and row['regular_bodies']==len(plan['regular_paths']) and row['logical_bytes']==plan['logical_bytes'] and row['tar_bytes_bound']==plan['tar_bytes_bound'],'exact sorted disjoint deterministic shard cover')
  for name in ('members','regular_bodies','logical_bytes','tar_bytes_bound'):R.require(type(row[name])is int,'integer shard denominator')
  mr=row['manifest'];ar=row['archive'];R.require(type(mr)is dict and set(mr)=={'path','bytes','sha256'} and type(ar)is dict and set(ar)=={'path','bytes','sha256','manifest_sha256'},'exact shard body refs')
  mrbody=R.encode(plan['manifest']);R.require(mr=={'path':'shards/'+row['id']+'-manifest.json','bytes':len(mrbody),'sha256':R.digest(mrbody)},'deterministic shard manifest reference')
  R.require(ar['path']=='shards/'+row['id']+'.tar.gz' and type(ar['bytes'])is int and 0<ar['bytes']<=R.FILE and ar['manifest_sha256']==mr['sha256'],'bounded actual shard archive reference');hashed(ar['sha256'])
  refs.extend({'path':prefix+'/'+r['path'],'bytes':r['bytes'],'sha256':r['sha256']} for r in (mr,ar))
 R.require(len({r['path'] for r in refs})==len(refs),'distinct shard bodies')
 return index,plans,refs
def authenticate_union(q,m,index,auth_raw,metadata_raw):
 auth=json.loads(auth_raw);mapping=json.loads(metadata_raw)
 fields={'schema_version','status','index','shard_count','union_mapping_sha256','ordinary_members','original_trees','original_typed_members','original_regular_members','original_lexical_links','source_capture_reused_unchanged','genuine_native_or_numerical_started','elapsed_seconds','free_bytes','qualification'}
 R.require(type(auth)is dict and set(auth)==fields and type(auth['schema_version'])is int and auth['schema_version']==1 and auth['status']=='complete-final-caller-review-sharded-byte-capture','actual sharded union auth schema/status')
 R.require(auth['index']=={'path':'SHARD_INDEX01.json','bytes':q['shard_index']['bytes'],'sha256':q['shard_index']['sha256'],'virtual_manifest_sha256':q['manifest']['sha256']} and auth['union_mapping_sha256']==R.digest(metadata_raw),'actual sharded index/mapping binding')
 R.require(type(auth['shard_count'])is int and auth['shard_count']==len(index['shards'])==q['expected_shards'],'actual complete shard denominator')
 R.require(auth['source_capture_reused_unchanged'] is True and auth['genuine_native_or_numerical_started'] is False and type(auth['free_bytes'])is int and auth['free_bytes']>=R.FLOOR,'actual capture qualification')
 mf={'schema_version','scope','source_manifest_sha256','source_archive_sha256','source_full_recovery_readback_sha256','source_commit','scope_trees','original_regular_logical_bytes','runtime_bodies_or_empirical_stores_recovered','links_followed_or_extracted','native_or_numerical_started'}
 R.require(type(mapping)is dict and set(mapping)==mf and type(mapping['schema_version'])is int and mapping['schema_version']==1 and R.encode(mapping)==metadata_raw,'canonical original trees schema')
 R.require(mapping['source_commit']=='0a2e7639b42b9423b90743feadcda4078aa21816' and mapping['source_manifest_sha256']=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8' and mapping['source_archive_sha256']=='b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24' and mapping['source_full_recovery_readback_sha256']=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825','separate genuine Source339 full recovery pins')
 R.require(all(mapping[k] is False for k in ('runtime_bodies_or_empirical_stores_recovered','links_followed_or_extracted','native_or_numerical_started')),'byte only scope')
 trees=mapping['scope_trees'];validate_expected_trees(trees);ordinary={r['path']:r for r in m['members']};expected={'ORIGINAL_TREES01.json'};typed=regular=links=logical=0
 R.require(ordinary['ORIGINAL_TREES01.json']['kind']=='file' and ordinary['ORIGINAL_TREES01.json']['sha256']==R.digest(metadata_raw) and ordinary['ORIGINAL_TREES01.json']['bytes']==len(metadata_raw),'virtual original metadata binding')
 for tree in trees:
  scope=tree['scope'];by={r['path']:r for r in tree['members']}
  for row in tree['members']:
   typed+=1;n=row['path'];kind=row['kind'];target=scope if n=='.' else scope+'/'+n
   if n!='.':R.path_name(n);R.require(by.get(str(PurePosixPath(n).parent),{}).get('kind')=='directory','complete original parent')
   if kind=='lexical-symlink':R.require(target not in ordinary,'link remains literal only');links+=1;continue
   expected.add(target);R.require(target in ordinary and ordinary[target]['kind']==kind,'complete virtual original member')
   if kind=='file':R.require(row['union_path']==target and row['bytes']==ordinary[target]['bytes'] and row['sha256']==ordinary[target]['sha256'],'exact original regular body mapping');regular+=1;logical+=row['bytes']
 R.require(expected==set(ordinary),'no missing/extra virtual union member')
 for k,v in {'ordinary_members':len(ordinary),'original_trees':20,'original_typed_members':typed,'original_regular_members':regular,'original_lexical_links':links}.items():R.require(type(auth[k])is int and auth[k]==v,'actual auth denominator '+k)
 R.require(type(mapping['original_regular_logical_bytes'])is int and mapping['original_regular_logical_bytes']==logical<=64*1024**2,'complete original logical denominator')
 return {'original_trees':20,'original_typed_members':typed,'original_regular_members':regular,'original_lexical_links':links,'ordinary_members':len(ordinary),'shard_count':len(index['shards']),'links_followed':False}

def restore_shards(remote,q,m,index,plans,out,floor,results=None):
 prefix=PurePosixPath(q['shard_index']['path']).parent;global_files={};results={} if results is None else results;started=time.monotonic()
 for row,plan in zip(index['shards'],plans):
  R.require(time.monotonic()-started<120,'bounded whole sharded restore');dest=out/row['id'];reserve(dest);floor()
  archive=remote/'selected'/str(prefix/row['archive']['path']);info={k:row['archive'][k] for k in ('bytes','sha256','manifest_sha256')}
  result=restore_ordinary(archive,info,plan['manifest'],dest);metadata=json.loads(R.read(dest,result['metadata_file']))
  R.require(set(metadata['flat_members'])==set(row['regular_paths']),'exact recovered shard file set')
  for name,leaf in metadata['flat_members'].items():
   R.require(name not in global_files,'no reused regular file');body=R.read(dest,leaf);r=next(r for r in plan['manifest']['members'] if r['path']==name)
   R.require(len(body)==r['bytes'] and R.digest(body)==r['sha256'],'actual recovered virtual body');global_files[name]={'shard':row['id'],'file':leaf,'bytes':len(body),'sha256':R.digest(body)}
  results[row['id']]=result;floor()
 R.require(set(global_files)=={r['path'] for r in m['members'] if r['kind']=='file'},'complete global regular cover')
 return global_files,results

def run(q):
 remote,out=request(q);floors=[]
 def floor():
  n=shutil.disk_usage(BASE).free;R.require(n>=R.FLOOR,'observed10GiB floor');floors.append(n)
 floor();base_refs=[q[k] for k in ('manifest','shard_index','union_auth')];first=selected(remote,q,base_refs);m=manifest_join(q,first[q['manifest']['path']]);index,plans,shard_refs=validate_index(q,m,first[q['shard_index']['path']]);refs=base_refs+shard_refs;bodies=selected(remote,q,refs)
 prefix=PurePosixPath(q['shard_index']['path']).parent
 for row,plan in zip(index['shards'],plans):R.require(bodies[str(prefix/row['manifest']['path'])]==R.encode(plan['manifest']),'actual selected shard manifest exact')
 floor();reserve(out);primary=None;results={}
 try:
  R.put(out/'request.json',q);R.put(out/'intent.json',{'pid':os.getpid(),'contract_sha256':contract(q),'remote_receipt_sha256':q['remote_receipt_sha256'],'lexical_links_interpreted':False,'shard_count':len(plans)})
  global_files,results=restore_shards(remote,q,m,index,plans,out,floor,results)
  ref=global_files['ORIGINAL_TREES01.json'];mapping_raw=R.read(out/ref['shard'],ref['file']);union=authenticate_union(q,m,index,bodies[q['union_auth']['path']],mapping_raw)
  R.require(selected(remote,q,refs)==bodies,'all actual remote shard bodies unchanged')
  virtual={'schema_version':1,'virtual_manifest':m,'flat_members':global_files,'shards':results,'union_semantic_joins':union,'posix_tree_instantiated':False,'links_followed':False,'runtime_or_empirical_stores':False,'research_authority':False};R.put(out/'VIRTUAL_RECOVERY01.json',virtual)
  R.put(out/'RECOVERY01.json',{'status':'COMPLETE_FINAL_UNION_SHARDED_ORDINARY_FLAT_BYTES','virtual_manifest':q['manifest'],'shard_index':q['shard_index'],'union_auth':q['union_auth'],'remote_receipt_sha256':q['remote_receipt_sha256'],'virtual_recovery_sha256':R.digest(R.encode(virtual)),'actual_shards':results,'union_semantic_joins':union,'observed_free_bytes':floors,'lexical_links_followed':False,'posix_tree_instantiated':False,'runtime_or_empirical_stores':False,'research_authority':False,'single_archive_identity':None})
 except BaseException as e:primary=e
 finally:
  def failed():
   if primary is not None:R.put(out/'FAILED01.json',{'status':'FAILED_RETAINED','error_type':type(primary).__name__,'partial_shard_results':results,'observed_free_bytes':floors})
  R._cleanup((failed,),primary=primary)
 if primary is not None:raise primary
 return results

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);a=p.parse_args();raw=R.read(a.request.parent.resolve(),a.request.name);R.require(R.digest(raw)==hashed(a.sha256),'actual Root request pin');print(json.dumps(run(json.loads(raw)),sort_keys=True))
