from pathlib import Path
import hashlib,json,difflib
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication';targets=[]
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for name in ('matching_numeric_policy.py','matching_immutable_session.py','phase_timing.py'):
 a=(P/('BASELINE_'+name)).read_text();b=(P/name).read_text();compile(b,str(P/name),'exec');target=str((S/name).relative_to(R))
 for suffix,x,y,xf,yf in [('diff',a,b,'a/'+target,'b/'+target),('inverse.diff',b,a,'b/'+target,'a/'+target)]:
  (P/(name+'.'+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=xf,tofile=yf)))
 targets.append({'target':target,'baseline':pin(P/('BASELINE_'+name)),'candidate':pin(P/name)})
for name in ('numeric_harness.py','numeric_checks01.py','benchmark01.py'):compile((P/name).read_text(),name,'exec')
m={'status':'UNINSTALLED_NUMERICAL_CHECKS_UNEXECUTED','retained_limit_bytes':33554432,'extra_scratch_bytes':65536,'caller_reservation_bytes':33619968,'targets':targets,'unchanged_source_pins':[pin(S/n) for n in ('matching_numeric_kernel.py','matching_annealing.py','matching_checkpoint.py','matching_reference.py','contracts.py')],'files':[pin(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='SOURCE_MANIFEST01.json']}
(P/'SOURCE_MANIFEST01.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'manifest':pin(P/'SOURCE_MANIFEST01.json'),'targets':targets},indent=2))
