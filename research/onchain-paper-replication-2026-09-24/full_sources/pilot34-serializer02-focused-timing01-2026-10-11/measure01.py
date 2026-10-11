"""One finite synthetic component measurement; no research-module imports."""
import ast, hashlib, json, os, resource, sys, time
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=Path.cwd()
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
SOURCES={ROOT/'tradingagents/research/onchain_replication/provenance.py':'daf6cc3e72202dff01c50034f6a5ed3d5dcbb339d0e050444f722ce82a353471',F/'authority-current-pins-serialization02-2026-10-11/imported_mcm_identity.py':'e4bec3da9737e40e81bdeddc081ba64ff2be57007885e947e061710883f3014f',F/'authority-current-pins-serialization-review02-2026-10-11/REVIEW01.json':'7a91495ea4502cff8e35fe27a02a031fa61204907fbac3a9c2c3ba2f9b8671aa'}
result={'status':'FAILED','synthetic_only':True,'failures':[],'blocks':[],'loops_per_block':16,'order':['baseline','candidate','candidate','baseline'],'shape':{'source_records':421,'input_refs':67,'graphs':7,'metadata_only':True},'source_pins':{str(p.relative_to(ROOT)):h for p,h in SOURCES.items()}}
start=time.perf_counter();cpu=time.process_time()
try:
    assert os.sched_getaffinity(0)=={3} and os.getpriority(os.PRIO_PROCESS,0)==10
    for name,cap in [(resource.RLIMIT_CPU,10),(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2)]:
        assert resource.getrlimit(name)==(cap,cap)
    bodies={p:p.read_bytes() for p in SOURCES}
    assert all(hashlib.sha256(bodies[p]).hexdigest()==h for p,h in SOURCES.items())
    env={'json':json}
    for p,names in [(next(iter(SOURCES)),{'canonical_bytes','thaw'}),(list(SOURCES)[1],{'_current_bytes'})]:
        tree=ast.parse(bodies[p]);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        assert {n.name for n in nodes}==names
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),env)
    fixture={'schema_version':1,'kind':'SYNTHETIC_METADATA_NOT_AUTHORITY','sources':{f'synthetic/module_{i:04d}.py':{'sha256':f'{i:064x}','bytes':1000+i,'flags':[True,False,None],'tags':('source','é')} for i in range(421)},'inputs':{f'input_{i:03d}':{'path':f'synthetic/input_{i}.json','sha256':f'{1000+i:064x}'} for i in range(67)},'graphs':[{'name':f'graph_{i}','shape_metadata':{'nodes':100+i,'motifs':32},'ratio':0.125} for i in range(7)]}
    expected=env['canonical_bytes'](fixture);assert env['_current_bytes'](fixture)==expected
    (OUT/'FIXTURE01.json').write_bytes(expected+b'\n')
    result['output_bytes']=len(expected);result['output_sha256']=hashlib.sha256(expected).hexdigest()
    funcs={'baseline':env['canonical_bytes'],'candidate':env['_current_bytes']}
    for name in result['order']:
        fun=funcs[name];t=time.perf_counter();c=time.process_time()
        for _ in range(16):
            actual=fun(fixture)
            if actual!=expected:raise AssertionError('fresh output bytes differ')
        result['blocks'].append({'route':name,'loops':16,'elapsed_seconds':time.perf_counter()-t,'cpu_seconds':time.process_time()-c})
    result['status']='PASS_COMPONENT_BYTES_AND_TIMING';result['equal_calls']=64
except BaseException as error:
    result['failures'].append({'type':type(error).__name__,'message':str(error)})
finally:
    result.update(total_elapsed_seconds=time.perf_counter()-start,total_cpu_seconds=time.process_time()-cpu,python=sys.version,affinity=sorted(os.sched_getaffinity(0)),nice=os.getpriority(os.PRIO_PROCESS,0),limits={k:resource.getrlimit(v) for k,v in [('CPU',resource.RLIMIT_CPU),('AS',resource.RLIMIT_AS),('FSIZE',resource.RLIMIT_FSIZE)]},maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    with (OUT/'RESULT01.json').open('x') as stream:json.dump(result,stream,sort_keys=True,indent=2);stream.write('\n')
print(json.dumps(result,sort_keys=True))
if result['failures']:raise SystemExit(1)
