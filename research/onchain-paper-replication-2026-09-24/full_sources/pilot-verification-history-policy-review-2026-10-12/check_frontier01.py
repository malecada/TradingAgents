from pathlib import Path
import ast,os,stat,tempfile,signal,json,hashlib,time
C=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot-verification-history-policy-candidate-2026-10-12')
t=ast.parse((C/'admission.py').read_text());t.body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_history_frontier'];env={'os':os,'stat':stat,'identity':lambda *a:None,'digest':lambda x:hashlib.sha256(x).hexdigest(),'_HISTORY_MAX_RUNS':512,'_HISTORY_MAX_BODY':8*1024**2,'_HISTORY_MAX_BYTES':64*1024**2};exec(compile(t,str(C/'admission.py'),'exec'),env)
class Alarm(Exception):pass
def alarm(*a):raise Alarm('reviewer deadline: FIFO open blocked before regular-file refusal')
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);child=root/'research_runs'/'fake';child.mkdir(parents=True);os.mkfifo(child/'claim.json');signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,.25)
 try:
  env['_history_frontier'](root)
 except ValueError as e:result={'status':'PASS','refused':str(e)}
 except Alarm as e:result={'status':'RED','blocked_fifo':str(e)}
 finally:signal.setitimer(signal.ITIMER_REAL,0)
print(json.dumps(result,indent=2));assert result['status']=='PASS'
