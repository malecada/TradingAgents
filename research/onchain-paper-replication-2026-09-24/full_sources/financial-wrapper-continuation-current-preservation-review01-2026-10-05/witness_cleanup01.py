"""One real owned-descriptor primary/cleanup overlap; no live capture execution."""
from pathlib import Path
import sys,os,json,hashlib,importlib.util
H=Path(__file__).resolve().parent;P=H.parent/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05';sys.path.insert(0,str(P));spec=importlib.util.spec_from_file_location('candidate',P/'bind02.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
root=H/'owned';root.mkdir(mode=0o700);f=root/'body';f.write_bytes(b'opaque');inode=f.stat().st_ino;read=os.read;close=os.close;opened=[];closed=[];primary=MemoryError('original owned read fatal');secondary=ValueError('later actual close error')
def target(fd):
 try:return os.fstat(fd).st_ino==inode
 except OSError:return False
def badread(fd,n):
 if target(fd):opened.append(fd);raise primary
 return read(fd,n)
def badclose(fd):
 hit=target(fd);close(fd)
 if hit:closed.append(fd);raise secondary
os.read=badread;os.close=badclose
try:
 try:B.Census().tree(root,{'body':'file'},set());raise AssertionError('unexpected success')
 except BaseException as error:result={'actual_raised_type':type(error).__name__,'actual_raised_is_original_fatal':error is primary,'actual_raised_is_later_close':error is secondary,'original_fatal_context_retained':error.__context__ is primary,'real_owned_fd_closed_once':opened==closed and len(closed)==1,'opened':opened,'closed':closed,'candidate_sha256':hashlib.sha256((P/'bind02.py').read_bytes()).hexdigest()}
finally:os.read=read;os.close=close
assert result['real_owned_fd_closed_once'] and not result['actual_raised_is_original_fatal'] and result['actual_raised_is_later_close'];(H/'WITNESS_CLEANUP01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
