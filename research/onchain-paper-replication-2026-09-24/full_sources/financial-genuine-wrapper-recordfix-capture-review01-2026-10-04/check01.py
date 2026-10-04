import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'financial-genuine-wrapper-recordfix-capture-preparation01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
raw=(P/'MANIFEST01.json').read_bytes();ck(sha(raw)=='bf017a004b512d498eac68319baac4249d9ee7c943fbfea7cba6b75bcf8a6497','exact candidate manifest');m=json.loads(raw);members=m['members'];actual={p.relative_to(P).as_posix() for p in P.rglob('*')};ck(actual=={r['path'] for r in members}|{'MANIFEST01.json'},'complete typed frozen candidate')
for r in members:
 p=P/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'all frozen modes')
 if r['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'all frozen ordinary bodies')
 elif r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'typed directory')
 elif r['kind']=='symlink':ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'symlink text only never target read')
 else:raise AssertionError('unexpected member type')
ck(sha((P/'capture01.py').read_bytes())=='c4710f2361e6f2e61b1da6e89988a6c1ff43f91f8e4e44c58b71a397feca1096','concrete helper pin')
U=O.parent/'held-consumer-final-recovery-preparation04-2026-10-03'
for n in ['recovery04.py','owned_io.py','bounded_git01.py']:ck((P/n).read_bytes()==(U/n).read_bytes(),'accepted primitive full byte inverse '+n)
sys.path.insert(0,str(P));spec=importlib.util.spec_from_file_location('capture_review_candidate',P/'capture01.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C);R=C.R
q=json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes());before=R.scan(C.CAP);ck(before==q['manifest']==json.loads((P/'CURRENT_COMPLETE_MANIFEST01.json').read_bytes()),'actual whole writable source manifest986');ck(len(before['members'])==986 and sum(x['kind']=='file' for x in before['members'])==713 and sum(x.get('bytes',0) for x in before['members'])==8642839,'actual typed/regular/logical denominator')
auth=C.authenticate();ck(auth==json.loads((P/'ACTUAL_SOURCE_AUTHENTICATION01.json').read_bytes()),'actual readonly authentication whole325Git324pins8roles194149')
errors=[]
def refuse(label,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,FileExistsError) as e:errors.append({'case':label,'type':type(e).__name__,'message':str(e)});ck(True,label)
 else:raise AssertionError('expected refusal '+label)
refuse('actual unreleased request',lambda:C.validate_request(q))
for key,value in [('schema_version',True),('source','0'*40),('capsule_root','/'),('output_root','/tmp/other')]:
 t=copy.deepcopy(q);t[key]=value;refuse('request '+key,lambda t=t:C.validate_request(t))
for kind in ['duplicate','oversize','badmode','unordered']:
 t=copy.deepcopy(before)
 if kind=='duplicate':t['members'].append(t['members'][0])
 if kind=='oversize':next(x for x in t['members'] if x['kind']=='file')['bytes']=R.FILE+1
 if kind=='badmode':t['members'][0]['mode']=-1
 if kind=='unordered':t['members'].reverse()
 refuse('manifest '+kind,lambda t=t:R.validate(t))
# Exact request schema and contract are source-reviewed; no fabricated accepted release.
ck(q['release'] is None and q['output_root'] is None,'actual release/output remain null')
owned=O/'owned';owned.mkdir(mode=0o700);tiny=owned/'source';tiny.mkdir(mode=0o700);(tiny/'dir').mkdir(mode=0o750);(tiny/'dir/a').write_bytes(b'opaque\x00first');(tiny/'b').write_bytes(b'second');tm=R.scan(tiny);archive=owned/'tiny.tar.gz';info=R.pack(tiny,tm,archive);flat=owned/'flat';flat.mkdir(mode=0o700);result=R.restore(archive,info,tm,flat);ck(result['regular_bodies']==2 and result['members']==3,'real tiny bounded canonical pack/restore')
meta=json.loads((flat/result['metadata_file']).read_bytes());ck(all((flat/leaf).read_bytes()==(tiny/n).read_bytes() for n,leaf in meta['flat_members'].items()),'actual tiny body mapping')
refuse('one-use archive',lambda:R.pack(tiny,tm,archive));refuse('one-use flat',lambda:R.restore(archive,info,tm,flat));(tiny/'b').write_bytes(b'changed');refuse('changed source',lambda:R.same(tiny,tm));redirect=owned/'redirect';redirect.symlink_to(tiny,target_is_directory=True);refuse('symlink scan',lambda:R.scan(redirect))
C.reserve(owned/'fresh');ck(stat.S_IMODE((owned/'fresh').stat().st_mode)==0o700,'actual tiny exclusive reserve0700');refuse('reserve reused identity',lambda:C.reserve(owned/'fresh'))
# Reproduce exact capture finalization shape with real exception instances; no capture receipt.
tree=ast.parse((P/'capture01.py').read_text());capture=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='capture');cleanup_calls=[n for n in ast.walk(capture) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_cleanup'];ck(len(cleanup_calls)==1 and ast.unparse(cleanup_calls[0])=='R._cleanup((terminal,), primary=primary)','exact finalizer firstfatal seam')
for primary in [MemoryError('first memory'),KeyboardInterrupt('first interrupt'),SystemExit('first system')]:
 events=[]
 def terminal():events.append('terminal');raise OSError('write failure')
 try:
  try:raise primary
  except BaseException as e:saved=e
  finally:R._cleanup((terminal,),primary=primary)
  raise saved
 except BaseException as observed:ck(observed is primary and events==['terminal'],'original actual firstfatal identity '+type(primary).__name__)
events=[];first=ValueError('ordinary body');fatal=MemoryError('later terminal fatal')
def terminal_fatal():events.append('terminal');raise fatal
try:R._cleanup((terminal_fatal,),primary=first)
except BaseException as observed:ck(observed is fatal and events==['terminal'],'later real fatal outranks ordinary')
else:raise AssertionError('later fatal swallowed')
ck(R.scan(C.CAP)==before and C.authenticate()==auth,'actual complete source stable after readonly checks')
ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numerical imports')
out={'schema_version':1,'decision':'ACCEPTED_CAPTURE_HELPER_SOURCE_ONLY_EXACT_REQUEST_RELEASE_STILL_REQUIRED','checks':len(checks),'helper_sha256':sha((P/'capture01.py').read_bytes()),'candidate_manifest_sha256':sha(raw),'source':C.SOURCE,'source_manifest_sha256':R.digest(R.encode(before)),'actual_members':986,'actual_regular':713,'actual_logical_bytes':8642839,'tracked':325,'source_pins':324,'implementation':194,'package':149,'actual_source_review_sha256':q['source_review']['sha256'],'actual_source_review_manifest_sha256':q['review_manifest']['sha256'],'actual_capsule_capture_count':0,'actual_independent_capture_contract_released':False,'refusals':errors,'native_or_numerical_authority':False}
(O/'READBACK01.json').write_bytes(R.encode(out));print(json.dumps(out,indent=2))
