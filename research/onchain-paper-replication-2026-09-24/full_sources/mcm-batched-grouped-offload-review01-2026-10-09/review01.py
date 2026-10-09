import ast,hashlib,importlib,json,os,resource,signal,struct,sys,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;R=H.parents[3];C=H.parent/'mcm-batched-grouped-offload01-2026-10-09';S=R/'tradingagents/research/onchain_replication';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((C/'MANIFEST01.json').read_text());assert all(sha(C/n)==v for n,v in manifest['sources'].items());pins=json.loads((C/'SOURCE_PINS.json').read_text());assert all(sha(R/n)==v for n,v in pins.items())
old=ast.parse((S/'typed_payload_operations.py').read_text());new=ast.parse((C/'typed_payload_operations.py').read_text());cls=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='_Operation');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='retire_batched_group');cls.body.remove(method);assert ast.dump(old)==ast.dump(new);assert (C/'inverse-typed-operations.py').read_bytes()==(S/'typed_payload_operations.py').read_bytes()
order={name:min(n.lineno for n in ast.walk(method) if isinstance(n,ast.Call) and ast.unparse(n.func)==name) for name in ('self.recover','semantic.recover','semantic.current','os.unlink')};assert list(order.values())==sorted(order.values())
pkg=types.ModuleType('independent_group');pkg.__path__=[str(C),str(S)];sys.modules[pkg.__name__]=pkg
m=importlib.import_module('independent_group.grouped_offload_semantics');jmod=importlib.import_module('independent_group.batched_journal');pres=importlib.import_module('independent_group.preservation')
f=H/'fixtures';f.mkdir();j=jmod.BatchJournal(f/'matching',batch_cells=1,max_cells=16,max_bytes=131072,max_body_bytes=1024,boundary=lambda:None);items=[]
for b in range(16):
 value=-0.0 if b%2 else 0.5
 j.run_batch_stream(1,iter([({'ordinal':b,'fresh_purpose':b},None,None)]),lambda *a,v=value:(v,7,'iteration_cap'),{'schema_version':2,'cells':16});token=b''
 for suffix in m.SUFFIXES:
  body,pin=j._read(f'{b:08d}{suffix}');token+=m.TOKEN.pack(*pin,len(body),hashlib.sha256(body).digest())
 items.append((b,token))
items=tuple(items);rows=m.source_rows(j,items);archive=f/'group16.tar';ma=pres.build_bundle(rows,archive,allowed_roots=[j.root],start_index=0);assert ma['archive_bytes']==m.archive_bound(rows)<=m.LIMIT;assert len(m.raw(m.binding(j,items,ma)))<=8192
original=[r for b,_ in items for r in j.read_complete(b)];seen=[]
e=m.recover(archive.read_bytes(),ma,j,items,f/'healthy',consume=lambda b,r:seen.extend(r));assert [(r[0],r[1],struct.pack('>d',r[2]),r[3],r[4]) for r in seen]==[(r[0],r[1],struct.pack('>d',r[2]),r[3],r[4]) for r in original] and e['stop']==16 and e['files']==48
checks=['actual16batch_48members_exact_f64_signedzero_purpose_status_closure','binding8192_and_archive4MiB_caps']
def refusal(name,callback):
 try:callback()
 except (ValueError,OSError):checks.append(name)
 else:raise AssertionError(name+' accepted')
def change_earlier(b,r):
 if b==15:
  p=f/'earlier/tree/00000000.pending.json';p.write_bytes(p.read_bytes()+b' ')
refusal('last_callback_earlier_pending_changed',lambda:m.recover(archive.read_bytes(),ma,j,items,f/'earlier',consume=change_earlier))
primary=RuntimeError('actual consumer primary')
def broken(b,r):raise primary
try:m.recover(archive.read_bytes(),ma,j,items,f/'primary',consume=broken)
except RuntimeError as err:assert err is primary;checks.append('consumer_primary_preserved')
else:raise AssertionError('missing primary')
# Execute the exact nested float64->float32 comparison without a fake Owner or View.
import numpy as np
fn=next(n for n in ast.walk(ast.parse((C/'grouped_offload.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name=='consume')
spool=f/'scores.f32';spool.write_bytes(np.asarray([r[2] for r in original],dtype='<f8').astype('<f4').tobytes());spool.chmod(0o600);fd=os.open(spool,os.O_RDONLY);ns={'np':np,'os':os,'semantic':m,'require':m.require,'spool_fd':fd,'spool':spool,'pin':jmod.sig(os.fstat(fd))};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_grouped_finalize_consumer','exec'),ns)
ns['consume'](0,original);checks.append('actual_cast_spool_comparison')
with spool.open('r+b') as stream:stream.seek(0);stream.write(struct.pack('<f',.75))
refusal('mutated_spool_refused',lambda:ns['consume'](0,original));os.close(fd)
assert all(hashlib.sha256((j.root/f'{b:08d}{s}').read_bytes()).digest()==m.TOKEN.unpack_from(t,i*56)[3] for b,t in items for i,s in enumerate(m.SUFFIXES));j.close()
out={'decision':'accepted_source_only','manifest_sha256':sha(C/'MANIFEST01.json'),'sources':manifest['sources'],'baseline_pins':pins,'checks':checks,'exact_default_typed_inverse':True,'genuine_recovery_before_retirement_source_order':order,'archive_bytes':ma['archive_bytes'],'binding_bytes':len(m.raw(e['binding'])),'original_fixture_files_retired':False,'genuine_owner_view_transport_executed':False,'full_capacity_admitted':False};(H/'RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
