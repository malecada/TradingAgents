"""Offline exact-delivery/startup composition checks; no scientific imports."""
from pathlib import Path
import ast,hashlib,json,os,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];F=HERE.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def need(v,m):
 if not v:raise AssertionError(m)
def reverse(text,edits):
 for e in reversed(edits):
  need(text.count(e['after'])==1,'literal inverse occurrence');text=text.replace(e['after'],e['before'])
 return text
parents=read(HERE/'PARENTS01.json');delivery=read(HERE/'INSTALL_MAP01.json');edges=[]
for v in parents.values():need(sha((ROOT/v['manifest']).read_bytes())==v['sha256'],'parent manifest changed')
for x in delivery['sources']:
 raw=(ROOT/x['candidate']).read_bytes();need(sha(raw)==x['sha256'],'candidate changed')
 need(raw==(ROOT/x['accepted_parent']).read_bytes(),'not exact accepted body')
 compile(raw,x['candidate'],'exec')
 if x['root_install_path']:
  p=ROOT/x['root_install_path'];need((sha(p.read_bytes()) if p.exists() else None)==x['before_sha256'],'Main baseline changed')
for key in ('durability','history'):
 p=(ROOT/parents[key]['manifest']).parent;inv=read(p/'INVERSE01.json')
 for name,item in inv.items():
  after=(HERE/'candidate'/name).read_text()
  if key=='durability':
   before=reverse(after,item['literal_edits']);expected=item['before_sha256']
  else:
   lines=after.splitlines(True)
   for h in reversed(item['hunks']):
    need(lines[h['candidate_start']:h['candidate_end']]==h['candidate'],'hunk changed')
    lines[h['candidate_start']:h['candidate_end']]=h['original']
   before=''.join(lines);expected=item['baseline_sha256']
  need(sha(before.encode())==expected,'inverse hash changed')
  edges.append({'parent':key,'name':name,'before_sha256':expected,'after_sha256':sha(after.encode()),'exact_inverse':True})
p=(ROOT/parents['legacy']['manifest']).parent;inv=read(p/'INVERSE01.json')
after=(HERE/'candidate/real_pilot_import_caller.py').read_text();before=reverse(after,inv['edits'])
need(sha(before.encode())==inv['before_sha256'],'legacy inverse')
edges.append({'parent':'legacy','name':'real_pilot_import_caller.py','exact_inverse':True})
p=(ROOT/parents['progress']['manifest']).parent;inv=read(p/'INVERSE01.json')
after=(HERE/'candidate/real_pilot_partial_progress.py').read_text();before=reverse(after,[inv]);need(sha(before.encode())==inv['before_sha256'],'progress02 inverse')
inv1=read(F/'real-data-pilot-buffered-progress-correction01-2026-10-06/INVERSE01.json')
original=reverse(before,inv1['edits']);need(sha(original.encode())==inv1['before_sha256'],'progress01 historical inverse')
edges.extend([{'parent':'progress02','name':'real_pilot_partial_progress.py','exact_inverse':True},{'parent':'progress01-withheld-intermediate-only','name':'real_pilot_partial_progress.py','exact_inverse':True}])
for p,h in read(HERE/'UNCHANGED_SOURCE01.json').items():need(sha((ROOT/p).read_bytes())==h,'unchanged source differs')
old=read(HERE/'DEPENDENCIES_BEFORE01.json');new=read(HERE/'DEPENDENCIES01.json')
for key in new:
 need(new[key]['sha256']==old[key]['sha256'],'dependency body selection changed')
 need(sha((ROOT/new[key]['path']).read_bytes())==new[key]['sha256'],'dependency changed')
 if key not in ('history','builder','controls','durability'):need(new[key]==old[key],'unexpected path change')
# Exercise the actual relocated metadata loader and its relative allocation joins.
successor=load(HERE/'successor01.py')
mods={k:successor.load(k) for k in new}
mods['controls'].allocation();mods['history'].validate(successor.HISTORY);mods['durability'].policy(successor.DURABILITY)
# No policy or graph input is invented: actual partial template still refuses seven-count preparation.
draft=read(F/'real-data-pilot-feature-policy-successor-preparation01-2026-10-06/draft01/INPUT_DRAFT01.json')
try:successor.prepare(ROOT,draft)
except (ValueError,AssertionError,KeyError,TypeError) as exc:missing_refusal=str(exc)
else:raise AssertionError('incomplete historical draft unexpectedly prepared')
need('missing' in missing_refusal.lower() or 'seven' in missing_refusal.lower() or 'absent' in missing_refusal.lower() or 'required' in missing_refusal.lower(),'unexpected draft refusal: '+missing_refusal)
# Startup order only: no Run/Owner/capability is constructed.
caller=(HERE/'candidate/real_pilot_import_caller.py').read_text()
execute=next(n for n in ast.parse(caller).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
segment=ast.get_source_segment(caller,execute)
positions=[segment.index(s) for s in ('admitted(run.admission,job)','verify(run,graph,role)','archive_dispatch.preflight(', 'resource_binding.open_first(', 'original_import_stage.attach(', 'activate(execution,')]
need(positions==sorted(positions),'startup authority order differs')
dispatch=(HERE/'candidate/archive_dispatch.py').read_text()
preflight=next(n for n in ast.parse(dispatch).body if isinstance(n,ast.FunctionDef) and n.name=='preflight')
imports={a.name for n in ast.walk(preflight) if isinstance(n,ast.ImportFrom) for a in n.names}
need({'chunk_durability','archive_control_history','typed_payload_policy','typed_payload_operations','typed_score_store','typed_tail_binding','mcm_raw_parts'}<=imports,'eager selected dependencies missing')
need(segment.index('from .real_pilot_partial_progress import MCMProgress')<segment.index('activate(execution,'),'progress import is late')
# Actual selected BatchSync/property/progress composition with a tiny regular file.
progress_tree=ast.parse((HERE/'candidate/real_pilot_partial_progress.py').read_text())
fn=next(n for n in progress_tree.body if isinstance(n,ast.FunctionDef) and n.name=='_buffered_prefix')
ns={'require':lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg))}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-progress-function','exec'),ns)
tailtree=ast.parse((HERE/'candidate/score_tail.py').read_text())
cls=next(n for n in tailtree.body if isinstance(n,ast.ClassDef) and n.name=='ScoreTail')
prop=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='durability_status')
carrier=ast.ClassDef(name='MetadataCarrier',bases=[],keywords=[],body=[prop],decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[carrier],type_ignores=[])),'actual-tail-property','exec'),ns)
sync=mods['durability'].BatchSync(successor.DURABILITY,'tail');clock=sync.observed;sync._clock=lambda:clock
active=ns['MetadataCarrier']();active._durability=sync;active.start={'start_cell':7,'cells':2};active.closed=False;active.poisoned=False
stream=types.SimpleNamespace(active=active,cells=9)
p=HERE/'synthetic-buffer01.bin';need(not p.exists(),'fresh synthetic body required');fd=os.open(p,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600)
try:
 os.write(fd,b'ab');sync.acknowledge(fd,1,'a'*64);sync.acknowledge(fd,2,'b'*64)
 need(ns['_buffered_prefix'](stream,7)==(7,False),'ack confused with durable')
 sync.barrier(fd);need(ns['_buffered_prefix'](stream,7)==(9,False),'flush missing')
 active.closed=True;need(ns['_buffered_prefix'](stream,9)==(9,False),'completed active-tail overlap rejected/doubled')
 active.poisoned=True
 try:ns['_buffered_prefix'](stream,9)
 except ValueError:pass
 else:raise AssertionError('poisoned closed overlap accepted')
finally:os.close(fd)
result={'status':'PASS_SOURCE_COMPOSITION_ONLY','runtime_bodies':14,'metadata_bodies':3,'same_file_merges':0,'inverse_edges':edges,'startup_order':positions,'eager_selected_helpers':sorted(imports),'historical_incomplete_draft_refusal':missing_refusal,'buffered_cross_seam':['ack2/durable0','barrier durable2','closed overlap without double count','poisoned overlap refused'],'no_genuine_authority_or_numerical_execution':True}
(HERE/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('inverse_edges','eager_selected_helpers')},sort_keys=True))
