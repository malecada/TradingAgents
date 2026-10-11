"""Independent stdlib source/clock controls; no actual authority or science imports."""
import ast,contextlib,hashlib,json,sys,types
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];S=R/'tradingagents/research/onchain_replication'
C=D.parent/'authority-expected-code-cache-candidate02-2026-10-11';checks=[]
def ck(value,name):
    assert value,name
    checks.append(name)
def nodes(path,names):
    return [n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
manifest=json.loads((C/'MANIFEST02.json').read_text());mismatches=[]
for name,ref in manifest['files'].items():
    if digest(C/name)!=ref['sha256'] or (C/name).stat().st_size!=ref['bytes']:mismatches.append(name)
ck(mismatches==['MANIFEST02.json'],'only manifest self-entry is stale; member hashes authenticate')
a=ast.parse((S/'imported_authority_lease.py').read_text());b=ast.parse((C/'imported_authority_lease.py').read_text())
for name in ('_loaded','_authenticate_loaded','_checked_value','target_lease'):
    get=lambda t:next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
    ck(ast.dump(get(a))==ast.dump(get(b)),'unchanged default '+name)
ns={};exec(compile((S/'phase_timing.py').read_text(),str(S/'phase_timing.py'),'exec'),ns)
clock=[0.];t=ns['PhaseTotals'](wall_clock=lambda:clock[0],cpu_clock=lambda:clock[0]);primary=KeyboardInterrupt('original')
try:
    with t.measure('entry'):
        clock[0]=1.
        with t.measure('role_read'):
            clock[0]=3.;raise primary
except KeyboardInterrupt as error:ck(error is primary,'nested fatal object preserved')
v=t.snapshot();ck(sum(x['wall_seconds'] for x in v['phases'].values())==3.,'nested exceptional intervals exclusive')
ck(v['phases']['entry']['failures']==v['phases']['role_read']['failures']==1,'nested failures recorded')
# Exact reader code plus the pure cleanup owner, with an explicitly inert module
# stand-in for descriptor-open/root signature operations. No numerical imports.
io=types.ModuleType('tradingagents.research.onchain_replication.score_batches')
exec(compile((S/'owned_io.py').read_text(),str(S/'owned_io.py'),'exec'),vars(io))
reader_ns={'require':lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg))}
exec(compile(ast.Module(body=nodes(S/'original_dictionary.py',{'_close_owned'}),type_ignores=[]),str(S/'original_dictionary.py'),'exec'),reader_ns)
import os
oldclose=os.close;seen=[]
def closing(fd):seen.append(fd);raise OSError('secondary close')
os.close=closing
try:
    try:
        try:raise primary
        finally:reader_ns['_close_owned']((1,2),io)
    except KeyboardInterrupt as error:ck(error is primary,'reader close keeps first fatal object')
    ck(seen==[1,2],'reader attempts both owned closes once')
finally:os.close=oldclose
# Publication values are scalar fixed-label rows; no success/authority state.
ck(ns['FORMAT']=='exclusive-wall-cpu-v1' and v['authority'] is False,'timing not authority')
result={'status':'PASS_WITH_MANIFEST_SELF_ENTRY_QUALIFICATION','checks':checks,'no_scientific_imports':True,'no_actual_authority':True,'manifest_non_authentic_self_entry':mismatches}
(D/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
