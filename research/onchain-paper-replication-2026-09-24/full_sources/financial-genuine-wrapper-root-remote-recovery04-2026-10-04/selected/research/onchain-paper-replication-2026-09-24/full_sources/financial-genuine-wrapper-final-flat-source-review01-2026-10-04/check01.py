import ast,difflib,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-root-flat-recovery03-2026-10-04';T=F/'financial-genuine-wrapper-root-remote-recovery03-2026-10-04';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';C=F/'financial-genuine-wrapper-root-preservation05-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
b=(P/'restore01.py').read_bytes();t=ast.parse(b);ck(sha(b)=='ca8bd0042db431e6c4d48ffbf7b55814ca4e68b4ec1d37a2f8f21c442813cfd6','exactflat')
def literal(n):return next(ast.literal_eval(x.value) for x in t.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==n for y in x.targets))
pins=literal('PINS');expected=literal('EXPECTED')
for n,h in pins.items():ck(sha((U/n).read_bytes())==h,'exact acceptedprimitive')
for n,h in expected.items():ck(sha((C/n).read_bytes())==h,'actualcapturepin '+n)
ck(len(expected)==8,'eight completecapturepins');sys.path.insert(0,str(U));sp=importlib.util.spec_from_file_location('three_target_review',U/'recovery04.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
def read(p):return R.read(p.parent,p.name)
review=F/'financial-genuine-wrapper-final-union-preservation-review01-2026-10-04';ck(sha(read(review/'MANIFEST01.json'))=='96d318852ae8c2bab34a132aefae29300bd501b6b5d355fc5a225dbdfc70e1c2','acceptedactualcapture manifest');rm=json.loads(read(review/'MANIFEST01.json'));ck({p.name for p in review.iterdir()}=={r['path'] for r in rm['entries']}|{'MANIFEST01.json'},'completeactualcapture review')
for r in rm['entries']:ck(sha(read(review/r['path']))==r['sha256'] and stat.S_IMODE((review/r['path']).stat().st_mode)==r['mode'],'acceptedbodymode')
old=read(F/'financial-genuine-wrapper-root-remote-recovery02-2026-10-04/recover_financial02.py');new=read(T/'recover_financial03.py');ck(sha(old)=='2d05df683ec6f12ce2e76be95cd5af0d602e40321939182a7b1fd283a9268e5f' and sha(new)=='8531e7bfeac0ae71091d6d2cb6feb5dde5c891e4a86faca626a5757cf7fe8bd2','transport both accepted/current pins');oc=[n.value for n in ast.walk(ast.parse(old)) if isinstance(n,ast.Constant)];nc=[n.value for n in ast.walk(ast.parse(new)) if isinstance(n,ast.Constant)];pairs=[(a,b) for a,b in zip(oc,nc) if a!=b];ck(len(pairs)==3 and len(oc)==len(nc) and all(isinstance(v,str) for pair in pairs for v in pair),'only three string deltas');inverse=new.decode()
for before,after in pairs:ck(inverse.count(after)==1,'unique transport literal');inverse=inverse.replace(after,before)
ck(inverse.encode()==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)),'full transport byte/AST inverse');ck('len(CALLS) < 1024' in new.decode() and 'START < 600' in new.decode() and 'begun < 60' in new.decode() and 11+2*506==1023 and 11+2*507>1024,'effective506 finiteops/time unchanged');(O/'TRANSPORT_DELTA01.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True))))
draft=read(P/'restore_draft01.py');ck(sha(draft)=='d91dae7132a9169ea64b4204578055682a0ab3a3a119091754047735ec1f460b','preserved unexecuted flatdraft');(O/'FLAT_DRAFT_DELTA01.diff').write_text(''.join(difflib.unified_diff(draft.decode().splitlines(True),b.decode().splitlines(True))))
main=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='main');text=ast.unparse(main);ck(text.index("'actual remote receipt'")<text.index("'actual Git OID'")<text.index("R.put(HERE / 'INTENT01.json'")<text.index('R.restore(')<text.index("'actual parent flat mapping'")<text.index("R.put(HERE / 'RECOVERY01.json'"),'auth beforewrite and finalmappedrequest before success');ck('R.authenticate_source' not in text and 'R.recover(' not in text,'no fixedheld API');ck("'independent_final_union_acceptance': False" in text and "'native_or_claim_started': False" in text,'no native/unionacceptance claim');ck("('flat-source01', 'flat-parent01', 'flat-review01', 'INTENT01.json')" in text,'allthree namespaces oneuse')
def predicate(message):return next(n for n in ast.walk(main) if isinstance(n,ast.Call) and ast.unparse(n.func)=='R.require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value==message)
def evaluate(message,ns):return eval(compile(ast.Expression(predicate(message)),message,'eval'),dict(ns,R=R,os=os))
for rows,allow in [([],False),([{'path':'a'},{'path':'a'}],False),([{'path':str(i)} for i in range(507)],False),([{'path':str(i)} for i in range(506)],True)]:
 try:evaluate('finite unique actual remote selection',{'rows':rows})
 except ValueError:ck(not allow,'finiteunique refuses')
 else:ck(allow,'finiteunique actual506allows')
cap=json.loads(read(C/'CAPTURE01.json'));request=json.loads(read(C/'REQUEST01.json'))
for label in ['source','parent','review']:
 m=json.loads(read(C/(label.upper()+'_MANIFEST01.json')));pin=expected[label.upper()+'_MANIFEST01.json'];ns={'cap':cap,'request':request,'pin':pin,'EXPECTED':expected,'label':label,'m':m};evaluate('archive manifest lineage',ns);evaluate('entire target cardinality',ns);ck(True,'actual three manifest lineage and count '+label)
 bad=json.loads(json.dumps(cap));bad['archives'][label]['manifest_sha256']='0'*64
 try:evaluate('archive manifest lineage',dict(ns,cap=bad))
 except ValueError:ck(True,'malformed lineage refuses '+label)
 else:raise AssertionError('lineage accepted')
# Extract precisely the real restore loop and real authenticated final mapping.
loop=next(n for n in main.body if isinstance(n,ast.For) and 'R.restore' in ast.unparse(n));i=main.body.index(loop);mapping=[]
for n in main.body[i+1:]:
 if isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='result' for z in n.targets):break
 mapping.append(n)
loopcode=compile(ast.Module(body=[loop],type_ignores=[]),'actual three-targetloop','exec');mapcode=compile(ast.Module(body=mapping,type_ignores=[]),'actual parentmapping','exec');fixture=O/'tiny01';fixture.mkdir(mode=0o700)
def setup(name):
 d=fixture/name;d.mkdir(mode=0o700);bundle=d/'bundle';bundle.mkdir(mode=0o700);here=d/'output';here.mkdir(mode=0o700);manifests={};archives={};final_body=b'opaque final request fixture\x00\n'
 for label in ['source','parent','review']:
  src=d/('input-'+label);src.mkdir(mode=0o700);(src/'opaque.bin').write_bytes((label+'\x00opaque\n').encode())
  if label=='parent':(src/'REQUEST_FINAL03.json').write_bytes(final_body)
  if label=='source':(src/('long-'+('x'*110))).mkdir(mode=0o700)
  manifests[label]=R.scan(src);archives[label]=R.pack(src,manifests[label],bundle/('complete-'+label+'01.tar.gz'))
 observations=[]
 def floor():observations.append(True)
 return {'HERE':here,'bundle':bundle,'manifests':manifests,'cap':{'archives':archives,'final_request_sha256':sha(final_body)},'actual':{},'R':R,'json':json,'floor':floor},observations
ns,obs=setup('success');exec(loopcode,ns);exec(mapcode,ns);ck(set(ns['actual'])=={'source','parent','review'} and len(obs)==6,'real three tiny targets complete')
for label in ['source','parent','review']:
 dest=ns['HERE']/('flat-'+label+'01');meta=json.loads(R.read(dest,'body-metadata.json'));ck(R.read(dest,meta['flat_members']['opaque.bin'])==(label+'\x00opaque\n').encode(),'actual recovered tinyopaque '+label);ck(all(stat.S_IMODE(p.stat().st_mode)==0o600 and p.stat().st_nlink==1 for p in dest.iterdir()),'allflatfiles0600singlelink')
# Original draft's assumed files tree really does not exist in a genuine flat recovery.
try:R.read(ns['HERE']/'flat-parent01','files/REQUEST_FINAL03.json')
except FileNotFoundError:ck(True,'RED preserved draft wrong instantiatedtree refuses')
else:raise AssertionError('instantiatedtree unexpectedly exists')
meta_path=ns['HERE']/'flat-parent01'/'body-metadata.json';saved=meta_path.read_bytes();changed=json.loads(saved);changed['flat_members']['REQUEST_FINAL03.json']='body-99999.body';meta_path.write_bytes(R.encode(changed))
try:exec(mapcode,ns)
except ValueError as e:ck(str(e)=='actual parent flat mapping','modified mapping rejected before body read')
else:raise AssertionError('modified mapping accepted')
# The tampered tiny output is deliberately retained, never passed as actual evidence.
ns,obs=setup('third_footer');p=ns['bundle']/'complete-review01.tar.gz';raw=p.read_bytes()+b'\0';p.write_bytes(raw);ns['cap']['archives']['review'].update(bytes=len(raw),sha256=sha(raw))
try:exec(loopcode,ns)
except ValueError as e:ck('canonical' in str(e) or 'framing' in str(e),'noncanonical trailing compressedfooter refuses');footer_error=str(e)
else:raise AssertionError('trailingfooter accepted')
ck(set(ns['actual'])=={'source','parent'} and not (ns['HERE']/'flat-review01/body-metadata.json').exists(),'partial firsttwo retained third no successmetadata')
try:evaluate('one-use three-target namespace',{'HERE':ns['HERE']})
except ValueError:ck(True,'partial namespace refuses reuse')
else:raise AssertionError('partial reused')
ns,obs=setup('third_bad_binding');ns['cap']['archives']['review']['manifest_sha256']='0'*64
try:exec(loopcode,ns)
except ValueError as e:ck(str(e)=='archive binding differs','bad manifest exact binding refused')
else:raise AssertionError('badbinding accepted')
ck(set(ns['actual'])=={'source','parent'} and list((ns['HERE']/'flat-review01').iterdir())==[],'firsttwo retained no thirdwrite beforeauth')
ns,obs=setup('third_fatal');original_create=R.FlatOutput.create;original_close=R.FlatOutput.close;fatal=MemoryError('original tiny third-target write fatal');closed=[]
def create(self,*args,**kwargs):
 if self.dest.name=='flat-review01':raise fatal
 return original_create(self,*args,**kwargs)
def close(self):
 original_close(self);closed.append(self.dest.name)
 if self.dest.name=='flat-review01':raise OSError('ordinary close uncertainty after actual close')
R.FlatOutput.create=create;R.FlatOutput.close=close
try:
 try:exec(loopcode,ns)
 except BaseException as e:ck(e is fatal and 'flat-review01' in closed,'original fatal identity survives ordinary actualclose error')
 else:raise AssertionError('fatal swallowed')
finally:R.FlatOutput.create=original_create;R.FlatOutput.close=original_close
ck(set(ns['actual'])=={'source','parent'} and not (ns['HERE']/'RECOVERY01.json').exists(),'fatal retains firsttwo no aggregate success');ck(all(not (P/n).exists() for n in ['flat-source01','flat-parent01','flat-review01','INTENT01.json','RECOVERY01.json']),'actual flat unexecuted');ck(all(not (T/n).exists() for n in ['fresh-financial03.git','selected','REMOTE_RECOVERY01.json']),'actual transport unexecuted');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','tradingagents'} for n in sys.modules),'no numerical/lifecycle imports');out={'schema_version':1,'decision':'ACCEPTED_THREE_TARGET_FLAT_AND_TRANSPORT_SOURCE_ONLY','checks':len(checks),'flat_source_sha256':sha(b),'transport_source_sha256':sha(new),'transport_exact_inverse':pairs,'actual_capture_pins':expected,'primitive_pins':pins,'original_draft_retained':True,'tiny_three_target_pipeline':True,'footer_refusal':footer_error,'partial_and_original_fatal_retained':True,'actual_full_archive_recovery':False,'actual_external_origin_verified':False,'actual_final_union_acceptance':False,'native_authority':False};(O/'READBACK01.json').write_bytes(R.encode(out));print(json.dumps(out,indent=2))
