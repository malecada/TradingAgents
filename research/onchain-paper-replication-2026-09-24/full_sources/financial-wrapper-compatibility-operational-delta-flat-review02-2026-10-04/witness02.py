from pathlib import Path
import os,sys,json,importlib.util,hashlib,stat
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));s=importlib.util.spec_from_file_location('flat_review_witness2',D/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M);B=D.parent/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';c,m=M.load_failed_capture(B);rows=[]
for kind in ('foreign-member','private-mode'):
 root=D/('witness02-'+kind);root.mkdir(mode=0o700);samples=[]
 def boundary():samples.append(M.W.census(root))
 r=M.restore_failed_delta(B,c,m,root,boundary);dest=root/M.FAILED_OUTPUT;meta=json.loads((dest/r['metadata_file']).read_bytes());files=[x for x in m['members'] if x['kind']=='file'];victim=dest/meta['flat_members'][files[0]['path']];trigger=dest/meta['flat_members'][files[-1]['path']];close=os.close;fired=[];before=len(os.listdir('/proc/self/fd'))
 def closed(fd):
  try:target=os.readlink('/proc/self/fd/'+str(fd))
  except OSError:target=None
  close(fd)
  if target==str(trigger) and not fired:
   if kind=='foreign-member':(dest/'foreign.body').write_bytes(b'not in original manifest')
   else:victim.chmod(0o644)
   fired.append(fd)
 os.close=closed
 try:result=M.verify_flat(dest,r,c,m,boundary)
 finally:os.close=close
 assert fired and result==meta and len(os.listdir('/proc/self/fd'))==before
 assert (dest/'foreign.body').is_file() if kind=='foreign-member' else stat.S_IMODE(victim.stat().st_mode)==0o644
 rows.append({'kind':kind,'returned_success':True,'closed_fds':fired,'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),'actual_members':len(list(dest.iterdir())),'expected_members':32,'victim_mode':stat.S_IMODE(victim.stat().st_mode),'last_boundary':samples[-1],'actual_recovery_receipt':None})
(D/'WITNESS02.json').write_text(json.dumps({'source_sha256':hashlib.sha256((D/'restore01.py').read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n');print(json.dumps(rows))
