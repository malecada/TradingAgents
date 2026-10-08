"""Finite subprocess checks. Every stdout/stderr is new and bounded."""
import json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
cases=[('METADATA_GREEN01',[str(H/'probe01.py'),'candidate','--require-deferred']),*[(case.upper()+'01',[str(H/'boundary_checks01.py'),'candidate',case]) for case in ('metadata','write_boundary','compact_matcher_boundary')],('FUNCTIONAL01',[str(H/'pytest_checks01.py')])]
records=[]
for label,args in cases:
 with (H/(label+'.stdout')).open('xb') as out,(H/(label+'.stderr')).open('xb') as err:
  result=subprocess.run([sys.executable,'-B',*args],stdout=out,stderr=err,timeout=30,env=env)
 records.append({'case':label,'returncode':result.returncode,'stdout':label+'.stdout','stderr':label+'.stderr'})
 print(json.dumps(records[-1]),flush=True)
 assert result.returncode==0,(label,result.returncode)
(H/'CHECK_RESULTS01.json').write_text(json.dumps(records,indent=2)+'\n')
