from pathlib import Path
import hashlib,importlib.util,json,os,sys,time,types
O=Path(__file__).resolve().parent;D=O.parent/'financial-wrapper-compatibility-complete100-outcome-capture-preparation01-2026-10-05';spec=importlib.util.spec_from_file_location('capture_candidate',D/'capture01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
H=lambda b:hashlib.sha256(b).hexdigest();assert H((D/'capture01.py').read_bytes())=='1b383b39c8d78593f1f5fb4b072e1a43d3c3c77f96a111d4f0ee378f91fd0c02'
results=[]
for case in ('late_archive_mutation','late_expired_deadline'):
 root=O/case;root.mkdir(mode=0o700);cap=root/'capsule';parent=root/'parent';cap.mkdir(mode=0o700);parent.mkdir(mode=0o700);(cap/'one.body').write_bytes(b'opaque complete original\0');(parent/'two.body').write_bytes(b'opaque Parent\0');out=root/'output'
 original_close=os.close;real_clock=time.monotonic;offset=[0.];M.time=types.SimpleNamespace(monotonic=lambda:real_clock()+offset[0]);closed=[]
 def close(fd):
  try:target=os.readlink('/proc/self/fd/'+str(fd))
  except OSError:target=''
  original_close(fd)
  if target==str(out/'CAPTURE01.json'):
   closed.append(fd)
   if case=='late_archive_mutation':
    p=out/'piece-000.tar.gz';b=p.read_bytes();p.write_bytes(bytes([b[0]^1])+b[1:])
   else:offset[0]=121.
 os.close=close
 try:result=M.capture({'capsule':cap,'parent':parent},out,M.time.monotonic());returned=True
 finally:os.close=original_close
 assert len(closed)==1
 if case=='late_archive_mutation':
  expected=result['pieces'][0]['archive_pin']['sha256'];actual=H((out/'piece-000.tar.gz').read_bytes());assert expected!=actual;details={'expected_sha256':expected,'actual_sha256':actual}
 else:
  try:M.boundary(real_clock())
  except ValueError as error:details={'subsequent_boundary_refusal':str(error),'clock_jump_seconds':offset[0]}
  else:raise AssertionError('boundary should refuse expired time')
 results.append({'case':case,'capture_returned_success':returned,'real_receipt_fd_closed_once':True,'source':H((D/'capture01.py').read_bytes()),**details})
(O/'WITNESS01.json').write_text(json.dumps(results,sort_keys=True,indent=2)+'\n');print(json.dumps(results,sort_keys=True))
