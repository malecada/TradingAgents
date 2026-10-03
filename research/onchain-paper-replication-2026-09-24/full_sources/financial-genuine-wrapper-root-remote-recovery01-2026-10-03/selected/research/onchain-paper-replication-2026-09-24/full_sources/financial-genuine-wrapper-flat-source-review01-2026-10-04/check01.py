"""Independent stdlib-only source pins and tiny opaque flat recovery controls."""
import ast,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;U=F/'held-consumer-final-recovery-preparation04-2026-10-03';C=F/'financial-genuine-wrapper-root-flat-recovery01-2026-10-04';P=F/'financial-genuine-wrapper-root-preservation02-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
source=(C/'restore_financial01.py').read_bytes();ck(sha(source)=='24da8af5f01e902e83f01a840d31f7fb24671e818c95dd17f331fbac44bdeac3','actual candidate pin');tree=ast.parse(source)
def literal(name):return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
pins=literal('PINS');expected=literal('EXPECTED')
for n,h in pins.items():ck(sha((U/n).read_bytes())==h,'unchanged accepted primitive '+n)
for n,h in expected.items():ck(sha((P/n).read_bytes())==h,'actual prior capture body '+n)
sys.path.insert(0,str(U));spec=importlib.util.spec_from_file_location('review_flat_primitives',U/'recovery04.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
from owned_io import _cleanup,CleanupFailure
I=F/'financial-genuine-wrapper-full-scope-preservation-review02-2026-10-04';raw=R.read(I,'MANIFEST01.json');ck(sha(raw)=='7166f7aebf764bf3957947935148b34e10b26bc928351433774203c198235aba','actual accepted complete capture review');m=json.loads(raw);ck({r['path'] for r in m['members']}|{'MANIFEST01.json'}=={p.name for p in I.iterdir()},'complete prior frozen review membership')
for row in m['members']:
 p=I/row['path'];b=R.read(I,row['path']);ck(row['kind']=='file' and len(b)==row['bytes'] and sha(b)==row['sha256'] and stat.S_IMODE(p.lstat().st_mode)==row['mode'],'prior frozen typed body')
# Exact source order: authenticate remote and fixed bodies before intent/mkdir/restore.
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');text=ast.unparse(main)
ck(text.index("'actual remote receipt pin'")<text.index('bodies = {}')<text.index("'actual complete source bindings'")<text.index("R.put(HERE / 'INTENT01.json'")<text.index("(HERE / 'flat01').mkdir")<text.index('R.restore('),'source authentication before mutations/restore')
ck('os.path.lexists' in text and 'a.review_manifest_sha256' in text and 'a.remote_receipt_sha256' in text and "hashlib.sha1(b'blob '" in text,'fresh namespace exact CLI receipt/review and Git OID joins')
ck('R.authenticate_source' not in text and 'R.recover(' not in text,'no held fixed authenticator/restore route')
fixtures=O/'tiny01';fixtures.mkdir(mode=0o700)
def tar_bytes(rows,mtime=0):
 b=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=b,mtime=mtime) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as t:
   for name,kind,mode,body in rows:
    x=tarfile.TarInfo(name);x.mode=mode;x.uid=x.gid=0;x.uname=x.gname='';x.mtime=0
    if kind=='directory':x.type=tarfile.DIRTYPE;x.size=0;t.addfile(x)
    else:x.size=len(body);t.addfile(x,io.BytesIO(body))
 return b.getvalue()
rows=[('a','directory',0o750,b''),('a/value.txt','file',0o640,b'opaque\x00one\n'),('long/'+('x'*120),'file',0o600,b'two')]
# Include every parent directory as real archive metadata.
rows.insert(2,('long','directory',0o700,b''));manifest={'schema_version':1,'root_mode':0o750,'members':[dict(path=n,kind=k,mode=m,**({'bytes':len(b),'sha256':sha(b)} if k=='file' else {})) for n,k,m,b in rows]}
archive=tar_bytes(rows)
def run_case(name,raw=archive,m=manifest,info_override=None,destmode=0o700,extra=False):
 folder=fixtures/name;folder.mkdir(mode=0o700);a=folder/'tiny.tar.gz';a.write_bytes(raw);dest=folder/'flat';dest.mkdir(mode=destmode)
 if extra:(dest/'preexisting').write_bytes(b'retained')
 info={'bytes':len(raw),'sha256':sha(raw),'manifest_sha256':sha(R.encode(m))}
 if info_override:info.update(info_override)
 return folder,dest,lambda:R.restore(a,info,m,dest)
def refuse(name,**kw):
 folder,dest,call=run_case(name,**kw)
 try:call()
 except (ValueError,FileExistsError):ck(True,'refused '+name)
 else:raise AssertionError('admitted '+name)
 ck(not any(p.name.endswith('metadata.json') for p in dest.iterdir()),'no success metadata '+name)
 return dest
folder,dest,call=run_case('valid');r=call();ck(r['members']==4 and r['regular_bodies']==2 and r['instantiated_posix_tree'] is False and r['research_authority'] is False,'genuine tiny byte recovery nonauthority');meta=json.loads(R.read(dest,'body-metadata.json'));ck(meta['manifest']==manifest and all(R.read(dest,meta['flat_members'][n])==b for n,k,m,b in rows if k=='file'),'full opaque bytes and semantic names/modes')
ck(all(stat.S_IMODE(p.lstat().st_mode)==0o600 for p in dest.iterdir()) and stat.S_IMODE(dest.stat().st_mode)==0o700,'actual private flat modes distinct archived modes')
d=refuse('bad_archive_hash',info_override={'sha256':'0'*64});ck(not list(d.iterdir()),'binding refused before write');refuse('bad_manifest_hash',info_override={'manifest_sha256':'0'*64});refuse('nonprivate',destmode=0o755);refuse('foreign_output',extra=True)
refuse('mode_mismatch',raw=tar_bytes([(n,k,0o777 if n=='a/value.txt' else m,b) for n,k,m,b in rows]));refuse('missing_member',raw=tar_bytes(rows[:-1]));refuse('duplicate_member',raw=tar_bytes(rows+[rows[-1]]));refuse('unknown_member',raw=tar_bytes(rows+[('z','file',0o600,b'z')]));refuse('noncanonical_gzip',raw=tar_bytes(rows,mtime=1));bad=json.loads(json.dumps(manifest));bad['members'][1]['path']='../escape';refuse('traversal_manifest',m=bad)
# First fatal identity and close-everything semantics with actual exceptions/callbacks.
seen=[];fatal=MemoryError('original tiny fatal');later=SystemExit('later tiny fatal')
def action(n,error=None):
 def f():
  seen.append(n)
  if error is not None:raise error
 return f
try:
 try:raise fatal
 finally:_cleanup((action(1,ValueError('close')),action(2,later),action(3)))
except BaseException as e:ck(e is fatal and seen==[1,2,3],'original firstfatal identity/all callbacks')
seen.clear()
try:_cleanup((action(1,ValueError('close')),action(2,later),action(3)),primary=None)
except BaseException as e:ck(e is later and seen==[1,2,3],'laterfatal outranks ordinary/all callbacks')
else:raise AssertionError('missing fatal')
# Restore failure after an actual acquired directory closes its FD and retains partial bytes.
folder,dest,unused=run_case('injected_body_failure');owned=R.FlatOutput(dest);fd_seen=[];orig_begin=R.FlatOutput.begin;orig_create=R.FlatOutput.create;fatal2=MemoryError('tiny body-write fatal')
def begin(self):orig_begin(self);fd_seen.append(self.fd)
def create(self,name,body):raise fatal2
R.FlatOutput.begin=begin;R.FlatOutput.create=create
try:
 try:unused()
 except BaseException as e:ck(e is fatal2,'restore actual firstfatal identity')
 else:raise AssertionError('lost fatal')
finally:R.FlatOutput.begin=orig_begin;R.FlatOutput.create=orig_create
for fd in fd_seen:
 try:os.fstat(fd)
 except OSError:ck(True,'owned root descriptor closed after fatal')
 else:raise AssertionError('descriptor leak')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports');out={'schema_version':1,'decision':'ACCEPTED_FLAT_CALLER_SOURCE_ONLY_PENDING_ACTUAL_TRANSPORT_AND_RECOVERY','candidate_sha256':sha(source),'primitive_sha256':pins,'fixed_capture_sha256':expected,'checks':len(checks),'checks_detail':checks,'actual_remote_receipt_available_or_authenticated':False,'actual_flat_executed':False,'tiny_opaque_fixtures_only':True,'source_execution_authority':False};(O/'READBACK01.json').write_bytes(R.encode(out));print(json.dumps({k:v for k,v in out.items() if k!='checks_detail'},indent=2))
