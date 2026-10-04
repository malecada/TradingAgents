"""One exact Source325 flat recovery, solely from an authenticated remote recovery."""
import argparse,hashlib,json,os,shutil,stat,sys,time
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent
SOURCE='649fb8a11089524aaef7843dffeeb90a3a55ca17'
REL='research/onchain-paper-replication-2026-09-24/full_sources/financial-genuine-wrapper-root-recordfix-capture01-2026-10-04'
GATE='fixture_inputs/financial_wrapper_recordfix01/gates.json'
GATEHASH='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a'
IDENTITY='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01'
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for n,pin in PINS.items():R.require(R.digest(R.read(H,n))==pin,'exact R4 primitive')
_pins=R.read(H,'CAPTURE_PINS01.json');R.require(R.digest(_pins)=='9b5b2c66e97fecd423afc5297ebb39c768d2cdb584bcd7060733488d9d4d0e17','fixed actual capture pins');EXPECTED=json.loads(_pins)

def ref(value):
 R.require(type(value)is dict and set(value)=={'path','sha256'},'exact external proof');p=Path(value['path']);raw=R.read(p.parent,p.name);R.require(R.digest(raw)==value['sha256'],'proof changed');return raw

def validate_request(q):
 R.require(type(q)is dict and set(q)=={'schema_version','source','remote_root','remote_receipt_sha256','review','release'},'request schema')
 R.require(type(q['schema_version'])is int and q['schema_version']==1 and q['source']==SOURCE,'fixed Source325')
 for k in ('remote_root','remote_receipt_sha256','review','release'):R.require(q[k] is not None,'unreleased '+k)
 root=Path(q['remote_root']);R.require(root.is_absolute() and root.resolve()==root,'actual remote root canonical')
 review=ref(q['review']);release=json.loads(ref(q['release']))
 R.require(release=={'decision':'accepted-exact-recordfix-flat-recovery','source':SOURCE,'helper_sha256':R.digest(R.read(H,'restore01.py')),'request_sha256':R.digest(R.encode({k:v for k,v in q.items() if k!='release'})),'review_sha256':R.digest(review)},'exact independent release')
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
 m=json.loads(body['source-manifest.json']);R.validate(m);a=json.loads(body['source-authentication.json']);t=json.loads(body['terminal.json']);q=json.loads(body['request.json']);outer=json.loads(body['ACTUAL_TERMINAL02.json'])
 R.require(len(m['members'])==986 and sum(r['kind']=='file' for r in m['members'])==713 and sum(r.get('bytes',0) for r in m['members'])==8642839,'whole actual source denominator')
 R.require(q['source']==t['source']==a['source']==outer['source']==SOURCE and q['manifest']==m and q['manifest_sha256']==EXPECTED['source-manifest.json']['sha256'],'original source/request/manifest')
 R.require(t['status']=='COMPLETE_BYTES_ONLY' and t['error_type'] is None and t['runtime_bodies'] is False and t['scientific_credit']==0 and t['external_recovery'] is False,'actual original capture disposition')
 R.require(t['archive']==dict(EXPECTED['source.tar.gz'],manifest_sha256=EXPECTED['source-manifest.json']['sha256']),'archive exact info')
 R.require(outer['actual_exit']==0 and outer['actual_original_terminal_sha256']==EXPECTED['terminal.json']['sha256'] and outer['native_or_numerical_claim_started'] is False,'separate actual root exit joins')
 R.require(a['tracked']==325 and a['selected']==324 and a['implementation']==194 and a['package']==149 and a['runtime_record_metadata_count']==251 and a['runtime_bodies_captured'] is False,'actual source authentication')
 R.require(a['changed']==['tradingagents/research/onchain_replication/financial_wrapper_fixture.py'] and len(a['git_entries'])==325 and len(a['role_hashes'])==8,'one correction/roles/Git denominator')
 R.require(len(t['observed_free_bytes'])==4 and all(type(n)is int and n>=R.FLOOR for n in t['observed_free_bytes']),'original observed floor points')
 return m,a,t

def flat_source_joins(destination,result,m,a):
 metadata=json.loads(R.read(destination,result['metadata_file']));R.require(R.digest(R.encode(metadata))==result['metadata_sha256'] and metadata['manifest']==m,'complete flat metadata')
 mapping=metadata['flat_members'];R.require(len(mapping)==713 and set(mapping)=={r['path'] for r in m['members'] if r['kind']=='file'},'all713 recovered body members')
 def raw(n):return R.read(destination,mapping[n])
 for n,(mode,oid) in a['git_entries'].items():
  b=raw(n);R.require(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid and mode in ('100644','100755'),'325 actual archived Git object body joins')
 gate=raw(GATE);R.require(R.digest(gate)==GATEHASH,'actual recovered gate');exp=json.loads(gate)['experiments'][IDENTITY];pins=exp['source_files'];R.require(len(pins)==324 and set(pins)|{GATE}==set(a['git_entries']),'complete selected325/324')
 for n,pin in pins.items():R.require(R.digest(raw(n))==pin,'recovered selected body pin')
 for ref in exp['inputs'].values():R.require(R.digest(raw(ref['path']))==ref['sha256']==a['role_hashes'][ref['path']],'eight recovered input joins')
 R.require(len(exp['inputs'])==8,'eight inputs')
 return {'tracked_git_body_joins':325,'selected_body_joins':324,'inputs':8,'recovered_regular_bodies':713,'private_flat_files_with_metadata':714,'posix_tree_instantiated':False}

def run(q):
 root=validate_request(q);R.require(not any(os.path.lexists(H/n) for n in ['INTENT01.json','flat-source01','RECOVERY01.json','FAILED01.json']),'one-use flat namespace');floors=[]
 def floor():
  free=shutil.disk_usage(H).free;R.require(free>=R.FLOOR,'10GiB floor');floors.append(free)
 floor();bundle,body,receipt=remote_bodies(root,q['remote_receipt_sha256']);m,a,t=joins(body)
 R.put(H/'INTENT01.json',{'pid':os.getpid(),'source':SOURCE,'remote_receipt_sha256':q['remote_receipt_sha256'],'native_started':False});primary=None;result=None;begun=time.monotonic()
 try:
  floor();destination=H/'flat-source01';destination.mkdir(mode=0o700);result=R.restore(bundle/'source.tar.gz',t['archive'],m,destination);floor();source_joins=flat_source_joins(destination,result,m,a);floor()
  R.put(H/'RECOVERY01.json',{'status':'actual-recordfix-source325-fresh-flat-recovered','source':SOURCE,'actual':result,'joins':source_joins,'remote_receipt_sha256':q['remote_receipt_sha256'],'disk_floor_observations':floors,'elapsed_seconds':time.monotonic()-begun,'original_capture_pid_observed':False,'runtime_bodies':False,'empirical_stores':False,'numerical_credit':0,'release_of_numerical_work':False})
 except BaseException as e:primary=e
 finally:
  def failure():
   if primary is not None:R.put(H/'FAILED01.json',{'status':'FAILED_RETAINED','error_type':type(primary).__name__,'source':SOURCE,'partial_restore':result,'disk_floor_observations':floors})
  R._cleanup((failure,),primary=primary)
 if primary is not None:raise primary
 return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);n=p.parse_args();raw=R.read(n.request.parent.resolve(),n.request.name);R.require(R.digest(raw)==n.sha256,'exact request');print(json.dumps(run(json.loads(raw)),sort_keys=True))
