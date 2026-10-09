"""Actual metadata inverse/refusals only; never creates Admission or runs preflight."""
import ast,hashlib,json,os,resource,difflib
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);os.nice(10)
H=Path(__file__).resolve().parent;F=H.parent;ROOT=H.parents[3];old=F/'real-data-pilot-final23-2026-10-09';source=(H/'preflight24.py').read_text();tree=ast.parse(source);original=ast.parse((old/'preflight02.py').read_text())
checks=[]
for name in ('reference','read_path','read','authenticate_committed','committed_refs','validate_opaque','inverse_binding'):
 find=lambda t:next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(find(tree))==ast.dump(find(original));checks.append('literal_AST_'+name)
assert (H/'root_io24.py').read_text().replace('from preflight24 import check','from preflight02 import check')==(old/'root_io02.py').read_text();checks.append('literal_root_io_inverse')
import copy
scope=dict(ROOT=ROOT,Path=Path,hashlib=hashlib,json=json,copy=copy,OPAQUE_ROLE='archive_transport')
names=('need','reference','read_path','read','inverse_binding','_path_envelope','_encoded','projected')
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<actual source helpers>','exec'),scope)
D=F/'real-data-pilot-full24-transport-binding01-2026-10-09';prepared=json.loads((D/'PREPARED01.json').read_text());unbound=json.loads((D/'UNBOUND_ARCHIVE01.json').read_text());bound=json.loads((D/'BOUND01.json').read_text());private=json.loads((D/'BINDING_CHECK01.json').read_text())['actual_opaque_input']['archive_transport']
binder=F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';body=binder.read_bytes();assert hashlib.sha256(body).hexdigest()=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
bt=ast.parse(body);bs=dict(json=json,hashlib=hashlib);exec(compile(ast.Module(body=[n for n in bt.body if isinstance(n,ast.FunctionDef) and n.name in ('raw','sha')],type_ignores=[]),'<actual binder encode>','exec'),bs)
scope['inverse_binding'](prepared,unbound,bound,private,bs['raw'],bs['sha']);checks.append('actual24_public_binder_inverse_no_private_read')
for label,fn in [('missing_ref',lambda:scope['reference'](None)),('unsafe_path',lambda:scope['_path_envelope']('/tmp/../bad')),('int_overflow',lambda:scope['_encoded']({'x':2**63})),('growth_cap',lambda:scope['projected'](dict(new_logical_growth_bytes=2,new_allocated_growth_bytes=2,new_entries=1),dict(logical_file_bytes=1,allocated_bytes=1,entries=1),dict(max_logical_bytes=2,max_allocated_bytes=2,max_entries=2)))]:
 try:fn()
 except (ValueError,KeyError):checks.append('refused_'+label)
 else:raise AssertionError(label)
assert source.count("runtime_inventory=subprocess.check_output(")==1 and 'timeout=30' in source and 'module.prepare(ROOT,draft' not in source and 'SUCCESSOR=' not in source
checks.append('single30s_inventory_no_old_metadata_replay')
(H/'inverse.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),(old/'preflight02.py').read_text().splitlines(True),fromfile='candidate/preflight24.py',tofile='original/preflight02.py')))
result=dict(status='PASS_SOURCE_METADATA_ONLY',checks=checks,preflight_executed=False,genuine_admission_constructed=False,opaque_body_read=False,affinity=sorted(os.sched_getaffinity(0)))
(H/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
