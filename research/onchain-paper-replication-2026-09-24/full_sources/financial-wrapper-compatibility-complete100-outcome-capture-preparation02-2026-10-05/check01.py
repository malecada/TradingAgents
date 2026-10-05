from pathlib import Path
import hashlib,importlib.util,json,os,sys,time,types,ast
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-complete100-outcome-capture-preparation01-2026-10-05';review=D.parent/'financial-wrapper-compatibility-complete100-capture-entry-review01-2026-10-05'
assert hashlib.sha256((review/'WITNESS01.json').read_bytes()).hexdigest()=='136381f3377dc986f939b84adc9a52b8c8df2dcc27653941654847cb26105e0e'
results=[]
for version,source in [('old',P/'capture01.py'),('new',D/'capture01.py')]:
 spec=importlib.util.spec_from_file_location(version,source);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
 for case in ('late_archive_mutation','late_expired_deadline','healthy'):
  root=D/(version+'-'+case);root.mkdir(mode=0o700);cap=root/'capsule';parent=root/'parent';cap.mkdir(mode=0o700);parent.mkdir(mode=0o700);(cap/'one.body').write_bytes(b'opaque complete original\0');(parent/'two.body').write_bytes(b'opaque Parent\0');out=root/'output'
  original_close=os.close;real_clock=time.monotonic;offset=[0.];M.time=types.SimpleNamespace(monotonic=lambda:real_clock()+offset[0]);closed=[];error=None;result=None
  def close(fd):
   try:target=os.readlink('/proc/self/fd/'+str(fd))
   except OSError:target=''
   original_close(fd)
   if target==str(out/'CAPTURE01.json') and not closed:
    closed.append(fd)
    if case=='late_archive_mutation':
     p=out/'piece-000.tar.gz';b=p.read_bytes();p.write_bytes(bytes([b[0]^1])+b[1:])
    elif case=='late_expired_deadline':offset[0]=121.
  os.close=close
  try:result=M.capture({'capsule':cap,'parent':parent},out,M.time.monotonic())
  except BaseException as e:error=e
  finally:os.close=original_close
  assert len(closed)==1
  if version=='old' or case=='healthy':assert error is None
  else:assert isinstance(error,ValueError) and ('retained archive changed' in str(error) if case=='late_archive_mutation' else 'capture deadline' in str(error))
  results.append({'version':version,'case':case,'returned':result is not None,'error':None if error is None else str(error),'actual_final_receipt_close':True})
v=json.loads((D/'INVERSE01.json').read_text());s=(P/'capture01.py').read_text()
for a,b in v['changes']:assert s.count(a)==1;s=s.replace(a,b)
assert s==(D/'capture01.py').read_text();ast.parse(s)
for p in (D/'utilities').iterdir():assert p.read_bytes()==(P/'utilities'/p.name).read_bytes()
(D/'CHECKS01.json').write_text(json.dumps({'results':results,'exact_inverse':True,'utilities_unchanged':True,'actual_Root_capture':False},indent=2)+'\n');print(json.dumps(results))
