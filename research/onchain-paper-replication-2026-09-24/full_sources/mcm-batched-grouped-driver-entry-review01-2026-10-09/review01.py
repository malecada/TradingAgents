import resource,signal,os
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.sched_setaffinity(0,{3,4});os.nice(10)
from pathlib import Path
OUT=Path(__file__).resolve().parent;C=OUT.parent/'mcm-batched-pilot-entry-integration02-2026-10-09'
s=(OUT.parent/'mcm-batched-pilot-entry-integration01-2026-10-09/check01.py').read_text();prefix=s.split('checks=[]')[0];prefix=prefix.replace('HERE=Path(__file__).resolve().parent','HERE=C').replace('signal.alarm(60)','signal.alarm(30)');prefix=prefix.split("helper=load(")[0];exec(compile(prefix,str(C/'check01.py'),'exec'))
import types
adapter_path=OUT.parent/'mcm-batched-grouped-driver01-2026-10-09/compact_mcm_batched.py'
at=ast.parse(adapter_path.read_text());ans={'require':original.require,'FORMAT':'ordered-mcm-batch-closure-v2'}
exec(compile(ast.Module(body=[n for n in at.body if isinstance(n,ast.FunctionDef) and n.name in ('selected','validate')],type_ignores=[]),str(adapter_path),'exec'),ans)
own=ast.parse((ROOT/'tradingagents/research/onchain_replication/compact_owner.py').read_text());assignment=next(n for n in own.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STAGE_BYTES' for t in n.targets));ons={"io":types.SimpleNamespace(META_LIMIT=8192)};exec(compile(ast.Module(body=[assignment],type_ignores=[]),'actual_stage_constant','exec'),ons)
helper=types.ModuleType(PKG+'.batched_pilot_reservations');helper.__package__=PKG;helper.compact_mcm_batched=types.SimpleNamespace(selected=ans['selected'],validate=ans['validate']);helper.compact_owner=types.SimpleNamespace(STAGE_BYTES=ons['STAGE_BYTES']);sys.modules[helper.__name__]=helper
ht=ast.parse((C/'batched_pilot_reservations.py').read_text());ht.body=[n for n in ht.body if not(isinstance(n,ast.ImportFrom) and any(a.name=='compact_mcm_batched' for a in n.names))];exec(compile(ht,str(C/'batched_pilot_reservations.py'),'exec'),helper.__dict__)
candidate=load(PKG+'.candidate_reservation_sourcecheck',C/'real_pilot_reservations.py')

legacy=candidate.validate(*args)
setup=s[s.index('n=max(legacy'):s.index('value=candidate.validate')];exec(compile(setup,'public_policy_fixture','exec'))
checks=[];totals={}
for schema in (5,6):
 current=copy.deepcopy(selected);current[2]['schema_version']=schema
 group=16 if schema==6 else 1
 if schema==6:current[2]['batched'].update(group_batches=16,retention='typed-grouped-recover-before-retire-v1')
 totalgroups=totalbytes=0
 for key,g in current[5]['graphs'].items():
  n=g['rows']*32;batch_cells=current[2]['batched']['batch_cells'];parts=[batch_cells]*(n//batch_cells)+([n%batch_cells] if n%batch_cells else [])
  extents=[]
  for first in range(0,len(parts),group):
   sizes=[]
   for cells in parts[first:first+group]:sizes.extend((92+53*cells,current[2]['batched']['max_body_bytes'],current[2]['batched']['max_body_bytes']))
   extent=((sum(512+((x+511)//512)*512 for x in sizes)+1024+10239)//10240)*10240
   extents.append(extent)
  G=len(extents);A=sum(extents);v=g['kinds']['mcm-batched-bundle-v3'];v.update(max_operations=2*G,max_chunks=3*G,max_preserved_bytes=A,max_recovered_bytes=2*A,chunk_bytes=max(extents));totalgroups+=G;totalbytes+=A
 actual=candidate.validate(*current);assert actual['batched_schema']==schema and actual['pair_occurrences']==legacy['pair_occurrences'];checks.append('schema'+str(schema)+'_actual_graph_exact_minima')
 for field in ('max_operations','max_chunks','max_preserved_bytes','max_recovered_bytes','chunk_bytes'):
  bad=copy.deepcopy(current);bad[5]['graphs'][keys[0]]['kinds']['mcm-batched-bundle-v3'][field]-=1
  try:candidate.validate(*bad)
  except ValueError:checks.append('schema'+str(schema)+'_'+field+'_one_short_refused')
  else:raise AssertionError('one_short passed')
 totals[schema]={'groups':totalgroups,'conservative_archive_bytes':totalbytes}
# Pure arithmetic extrema independent of the original graph fixture.
for cells in (1,4095,4096,4097,65535,65536,65537):
 B=(cells+4095)//4096;G=(B+15)//16;assert G==(cells+65535)//65536
 checks.append('partition_boundary_'+str(cells))
(H if 'H' in globals() else OUT)
result={'decision':'arithmetic_pass','checks':checks,'totals':totals,'empirical_arrays':False,'genuine_authority':False,'capacity_admitted':False};(OUT/'ARITHMETIC01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
