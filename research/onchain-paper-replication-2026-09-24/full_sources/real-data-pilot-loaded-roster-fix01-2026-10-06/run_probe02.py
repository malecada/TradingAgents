import json,os,subprocess,time
from pathlib import Path
out=Path(__file__).resolve().parent
p=subprocess.Popen([str(Path.cwd()/'.venv/bin/python'),'-B',str(out/'probe02.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,PYTHONPATH='.',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
began=time.monotonic();peak=0;reason=None
while p.poll() is None:
 try:
  values=Path(f'/proc/{p.pid}/status').read_text().splitlines();rss=int(next(v for v in values if v.startswith('VmRSS:')).split()[1])*1024;peak=max(peak,rss)
 except (FileNotFoundError,StopIteration):pass
 if peak>=1024**3 or time.monotonic()-began>120:
  reason='rss or elapsed cap';p.kill();break
 time.sleep(.05)
a,b=p.communicate();record={'exit':p.returncode,'elapsed_seconds':time.monotonic()-began,'sampled_rss_peak_bytes':peak,'memory_limit_bytes':1024**3,'seconds_limit':120,'killed_reason':reason,'stdout':a.decode(),'stderr':b.decode()}
(out/'PROBE_RESULT02.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(p.returncode)
