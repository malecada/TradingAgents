"""Owned opaque controls; never runs entry, makes a remote receipt, or imports science."""
import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
P=Path(__file__).absolute().parent
spec=importlib.util.spec_from_file_location('delta_flat',P/'restore01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
R=M.R
O=P/'owned01';O.mkdir(mode=0o700)
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
 (P/'CHECK_PROGRESS01.json').write_text(json.dumps(checks,indent=2)+'\n')
def refuse(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,FileNotFoundError,FileExistsError,NotADirectoryError):check(name,True)
 else:raise AssertionError('accepted: '+name)
for name,pin in M.PINS.items():check('unchanged:'+name,hashlib.sha256((P/name).read_bytes()).hexdigest()==pin)
for value in [None,'','a'*63,'A'*64,1,True,'x'*64]:refuse('invalidpin:'+str(type(value))+str(value)[:5],lambda v=value:M.hexpin(v))
# A real prior commit value is used only in a draft selection schema control.
oldroot=P.parent/'financial-wrapper-complete100-failed-root-remote03-2026-10-04'
old=json.loads((oldroot/'REMOTE_RECOVERY01.json').read_bytes())
sel={'remote_commit':old['remote_commit'],'rows':[dict(path=n,**p) for n,p in sorted(M.REQUIRED.items())]}
check('exact10selected451691',len(M.selection_rows(sel))==10 and sum(r['bytes'] for r in sel['rows'])==451691)
for key,change in [('missing',lambda s:s['rows'].pop()),('duplicate',lambda s:s['rows'].__setitem__(1,s['rows'][0])),('reverse',lambda s:s['rows'].reverse()),('hash',lambda s:s['rows'][0].__setitem__('sha256','0'*64)),('extent',lambda s:s['rows'][0].__setitem__('bytes',0)),('traversal',lambda s:s['rows'][0].__setitem__('path','../x')),('extra',lambda s:s.__setitem__('extra',None)),('nullcommit',lambda s:s.__setitem__('remote_commit',None))]:
 s=copy.deepcopy(sel);change(s);refuse('selection:'+key,lambda s=s:M.selection_rows(s))
refuse('authentic-old-remote-wrong-scope',lambda:M.validate_remote(old,sel,'0'*64))
refuse('missingactualremote',lambda:M.run('0'*64,'0'*64))
check('missingreceipt-no-intent',not(P/'FLAT_INTENT01.json').exists())
# Independent evaluation of exact source predicates on actual prior operation rows;
# no new receipt is assembled or represented as actual remote provenance.
tree=ast.parse((P/'restore01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_remote')
operation_for=next(n for n in ast.walk(fn) if isinstance(n,ast.For) and ast.unparse(n.iter)=='operations')
conditions=[n.value.args[0] for n in operation_for.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='R.require']
for i,condition in enumerate(conditions):
 code=compile(ast.Expression(condition),'actual-source-predicate','eval')
 for j,row in enumerate(old['operations']):check('actualold-op:%d:%d'%(i,j),eval(code,vars(M),{'row':row}))
for field,value in [('exit',1),('actual_reaped_exit',None),('cleanup_failures',['OSError']),('pid',False)]:
 row=copy.deepcopy(old['operations'][0]);row[field]=value
 check('operation-refusal:'+field,not eval(compile(ast.Expression(conditions[0]),'predicate','eval'),vars(M),{'row':row}))
row=copy.deepcopy(old['operations'][0]);row['actual_child_limits']['fsize']=[4194305,4194305]
check('actual-limit-refusal',not eval(compile(ast.Expression(conditions[1]),'predicate','eval'),vars(M),{'row':row}))
bundle=P.parent/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04'
c,m=M.load_capture(bundle);check('actualfullmanifest',len(m['members'])==41)
bounds=[]
def boundary():bounds.append(M.W.census(O))
result=M.restore_delta(bundle,c,m,O,boundary)
meta=M.verify_flat(O/M.OUTPUT,result,c,m,boundary)
check('actual-local41-33-roundtrip',result['members']==41 and result['regular_bodies']==33)
for row in m['members']:
 if row['kind']=='file':check('body:'+row['path'],R.digest(R.read(O/M.OUTPUT,meta['flat_members'][row['path']]))==row['sha256'])
check('ordinary-originalmodes-retained',meta['manifest']==m)
refuse('oneuse-output-present',lambda:M.restore_delta(bundle,c,m,O,boundary))
refuse('wrongarchivehash',lambda:R.restore(bundle/'operational-delta01.tar.gz',dict(c['archive'],sha256='0'*64),m,O/'no-create'))
for label,mutate in [('duplicate',lambda v:v['members'].append(v['members'][0])),('traversal',lambda v:v['members'][0].__setitem__('path','../escape')),('type',lambda v:v['members'][0].__setitem__('kind','symlink')),('overfile',lambda v:next(r for r in v['members'] if r['kind']=='file').__setitem__('bytes',4194305))]:
 mm=copy.deepcopy(m);mutate(mm);refuse('manifest:'+label,lambda mm=mm:R.validate(mm))
# Small independent opaque pipeline; all physical writes remain owned.
tiny=O/'tiny';tiny.mkdir(mode=0o700);(tiny/'empty').mkdir(mode=0o700);(tiny/'opaque').write_bytes(b'opaque\x00bytes\xff'*9)
tm=R.scan(tiny);ta=O/'tiny.tar.gz';ti=R.pack(tiny,tm,ta)
for mode in (0o755,0o711):
 d=O/('wrongmode'+oct(mode));d.mkdir(mode=mode);refuse('flat-mode:'+str(mode),lambda d=d:R.restore(ta,ti,tm,d))
d=O/'foreign';d.mkdir(mode=0o700);(d/'foreign').write_bytes(b'owned');refuse('flat-existing-foreign',lambda:R.restore(ta,ti,tm,d))
link=O/'redirect';link.symlink_to(tiny,target_is_directory=True);refuse('flat-redirect',lambda:R.restore(ta,ti,tm,link))
hard=O/'hardbody';os.link(tiny/'opaque',hard);refuse('hardlink-reader',lambda:R.read(O,'hardbody'))
# Real FD write-interruption and actual closes; no fake owner/handles.
fatal=KeyboardInterrupt('owned control');closed=[];originalwrite=R.os.write;originalclose=R.os.close
fdroot=O/'fatal';fdroot.mkdir(mode=0o700)
def failwrite(fd,body):raise fatal
def close(fd):
 originalclose(fd);closed.append(fd)
R.os.write=failwrite;R.os.close=close
caught=None
try:R.restore(ta,ti,tm,fdroot)
except BaseException as e:caught=e
finally:R.os.write=originalwrite;R.os.close=originalclose
check('real-write-fatal-identity',caught is fatal)
for fd in set(closed):
 try:os.fstat(fd)
 except OSError:check('real-closed-fd:'+str(fd),True)
 else:raise AssertionError('live descriptor')
check('partial-fatal-retained',list(fdroot.iterdir())!=[])
# Original exception selection through actual entry, with only owned callbacks.
originalmain=M.main;originalput=R.put
for i,(primary,secondary) in enumerate([(KeyboardInterrupt(),SystemExit()),(MemoryError(),OSError()),(ValueError(),KeyboardInterrupt()),(ValueError(),OSError())]):
 def failmain(p=primary):raise p
 def failjournal(*a,e=secondary,**kw):raise e
 M.main=failmain;R.put=failjournal;caught=None
 try:M.entry()
 except BaseException as e:caught=e
 finally:M.main=originalmain;R.put=originalput
 expected=primary if isinstance(primary,MemoryError) or not isinstance(primary,Exception) else secondary if isinstance(secondary,MemoryError) or not isinstance(secondary,Exception) else None
 check('entry-fatal-selection:'+str(i),caught is expected if expected is not None else isinstance(caught,BaseException))
 check('entry-retained-originalobjects:'+str(i),any(e is primary for e in M.FAILURE_OBJECTS) and any(e is secondary for e in M.FAILURE_OBJECTS))
check('no-numericalimports',not any(n.split('.')[0] in ('numpy','torch','scipy','pandas') for n in sys.modules))
(P/'CONTROLS01.json').write_text(json.dumps({'status':'PASSED_SOURCE_OWNED_CONTROLS_ONLY','checks':len(checks),'names':checks,'actual_entry_executed':False,'actual_remote_receipt_created':False,'actual_local_frozen_archive_roundtrip':result,'sampled_owned_observations':bounds,'limitations':['No actual new remote receipt exists or was fabricated. Exact operation predicates replay genuine old closed remote rows independently; full new receipt admission remains future.','Local frozen opaque archive roundtrip is not external recovery or original POSIX reconstruction.']},sort_keys=True,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'status':'passed-source-only'}))
