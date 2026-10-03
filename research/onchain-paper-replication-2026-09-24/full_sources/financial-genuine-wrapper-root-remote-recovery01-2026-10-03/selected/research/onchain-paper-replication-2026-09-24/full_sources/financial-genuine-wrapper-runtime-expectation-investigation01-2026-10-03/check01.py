import ast,copy,json
from pathlib import Path
import prepare01 as P
H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
def refusal(n,fn):
 try:fn()
 except (ValueError,StopIteration):checks.append(n);return
 raise AssertionError(n+' accepted')
raw=(H/'prepared01/environment.EXPECTATION.json').read_bytes();report=json.loads((H/'prepared01/EVIDENCE01.json').read_bytes());basic=report['current_basic_observations']
ok('exact original compact bytes preserved',P.R.digest(raw)==P.EXPECTED_SHA)
ok('current basic equality',P.expected_check(raw,basic)['cpu_count']==12)
for k,v in [('cpu_count',11),('python','3.12'),('lock_sha256','0'*64),('packages',{})]:
 bad=copy.deepcopy(basic);bad[k]=v;refusal('basic mismatch '+k,lambda:P.expected_check(raw,bad))
value=json.loads(raw)
for k,v in [('cuda_available',None),('cuda_available',0),('torch_version',None),('cuda_build',0),('cpu_count',True)]:
 bad=copy.deepcopy(value);bad[k]=v;refusal('malformed historical expectation '+k+' '+str(v),lambda:P.expected_check(P.R.encode(bad),basic))
for name in ('historical-job.py','current-job.py'):
 code=(H/'prepared01'/name).read_bytes();tree=ast.parse(code);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker');order=P.ordering(code)
 guard=[n.lineno for n in ast.walk(fn) if isinstance(n,ast.Call) and ast.unparse(n.func)=='resources.assert_guarded_worker']
 ok(name+' guard before claim',len(guard)==1 and guard[0]<order['claim_context_line']<order['comparison_line'])
 bad=code.replace(b'with ResearchRun.start(',b'with DifferentLifecycle.start(')
 refusal(name+' fake lifecycle source refusal',lambda:P.ordering(bad))
 bad=code.replace(b'registered execution environment differs',b'ignore runtime mismatch')
 refusal(name+' missing mismatch refusal',lambda:P.ordering(bad))
ok('no current Torch API or driver claim',report['current_torch_api_observed'] is False and report['driver_unchanged_claim'] is False and report['current_environment_equality_proven'] is False)
ok('no released financial identity',report['input_adoption'] is None and report['registration'] is None and report['cumulative_authority'] is None and report['phase_slots_unreserved']==18 and report['paper_fit_credit']==0)
(H/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'status':'passed'},indent=2)+'\n');print(len(checks),'checks passed')
