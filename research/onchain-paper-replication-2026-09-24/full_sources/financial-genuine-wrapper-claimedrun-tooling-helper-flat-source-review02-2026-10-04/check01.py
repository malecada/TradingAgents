import ast,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B/'financial-genuine-wrapper-root-claimedrun-tooling-helper-flat01-2026-10-04';OLD=B/'financial-genuine-wrapper-claimedrun-tooling-helper-flat-source-review01-2026-10-04';checks=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
s=(ROOT/'restore_scopes01.py').read_text();old=(ROOT/'SOURCE_DRAFT02_8dd.py').read_text();ok(sha(s.encode())=='82ac718ccca22234a6d4425d99c5aa41aba0b6173c1d0fa5424b8f1ae084fdab','exact new source');ok(sha(old.encode())=='8dd3640ea7e5bd58f30de1c091f68c0272205be9a20ed36f8bb322841f9c8880','exact old source');ok(old.encode()==(OLD/'ORIGINAL_restore_scopes01.py').read_bytes(),'old review raw authentic');ok(sha((OLD/'MANIFEST01.json').read_bytes())=='31439250f852e81c19659327366156deac5a378b2c76ce3a5514c999534d2178','genuine withheld review')
added="os.mkdir(dest,0o700);R.require(dest.resolve()==dest and (dest.lstat().st_mode & 0o777)==0o700,'fresh private per-scope output');";ok(s.count(added)==1,'one exact added correction');inverse=s.replace(added,'');ok(inverse==old,'complete byte inverse');ok(ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)),'complete AST inverse')
for n in ['recovery04.py','owned_io.py','bounded_git01.py','REQUEST_DRAFT01.json']:
 ok((ROOT/n).read_bytes()==(OLD/('ORIGINAL_'+n)).read_bytes(),'unchanged '+n)
sys.path.insert(0,str(ROOT));import recovery04 as R
qraw=(ROOT/'REQUEST_DRAFT01.json').read_bytes();q=json.loads(qraw);ok(sha(qraw)=='42981fa8219e36288027946c1fdcae216fda09777898fa7761214cbe775b4043','fixed actual draft');ok(q['actual_execution'] is False and q['remote_commit'] is None and q['remote_receipt_sha256'] is None,'future pins unavailable')
ns={'__name__':'only_definitions','__file__':str(ROOT/'restore_scopes01.py')};exec(compile(s,'new source','exec'),ns);ok(not os.path.lexists(ROOT/'flat-eight-scopes01'),'Root output absent before')
argv=sys.argv;sys.argv=['review','--request',str(ROOT/'REQUEST_DRAFT01.json'),'--sha256',sha(qraw)]
try:ns['main']()
except ValueError as e:ok(str(e)=='released fixed eight ordinary scopes','actual earlyNULL refusal')
else:raise AssertionError('draft accepted')
finally:sys.argv=argv
ok(not os.path.lexists(ROOT/'flat-eight-scopes01'),'Root output absent after')
# Exact old/new loop body on a real tiny opaque pack. No remote receipt/admission is constructed.
fixture=H/'tiny-opaque';fixture.mkdir(mode=0o700);source=fixture/'source';source.mkdir(mode=0o700);(source/'body').write_bytes(b'opaque');metadata=R.encode({'tiny_utility_fixture':True});(source/'CAPTURE_ORIGINAL_TREE01.json').write_bytes(metadata);m=R.scan(source);remote=fixture/'remote-shaped-opaque-container';remote.mkdir(mode=0o700);selected=remote/'selected';selected.mkdir(mode=0o700);info=R.pack(source,m,selected/'tiny.tar.gz');scope={'label':'opaque-only','archive':dict(info,path='tiny.tar.gz'),'manifest':{'sha256':R.digest(R.encode(m))},'original_metadata_sha256':sha(metadata)}
results={}
def loopbody(text):
 tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');tr=next(n for n in main.body if isinstance(n,ast.Try));loop=next(n for n in tr.body if isinstance(n,ast.For));return compile(ast.fix_missing_locations(ast.Module(body=loop.body,type_ignores=[])),'<exact source loop body>','exec')
for label,text in [('old',old),('new',s)]:
 out=fixture/label;out.mkdir(mode=0o700);local={'R':R,'os':os,'Path':Path,'json':json,'out':out,'i':0,'s':scope,'m':m,'remote':remote,'results':[],'floor':lambda:None}
 try:exec(loopbody(text),local)
 except FileNotFoundError as e:ok(label=='old','old loop genuine missingdirectory RED');results[label]={'error':type(e).__name__,'message':str(e),'recovered_bodies':0}
 else:
  ok(label=='new','corrected loop GREEN');dest=out/'scope-00';ok(stat.S_IMODE(dest.stat().st_mode)==0o700,'actual private directory');ok(len(local['results'])==1 and (out/'COMPLETED_SCOPE00.json').exists(),'exact loop publishes completion');result=local['results'][0]['result'];ok(result['regular_bodies']==2 and result['research_authority'] is False,'genuine tiny whole flat bytes noauthority');md=json.loads(R.read(dest,result['metadata_file']));ok(R.read(dest,md['flat_members']['body'])==b'opaque' and R.read(dest,md['flat_members']['CAPTURE_ORIGINAL_TREE01.json'])==metadata,'full original opaque bytes');results[label]={'result':result,'directory_mode':stat.S_IMODE(dest.stat().st_mode)}
# Reuse existing private target refuses before original restore.
local=dict(local);local['results']=[]
try:exec(loopbody(s),local)
except FileExistsError:ok(True,'existing scope refuses')
else:raise AssertionError('scope reused')
# New prefix with an owned redirect refuses canonicality; retained created child is explicit.
physical=fixture/'physical';physical.mkdir(mode=0o700);redirect=fixture/'redirect';redirect.symlink_to('physical');dest=redirect/'scope-00';prefix=compile(ast.parse(added).body[0:2] and ast.Module(body=ast.parse(added).body,type_ignores=[]),'<exact directory prefix>','exec')
try:exec(prefix,{'os':os,'R':R,'dest':dest})
except ValueError as e:ok(str(e)=='fresh private per-scope output','redirect canonicality refusal');ok((physical/'scope-00').is_dir(),'retained child before refusal explicitly recorded')
else:raise AssertionError('redirect accepted')
for n in ['restore_scopes01.py','SOURCE_DRAFT02_8dd.py','REQUEST_DRAFT01.json','PREPARATION_CORRECTION02.json']:
 with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((ROOT/n).read_bytes())
r={'schema_version':1,'status':'ACCEPTED_SOURCE_ONLY','checks':len(checks),'check_names':checks,'source_sha256':sha(s.encode()),'predecessor_sha256':sha(old.encode()),'whole_inverse':True,'old_new_actual_tiny_loop':results,'original_root_actual_restore':False,'actual_remote_receipt':None,'Rootoutput_reserved':False,'redirect_limitation':'Canonicality refuses redirected parent after os.mkdir; created owned physical child is retained, not a zero-sideeffect claim.','unchanged_scope_evidence':{'manifest':'31439250f852e81c19659327366156deac5a378b2c76ce3a5514c999534d2178','whole8scope_logical':52444730},'numeric_authority':False}
with (H/'READBACK01.json').open('x') as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'readback_sha256':sha((H/'READBACK01.json').read_bytes())}))
