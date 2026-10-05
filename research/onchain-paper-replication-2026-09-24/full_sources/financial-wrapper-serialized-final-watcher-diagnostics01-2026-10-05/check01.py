"""Real filesystem link observations; no numeric/research authority."""
from pathlib import Path
import importlib.util,os,hashlib,json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_watch',HERE/'watch01.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
T=HERE/'actual-controls01';assert not T.exists();T.mkdir(mode=0o700);(T/'objects').mkdir(mode=0o700);(T/'outside').mkdir(mode=0o700)
(T/'objects'/'source').write_bytes(b'actual link input');os.link(T/'objects'/'source',T/'objects'/'second')
rows=[]
for scope in [None,T/'objects']:
 try:W._sample(T,owned_fetch_objects=scope)
 except ValueError as e:
  text=str(e);rows.append({'scope':None if scope is None else 'objects','error_type':type(e).__name__,'error':text})
  if scope is None:assert type(e) is ValueError and "'relative_path': 'objects/" in text and "'nlink': 2" in text and "'allowed_owned_fetch_objects': None" in text
  else:assert type(e) is W.ChangingTree and 'nlink=2' in text
 else:raise AssertionError('actual hardlink must not be accepted')
os.link(T/'objects'/'source',T/'outside'/'third')
try:W._sample(T,owned_fetch_objects=T/'outside')
except ValueError as e:
 text=str(e);assert type(e) is ValueError and "'nlink': 3" in text and "'allowed_owned_fetch_objects': 'outside'" in text;rows.append({'scope':'outside','error_type':type(e).__name__,'error':text})
else:raise AssertionError('wrong scoped link must refuse')
p=HERE/'AUTHOR_CHECK01.json';assert not p.exists();p.write_text(json.dumps({'schema_version':1,'status':'THREE_REAL_FILESYSTEM_OBSERVATIONS_PASSED','observations':rows,'qualification':'Actual filesystem link failures retain context without changing strict predicates. This does not establish the original failed fetch cause or admit a retry.'},sort_keys=True,indent=2)+'\n');print('three actual link observations passed')
