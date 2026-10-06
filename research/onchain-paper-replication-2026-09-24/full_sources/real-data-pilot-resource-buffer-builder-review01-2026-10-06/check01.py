import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).parent;F=H.parent;ROOT=F.parents[2]
A=F/'real-data-pilot-resource-buffer-allocation01-2026-10-06';B=F/'real-data-pilot-resource-input-builder03-2026-10-06';O=F/'real-data-pilot-resource-input-builder02-2026-10-06'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
members=0
for folder,manifest in [(A,'MANIFEST01.json'),(B,'MANIFEST03.json')]:
 for n,h in json.loads((folder/manifest).read_text()).items():assert sha(folder/n)==h;members+=1
 for n,h in json.loads((folder/('SOURCE_PINS01.json' if folder==A else 'SOURCE_PINS03.json')).read_text()).items():assert sha(ROOT/n)==h
assert sha(A/'allocation01.py')=='3912e68c232553f1fab5e39a92c0741c2c0ddab49316321c1189781d19611dfd'
assert sha(B/'build_inputs03.py')=='e100a1fa2f8caaa6baf6cde85d5f50aa667ed6e04b6470d9c8368d5424748a2d'
a=load('allocation_review',A/'allocation01.py');b=load('builder_review',B/'build_inputs03.py');o=load('old_builder_review',O/'build_inputs02.py')
change=json.loads((B/'CHANGE03.json').read_text());s=(B/'build_inputs03.py').read_text();assert len(change['literal_edits'])==9
for e in reversed(change['literal_edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'])
assert s==(O/'build_inputs02.py').read_text()
# Non-divisible selected batch/part witness, independently enumerate actual payload partitions.
rows,cells,part=3,40,1600
batches=[min(cells,rows*32-i) for i in range(0,rows*32,cells)]
parts=[min(part,n*80-i) for n in batches for i in range(0,n*80,part)]
q=a.graph(rows,cells,part,128,4096)
assert batches==[40,40,16] and parts==[1600,1600,1600,1600,1280]
assert q['required_typed_allowances']['score-tail-f64']=={'max_preserved_bytes':7680,'max_recovered_bytes':7680,'max_chunks':10,'max_operations':3}
# Run the actual bounded _Parts reader with scalar synthetic receipts; no genuine authority is constructed.
path=ROOT/'tradingagents/research/onchain_replication/typed_score_store.py';tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='_Parts')
ns={'require':lambda ok,why:None if ok else (_ for _ in ()).throw(ValueError(why))};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
class Counter:
 def __init__(self):self.calls=[]
 def recover(self,r,*,attempt):self.calls.append((r,attempt));return b'x'*r
counter=Counter();reader=ns['_Parts'](counter,parts,Path('/unused-synthetic-no-file'));readbytes=0
while chunk:=reader.read(80):readbytes+=len(chunk)
assert readbytes==7680 and len(counter.calls)==5
source=ROOT/'tradingagents/research/onchain_replication/typed_payload_operations.py';tree=ast.parse(source.read_text());call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='typed recovery allowance exhausted' for x in n.args));predicate=compile(ast.Expression(call.args[0]),str(source),'eval')
state=SimpleNamespace(counter={'recovered':7680,'chunks':10},budget={'max_recovered_bytes':7680,'max_chunks':10});assert eval(predicate,{'self':state})
for key in ('max_recovered_bytes','max_chunks'):
 state.budget[key]-=1;assert not eval(predicate,{'self':state});state.budget[key]+=1
# Whole builder: same funded fixture emits unchanged scientific templates and cumulative transport limits.
root=F/'real-data-pilot-resource-input-builder01-2026-10-06/synthetic02';spec=json.loads((B/'SYNTHETIC_SPEC03.json').read_text());oldspec=json.loads((O/'SYNTHETIC_SPEC02.json').read_text());after=b.build(root,spec);before=o.build(root,oldspec)
assert after['inputs']==before['inputs'] and after['opaque_references']==before['opaque_references'] and after['capacity_lower_bounds']['shared']==before['capacity_lower_bounds']['shared']
quota=sum(k['max_chunks'] for kinds in spec['typed_allocations']['by_week'].values() for k in kinds.values());bound=after['capacity_lower_bounds']['retained_local_lower_bounds']['typed_attempt_metadata_bytes'];assert bound>=4*8192*quota
refusals=[]
for key in ('typed_attempt_metadata_bytes','caller_scratch_bytes'):
 bad=copy.deepcopy(spec);bad['physical_store'][key]=after['capacity_lower_bounds']['retained_local_lower_bounds'][key]-1
 try:b.build(root,bad)
 except ValueError as e:assert key in str(e);refusals.append(str(e))
 else:raise AssertionError(key)
bad=copy.deepcopy(spec);bad['physical_store']['remaining_control_inventory']['other_selected_controls_bytes']=2**40
try:b.build(root,bad)
except ValueError as e:assert 'common store allocation' in str(e);refusals.append(str(e))
else:raise AssertionError('aggregate cap')
large=a.graph(100000,65536,4194240,4194304,(8*1024**2//168)*168)
assert large['selected_payload_overlap_upper_bytes']==30932896 and large['selected_payload_overlap_upper_bytes']>3*8*1024**2
assert 'numpy' not in sys.modules and 'torch' not in sys.modules
out={'decision':'pass-source-only','sealed_members_authenticated':members,'exact_literal_inverse_edits':9,'nondivisible_batches':batches,'part_sizes':parts,'actual_parts_reader_recovered_bytes':readbytes,'actual_recover_predicate_refuses_one_byte_or_one_credit_short':True,'unchanged_scientific_inputs_and_opaque_roles':True,'unchanged_shared_transport_caps':True,'quota_bound_attempt_metadata_bytes':bound,'selected_overlap_witness_bytes':large['selected_payload_overlap_upper_bytes'],'refusals':refusals,'numerical_import_or_genuine_authority_constructed':False,'capacity_claim':False}
(H/'CHECK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
