"""Focused offline changed-seam checks; no live graph/guard/transport execution."""
import ast, hashlib, json, types
from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parents[3]
changes=json.loads((H/'INVERSE01.json').read_bytes())
for name,delta in changes.items():
    text=(H/name).read_text();compile(text,str(H/name),'exec')
    assert hashlib.sha256(text.encode()).hexdigest()==delta['after_sha256']
    for e in reversed(delta['literal_edits']):
        assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'])
    assert text.encode()==(M/delta['baseline']).read_bytes()
space={'__name__':'offline_preparation_check'};exec(compile((H/'prepare01.py').read_bytes(),str(H/'prepare01.py'),'exec'),space)
temp=H/'synthetic';temp.mkdir();run=temp/space['ROOTS'][0];run.mkdir(parents=True)
ref={'path':'review.json','sha256':'0'*64};refusals=[]
for label in ['active','failed']:
    if label=='failed':(run/'failed.json').write_text('{}')
    try:space['select'](temp,ref,ref)
    except ValueError as e:assert 'genuine COMPLETE' in str(e);refusals.append(label)
    else:raise AssertionError(label)
# Only select's prefix through the exact review predicate, stopping before body proofs.
tree=ast.parse((H/'prepare01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='select')
stop=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='evidence' for t in n.targets))
fn.body=fn.body[:stop];fn.name='prefix';exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'review-predicate','exec'),space)
(run/'failed.json').unlink();(run/'complete.json').write_text('{}')
review={'decision':'accepted','experiment':space['GRAPH'],'source':space['SOURCE'],'root_actual_exit':{'exit_code':1}}
def write_review():
    p=temp/'review.json';p.write_text(json.dumps(review));return {'path':'review.json','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
try:space['prefix'](temp,write_review(),ref)
except ValueError as e:assert 'actual Root zero' in str(e);refusals.append('Root1')
else:raise AssertionError('Root1')
review['root_actual_exit']['exit_code']=0;space['prefix'](temp,write_review(),ref)
# Actual changed helper exception branch: tiny stand-ins, no body or network call.
ks={'__name__':'offline_keep_check'};exec(compile((H/'keep.py').read_bytes(),str(H/'keep.py'),'exec'),ks)
primary=RuntimeError('original transfer failure');secondary=OSError('failure receipt unavailable');calls=[]
class Primitive:
    def publish(self,p,v):
        calls.append(p.name)
        if p.name=='failed.json':raise secondary
class Transport:
    remaining=8*1024**3
    def available(self):raise primary
ks['bind_primitives']=lambda root:Primitive()
ks['shutil']=types.SimpleNamespace(disk_usage=lambda path:types.SimpleNamespace(free=100*1024**3))
root=temp.resolve();out=root/'out';out.mkdir();source=root/'tiny';source.write_bytes(b'')
c={'identity':ks['ID'],'schema_version':1,'files':[{'path':'tiny','bytes':0,'sha256':hashlib.sha256(b'').hexdigest(),'stat_identity':[1,1,0,1,1]}],'count':1,'total_bytes':0,'max_body_bytes':0,'disk_floor_bytes':10*1024**3,'transport_payload_budget_bytes':8*1024**3,'owned_tree_limit_bytes':5*1024**3,'remote':'synthetic-unused'}
try:ks['preserve_selected'](root,out,c,Transport(),lambda:None)
except BaseException as e:assert e is primary and any('failure receipt unavailable' in n for n in e.__notes__)
else:raise AssertionError('original error was lost')
assert calls==['intent.json','failed.json']
result={'decision':'pass-source-only','exact_inverses':list(changes),'refusals':refusals,'Root0_predicate_pass':True,'original_exception_identity_preserved':True,'secondary_failure_recorded_as_note':True,'genuine_admission_or_guard_tested':False,'live_graph_or_payload_reads':0,'native_network_or_claim_calls':0}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
