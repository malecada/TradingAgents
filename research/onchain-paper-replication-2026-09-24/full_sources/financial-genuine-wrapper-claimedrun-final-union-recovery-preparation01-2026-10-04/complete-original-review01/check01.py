import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(x,m):
 assert x,m
 checks.append(m)
raw=(P/'MANIFEST01.json').read_bytes();ck(sha(raw)=='4cdd415f9f318c5931da073709383825e8c7e9edcf5b6d601253d2fe2f8f86be','frozen candidate manifest');manifest=json.loads(raw);ck({p.relative_to(P).as_posix() for p in P.rglob('*')}=={r['path'] for r in manifest['members']}|{'MANIFEST01.json'},'complete candidate membership')
for r in manifest['members']:
 p=P/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'all frozen modes')
 if r['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'all frozen source/evidence bodies')
 else:ck(r['kind']=='directory' and stat.S_ISDIR(s.st_mode),'all typed directories')
ck(sha((P/'restore_union01.py').read_bytes())=='2bda6b41ef21c1ed8e1e38a10d5cc3f982ae8d30beb5ae4425fe2b701ee3cc02','exact concrete adapter')
for n in ['recovery04.py','owned_io.py','bounded_git01.py']:ck((P/n).read_bytes()==(O.parent/'held-consumer-final-recovery-preparation04-2026-10-03'/n).read_bytes(),'full unchanged primitive inverse '+n)
sys.path.insert(0,str(P));sp=importlib.util.spec_from_file_location('union_source_review',P/'restore_union01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);R=M.R
errors=[]
def refuse(label,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,FileExistsError) as e:errors.append({'label':label,'type':type(e).__name__,'message':str(e)});ck(True,label)
 else:raise AssertionError('missing refusal '+label)
q=json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes());refuse('genuine null actual request',lambda:M.request(q))
for key,value in [('schema_version',True),('extra',1)]:
 z=dict(q);z[key]=value;refuse('request '+key,lambda z=z:M.request(z))
# Tiny owned ordinary archive: lexical link text is ordinary opaque JSON, never a link object.
owned=O/'owned';owned.mkdir(mode=0o700);src=owned/'ordinary';src.mkdir(mode=0o700);(src/'group').mkdir();(src/'group/opaque').write_bytes(b'complete tiny opaque body\x00');(src/'lexical.json').write_bytes(R.encode({'scope':'synthetic opaque test metadata only','literal_target':'/never/follow/or/materialize'}));m=R.scan(src);den={'expected_members':3,'expected_files':2,'expected_logical_bytes':sum(r.get('bytes',0) for r in m['members'])};ck(M.manifest_join(den,R.encode(m))==m,'actual tiny manifest denominator')
for k in den:
 z=dict(den);z[k]+=1;refuse('wrong exact denominator '+k,lambda z=z:M.manifest_join(z,R.encode(m)))
archive=owned/'tiny.tar.gz';info=R.pack(src,m,archive);dest=owned/'flat';M.reserve(dest);result=M.restore_ordinary(archive,info,m,dest);meta=json.loads(R.read(dest,result['metadata_file']));ck(result['regular_bodies']==2 and set(meta['flat_members'])=={'group/opaque','lexical.json'},'actual complete tiny flat mapping')
for n,leaf in meta['flat_members'].items():ck(R.read(dest,leaf)==(src/n).read_bytes() and stat.S_IMODE((dest/leaf).stat().st_mode)==0o600,'real tiny flat opaque body and mode')
ck(not (dest/'group').exists() and not (dest/'never').exists(),'no semantic path or link instantiated');refuse('oneuse output reserve',lambda:M.reserve(dest));refuse('oneuse flat body namespace',lambda:M.restore_ordinary(archive,info,m,dest))
# In-memory eleven-tree schema projections only, not fabricated actual capture/remote/release records.
scopes=sorted({'actual-parent','root-parent-adoption','final-parent-review','root-verifier-binding','actual-verifier-review','binder-preparation','binder-review','caller-preparation','caller-review','verifier-preparation','verifier-review'})
trees=[{'scope':n,'original_root':str(owned/n),'members':[{'path':'.','kind':'directory','mode':0o700}]} for n in scopes];trees[0]['members'].append({'path':'literal','kind':'lexical-symlink','mode':0o777,'target':'/never/follow'})
mapping={'schema_version':1,'scope':'explicit synthetic schema projection only; not actual union','source_manifest_sha256':'26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53','source_archive_sha256':'8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb','source_full_recovery_readback_sha256':'f86497ee97d6b5d91066db1aa2520d1bed844165b4e08d7169a5917c5bfda4df','source_commit':'649fb8a11089524aaef7843dffeeb90a3a55ca17','scope_trees':trees,'original_regular_logical_bytes':0,'runtime_bodies_or_empirical_stores_recovered':False,'links_followed_or_extracted':False,'native_or_numerical_started':False}
def projection(value):
 metadata=R.encode(value);members=[{'path':'ORIGINAL_TREES01.json','kind':'file','mode':0o600,'bytes':len(metadata),'sha256':R.digest(metadata)}]+[{'path':n,'kind':'directory','mode':0o700} for n in scopes];ordinary={'schema_version':1,'root_mode':0o700,'members':sorted(members,key=lambda r:r['path'])};pin={'archive':{'bytes':0,'sha256':'0'*64},'manifest':{'sha256':R.digest(R.encode(ordinary))}};auth={'schema_version':1,'status':'complete-final-caller-review-byte-capture','archive':dict(pin['archive'],manifest_sha256=pin['manifest']['sha256']),'union_mapping_sha256':R.digest(metadata),'ordinary_members':12,'original_trees':11,'original_typed_members':12,'original_regular_members':0,'original_lexical_links':1,'source_capture_reused_unchanged':True,'genuine_native_or_numerical_started':False,'elapsed_seconds':0,'free_bytes':R.FLOOR,'qualification':'synthetic in-memory schema projection only'};return pin,ordinary,auth,metadata
pin,ordinary,auth,metadata=projection(mapping);v=M.authenticate_union(pin,ordinary,R.encode(auth),metadata);ck(v['original_trees']==11 and v['original_lexical_links']==1 and v['links_followed'] is False,'explicit synthetic11schema/link accounting')
for label,mutate in [('missing_tree',lambda z:z['scope_trees'].pop()),('duplicate_tree',lambda z:z['scope_trees'].__setitem__(1,z['scope_trees'][0])),('source_commit',lambda z:z.update(source_commit='0'*40)),('links_followed',lambda z:z.update(links_followed_or_extracted=True)),('boolean_mode',lambda z:z['scope_trees'][0]['members'][0].update(mode=True)),('missing_parent',lambda z:z['scope_trees'][0]['members'][1].update(path='missing/link')),('invented_actual_field',lambda z:z.update(fake_authority=True))]:
 z=copy.deepcopy(mapping);mutate(z);p2,m2,a2,b2=projection(z);refuse(label,lambda:M.authenticate_union(p2,m2,R.encode(a2),b2))
for label,mutate in [('bad_archive_pin',lambda z:z['archive'].update(sha256='1'*64)),('bad_mapping_pin',lambda z:z.update(union_mapping_sha256='1'*64)),('wrong_count',lambda z:z.update(original_lexical_links=0)),('native_true',lambda z:z.update(genuine_native_or_numerical_started=True)),('low_floor',lambda z:z.update(free_bytes=R.FLOOR-1))]:
 z=copy.deepcopy(auth);mutate(z);refuse(label,lambda z=z:M.authenticate_union(pin,ordinary,R.encode(z),metadata))
# Exact firstfatal semantics with real exceptions and all cleanup callbacks executed.
classes=[ValueError,MemoryError,KeyboardInterrupt,SystemExit]
for A in classes:
 for B in classes:
  first=A('original');later=B('cleanup');events=[]
  def fail():events.append('first');raise later
  def finish():events.append('last')
  observed=None
  try:
   try:raise first
   except BaseException as e:primary=e
   finally:R._cleanup((fail,finish),primary=primary)
   raise primary
  except BaseException as e:observed=e
  firstfatal=isinstance(first,MemoryError) or not isinstance(first,Exception);laterfatal=isinstance(later,MemoryError) or not isinstance(later,Exception)
  ck((observed is first if firstfatal else observed is later if laterfatal else type(observed).__name__=='CleanupFailure' and observed.failures==(first,later)) and events==['first','last'],'real firstfatal ordered cleanup '+A.__name__+'/'+B.__name__)
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_FINAL_UNION_RECOVERY_ADAPTER_SOURCE_ONLY_PENDING_ACTUAL_REQUEST_AND_RELEASE','checks':len(checks),'helper_sha256':sha((P/'restore_union01.py').read_bytes()),'candidate_manifest_sha256':sha(raw),'unchanged_R4_primitive_bodies':True,'actual_remote_or_full_union_restore':False,'actual_request_or_release':None,'synthetic_schema_projection_is_actual_capture':False,'refusals':errors,'numerical_or_native_authority':False,'qualification':'Copied Root capture01 is historical schema evidence only; late-extra successor acceptance is independent and not inferred. Exact future pins/current original membership must be independently reviewed.'}
(O/'READBACK01.json').write_bytes(R.encode(out));print(json.dumps(out,indent=2))
