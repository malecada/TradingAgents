import resource,signal,os
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.sched_setaffinity(0,{3,4});os.nice(10)
from pathlib import Path
OUT=Path(__file__).resolve().parent;C=OUT.parent/'mcm-batched-pilot-entry-integration01-2026-10-09'
s=(C/'check01.py').read_text();prefix=s.split('checks=[]')[0];prefix=prefix.replace('HERE=Path(__file__).resolve().parent','HERE=C').replace('signal.alarm(60)','signal.alarm(30)');prefix=prefix.split("helper=load(")[0];exec(compile(prefix,str(C/'check01.py'),'exec'))
import types
adapter_path=ROOT/'tradingagents/research/onchain_replication/compact_mcm_batched.py'
at=ast.parse(adapter_path.read_text());ans={'require':original.require,'FORMAT':'ordered-mcm-batch-closure-v2'}
exec(compile(ast.Module(body=[n for n in at.body if isinstance(n,ast.FunctionDef) and n.name in ('selected','validate')],type_ignores=[]),str(adapter_path),'exec'),ans)
own=ast.parse((ROOT/'tradingagents/research/onchain_replication/compact_owner.py').read_text());assignment=next(n for n in own.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STAGE_BYTES' for t in n.targets));ons={};exec(compile(ast.Module(body=[assignment],type_ignores=[]),'actual_stage_constant','exec'),ons)
helper=types.ModuleType(PKG+'.batched_pilot_reservations');helper.__package__=PKG;helper.compact_mcm_batched=types.SimpleNamespace(selected=ans['selected'],validate=ans['validate']);helper.compact_owner=types.SimpleNamespace(STAGE_BYTES=ons['STAGE_BYTES']);sys.modules[helper.__name__]=helper
ht=ast.parse((C/'batched_pilot_reservations.py').read_text());ht.body=[n for n in ht.body if not(isinstance(n,ast.ImportFrom) and any(a.name=='compact_mcm_batched' for a in n.names))];exec(compile(ht,str(C/'batched_pilot_reservations.py'),'exec'),helper.__dict__)
candidate=load(PKG+'.candidate_reservation_sourcecheck',C/'real_pilot_reservations.py')
manifest=read(C/'MANIFEST01.json');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert all(sha(C/k)==v for k,v in manifest['files'].items());assert all(sha(ROOT/'tradingagents/research/onchain_replication'/k)==v for k,v in manifest['originals'].items())
legacy=candidate.validate(*args)
setup=s[s.index('n=max(legacy'):s.index('value=candidate.validate')];exec(compile(setup,'fixture_metadata','exec'))
# Independently compute exact conservative tar ceilings, set minima per graph.
batch=4096;total_archives=total_bytes=0
for key,g in selected[5]['graphs'].items():
 n=g['rows']*32;full,last=divmod(n,batch);B=full+bool(last)
 def tar_bound(n):
  padded=lambda x:((x+511)//512)*512
  return ((512*3+padded(92+53*n)+2*padded(selected[2]['batched']['max_body_bytes'])+1024+10239)//10240)*10240
 A=full*tar_bound(batch)+(tar_bound(last) if last else 0);v=g['kinds']['mcm-batched-bundle-v3'];v.update(max_operations=2*B,max_chunks=3*B,max_preserved_bytes=A,max_recovered_bytes=2*A,chunk_bytes=max(tar_bound(batch),tar_bound(last) if last else 0));total_archives+=B;total_bytes+=A
result=candidate.validate(*selected);assert sum(result['pair_occurrences'].values())==415968128 and total_archives==101559 and result['physical_capacity_admitted'] is False
checks=['exact_per_graph_tar_upper_and_minimum_2B_3B_2A_pass']
for key in ('max_operations','max_chunks','max_preserved_bytes','max_recovered_bytes','chunk_bytes'):
 bad=copy.deepcopy(selected);bad[5]['graphs'][keys[0]]['kinds']['mcm-batched-bundle-v3'][key]-=1
 try:candidate.validate(*bad)
 except ValueError:checks.append(key+'_one_below_minimum_refused')
 else:raise AssertionError('one below accepted '+key)
# Original legacy failure corrected without changing original formulas.
try:original.validate(*args)
except KeyError as e:assert e.args==('mcm-batched-bundle-v3',);checks.append('actual_legacy_added_kind_red_green')
else:raise AssertionError('expected legacy bug absent')
text=(C/'real_pilot_reservations.py').read_text();a=text.index('    if type(mcm) is dict');b=text.index('    typed_payload_policy.validate(typed)',a);inverse=(text[:a]+text[b:]).replace('typed_payload_policy.LEGACY_KINDS.items()','typed_payload_policy.KINDS.items()');assert inverse==(ROOT/'tradingagents/research/onchain_replication/real_pilot_reservations.py').read_text()
# Caller unchanged functions retain exact AST. Admission archive role equality
# predates and dominates the new transport-role dereference.
new=ast.parse((C/'real_pilot_import_caller.py').read_text());old=ast.parse((ROOT/'tradingagents/research/onchain_replication/real_pilot_import_caller.py').read_text());fn=lambda t:{n.name:n for n in t.body if isinstance(n,ast.FunctionDef)};nf=fn(new);of=fn(old)
for name in of:
 if name not in ('admitted','_prepare_lease_modules','execute'):assert ast.dump(of[name])==ast.dump(nf[name])
preload=nf['_prepare_lease_modules'];newmods={a.name for n in ast.walk(preload) if isinstance(n,ast.ImportFrom) for a in n.names};required={'compact_mcm_batched','matching_immutable_session','batched_driver','batched_journal','batched_pair_executor','batched_numeric_execution','batched_numeric_reuse','registered_offload','batched_offload_semantics','batched_pilot_reservations'};assert required<=newmods
ad=ast.unparse(nf['admitted']);assert ad.index("p.get('archive_inputs') == expected_archive")<ad.index("transport = _read(ad, p['archive_inputs']['transport_input'])");assert ad.index("'partial_progress' not in p and 'scoring_diagnostic' not in p")<ad.index('reservations(')
execute=ast.unparse(nf['execute']);assert execute.index('_prepare_lease_modules(')<execute.index('activate(execution,')
record={'decision':'accepted_source_only','manifest_sha256':sha(C/'MANIFEST01.json'),'sources':manifest['files'],'baseline_sources':manifest['originals'],'checks':checks,'total_graph_reset_batches':total_archives,'conservative_archive_bytes':total_bytes,'source_preload_roles':sorted(required),'legacy_inverse':True,'genuine_authority':False,'physical_capacity_admitted':False,'claim':False};(OUT/'RESULT02.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
