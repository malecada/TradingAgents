"""One fresh bounded ordinary-byte restore with unchanged accepted primitives."""
import argparse,hashlib,json,os,shutil,time
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent
PINS={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True);a=p.parse_args();raw=R.read(a.request.parent.resolve(),a.request.name)
 R.require(R.digest(raw)==a.sha256,'exact Root request');q=json.loads(raw);R.require(R.encode(q)==raw,'canonical Root request')
 R.require(q['actual_execution'] is True and len(q['scopes'])==8,'released fixed eight ordinary scopes')
 for n,pin in PINS.items():R.require(R.digest(R.read(H,n))==pin,'unchanged accepted primitive')
 R.require(Path(R.__file__).resolve()==H/'recovery04.py','actual primitive origin')
 R.require(q['limits']=={'whole_logical':64*1024**2,'body_archive':4*1024**2,'disk_floor':10*1024**3,'seconds':120},'fixed finite byte controls')
 start=time.monotonic();remote=Path(q['remote_root']);R.require(remote.is_absolute() and remote.resolve()==remote,'canonical remote')
 receipt_raw=R.read(remote,'REMOTE_RECOVERY01.json');R.require(R.digest(receipt_raw)==q['remote_receipt_sha256'],'actual remote receipt');receipt=json.loads(receipt_raw)
 R.require(receipt['remote_commit']==q['remote_commit'] and receipt['genuine_run_or_native_started'] is False,'actual remote context');rows={r['path']:r for r in receipt['selected_blobs']};R.require(len(rows)==receipt['selected_count']<=506,'complete remote denominator')
 def floor():
  R.require(time.monotonic()-start<120 and shutil.disk_usage(H).free>=10*1024**3,'120-second budget and10GiB floor')
 def body(ref):
  floor();row=rows[ref['path']];b=R.read(remote/'selected',ref['path']);R.require(row['sha256']==ref['sha256']==R.digest(b) and row['bytes']==ref['bytes']==len(b)<=R.FILE and row['git_mode'] in ('100644','100755'),'actual selected body pins');R.require(row['git_object']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'actual selected Git object');return b
 prepared=[];whole=0
 for s in q['scopes']:
  m=json.loads(body(s['manifest']));R.validate(m);R.require(len(m['members'])==s['ordinary_members'],'complete scope count');whole+=sum(r.get('bytes',0)for r in m['members']);R.require(whole<=64*1024**2,'whole eight-scope logical limit');body(s['archive']);prepared.append((s,m))
 out=H/'flat-eight-scopes01';R.require(not os.path.lexists(out),'fresh one-use ordinary output');floor();os.mkdir(out,0o700);R.put(out/'REQUEST01.json',q);R.put(out/'INTENT01.json',{'actual_pid':os.getpid(),'actual_start_ticks':int(Path('/proc',str(os.getpid()),'stat').read_text().rsplit(')',1)[1].split()[19]),'pgid':os.getpgid(os.getpid()),'schema_version':1,'genuine_numerical_started':False});results=[]
 try:
  for i,(s,m)in enumerate(prepared):
   floor();ar=s['archive'];info={'bytes':ar['bytes'],'sha256':ar['sha256'],'manifest_sha256':s['manifest']['sha256']};dest=out/('scope-'+str(i).zfill(2));result=R.restore(remote/'selected'/ar['path'],info,m,dest);metadata=json.loads(R.read(dest,result['metadata_file']));R.require(metadata['manifest']==m and len(metadata['flat_members'])==result['regular_bodies'],'actual full flat membership');meta_matches=[]
   for n,leaf in metadata['flat_members'].items():
    if R.digest(R.read(dest,leaf))==s['original_metadata_sha256']:meta_matches.append(n)
   R.require(meta_matches==['CAPTURE_ORIGINAL_TREE01.json'],'exact original mode/link/emptydir metadata recovered');results.append({'label':s['label'],'result':result,'output':str(dest),'original_metadata_path':meta_matches[0]});R.put(out/('COMPLETED_SCOPE'+str(i).zfill(2)+'.json'),results[-1])
  floor();R.put(out/'RECOVERY01.json',{'status':'COMPLETE_EIGHT_ORDINARY_ARCHIVE_FLAT_BYTES','remote_commit':q['remote_commit'],'remote_receipt_sha256':q['remote_receipt_sha256'],'whole_logical_bytes':whole,'scopes':results,'elapsed_seconds':time.monotonic()-start,'free_bytes':shutil.disk_usage(H).free,'genuine_numerical_started':False,'posix_tree_instantiated':False,'runtime_or_empirical_store_recovery':False});print(json.dumps({'status':'COMPLETE_EIGHT_ORDINARY_ARCHIVE_FLAT_BYTES','scopes':len(results),'whole_logical':whole}))
 except BaseException as e:
  try:R.put(out/'FAILED01.json',{'status':'FAILED_ORIGINAL_ATTEMPT','error_type':type(e).__name__,'error':str(e),'completed_scopes':results,'genuine_numerical_started':False})
  except BaseException as secondary:R._cleanup((lambda:(_ for _ in ()).throw(secondary),),primary=e)
  raise
if __name__=='__main__':main()
