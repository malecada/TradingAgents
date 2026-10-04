from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path.insert(0,str(D/'utilities'));import recovery_ustar02 as U;import recovery_pax01 as P
q=json.loads((D.parent/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05/ROOT_REQUEST_FLAT01.json').read_text());rows=[]
for b in q['bundles']:
 manifest=json.loads(U.read(ROOT,b['manifest']['path']));raw=U.read(ROOT,b['archive']['path']);assert U.digest(raw)==b['archive']['sha256'];out=D/('opaque-'+b['name']);already=out.exists()
 if not already:out.mkdir(mode=0o700)
 info={k:b['archive'][k] for k in ('bytes','sha256')};info['manifest_sha256']=b['manifest']['sha256'];result=U.restore(ROOT/b['archive']['path'],info,manifest,out) if not already else {'metadata_file':'body-metadata.json'}
 meta=json.loads((out/result['metadata_file']).read_bytes());assert meta['manifest']==manifest
 for x in manifest['members']:
  if x['kind']=='file':assert U.digest(U.read(out,meta['flat_members'][x['path']]))==x['sha256']
 old_error=None;fo=P.FlatOutput(out);fo.names=set(meta['flat_members'].values())|{result['metadata_file']};fo.begin()
 try:
  sink=P.ExactSink(raw);P.flat_tar_stream(fo,manifest,meta['flat_members'],sink);assert sink.count==len(raw) and sink.hash.hexdigest()==P.digest(raw)
 except BaseException as error:old_error=repr(error)
 finally:fo.close()
 rows.append({'bundle':b['name'],'archive_sha256':U.digest(raw),'restored_bodies':len(meta['flat_members']),'old_pax_error':old_error,'ustar_exact_restore':True})
assert rows[0]['old_pax_error'] is not None
(D/'ARCHIVE_CHECK01.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
