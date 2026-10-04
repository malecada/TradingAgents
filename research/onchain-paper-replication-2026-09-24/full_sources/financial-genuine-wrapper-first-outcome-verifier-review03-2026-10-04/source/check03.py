"""Exact-source CPU predicates and opaque empty-procs file; no native receipts."""
import ast,copy,json,os
from pathlib import Path
import verifier01 as V
R=Path(__file__).resolve().parent;checks=[]
def check(n,v):assert v,n;checks.append(n)
prior=R.parent/'financial-genuine-wrapper-first-outcome-verifier-preparation01-2026-10-04';source=prior/'baseline/capsule/tradingagents/research/onchain_replication/resources.py';raw=source.read_bytes();q=json.loads((R/'REQUEST_FINAL03.json').read_bytes());check('exact original resource source',V.sha(raw)==q['source_files']['tradingagents/research/onchain_replication/resources.py']);tree=ast.parse(raw);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='verify_cpu_tree');ns={'Path':Path,'os':os};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<original cpu tree>','exec'),ns);owned=R/'owned-empty-procs';owned.mkdir();(owned/'cgroup.procs').write_bytes(b'');actual=ns['verify_cpu_tree'](owned,[0,1]);check('actual original empty-procs returns empty census',actual=={})
oldfn=next(x for x in ast.parse((R/'original_verifier02.py').read_bytes()).body if isinstance(x,ast.FunctionDef)and x.name=='planned_failure_route');oldpredicate=next(x for x in oldfn.body if isinstance(x,ast.Expr)and any(isinstance(z,ast.Constant)and z.value=='CPU thread readback differs/missing'for z in ast.walk(x)));code=compile(ast.Module(body=[oldpredicate],type_ignores=[]),'<old exact finalcpu predicate>','exec')
for census in ({},{'11':[0]},{'11':[1]},{'11':[0],'12':[1]}):
 errors=[];exec(code,{'cpus':[0,1],'readback':census,'need':lambda yes,why:None if yes else errors.append(why)});check('RED old rejects original-permitted '+str(census),bool(errors));check('GREEN original permitted '+str(census),V.final_cpu_census([0,1],census))
for census in (None,[],{'x':[0]},{'11':[]},{'11':[2]},{'11':[True]},{'11':[1,0]},{'11':[0,0]},{1:[0]}):check('invalid final census '+str(census),not V.final_cpu_census([0,1],census))
# Exact original affinity subset condition with scalar sets (no OS calls).
condition=next(x for x in ast.walk(fn)if isinstance(x,ast.If)and any(isinstance(y,ast.Constant)and y.value=='thread widened CPU affinity beyond registered two CPUs'for y in ast.walk(x)));pred=compile(ast.Expression(condition.test),'<original subset predicate>','eval')
for mask in ({0},{1},{0,1},set(),{2},{0,2}):check('original subset policy '+str(mask),eval(pred,{'mask':mask,'allowed':{0,1}})==(not mask or not mask<={0,1}))
# Minimal scalar projections of original fields. Never full receipts/Owner/claim.
ready={'pid':11,'cpus':[0,1],'native_unit_limits':{'file_size_bytes':4194304},'file_size_limit':[4194304,4194304],'native_environment':{'opaque':'scalar projection'}};release={'kernel_controls_verified':True};guard={'cpus':[0,1],'native_unit_limits':{'file_size_bytes':4194304},'native_environment':ready['native_environment'],'kernel_controls':{'memory.max':'3221225472','memory.high':'3221225472','memory.swap.max':'0'},'initial_memory_events':{'oom':0,'oom_kill':0}}
check('early ready-release projection',V.early_cpu_evidence(guard,ready,release))
for which,original in [('guard',guard),('ready',ready),('release',release)]:
 for key in original:
  bad=copy.deepcopy(original);bad.pop(key);values={'guard':guard,'ready':ready,'release':release};values[which]=bad;check('missing early '+which+'/'+key,not V.early_cpu_evidence(**values))
for field,value in [('pid',None),('pid',True),('cpus',[0]),('cpus',[0,2]),('cpus',[False,1]),('file_size_limit',[1,1]),('native_environment',{}),('native_unit_limits',None)]:check('bad readiness '+field+str(value),not V.early_cpu_evidence(guard,dict(ready,**{field:value}),release))
for bad in ({},{'kernel_controls_verified':1},{'kernel_controls_verified':False},{'kernel_controls_verified':True,'invented':1}):check('bad release '+str(bad),not V.early_cpu_evidence(guard,ready,bad))
check('early OOM refuses',not V.early_cpu_evidence(dict(guard,initial_memory_events={'oom':1,'oom_kill':0}),ready,release))
# All prior VF1 logic is byte-identical outside the explicit CPU/signature/IO seams.
s=(R/'verifier01.py').read_text()
for e in reversed(json.loads((R/'INVERSE03.json').read_bytes())['edits']):check('unique inverse '+str(len(checks)),s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
check('full byte inverse',s==(R/'original_verifier02.py').read_text());check('full AST inverse',ast.dump(ast.parse(s),include_attributes=False)==ast.dump(ast.parse((R/'original_verifier02.py').read_text()),include_attributes=False))
check('fixed QHASH unchanged',V.QHASH=='dc80a4dff93fbf3261bdf151076c1420630ed38926ab7094d60eb1902bde25bc');(R/'CHECKS03.json').write_bytes(V.R.encode({'count':len(checks),'checks':checks,'native_executions':0,'fabricated_real_receipts':0}));print(len(checks))
