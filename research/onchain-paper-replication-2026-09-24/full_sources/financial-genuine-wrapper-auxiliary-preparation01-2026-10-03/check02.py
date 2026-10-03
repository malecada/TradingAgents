import copy,json,os
from pathlib import Path
import build_aux01 as B
H=Path(__file__).resolve().parent;checks=[]
def ok(name,v):assert v,name;checks.append(name)
def refuse(name,fn):
 try:fn()
 except ValueError:checks.append(name);return
 raise AssertionError(name+' accepted')
p=H/'opaque02';p.write_bytes(b'bounded metadata');q=H/'opaque02-hardlink';os.link(p,q)
refuse('source-style reader retains single-link refusal',lambda:B.stream_pin(p))
ok('read-only runtime metadata permits actual hardlinks',B.stream_pin(p,64,runtime_metadata=True)==b'bounded metadata')
refuse('runtime metadata bound retained',lambda:B.stream_pin(p,3,runtime_metadata=True))
refuse('Git nonhex OID rejects',lambda:B.parse_tree(b'100644 blob '+b'z'*40+b'\tx.py\0'))
x=json.loads((H/'generated02/runtime_mapping.json').read_bytes())
ok('all251 original record/interpreter joins',B.baseline_runtime_join(x)['all251_prior_records_equal'])
y=copy.deepcopy(x);y['distribution_records'][0]['record_sha256']='0'*64
refuse('changed record refuses',lambda:B.baseline_runtime_join(y))
y=copy.deepcopy(x);y['distribution_records'].append(y['distribution_records'][0])
refuse('duplicate normalized name refuses',lambda:B.baseline_runtime_join(y))
y=copy.deepcopy(x);y['prefix']='/different'
refuse('wrong interpreter prefix refuses',lambda:B.baseline_runtime_join(y))
d=json.loads((H/'generated02/DRAFT01.json').read_bytes())
ok('exact18 drafts with no paper credit',len(d['slots'])==18 and d['paper_financial_fit_credit']==0 and d['phase_slots_unreserved']==18)
ok('all real release fields remain absent',all(v is None for v in d['future'].values()) and d['future_admitted_source_total'] is None)
for slot in d['slots']:
 ok('exact8 inputs slot'+str(slot['slot_index']),set(slot['inputs'])==B.BASE_INPUTS)
 for role,ref in slot['inputs'].items():
  ok('actual draft body pin '+str(slot['slot_index'])+'/'+role,B.R.digest(Path(ref['prepared_path']).read_bytes())==ref['sha256'] and ref['path'] is None and ref['dataset'] is None)
 plan=json.loads(Path(slot['inputs']['wrapper_plan']['prepared_path']).read_bytes())
 ok('null identity slot'+str(slot['slot_index']),all(plan[k] is None for k in ('cell_id','experiment','namespace')))
env=json.loads((H/'generated02/environment.DRAFT.json').read_bytes())
ok('Torch fields unresolved rather than inferred',all(env[k] is None for k in ('cuda_available','torch_version','cuda_build')))
refuse('generated draft cannot release',lambda:B.refuse_runnable(d))
(H/'CHECKS02.json').write_text(json.dumps({'checks':checks,'count':len(checks),'status':'passed'},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'status':'passed'}))
