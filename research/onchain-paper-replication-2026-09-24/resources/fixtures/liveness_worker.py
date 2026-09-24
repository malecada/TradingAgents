"""No-data worker to verify cleanup of a process and a new-session descendant."""
import os
from pathlib import Path
import subprocess
import sys
import time

if sys.argv[1]=='descendant':
    time.sleep(30)
else:
    child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'descendant'],start_new_session=True)
    print({'pid':os.getpid(),'descendant':child.pid},flush=True)
    if sys.argv[1]=='widen':os.sched_setaffinity(0,{0,1,2})
    time.sleep(30)
