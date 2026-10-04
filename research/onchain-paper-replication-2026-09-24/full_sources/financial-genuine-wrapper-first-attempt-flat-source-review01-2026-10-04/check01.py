import ast,difflib,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-root-flat-recovery04-2026-10-04';T=F/'financial-genuine-wrapper-root-remote-recovery04-2026-10-04';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';C=F/'financial-genuine-wrapper-root-preservation06-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
b=(P/'restore01.py').read_bytes();t=ast.parse(b);ck(sha(b)=='1b36e40c96045f35ea4a4e6926b9da6a594ab82c0346aa0ddb6c2bbb5aa5c02c','exactflat')
def literal(n):return next(ast.literal_eval(x.value) for x in t.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==n for y in x.targets))
pins=literal('PINS');expected=literal('EXPECTED')
for n,h in pins.items():ck(sha((U/n).read_bytes())==h,'exact acceptedprimitive')
for n,h in expected.items():ck(sha((C/n).read_bytes())==h,'actualcapturepin '+n)
ck(len(expected)==8,'eight completecapturepins');sys.path.insert(0,str(U));sp=importlib.util.spec_from_file_location('three_target_review',U/'recovery04.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
def read(p):return R.read(p.parent,p.name)
review=F/'financial-genuine-wrapper-first-attempt-preservation-review01-2026-10-04';ck(sha(read(review/'MANIFEST01.json'))=='9f58e0dc7b4069e496a4bf343119fdba6882fec0ff2685ac10c6940f08ae9b17','acceptedactualcapture manifest');rm=json.loads(read(review/'MANIFEST01.json'));ck({p.name for p in review.iterdir()}=={r['path'] for r in rm['entries']}|{'MANIFEST01.json'},'completeactualcapture review')
for r in rm['entries']:ck(sha(read(review/r['path']))==r['sha256'] and stat.S_IMODE((review/r['path']).stat().st_mode)==r['mode'],'acceptedbodymode')
old=read(F/'financial-genuine-wrapper-root-remote-recovery03-2026-10-04/recover_financial03.py');new=read(T/'recover_financial04.py');ck(sha(old)=='8531e7bfeac0ae71091d6d2cb6feb5dde5c891e4a86faca626a5757cf7fe8bd2' and sha(new)=='188a60d2dace234a2090024109ca6cf7beb2b3355b1e759631eac8b4160dfb31','transport both accepted/current pins');oc=[n.value for n in ast.walk(ast.parse(old)) if isinstance(n,ast.Constant)];nc=[n.value for n in ast.walk(ast.parse(new)) if isinstance(n,ast.Constant)];pairs=[(a,b) for a,b in zip(oc,nc) if a!=b];ck(len(pairs)==3 and len(oc)==len(nc) and all(isinstance(v,str) for pair in pairs for v in pair),'only three string deltas');inverse=new.decode()
for before,after in pairs:ck(inverse.count(after)==1,'unique transport literal');inverse=inverse.replace(after,before)
ck(inverse.encode()==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old)),'full transport byte/AST inverse');ck('len(CALLS) < 1024' in new.decode() and 'START < 600' in new.decode() and 'begun < 60' in new.decode() and 11+2*506==1023 and 11+2*507>1024,'effective506 finiteops/time unchanged');(O/'TRANSPORT_DELTA01.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True))))
priorflat=read(F/'financial-genuine-wrapper-root-flat-recovery03-2026-10-04/restore01.py');ck(sha(priorflat)=='ca8bd0042db431e6c4d48ffbf7b55814ca4e68b4ec1d37a2f8f21c442813cfd6','accepted flat03 baseline');(O/'FLAT_DELTA01.diff').write_text(''.join(difflib.unified_diff(priorflat.decode().splitlines(True),b.decode().splitlines(True))))
main=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='main');text=ast.unparse(main);ck(text.index("'actual remote receipt'")<text.index("'actual Git OID'")<text.index("R.put(HERE / 'INTENT01.json'")<text.index('R.restore(')<text.index("'actual original failed terminal semantics'")<text.index("R.put(HERE / 'RECOVERY01.json'"),'actual authenticated lineage/write/terminal/success order');ck('R.authenticate_source' not in text and 'R.recover(' not in text,'no fixedheld API');ck("('flat-source01', 'flat-parent01', 'flat-outer01', 'INTENT01.json')" in text and "'independent_failed_scope_acceptance': False" in text and "'original_identity_permanently_reserved': True" in text,'allthree fresh andreserved noacceptanceclaim')
def predicate(message):return next(n for n in ast.walk(main) if isinstance(n,ast.Call) and ast.unparse(n.func)=='R.require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value==message)
def evaluate(message,ns):return eval(compile(ast.Expression(predicate(message)),message,'eval'),dict(ns,R=R,os=os))
for rows,allow in [([],False),([{'path':'a'},{'path':'a'}],False),([{'path':str(i)} for i in range(507)],False),([{'path':str(i)} for i in range(506)],True)]:
 try:evaluate('finite unique actual remote selection',{'rows':rows})
 except ValueError:ck(not allow,'finiteunique refuses')
 else:ck(allow,'finiteunique maxallows')
cap=json.loads(read(C/'CAPTURE01.json'));request=json.loads(read(C/'REQUEST01.json'))
for label in ['source','parent','outer']:
 m=json.loads(read(C/(label.upper()+'_MANIFEST01.json')));pin=expected[label.upper()+'_MANIFEST01.json'];ns={'cap':cap,'request':request,'pin':pin,'EXPECTED':expected,'label':label,'m':m};evaluate('archive manifest lineage',ns);evaluate('entire target cardinality',ns);ck(True,'actualthree lineage/cardinality '+label);bad=json.loads(json.dumps(cap));bad['archives'][label]['manifest_sha256']='0'*64
 try:evaluate('archive manifest lineage',dict(ns,cap=bad))
 except ValueError:ck(True,'wronglineage refuses '+label)
 else:raise AssertionError('wronglineage accepted')
evaluate('exact original failed byte capture',{'cap':cap,'request':request,'EXPECTED':expected});evaluate('original failed identity and actual versus NULL exits',{'cap':cap,'request':request});ck(True,'exact realcaptured failedsemantics')
for field,value in [('actual_outer_exit',0),('original_parent_terminal_exit',1)]:
 bad=dict(cap);bad[field]=value
 try:evaluate('original failed identity and actual versus NULL exits',{'cap':bad,'request':request})
 except ValueError:ck(True,'fake exit/refund interpretation refused')
 else:raise AssertionError('changedexit accepted')
loop=next(n for n in main.body if isinstance(n,ast.For) and 'R.restore' in ast.unparse(n));i=main.body.index(loop);mapping=[]
for n in main.body[i+1:]:
 if isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='result' for z in n.targets):break
 mapping.append(n)
loopcode=compile(ast.Module(body=[loop],type_ignores=[]),'exact failedthree loop','exec');mapcode=compile(ast.Module(body=mapping,type_ignores=[]),'exact failed metadata mapping','exec');fixture=O/'tiny01';fixture.mkdir(mode=0o700);realP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-root-launch-20261004-01');realOuter=F/'financial-genuine-wrapper-root-first-launch01-2026-10-04'
def setup(name):
 d=fixture/name;d.mkdir(mode=0o700);bundle=d/'bundle';bundle.mkdir(mode=0o700);here=d/'output';here.mkdir(mode=0o700);manifests={};archives={}
 for label in ['source','parent','outer']:
  src=d/('input-'+label);src.mkdir(mode=0o700);(src/'opaque.bin').write_bytes((label+'\x00opaque\n').encode())
  if label=='parent':
   (src/'REQUEST_FINAL03.json').write_bytes(read(realP/'REQUEST_FINAL03.json'));(src/'attempt').mkdir(mode=0o700);(src/'attempt/parent-terminal.json').write_bytes(read(realP/'attempt/parent-terminal.json'))
  if label=='outer':(src/'ACTUAL_TERMINAL01.json').write_bytes(read(realOuter/'ACTUAL_TERMINAL01.json'))
  manifests[label]=R.scan(src);archives[label]=R.pack(src,manifests[label],bundle/('complete-'+label+'01.tar.gz'))
 observations=[]
 def floor():observations.append(True)
 return {'HERE':here,'bundle':bundle,'manifests':manifests,'cap':{'archives':archives},'actual':{},'R':R,'json':json,'floor':floor},observations
ns,obs=setup('success');exec(loopcode,ns);exec(mapcode,ns);ck(set(ns['actual'])=={'source','parent','outer'} and len(obs)==6,'real tinythree recovery plus actualoriginalreceipt mapping');ck(ns['parent_terminal']['actual_parent_exit'] is None and ns['outer_terminal']['actual_parent_exit']==1,'actual copied originalNULL/root1 retained')
for label in ['source','parent','outer']:
 dest=ns['HERE']/('flat-'+label+'01');meta=json.loads(R.read(dest,'body-metadata.json'));ck(R.read(dest,meta['flat_members']['opaque.bin'])==(label+'\x00opaque\n').encode(),'real opaque pipeline '+label);ck(all(stat.S_IMODE(p.stat().st_mode)==0o600 and p.stat().st_nlink==1 for p in dest.iterdir()),'allactualtiny files0600singlelink')
# Missing actual flat semantic body refuses; only this owned tiny copy is removed.
leaf=ns['parent_metadata']['flat_members']['attempt/parent-terminal.json'];(ns['HERE']/'flat-parent01'/leaf).unlink()
try:exec(mapcode,ns)
except FileNotFoundError:ck(True,'missing recovered terminal body refuses')
else:raise AssertionError('missingbody accepted')
ns,obs=setup('outer_bad_footer');p=ns['bundle']/'complete-outer01.tar.gz';raw=p.read_bytes()+b'\0';p.write_bytes(raw);ns['cap']['archives']['outer'].update(bytes=len(raw),sha256=sha(raw))
try:exec(loopcode,ns)
except ValueError as e:ck('canonical' in str(e) or 'framing' in str(e),'hashcorrect noncanonicalfooter rejected');footer=str(e)
else:raise AssertionError('footer accepted')
ck(set(ns['actual'])=={'source','parent'} and not (ns['HERE']/'flat-outer01/body-metadata.json').exists(),'firsttwo retained third no metadata')
try:evaluate('one-use three-target namespace',{'HERE':ns['HERE']})
except ValueError:ck(True,'partial namespace refused')
else:raise AssertionError('partial reused')
ns,obs=setup('outer_bad_binding');ns['cap']['archives']['outer']['manifest_sha256']='0'*64
try:exec(loopcode,ns)
except ValueError as e:ck(str(e)=='archive binding differs','wrongarchive manifestbinding refused')
else:raise AssertionError('badbinding accepted')
ck(set(ns['actual'])=={'source','parent'} and list((ns['HERE']/'flat-outer01').iterdir())==[],'third no writes before binding')
ns,obs=setup('outer_fatal');ocreate=R.FlatOutput.create;oclose=R.FlatOutput.close;fatal=MemoryError('original third-target fixture write');closed=[]
def create(self,*args,**kwargs):
 if self.dest.name=='flat-outer01':raise fatal
 return ocreate(self,*args,**kwargs)
def close(self):
 oclose(self);closed.append(self.dest.name)
 if self.dest.name=='flat-outer01':raise OSError('after actual close ordinaryerror')
R.FlatOutput.create=create;R.FlatOutput.close=close
try:
 try:exec(loopcode,ns)
 except BaseException as e:ck(e is fatal and 'flat-outer01' in closed,'originalfatal survives ordinary actualclose failure')
 else:raise AssertionError('fatal hidden')
finally:R.FlatOutput.create=ocreate;R.FlatOutput.close=oclose
ck(set(ns['actual'])=={'source','parent'} and not (ns['HERE']/'RECOVERY01.json').exists(),'fatal firsttwo retained nooverall receipt');ck(all(not (P/n).exists() for n in ['flat-source01','flat-parent01','flat-outer01','INTENT01.json','RECOVERY01.json']),'actual failedflat notexecuted');ck(all(not (T/n).exists() for n in ['fresh-financial04.git','selected','REMOTE_RECOVERY01.json']),'actualfailedtransport notexecuted');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','tradingagents'} for n in sys.modules),'no numerical lifecycle imports');out={'schema_version':1,'decision':'ACCEPTED_ORIGINAL_FAILED_SCOPE_TRANSPORT_FLAT_SOURCE_ONLY','checks':len(checks),'flat_source_sha256':sha(b),'transport_source_sha256':sha(new),'transport_exact_three_string_inverse':pairs,'actual_capture_pins':expected,'primitive_pins':pins,'targets':{'source':878,'parent':30,'outer':8},'expected_actual_private_files':670,'tiny_three_target_pipeline':True,'tiny_original_receipt_copies_authentic':True,'footer_refusal':footer,'partial_and_original_fatal_retained':True,'actual_failedscope_recovery':False,'actual_external_origin_verified':False,'independent_failedscope_acceptance':False,'original_identity_permanently_reserved':True,'further_numerical_release_halted':True,'native_authority':False};(O/'READBACK01.json').write_bytes(R.encode(out));print(json.dumps(out,indent=2))
