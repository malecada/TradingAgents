import fcntl,json,os
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'synthetic-nonrecursive-lock';first=os.open(p,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);second=None
try:
 fcntl.flock(first,fcntl.LOCK_EX);second=os.open(p,os.O_RDWR)
 try:fcntl.flock(second,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:result={'same_process_second_open_description_blocked':True,'nonblocking_control':True,'actual_Run_or_source_lock_used':False,'implication':'Calling read_input inside _reserve lock can block on the second flock; original read_input uses blocking LOCK_EX.'}
 else:raise AssertionError('unexpected recursive lock behavior')
finally:
 if second is not None:os.close(second)
 os.close(first)
(H/'LOCK_CONTROL01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
