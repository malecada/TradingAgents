"""Explicit synthetic schema projections; no actual union receipt or authority."""
import copy,json
from pathlib import Path
import restore_union01 as M
R=M.R;H=Path(__file__).resolve().parent;checks=[]
scopes=['actual-parent','root-parent-adoption','final-parent-review','root-verifier-binding','actual-verifier-review','binder-preparation','binder-review','caller-preparation','caller-review','verifier-preparation','verifier-review'];trees=[];ordinary=[]
for scope in sorted(scopes):
 rows=[{'path':'.','kind':'directory','mode':448},{'path':'a','kind':'file','mode':420,'bytes':1,'sha256':R.digest(b'x'),'union_path':scope+'/a'}]
 if scope=='actual-parent':rows.append({'path':'link','kind':'lexical-symlink','mode':511,'target':'/synthetic/do-not-follow'})
 trees.append({'scope':scope,'original_root':'/synthetic/'+scope,'members':rows});ordinary.extend([{'path':scope,'kind':'directory','mode':448},{'path':scope+'/a','kind':'file','mode':384,'bytes':1,'sha256':R.digest(b'x')}])
mapping={'schema_version':1,'scope':'synthetic source schema projection only','source_manifest_sha256':'26c67e9c9b28dd4cd607ab3833fa14143d6e8e4c7c3617024275294940ffbc53','source_archive_sha256':'8d49d60b509bc9c95cd04274127b12387b8070295499dad3d24db63b9a376efb','source_full_recovery_readback_sha256':'f86497ee97d6b5d91066db1aa2520d1bed844165b4e08d7169a5917c5bfda4df','source_commit':'649fb8a11089524aaef7843dffeeb90a3a55ca17','scope_trees':trees,'original_regular_logical_bytes':11,'runtime_bodies_or_empirical_stores_recovered':False,'links_followed_or_extracted':False,'native_or_numerical_started':False}
raw=R.encode(mapping);ordinary.append({'path':'ORIGINAL_TREES01.json','kind':'file','mode':384,'bytes':len(raw),'sha256':R.digest(raw)});manifest={'schema_version':1,'root_mode':448,'members':sorted(ordinary,key=lambda r:r['path'])};R.validate(manifest)
q={'archive':{'bytes':1,'sha256':'a'*64},'manifest':{'sha256':R.digest(R.encode(manifest))}}
auth={'schema_version':1,'status':'complete-final-caller-review-byte-capture','archive':dict(q['archive'],manifest_sha256=q['manifest']['sha256']),'union_mapping_sha256':R.digest(raw),'ordinary_members':23,'original_trees':11,'original_typed_members':23,'original_regular_members':11,'original_lexical_links':1,'source_capture_reused_unchanged':True,'genuine_native_or_numerical_started':False,'elapsed_seconds':0,'free_bytes':R.FLOOR,'qualification':'synthetic projection not a receipt'}
result=M.authenticate_union(q,manifest,R.encode(auth),raw);assert result['original_lexical_links']==1;checks.append('synthetic complete11 projection with literal link')
for field in ['ordinary_members','original_trees','original_typed_members','original_regular_members','original_lexical_links']:
 for val in [0,True,None]:
  z=copy.deepcopy(auth);z[field]=val
  try:M.authenticate_union(q,manifest,R.encode(z),raw)
  except (ValueError,KeyError,TypeError):checks.append('wrong auth '+field+str(val))
  else:raise AssertionError(field)
for field,val in [('source_capture_reused_unchanged',False),('genuine_native_or_numerical_started',True),('union_mapping_sha256','0'*64),('status','partial')]:
 z=copy.deepcopy(auth);z[field]=val
 try:M.authenticate_union(q,manifest,R.encode(z),raw)
 except (ValueError,KeyError,TypeError):checks.append('wrong scope '+field)
 else:raise AssertionError(field)
(H/'UNION_CHECKS03.json').write_bytes(R.encode({'count':len(checks),'checks':checks,'actual_union_metadata_created':False,'actual_network_or_restore':False}));print('PASS',len(checks))
