"""Exact canonical-byte predicate and fresh namespace correction; no public receiver main."""
from pathlib import Path
import sys,json,ast,stat,importlib.util,types
HERE=Path(__file__).resolve().parent;OLDREVIEW=HERE.parent/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05';sys.path.insert(0,str(OLDREVIEW));from verify_capture01 import Reader,R,F,D
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation04-2026-10-05';OLD=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation03-2026-10-05';rd=Reader();seal=json.loads(rd.read(P/'MANIFEST01.json','968ab25a9db55288c96e503127f8a6b4dd225666348526c38354f81f872040f6'));inv=json.loads(rd.read(P/'INVERSE01.json'))
for r in seal['members']:
 p=P/r['path'];rd.pin(p);rd.need(stat.S_IMODE(p.lstat().st_mode)==r['mode'],'declared source04 type/mode')
 if r['kind']=='file':rd.need(len(rd.read(p,r['sha256']))==r['bytes'],'complete source04 seal body')
for name,changes in inv.items():
 back=rd.read(P/name).decode()
 for old,new in reversed(changes):rd.need(new in back,'declared exact inverse seam');back=back.replace(new,old)
 rd.need(back.encode()==rd.read(OLD/name),'complete inverse '+name)
for n in ('join01.py','restore_bundle01.py','flat_primitives01.py','cohort01.py','original_tree01.py','watch01.py','recover.template01.py','caller_remote01.py','caller_flat01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py'):rd.need(rd.read(P/n)==rd.read(OLD/n),'unchanged accepted helper '+n)
sys.path[:0]=[str(P),str(P/'utilities')];spec=importlib.util.spec_from_file_location('canonical_outcome04',P/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O);capture=rd.read(D/'CAPTURE01.json',O.CAPTURE);results=[]
for i in range(4):
 oldroot=F/('financial-wrapper-compatibility-complete100-outcome-remote-lane%02d-2026-10-05'%(i+1));q=json.loads(rd.read(oldroot/'ROOT_REQUEST01.json'));oldraw=rd.read(oldroot/'SELECTED_BODIES01.json');generated=O.generate(q,capture);code=ast.parse(generated['receiver']);defs={n.name:n for n in code.body if isinstance(n,ast.FunctionDef)}
 rd.need(ast.dump(defs['encode'],include_attributes=False)==ast.dump(next(n for n in ast.parse(rd.read(P/'receipt01.py')).body if isinstance(n,ast.FunctionDef) and n.name=='encode'),include_attributes=False),'one exact receiver/receipt encode AST')
 prelude=defs['main'].body;start=next(j for j,n in enumerate(prelude) if 'explicit frozen selection pin' in ast.unparse(n));stop=next(j for j,n in enumerate(prelude) if 'actual configured origin join' in ast.unparse(n));predicate=compile(ast.Module(body=prelude[start:stop],type_ignores=[]),'<exact receiver pre-Git predicates>','exec')
 for label,raw in [('actual_failed_compact',oldraw),('generated_canonical',generated['selection_body'])]:
  ns={'json':json,'Path':Path,'require':R.require,'digest':R.digest,'FILE':R.FILE,'REQUIRED':q['required'],'FINAL_POPULATION_COUNT':len(q['required']),'selection_body':raw,'args':types.SimpleNamespace(selection_sha256=R.digest(raw))}
  exec(compile(ast.Module(body=[defs['encode'],defs['validate_fixed_selection']],type_ignores=[]),'<exact receiver metadata functions>','exec'),ns)
  caught=None
  try:exec(predicate,ns)
  except ValueError as e:caught=e
  if label=='actual_failed_compact':rd.need(type(caught)is ValueError and str(caught)=='frozen canonical selection','actual old failure reproduced')
  else:rd.need(caught is None and raw==ns['encode'](json.loads(raw)) and json.loads(raw)==json.loads(oldraw),'exact new canonical prefix passes without Git')
  results.append({'lane':i,'case':label,'result':'pass' if caught is None else str(caught)})
 for phase in ('remote','flat'):
  root=O.lane_root(i,phase);rd.need(root.name=='financial-wrapper-compatibility-complete100-outcome-'+phase+'-lane%02d-canonical02-2026-10-05'%(i+1),'exact distinct prospective root');rd.need(root!=oldroot,'terminal identity not reused')
 rd.need('fresh-compatibility-complete100-outcome-lane%02d-canonical02.git'%(i+1) in generated['receiver'] and 'ROOT_BOUND_OUTCOME_LANE%02d_CANONICAL02_ENTRY'%(i+1) in generated['callers']['remote'],'fresh Git/status/caller labels')
rd.need(set(O.W.ROOTS)=={O.lane_root(i,phase) for i in range(4) for phase in ('remote','flat')} and O.W.MARGIN==805306368,'all eight fresh roots and unchanged shared margin')
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_SOURCE04_CANONICAL_SELECTION_AND_NEW_NAMESPACES_ONLY','source_sha256':R.digest((P/'outcome01.py').read_bytes()),'full_literal_inverse':True,'other_helpers_unchanged':True,'exact_receiver_preGit_controls':results,'original_four_failures_not_reused':True,'public_main_or_Git_operations':0,'actual_future_entry_released':False,'numerical_authority':False,'checks':rd.checks}
(HERE/'SOURCE04_CHECKS01.json').write_bytes(R.encode(result));print(json.dumps(result))
