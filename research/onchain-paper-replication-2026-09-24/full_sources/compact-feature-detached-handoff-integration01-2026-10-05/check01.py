from pathlib import Path
import ast,hashlib,json,importlib.util,gc,weakref,sys
D=Path(__file__).resolve().parent;ROOT=D.parents[3];CORE=Path('tradingagents/research/onchain_replication');P=D.parent/'compact-feature-detached-handoff02-2026-10-05';P1=D.parent/'compact-feature-detached-handoff01-2026-10-05';checks=[]
def check(x,n):assert x,n;checks.append(n)
for r in json.loads((D/'INSTALL_MAP01.json').read_text()):
 path=Path(r['path']);new=(D/path).read_bytes();check(new==(P/'overlay'/path.name).read_bytes(),path.name+' exact accepted body');ast.parse(new)
 if r['base_absent']:check(not (ROOT/path).exists(),path.name+' actual Main absent')
 else:check((ROOT/path).read_bytes()==(D/('ORIGINAL_'+path.name+'.txt')).read_bytes()==(P1/('ORIGINAL_'+path.name+'.txt')).read_bytes(),path.name+' actual Main/predecessor exact base')
for path,h in json.loads((P1/'MACHINE01.json').read_text())['source_inputs'].items():check(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path+' scientific/dependency unchanged')
old=ast.parse((D/'ORIGINAL_compact_native_features.py.txt').read_text());new=ast.parse((D/CORE/'compact_native_features.py').read_text())
for n in old.body:
 if isinstance(n,(ast.FunctionDef,ast.ClassDef)):check(any(type(t)is type(n) and t.name==n.name and ast.dump(t)==ast.dump(n) for t in new.body),'resident original AST '+n.name)
helper=D/CORE/'compact_detached_handoff.py';spec=importlib.util.spec_from_file_location('detached_opaque',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Sentinel:pass
sentinel=Sentinel();weak=weakref.ref(sentinel)
for value in [sentinel,lambda:sentinel,{'graph':sentinel}]:
 try:m.encoded(value)
 except ValueError:checks.append('strong producer object/callback refused')
 else:raise AssertionError('retained producer accepted')
value=None;sentinel=None;gc.collect();check(weak() is None,'no test object retained')
r=m.Record({'status':m.STATUS,'lifetime':'original-reader-sampled-content-v1','components':{}});check(m.Record.__slots__==('_raw',) and m.Authority.__slots__==('_record','_run_ref'),'immutable bytes and weak authority slots')
a=next(n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Authority');check('weakref.ref(run)' in ast.unparse(a) and not any(isinstance(n,ast.Name) and n.id=='terminal' for n in ast.walk(a)),'authority no terminal capture')
check(not any(n in sys.modules for n in ('numpy','torch','pandas')),'no numerical imports')
(D/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'actual_factory_or_loader':False,'memory_saving_observed':False},indent=2)+'\n');print(len(checks))
