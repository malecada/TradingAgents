from pathlib import Path
import types,os,stat,json,hashlib,copy,ast
D=Path(__file__).resolve().parent;H=D.parent/'financial-wrapper-compatibility-coalesced-evidence-preparation03-2026-10-04';M=types.ModuleType('copier');M.__file__=str(H/'copy_layout01.py');exec(compile((H/'copy_layout01.py').read_bytes(),M.__file__,'exec'),M.__dict__);checks=[];cases=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
sha=lambda b:hashlib.sha256(b).hexdigest()
ok(M.PRECLAIM_BYTES==(H/'preclaim01.py').read_bytes(),'exact preclaim bytes');ok(M.OWNED_IO_BYTES==(H/'owned_io.py').read_bytes(),'exact IO bytes')
for b,p in [(M.PRECLAIM_BYTES,H/'preclaim01.py'),(M.OWNED_IO_BYTES,H/'owned_io.py')]:ok(ast.dump(ast.parse(b))==ast.dump(ast.parse(p.read_bytes())),'full primitive AST identical')
T=D/'owned-replay02';T.mkdir(mode=0o700)
def fixture(name):
 d=T/name;d.mkdir(mode=0o700);src=d/'input';src.mkdir(mode=0o700);rows=[]
 for i,mode in enumerate([0o600,0o664]):
  p=src/('origin'+str(i));q=src/('retained'+str(i));b=('opaque'+str(i)).encode();p.write_bytes(b);p.chmod(mode);q.write_bytes(b);q.chmod(0o600);rows.append({'original_path':str(p),'path':str(q),'destination':'copies/body'+str(i),'bytes':len(b),'sha256':sha(b),'original_mode':mode,'copy_mode':0o600,'output_mode':mode,'role':'receipt'})
 return {'rows':rows},d/'flat'
spec,out=fixture('success');r=M.PC.Reader();result=M.copy_layout(spec,out,r);ok(result['status']=='DRAFT_COPIED_NOT_AUTHORITY' and result['receipt_bodies']==2,'actual tiny one-use copy');ok(result['actual_bytes_read_including_full_finish']==r.total<8388608,'actual reader accounting')
for row in spec['rows']:ok((out/row['destination']).read_bytes()==Path(row['original_path']).read_bytes() and stat.S_IMODE((out/row['destination']).stat().st_mode)==row['output_mode'],'literal byte/mode')
try:M.copy_layout(spec,out,M.PC.Reader())
except ValueError:ok(True,'spent output refused')
else:raise AssertionError('reused')
mutations={
'bad_hash':lambda s,o:s['rows'][0].update(sha256='0'*64),
'duplicate':lambda s,o:s['rows'].append(dict(s['rows'][0])),
'order':lambda s,o:s['rows'].reverse(),
'escape':lambda s,o:s['rows'][0].update(destination='../outside'),
'bad_mode':lambda s,o:s['rows'][0].update(output_mode=0o777),
'oversized':lambda s,o:s['rows'][0].update(bytes=4194305),
'original_mode':lambda s,o:Path(s['rows'][0]['original_path']).chmod(0o644),
'retained_tamper':lambda s,o:Path(s['rows'][0]['path']).write_bytes(b'changed'),
'hardlink':lambda s,o:os.link(s['rows'][0]['original_path'],o.parent/'hardlinked-original'),
'symlink':lambda s,o:(o.parent/'linked').symlink_to(Path(s['rows'][0]['original_path'])) or s['rows'][0].update(original_path=str(o.parent/'linked')),
'output_link':lambda s,o:o.symlink_to(o.parent/'input',target_is_directory=True),
}
for name,change in mutations.items():
 s,o=fixture(name);change(s,o)
 try:M.copy_layout(s,o,M.PC.Reader())
 except (ValueError,OSError):ok(True,'refusal '+name);cases.append(name)
 else:raise AssertionError('accepted '+name)
# Genuine actual input fixed57-source and saved51 origins are authenticated read-only.
real_spec=json.loads((H/'INPUTS01.json').read_bytes());ok(sha((H/'INPUTS01.json').read_bytes())==M.INPUTS_SHA,'fixed input pin');ok(len(real_spec['rows'])==57 and sum(x['role']=='receipt' for x in real_spec['rows'])==38 and sum(x['role']=='source-evidence' for x in real_spec['rows'])==13,'full fixed denominator')
rr=M.PC.Reader()
for x in real_spec['rows']:
 for key,mkey in [('original_path','original_mode'),('path','copy_mode')]:
  p=Path(x[key]);b=rr.read(p);ok(sha(b)==x['sha256'] and len(b)==x['bytes'] and stat.S_IMODE(p.lstat().st_mode)==x[mkey],'actual fixed original/readback')
rr.finish();ok(rr.total<8388608,'actual source-only input two-pass8MiB');ok(not M.OUTPUT.exists(),'actualRoot output not executed')
# Actual raw descriptor write/close error pairs; every descriptor is really closed.
classes=[ValueError,OSError,MemoryError,KeyboardInterrupt,SystemExit]
fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
for i,pc in enumerate(classes):
 for k,sc in enumerate(classes):
  d=T/('fatal-%d-%d'%(i,k));d.mkdir(mode=0o700);fd=os.open(d,os.O_RDONLY|os.O_DIRECTORY);fds=[];primary=pc('body');secondary=sc('close');proxy=types.SimpleNamespace(**{n:getattr(os,n) for n in dir(os)});real=M.os
  def write(f,b):fds.append(f);raise primary
  def close(f):os.close(f);raise secondary
  proxy.write=write;proxy.close=close;M.os=proxy
  try:
   try:M.put(fd,'partial',b'opaque',0o600)
   except BaseException as actual:
    expected=primary if fatal(primary) else secondary if fatal(secondary) else None
    ok(actual is expected if expected else isinstance(actual,M.IO.CleanupFailure),'real FD firstfatal pair')
    dct=BaseException.__dict__['__dict__'].__get__(actual);ok(actual is secondary or secondary in dct.get('layout_cleanup_errors',()) or secondary in dct.get('failures',()),'actual secondary retained')
   else:raise AssertionError('write error accepted')
  finally:M.os=real;os.close(fd)
  for f in fds:
   try:os.fstat(f)
   except OSError:ok(True,'actual owned FD closed')
   else:raise AssertionError('fd leaked')
# Final output namespace observation cannot mask changed cached bytes/mode.
for kind in ['body','mode','floor','extra']:
 s,o=fixture('late-'+kind);original=M.namespace
 def observed(root):
  value=original(root)
  if (root/'DRAFT_LAYOUT01.json').exists():
   if kind=='body':(root/'copies/body0').write_bytes(b'CHANGED')
   elif kind=='mode':(root/'copies/body0').chmod(0o644)
   elif kind=='extra':(root/'added').write_bytes(b'x')
   else:raise ValueError('injected floor refusal')
  return value
 M.namespace=observed
 try:
  try:M.copy_layout(s,o,M.PC.Reader())
  except ValueError:ok(True,'actual final boundary '+kind)
  else:raise AssertionError('late accepted')
 finally:M.namespace=original
output={'assertions':len(checks),'checks':checks,'refusal_cases':cases,'real_descriptor_error_pairs':25,'actual_fixed_input_reader_bytes':rr.total,'actualRoot_entry_invoked':False,'numerical_or_claim_authority':False}
(D/'REPLAY02.json').write_text(json.dumps(output,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k not in ['checks','refusal_cases']}))
