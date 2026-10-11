import ast,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-uncached-edge-caller-candidate01-2026-10-11';refs={};checks=[]
def read(p):
 assert not ({'.git','.venv','research_artifacts','research_runs','keys','apis'}&set(p.parts)) and p.suffix!='.so'
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
m=json.loads(read(D/'MANIFEST01.json'));ck(refs[str((D/'MANIFEST01.json').relative_to(R))]['sha256']=='432a01abf00c70c33b7c23d7d487bb6fd10973959d4030daed29150cb16cf677','exact lower source manifest')
for name,row in m['files'].items():b=read(D/name).encode();ck(hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['bytes'],'frozen lower textual member '+name)
review=read(F/'pilot34-acceleration-candidates-source-review02-2026-10-11/REVIEW01.json');ck(hashlib.sha256(review.encode()).hexdigest()=='b6db0c69b4cfd8feb8e829f134b5315ac3390dfc40d5a6dcb7ce85a757b0c475','accepted corrected kernel source review')
ck(read(D/'matching_annealing.py')==read(F/'matching-compiled-uncached-edge-chunk02-2026-10-11/matching_annealing.py'),'exact corrected02 kernel reused')
owner=read(D/'compiled_edge_owner.py');tree=ast.parse(owner)
nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in ('require','freeze','abi_metadata')]
ns={'Path':Path,'json':json};exec(compile(ast.Module(body=nodes,type_ignores=[]),'policy-parser-only-no-owner','exec'),ns)
ck(ns['freeze'](None) is None,'unselected policy returns without reads')
policy={'format':ns['FORMAT'],'source_sha256':ns['SOURCE'],'adapter_sha256':ns['ADAPTER'],'library_sha256':ns['LIBRARY'],'runtime_sha256':'1'*64,'abi_sha256':'2'*64,'runtime_bytes':345,'abi_bytes':200}
for role in ('source','adapter','library','runtime','abi'):policy[role+'_path']='/synthetic/'+role
pin=ns['freeze'](policy);policy['runtime_bytes']=346;ck(dict(pin)['runtime_bytes']==345 and ns['freeze'](policy)!=pin,'policy immutable snapshot reflects later input mutation freshly')
for label,edit in [('unknown',lambda p:p.update(extra=1)),('escape',lambda p:p.update(source_path='/synthetic/../source')),('bool_size',lambda p:p.update(abi_bytes=True)),('wrong_adapter',lambda p:p.update(adapter_sha256='0'*64))]:
 value=dict(policy);edit(value)
 try:ns['freeze'](value)
 except ValueError:ck(True,'policy refusal '+label)
 else:raise AssertionError(label)
# Source-only lifecycle ordering; no EdgeOwner or filesystem/loader method runs.
close=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='close');segment=ast.get_source_segment(owner,close)
ck(segment.index('fd=None')<segment.index('close_fd(value)') and 'close_error=error;raise' in segment,'owner clears descriptor before captured close and retains ambiguous error')
ck('if close_error is not None:raise close_error' in segment,'repeated close raises retained error without retry')
acquire=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='acquire');segment=ast.get_source_segment(owner,acquire)
ck(segment.index('attempted=True')<segment.index('os.memfd_create')<segment.index('F_ADD_SEALS')<segment.index('os.pread')<segment.index('ExtensionFileLoader')<segment.index('module_from_spec')<segment.index('make_filler'),'one-attempt seal/body readback precedes native loader and adapter creation')
ck("uuid.uuid4().hex+'._edge_chunk'" in segment and 'current()' in segment,'unique qualified module identity and post-acquisition currentness present')
current=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='current');segment=ast.get_source_segment(owner,current)
ck('metadata()' in segment and 'F_GET_SEALS' in segment and 'module.fill is native_fill' in segment and 'try:close()' in segment,'current body/runtime/module/seal checks terminally close on refusal')
session=read(D/'matching_immutable_session.py');checkpoint=read(D/'matching_checkpoint.py')
ck('edge_chunk_owner=None' in session and 'if edge_chunk_owner is not None:' in session and 'lease = edge_chunk_owner.borrow(self)' in session,'explicit selected owner only borrow')
ck('if self._edge_lease is not None else {}' in session and 'if edge_chunk_fill is not None else {}' in checkpoint,'default omission across session and checkpoint')
ck('self._edge_functions[0][1]' in session and 'self._edge_current()' in session and 'edge_chunk_fill' in checkpoint,'captured filler and pre/post edge-current forwarding source')
out={'status':'LOWER_SOURCE_OBSERVATIONS_PENDING_UPPER_COMBINED_REVIEW','checks':checks,'references':refs,'native_owner_constructed':False,'native_loader_executed':False,'qualification':'Finite parser and source ordering only. Actual close/seal/ABI/extension loader and numerical behavior unproved; wait exact upper caller/role/lifetime closure before final source decision.'}
with (P/'LOWER_OBSERVATIONS01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'sha256':hashlib.sha256((P/'LOWER_OBSERVATIONS01.json').read_bytes()).hexdigest()},sort_keys=True))
