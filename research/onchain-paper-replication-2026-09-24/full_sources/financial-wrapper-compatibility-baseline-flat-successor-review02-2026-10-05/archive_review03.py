from pathlib import Path
import json,hashlib,stat,sys,traceback
F=Path(__file__).resolve().parent.parent;D=Path(__file__).resolve().parent;P=F/'financial-wrapper-compatibility-baseline-flat-successor-preparation02-2026-10-05';ROOT=F.parents[2];h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(P/'MANIFEST01.json')=='3ef2b3c37caec4ef62b6dcb64705b2ddcfe96e5d421bf98d6cb91635d25a39fc';m=json.loads((P/'MANIFEST01.json').read_bytes());declared=set()
for r in m['members']:
 p=P/r['path'];s=p.lstat();declared.add(r['path']);assert stat.S_IMODE(s.st_mode)==r['mode']
 if r['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and h(p)==r['sha256']
 else:assert stat.S_ISDIR(s.st_mode)
assert declared=={p.relative_to(P).as_posix() for p in P.rglob('*') if p.name!='MANIFEST01.json'}
inv=json.loads((P/'INVERSE02.json').read_bytes());inverse=[]
for r in inv:
 assert r['new'].encode()==(P/r['file']).read_bytes();inverse.append({'path':r['file'],'old_sha256':hashlib.sha256(r['original'].encode()).hexdigest(),'new_sha256':hashlib.sha256(r['new'].encode()).hexdigest()})
assert (P/'utilities/recovery_ustar02.py').read_bytes().replace(b'tarfile.USTAR_FORMAT',b'tarfile.PAX_FORMAT')==(P/'utilities/recovery_pax01.py').read_bytes()
oldroot=F/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05'
for n in ('binding01.py','cohort01.py','receipt01.py','watch01.py','KNOWN_REQUIRED01.json','recover.template01.py','utilities/owned_io.py','utilities/bounded_git01.py','utilities/recovery_pax01.py'):assert (P/n).read_bytes()==(oldroot/n).read_bytes()
sys.path[:0]=[str(P/'utilities')];import recovery_ustar02 as U;import recovery_pax01 as PX
q=json.loads((oldroot/'ROOT_REQUEST_FLAT01.json').read_bytes());archives=[]
for b in q['bundles']:
 manifest=json.loads(U.read(ROOT,b['manifest']['path']));raw=U.read(ROOT,b['archive']['path']);assert U.digest(raw)==b['archive']['sha256'];out=P/('opaque-'+b['name']);metadata=json.loads(U.read(out,'body-metadata.json'));assert metadata['manifest']==manifest
 for r in manifest['members']:
  if r['kind']=='file':assert U.digest(U.read(out,metadata['flat_members'][r['path']]))==r['sha256']
 observed={}
 for name,module in [('USTAR',U),('PAX',PX)]:
  fo=module.FlatOutput(out);fo.names=set(metadata['flat_members'].values())|{'body-metadata.json'};fo.begin();error=None
  try:
   sink=module.ExactSink(raw);module.flat_tar_stream(fo,manifest,metadata['flat_members'],sink);assert sink.count==len(raw) and sink.hash.hexdigest()==module.digest(raw)
  except BaseException as e:
   if name=='USTAR':raise
   error=type(e).__name__+': '+str(e);(D/(b['name']+'-PAX_RED01.txt')).write_text(traceback.format_exc())
  finally:fo.close()
  observed[name]=error
 assert observed['USTAR'] is None
 archives.append({'name':b['name'],'file_count':len(metadata['flat_members']),'archive_sha256':U.digest(raw),'exact_reencoding':observed})
assert sum(x['file_count'] for x in archives)==323 and archives[0]['exact_reencoding']['PAX'] is not None
result={'author_members':len(m['members']),'author_manifest_sha256':h(P/'MANIFEST01.json'),'source_inverse':inverse,'unchanged_dependencies':9,'ustar_exact_two_format_substitutions':True,'archives':archives,'body_count':323,'actual_public_restore_invoked':False,'old_receiver_mutated':False,'caller03_normal_exit_refusal_pending_correction':True,'prior_navigation_note_erratum':'Actual inverse keys are file/original/new, not path or name.'};(D/'SOURCE_ARCHIVE_AUTHENTICATION01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
