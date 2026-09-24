"""Tiny no-data guard probe; parent, child and three sleeping threads."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

print({'pid':os.getpid(),'cpus':sorted(os.sched_getaffinity(0))},flush=True)
if '--child' in sys.argv:
    time.sleep(1)
else:
    child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child'])
    threads=[threading.Thread(target=lambda:time.sleep(1)) for _ in range(3)]
    for thread in threads:thread.start()
    for thread in threads:thread.join()
    raise SystemExit(child.wait())
