"""Exact runtime-input chain and six actual bodies; metadata only."""
import base64,builtins,csv,email.parser,hashlib,importlib.util,io,json,os,platform,resource,signal,stat,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];I=F/'matching-compiled-runtime-input01-2026-10-10';C=F/'matching-compiled-normalization-connected04-2026-10-10'
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(15,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(20);assert os.sched_getaffinity(0)=={3}
start=time.perf_counter_ns();checks=[];refs={};actual=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(n,v=True):assert v,n;checks.append(n)
def small(path):
 b=Path(path).read_bytes();assert len(b)<=1048576;refs[str(path)]={'sha256':sha(b),'bytes':len(b)};return b
orig=builtins.__import__
def guard(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes','array','tradingagents'},name
 return orig(name,*a,**kw)
builtins.__import__=guard
pins={'MANIFEST01.json':'c4b2ac89dd60d1db4a40035d47d174e2165007c7424745d1e8809bb521b69d78','INVENTORY01.json':'7f0cbd1a34389ac112c9e09241cb1bcab7b1972e77e5fe7d13dc124984266175','RUNTIME_REFERENCE01.json':'247d62394372e4ef10b4e79f351e5c2aee017b846cb2fc35e29b774b2a7eb366','POLICY01.json':'cf9cbe5ca7aa1a9e1849d59ec63916f8aa288b35a82d84f8b35c432c575506be'}
bodies={n:small(I/n) for n in pins}
for n,d in pins.items():ok('frozen input '+n,sha(bodies[n])==d)
m=json.loads(bodies['MANIFEST01.json']);inv=json.loads(bodies['INVENTORY01.json']);runtime=json.loads(bodies['RUNTIME_REFERENCE01.json']);policy=json.loads(bodies['POLICY01.json'])
for field,name in [('inventory','INVENTORY01.json'),('runtime','RUNTIME_REFERENCE01.json'),('policy','POLICY01.json')]:
 ref=m[field];ok('manifest exact '+field,ref['path']==str(I/name) and ref['sha256']==sha(bodies[name]) and ref['bytes']==len(bodies[name]))
ok('external inventory-body digest join',runtime['runtime_inventory_sha256']==sha(bodies['INVENTORY01.json']))
ok('policy exact runtime body join',policy['runtime_path']==str(I/'RUNTIME_REFERENCE01.json') and policy['runtime_sha256']==sha(bodies['RUNTIME_REFERENCE01.json']) and policy['runtime_bytes']==len(bodies['RUNTIME_REFERENCE01.json'])==382)
ok('exact observed metadata fields',set(runtime)==set(inv['metadata'])|{'format','runtime_inventory_sha256'} and all(runtime[k]==v for k,v in inv['metadata'].items()))
observed=dict(python=platform.python_version(),platform=sys.platform,machine=platform.machine(),byteorder=sys.byteorder,executable=sys.executable)
ok('actual pinned interpreter metadata',all(runtime[k]==v for k,v in observed.items()))
ok('six explicitly listed bodies',len(inv['references'])==6 and len({v['path'] for v in inv['references']})==6)
metadata={};records={};environment=None
for ref in inv['references']:
 path=Path(ref['path']);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);digest=hashlib.sha256();total=0;chunks=[]
 try:
  before=os.fstat(fd);assert stat.S_ISREG(before.st_mode) and 0<before.st_size<=64*1024**2
  while True:
   b=os.read(fd,1024*1024)
   if not b:break
   total+=len(b);assert total<=64*1024**2;digest.update(b)
   if before.st_size<=1048576:chunks.append(b)
  after=os.fstat(fd)
 finally:os.close(fd)
 signature=lambda s:[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
 ok('actual body '+path.name+str(len(actual)),digest.hexdigest()==ref['sha256'] and total==ref['bytes'])
 ok('recorded stable descriptor '+str(len(actual)),signature(before)==signature(after)==ref['stat'] and before.st_nlink==ref['nlink'] and before.st_mode==ref['mode'])
 actual.append({'path':str(path),'sha256':digest.hexdigest(),'bytes':total,'mode':before.st_mode,'nlink':before.st_nlink,'stat':signature(after)})
 content=b''.join(chunks)
 if path.name=='METADATA':
  parsed=email.parser.BytesParser().parsebytes(content);name=parsed['Name'].lower();metadata[name]=(path,content,parsed['Version']);ok('distribution metadata version '+name,name in ('numpy','scipy') and parsed['Version']==runtime[name])
 elif path.name=='RECORD':records[path.parent.name]=list(csv.reader(io.StringIO(content.decode())))
 elif path.name=='environment.json':environment=(path,json.loads(content),ref['sha256'])
 else:ok('actual resolved interpreter body',path==Path(sys.executable).resolve())
for name,(path,content,version) in metadata.items():
 rows=records[path.parent.name];matching=[row for row in rows if row[0]==path.parent.name+'/METADATA'];encoded=base64.urlsafe_b64encode(hashlib.sha256(content).digest()).decode().rstrip('=')
 ok('RECORD joins actual METADATA only '+name,len(matching)==1 and matching[0][1]=='sha256='+encoded and int(matching[0][2])==len(content))
ok('actual metadata package set',set(metadata)=={'numpy','scipy'} and len(records)==2)
gatepath=F/'real-data-pilot-full29-entry01-2026-10-09/gate04.json';gate=json.loads(small(gatepath));exp=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261009-29'];ep,env,ed=environment
ok('actual29 environment pin',any(x['path']==str(ep.relative_to(R)) and x['sha256']==ed for x in exp['inputs'].values()))
ok('environment version join',env['python']==runtime['python'] and all(env['packages'][n]==runtime[n] for n in ('numpy','scipy')))
scopepath=F/'matching-compiled-runtime-policy-scope-review01-2026-10-10/REVIEW01.json';ok('accepted scope preserved',sha(small(scopepath))=='9a82f6c58835f1c60a45992f329b939dc9424d16d2a46aa01c61a0dbf47b9ebe')
policybody=small(C/'compiled_normalization_policy.py');ok('accepted exact04 parser',sha(policybody)=='f60237416454998bbe41a969400775b134a9f285c4b64c1a5507453515b25c01')
spec=importlib.util.spec_from_file_location('runtime_metadata_parser',C/'compiled_normalization_policy.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
ok('genuine eight-field policy parser',len(policy)==8 and module.freeze(policy) is not None)
ok('genuine nine-field runtime parser',len(runtime)==9 and module.runtime_metadata(bodies['RUNTIME_REFERENCE01.json'])==runtime)
for name,expected in [('source',module.SOURCE_SHA256),('library',module.LIBRARY_SHA256)]:
 path=Path(policy[name+'_path']);b=module.read_reference(path,expected,65536,owned=name=='library');refs[str(path)]={'sha256':sha(b),'bytes':len(b)};ok('exact original '+name,policy[name+'_sha256']==expected==sha(b))
ok('metadata-only exclusions explicit',all(any(term in x for x in inv['excluded']) for term in ('package payload','Loaded numerical versions','compiler','libm','writer exclusion','Financial Admission')) and inv['scientific_modules_imported'] is False)
ok('no financial authority',m['authority']=='NONE' and m['numerical_or_native_execution'] is False)
output=F/'matching-compiled-connected-qualification02-execution01-2026-10-10';ok('proposed output currently absent',not output.exists())
ok('no prohibited imports',not {'numpy','scipy','torch','ctypes','array','tradingagents'}&set(sys.modules))
for n,d in pins.items():ok('input remains frozen '+n,sha((I/n).read_bytes())==d)
r={'disposition':'ACCEPT_METADATA_SCOPED_RUNTIME_ENTRY_ONLY_UNEXECUTED','checks':checks,'check_count':len(checks),'body_references':refs,'verified_actual_inventory_bodies':actual,'total_inventory_body_bytes':sum(x['bytes'] for x in actual),'actual_interpreter_metadata':observed,'runtime':runtime,'policy':policy,'hardlinked_distribution_metadata_accepted_as_metadata_only':True,'package_payloads_verified':False,'loaded_numpy_scipy_versions_verified':False,'numerical_native_execution':False,'actual_admission':False,'elapsed_ns':time.perf_counter_ns()-start,'peak_reviewer_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(P/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('disposition','check_count','total_inventory_body_bytes','elapsed_ns')}))
