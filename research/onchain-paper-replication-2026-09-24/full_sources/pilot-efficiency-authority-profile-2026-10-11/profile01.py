"""Actual metadata helper timing only; no Lease/Run/Owner is constructed."""
import os,resource,signal,sys,time,json,hashlib,types,traceback
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
H=Path(__file__).resolve().parent;ROOT=H.parents[3];A=H/'attempt01';A.mkdir()
sys.path.insert(0,str(ROOT))
result={'scope':'metadata-only helper timing; SimpleNamespace carries cache context, never a Lease or authority','success':False,'rows':[]}
try:
    from tradingagents.research.onchain_replication import imported_authority_lease as auth, imported_authority_interval as interval, phase_timing
    modules=(auth,interval,phase_timing)
    sources={str(Path(m.__file__).relative_to(ROOT)):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules}
    loaded=auth._loaded(ROOT,sources)
    assert len(loaded)==3
    public_policy=H.parent/'authority-expected-code-cache-candidate02-2026-10-11/POLICY02.json'
    raw_policy=public_policy.read_bytes();selected=auth.expected_code_policy(json.loads(raw_policy))
    context=types.SimpleNamespace(loaded=loaded,sources=sources,run=types.SimpleNamespace(admission=types.SimpleNamespace(root=ROOT)),_expected_policy=selected,_expected_policy_pin=selected,_expected_tables=None,_expected_tables_pin=None)
    context._expected_context=context._expected_context_pin=auth._expected_context(context,selected)
    auth._expected_current(context,check_scope=True)
    source_paths={str(ROOT/p) for p in sources};active=None
    def audit(event,args):
        if active is None:return
        if event=='compile' and len(args)>1 and args[1] in source_paths:active['compile_events']+=1
        if event=='open' and args and type(args[0]) is str and args[0] in source_paths:active['source_open_events']+=1
    sys.addaudithook(audit)
    def measure(name,fn):
        global active
        counts={'compile_events':0,'source_open_events':0};totals=phase_timing.PhaseTotals()
        wall=time.perf_counter();cpu=time.process_time();active=counts
        try:
            with phase_timing.activate(totals):value=fn()
        finally:active=None
        row={'name':name,'wall_seconds':time.perf_counter()-wall,'cpu_seconds':time.process_time()-cpu,'audit_counts':counts,'phase_timing':totals.snapshot()}
        result['rows'].append(row)
        assert counts['source_open_events']==3
        phase=row['phase_timing']['phases']['source_read']
        assert phase['calls']==3 and phase['bytes']==sum((ROOT/p).stat().st_size for p in sources)
        return value
    measure('original_first',lambda:auth._authenticate_loaded(loaded,sources,ROOT))
    context._expected_tables=context._expected_tables_pin=measure('selected_first_build',lambda:auth._authenticate_expected(context))
    for i in range(6):
        for name in (('original','selected') if i%2==0 else ('selected','original')):
            if name=='original':measure(name+'_repeat_'+str(i),lambda:auth._authenticate_loaded(loaded,sources,ROOT))
            else:assert measure(name+'_repeat_'+str(i),lambda:auth._authenticate_expected(context)) is context._expected_tables
    for row in result['rows']:
        assert row['audit_counts']['compile_events']==(0 if row['name'].startswith('selected_repeat') else 3)
        assert row['phase_timing']['invalid_measurements']==0
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in sources.items())
    assert not any(n in sys.modules for n in ('numpy','scipy','torch'))
    result.update(success=True,source_sha256=sources,policy_sha256=hashlib.sha256(raw_policy).hexdigest(),loaded_module_count=len(loaded),loaded_function_entries=sum(len(row[2]) for row in loaded.values()),retained_code_objects=sum(len(values) for _,_,table in context._expected_tables for values in table.values()),source_read_includes='Path.read_bytes plus full SHA256 and comparison; no hash-only timer',module_auth_exclusive_includes='code-table walking/comparison and selected scope/policy checks, not a pure code-comparison timer',repeat_count_per_route=6,scientific_imported=False)
except BaseException as error:
    result['failure_type']=type(error).__name__
    with (A/'failure.txt').open('x') as f:traceback.print_exc(file=f)
    raise
finally:
    with (A/'RESULT01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'success':result['success'],'rows':len(result['rows']),'retained_code_objects':result['retained_code_objects']}))
