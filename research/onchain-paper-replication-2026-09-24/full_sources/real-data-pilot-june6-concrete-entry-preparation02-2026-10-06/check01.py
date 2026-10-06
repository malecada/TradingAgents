from pathlib import Path
import ast,copy,hashlib,importlib.util,json
from unittest.mock import patch
H=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('boundary_candidate',H/'boundary01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
draft=json.loads((H/'BOUNDARY_DRAFT01.json').read_text());results=[]
def refuses(name,call):
    try:call()
    except ValueError as error:results.append({'case':name,'refusal':str(error)})
    else:raise AssertionError(name)
refuses('actual continuation evidence absent',lambda:m.check(draft))
bad=copy.deepcopy(draft);bad['identity']='replacement-id'
refuses('original unused identity cannot transfer',lambda:m.check(bad))
# Minimal synthetic metadata supplies only enough ancestry to reach the real failed-terminal branch.
c=copy.deepcopy(draft)
for key in m.FUTURE:c['dependencies'][key]={'path':key,'sha256':'a'*64}
c['dependencies']['continuation_claim']['path']='research_runs/'+m.CONT+'/claim.json';c['dependencies']['continuation_terminal']['path']='research_runs/'+m.CONT+'/complete.json'
docs={key:{} for key in c['dependencies']};docs['continuation_claim']={'experiment_id':m.CONT,'source':'s'};docs['continuation_terminal']={'experiment_id':m.CONT,'source':'s','claim_sha256':'a'*64,'status':'failed'}
def read(ref):return docs[next(k for k,v in c['dependencies'].items() if v==ref)]
with patch.object(m,'read',read):refuses('failed continuation cannot be complete predecessor',lambda:m.check(c))
for name in ('prepare01.py','preflight01.py','launch01.py','boundary01.py'):compile((H/name).read_bytes(),str(H/name),'exec')
base=m.ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-sixth-graph-failed-predecessor-entry01-2026-10-06/preflight01.py'
a=base.read_text();b=(H/'preflight01.py').read_text();f=lambda text:next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='check')
restored=b.replace('admission.effective_attempt_budget!=72','admission.effective_attempt_budget!=71').replace("'effective_attempt_budget':72","'effective_attempt_budget':71").replace("policy.get('preceding_continuation_boundary')","policy.get('failed_predecessor_retained')").replace('fresh storage policy must bind actual continuation closure, preserved failure and separate Data retention','fresh storage policy must explicitly retain failed originals and recoveries; no retirement credit')
assert ast.dump(f(restored))==ast.dump(f(a))
legacy=m.ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-sixth-graph-entry-preparation01-2026-10-06/launch01.py';assert legacy.read_bytes()==(H/'launch01.py').read_bytes()
source=m.ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-sixth-graph-input-preparation01-2026-10-06/draft01';extent=json.loads((source/'RAW_EXTENT_DRAFT01.json').read_bytes());assert extent['declared_rows']==7293215 and extent['segments']==223 and extent['days']==7
result={'decision':'pass','refusals':results,'original_check_AST_restored_exact':True,'launch_bytes_unchanged':True,'accepted_input_counts_reused':{'days':7,'rows':7293215,'extents':223},'active_continuation_outputs_read':False,'payload_reads':0,'genuine_admission_or_claim':False,'preparer_executed':False}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
