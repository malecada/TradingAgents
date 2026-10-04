import ast,copy,hashlib,importlib.util,json,os,stat,sys,types
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-recordfix-failed-scope-recovery-preparation01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];refusals=[]
def ck(v,m):assert v,m;checks.append(m)
def refuses(n,f):
 try:f()
 except (ValueError,TypeError,KeyError,FileExistsError) as e:refusals.append({'name':n,'type':type(e).__name__,'message':str(e)});ck(True,n)
 else:raise AssertionError('missing refusal '+n)
mr=(P/'MANIFEST01.json').read_bytes();ck(sha(mr)=='ccc79a5107ebe0b9db370ea42bcad984dfb2ee72e1284e7565e6c977dc9c2a38','frozen preparation manifest');m=json.loads(mr);ck({p.relative_to(P).as_posix() for p in P.rglob('*')}=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete candidate namespace')
for r in m['members']:
 p=P/r['path'];s=p.lstat();ck(oct(stat.S_IMODE(s.st_mode))==r['mode'],'candidate original mode')
 if r['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'candidate actual regular body')
 else:ck(r['kind']=='directory' and stat.S_ISDIR(s.st_mode),'candidate typed directory')
ck(sha((P/'restore01.py').read_bytes())=='9996683a2e10905426c110097379514d1fdd152c23ff1935aa6e197ea791257f','actual adapter pin')
for n in ['recovery04.py','owned_io.py','bounded_git01.py']:ck((P/n).read_bytes()==(F/'held-consumer-final-recovery-preparation04-2026-10-03'/n).read_bytes(),'complete accepted primitive byte inverse '+n)
sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('failedscope_adapter',P/'restore01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);R=M.R
ck((P/'original-review-pin-draft01.py').read_bytes().replace((M.CAPTURE_REVIEW+'19').encode(),M.CAPTURE_REVIEW.encode())==(P/'restore01.py').read_bytes(),'only overlong original pin correction inverse')
q=json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes());refuses('actual unknown draft',lambda:M.request(q));rootq=json.loads((F/'financial-genuine-wrapper-root-recordfix-failed-flat01-2026-10-04/REQUEST_DRAFT01.json').read_bytes());refuses('actual Root null review/release draft',lambda:M.request(rootq))
for key in list(q):
 z=dict(q);z.pop(key);refuses('missing exact request '+key,lambda z=z:M.request(z))
z=dict(q,extra=True);refuses('unknown extra request',lambda:M.request(z));z=dict(q,schema_version=True);refuses('bool request schema',lambda:M.request(z))
remote=F/'financial-genuine-wrapper-root-recordfix-failed-remote01-2026-10-04';bundle,bodies=M.remote_bodies(remote,'61ce415a7b951e0922350c2c16e95b5b6d51ce4abefc4c45404e75f82ab117b2');c,ms=M.joins(bodies);ck(sum(len(v['members']) for v in ms.values())==1049 and sum(sum(r['kind']=='file' for r in v['members']) for v in ms.values())==763,'actual real received three-role manifest joins only');refuses('wrong real remote receipt digest',lambda:M.remote_bodies(remote,'0'*64))
for role in M.COUNTS:
 z=dict(bodies);value=json.loads(z[role+'-manifest.json']);value['members']=value['members'][:-1];z[role+'-manifest.json']=R.encode(value);refuses('missing actual role member '+role,lambda z=z:M.joins(z))
z=dict(bodies);z['CAPTURE01.json']=z['CAPTURE01.json']+b' ';refuses('changed capture actualbody',lambda:M.joins(z));z=dict(bodies);del z['outer-manifest.json'];refuses('missing real third role',lambda:M.joins(z))
# Only tiny opaque files are packed/restored; no claim/Owner/Run/actual outcome invented.
owned=O/'owned';owned.mkdir(mode=0o700);archives={};manifests={};infos={};results={};full=owned/'three-flat';M.reserve(full)
for i,role in enumerate(M.COUNTS):
 src=owned/('tiny-'+role);src.mkdir(mode=0o700);(src/'nested').mkdir();(src/'nested/payload').write_bytes(bytes([i])+b'opaque tiny independent review');(src/'empty').write_bytes(b'');manifest=R.scan(src);arc=owned/(role+'.tar.gz');info=R.pack(src,manifest,arc);dest=full/('flat-'+role);M.reserve(dest);result=R.restore(arc,info,manifest,dest);meta=M.recovered_metadata(dest,result,manifest);ck(len(meta['flat_members'])==2 and result['regular_bodies']==2,'actual tiny complete role '+role)
 for n,leaf in meta['flat_members'].items():ck(R.read(dest,leaf)==R.read(src,n) and stat.S_IMODE((dest/leaf).lstat().st_mode)==0o600,'actual tiny role private complete body')
 archives[role]=arc;manifests[role]=manifest;infos[role]=info;results[role]=result
 refuses('same role namespace reuse '+role,lambda dest=dest,arc=arc,info=info,manifest=manifest:R.restore(arc,info,manifest,dest));bad=copy.deepcopy(result);bad['metadata_sha256']='0'*64;refuses('wrong actual recovered metadata '+role,lambda dest=dest,bad=bad,manifest=manifest:M.recovered_metadata(dest,bad,manifest))
refuses('oneuse outer namespace',lambda:M.reserve(full))
# A real failed second role leaves completed first role intact and never creates third role.
partial=owned/'partial';M.reserve(partial);M.reserve(partial/'flat-source');first=R.restore(archives['source'],infos['source'],manifests['source'],partial/'flat-source');before=R.read(partial/'flat-source',first['metadata_file']);badarchive=owned/'bad-parent.tar.gz';badarchive.write_bytes(archives['parent'].read_bytes()[:-1]);M.reserve(partial/'flat-parent');refuses('real truncated second-role archive',lambda:R.restore(badarchive,infos['parent'],manifests['parent'],partial/'flat-parent'));ck(R.read(partial/'flat-source',first['metadata_file'])==before and not (partial/'flat-outer').exists(),'real partial first role preserved/third unstarted')
# Exact reserve function with real owned descriptors; cleanup defaults observe active primary.
node=next(n for n in ast.parse((P/'restore01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='reserve');classes=[ValueError,MemoryError,KeyboardInterrupt,SystemExit]
for i,A in enumerate(classes):
 for j,B in enumerate(classes):
  first=A('original');later=B('close');closed=[]
  def failsync(fd):raise first
  def failclose(fd):os.close(fd);closed.append(fd);raise later
  proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os) if not n.startswith('__')});proxy.fsync=failsync;proxy.close=failclose;ns=dict(M.__dict__,os=proxy);exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'restore01.py'),'exec'),ns);observed=None
  try:ns['reserve'](owned/('fatal-'+str(i)+'-'+str(j)))
  except BaseException as e:observed=e
  fatalA=isinstance(first,MemoryError) or not isinstance(first,Exception);fatalB=isinstance(later,MemoryError) or not isinstance(later,Exception);ck((observed is first if fatalA else observed is later if fatalB else type(observed).__name__=='CleanupFailure' and observed.failures==(first,later)) and len(closed)==1,'exact reserve actual firstfatal '+A.__name__+'/'+B.__name__)
  try:os.fstat(closed[0]);raise AssertionError('descriptor still open')
  except OSError:pass
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
x={'schema_version':1,'decision':'ACCEPTED_FAILED_SCOPE_THREE_ROLE_FLAT_ADAPTER_SOURCE_ONLY','checks':len(checks),'helper_sha256':sha((P/'restore01.py').read_bytes()),'preparation_manifest_sha256':sha(mr),'capture_sha256':M.CAPTURE_HASH,'capture_review_manifest_sha256':M.CAPTURE_REVIEW,'actual_received_manifest_joins':True,'tiny_real_three_role_pipeline':True,'real_partial_failure_retained':True,'actual_full_scope_restore':False,'exact_actual_release':None,'numerical_authority':False,'refusals':refusals};(O/'READBACK01.json').write_bytes(R.encode(x));print(json.dumps(x,sort_keys=True))
