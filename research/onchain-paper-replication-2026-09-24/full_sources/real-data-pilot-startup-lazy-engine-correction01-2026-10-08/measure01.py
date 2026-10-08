"""Finite checked subprocesses, bounded output files, no production launcher."""
import json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
modes=sys.argv[1:] or ['baseline','hypothesis']*3
records=[]
for index,mode in enumerate(modes):
 label=os.environ.get('STARTUP_PROBE_PREFIX','')+f'{index:02d}-{mode}';out=H/(label+'.json');err=H/(label+'.stderr')
 with out.open('xb') as o,err.open('xb') as e:
  try:p=subprocess.run([sys.executable,'-B',str(H/'probe01.py'),mode],stdout=o,stderr=e,timeout=20,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'})
  except subprocess.TimeoutExpired:
   records.append({'label':label,'timeout_seconds':20});raise
 assert out.stat().st_size<=4*1024**2 and err.stat().st_size<=4*1024**2
 records.append({'label':label,'exit_code':p.returncode,'stdout':out.name,'stderr':err.name})
 assert p.returncode==0,(label,p.returncode)
print(json.dumps(records,indent=2))
