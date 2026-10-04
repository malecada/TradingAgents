import ast,hashlib,importlib.util,json,os,stat,sys,time
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;P=F/'financial-genuine-wrapper-root-flat-recovery02-2026-10-04';U=F/'held-consumer-final-recovery-preparation04-2026-10-03';C=F/'financial-genuine-wrapper-root-preservation03-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):
 assert v,m
 checks.append(m)
b=(P/'restore01.py').read_bytes();t=ast.parse(b)
def literal(n):return next(ast.literal_eval(x.value) for x in t.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==n for y in x.targets))
pins=literal('PINS');expected=literal('EXPECTED')
for n,h in pins.items():ck(sha((U/n).read_bytes())==h,'exact acceptedprimitive')
for n,h in expected.items():ck(sha((C/n).read_bytes())==h,'actualfixedcapturebody')
ck(len(expected)==6,'sixexactrealcapturepins');sys.path.insert(0,str(U));sp=importlib.util.spec_from_file_location('two_target_review_primitives',U/'recovery04.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R);review=F/'financial-genuine-wrapper-full-scope-preservation-review03-2026-10-04';ck(sha(R.read(review,'MANIFEST01.json'))=='c6e9a4d2e626ab6943e1c3d8b513f849989df2683b5a7a1c879632c234736614','actualcapture independentacceptedmanifest');m=json.loads(R.read(review,'MANIFEST01.json'))
for row in m['members']:ck(sha(R.read(review,row['path']))==row['sha256'] and stat.S_IMODE((review/row['path']).stat().st_mode)==row['mode'],'complete frozenprior bodymode')
main=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='main');text=ast.unparse(main);ck(text.index("'actual remote receipt'")<text.index("'actual Git OID'")<text.index("R.put(HERE / 'INTENT01.json'")<text.index('R.restore(')<text.index("R.put(HERE / 'RECOVERY01.json'"),'actualauth/write/success ordering');ck('R.authenticate_source' not in text and 'R.recover(' not in text,'nofixedheld API');ck("('flat-source01', 'flat-parent01', 'INTENT01.json')" in text,'freshbothtargetsandintent required');ck("'final_release_recovered': False" in text and "'continuous_floor_watch_claim': False" in text,'explicitnonauthority/no continuouswatch')
# Exact finite unique-selection predicate, no fabricated receipt or authority object.
predicate=next(n for n in ast.walk(main) if isinstance(n,ast.Call) and ast.unparse(n.func)=='R.require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='finite unique actual remote selection');code=compile(ast.Expression(predicate),'exact selectedrows predicate','eval')
for rows,allow in [([],False),([{'path':'a'},{'path':'a'}],False),([{'path':str(i)} for i in range(507)],False),([{'path':str(i)} for i in range(506)],True),([{'path':'a'}],True)]:
 try:eval(code,{'R':R,'rows':rows})
 except ValueError:ck(not allow,'exactrowpredicate refuse')
 else:ck(allow,'exactrowpredicate accepts boundedunique')
# Exact two-target loop, driven solely by real tiny opaque archive files.
loop=next(n for n in main.body if isinstance(n,ast.For) and ast.unparse(n.target)=='(label, m)' and 'R.restore' in ast.unparse(n));loopcode=compile(ast.Module(body=[loop],type_ignores=[]),'exact two-targetloop','exec');fixtures=O/'tiny01';fixtures.mkdir(mode=0o700)
def setup(name):
 d=fixtures/name;d.mkdir(mode=0o700);bundle=d/'bundle';bundle.mkdir(mode=0o700);here=d/'output';here.mkdir(mode=0o700);manifests={};archives={}
 for label in ['source','parent']:
  src=d/('input-'+label);src.mkdir(mode=0o700);(src/'opaque.txt').write_bytes((label+'\x00opaque\n').encode());manifests[label]=R.scan(src);archives[label]=R.pack(src,manifests[label],bundle/('complete-'+label+'01.tar.gz'))
 observations=[]
 def floor():observations.append(True)
 return {'HERE':here,'bundle':bundle,'manifests':manifests,'cap':{'archives':archives},'actual':{},'R':R,'floor':floor},observations
ns,obs=setup('success');exec(loopcode,ns);ck(set(ns['actual'])=={'source','parent'} and len(obs)==4,'exactloop bothactualtiny recoveries and fourfloorcalls')
for label in ['source','parent']:
 dest=ns['HERE']/('flat-'+label+'01');meta=json.loads(R.read(dest,'body-metadata.json'));ck(R.read(dest,meta['flat_members']['opaque.txt'])==(label+'\x00opaque\n').encode(),'tiny actualfullbody '+label)
ns,obs=setup('second_bad_hash');ns['cap']['archives']['parent']['sha256']='0'*64
try:exec(loopcode,ns)
except ValueError as e:ck(str(e)=='archive binding differs','actualsecondtarget badhash refused')
else:raise AssertionError('accepted badsecond')
ck(set(ns['actual'])=={'source'} and (ns['HERE']/'flat-source01/body-metadata.json').exists() and list((ns['HERE']/'flat-parent01').iterdir())==[] and not (ns['HERE']/'RECOVERY01.json').exists(),'firsttarget retained secondempty noaggregatesuccess')
ns,obs=setup('second_fatal');original=R.restore;fatal=MemoryError('second tiny archive failure')
def fail_second(archive,*args,**kwargs):
 if Path(archive).name=='complete-parent01.tar.gz':raise fatal
 return original(archive,*args,**kwargs)
R.restore=fail_second
try:
 try:exec(loopcode,ns)
 except BaseException as e:ck(e is fatal,'exactsecondfatal originalidentity')
 else:raise AssertionError('fatal swallowed')
finally:R.restore=original
ck(set(ns['actual'])=={'source'} and not (ns['HERE']/'RECOVERY01.json').exists(),'fatal nooverallreceipt firsttargetretained')
# Exact fresh namespace predicate refuses spent first target and existing intent.
fresh=next(n for n in ast.walk(main) if isinstance(n,ast.Call) and ast.unparse(n.func)=='R.require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='one-use two-target namespace');freshcode=compile(ast.Expression(fresh),'exact freshpredicate','eval')
try:eval(freshcode,{'R':R,'HERE':ns['HERE'],'os':os})
except ValueError:ck(True,'partial firsttarget preventsreuse')
else:raise AssertionError('partial namespace reused')
ck(all(not (P/n).exists() for n in ['flat-source01','flat-parent01','INTENT01.json','RECOVERY01.json']),'actualRoot namespace unexecuted');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','pandas'} for n in sys.modules),'no numericalimports');out={'schema_version':1,'decision':'ACCEPTED_TWO_TARGET_FLAT_SOURCE_ONLY_PENDING_ACTUAL_REMOTE','source_sha256':sha(b),'checks':len(checks),'expected_actual_capture_pins':expected,'primitive_pins':pins,'exact_extracted_loop_and_predicates_tested':True,'actual_archive_restore_performed':False,'tiny_opaque_recovery_only':True,'partial_target_and_failures_retained':True,'runtime_native_registration_authority':False};(O/'READBACK01.json').write_bytes(R.encode(out));print(json.dumps(out,indent=2))
