"""Concrete successor public metadata; no authority, private connection or numerical imports."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent;F=HERE.parent
EDITION=sys.argv[1] if len(sys.argv)>1 else '02'
assert EDITION in ('01','02')
OLD='eth-paper-real-data-end-to-end-resource-20261009-26';NEW='eth-paper-real-data-end-to-end-resource-20261009-27'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def save(p,v):
 with p.open('xb') as f:f.write(raw(v))
 return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def move(v):
 if type(v) is dict:return {move(k):move(x) for k,x in v.items()}
 if type(v) is list:return [move(x) for x in v]
 if type(v) is str:return v.replace(OLD,NEW).replace('real-eth-seven-graph-joint-update-resource26','real-eth-seven-graph-joint-update-resource27').replace('ethpilot-20261009-26','ethpilot-20261009-27')
 return v
assert not (ROOT/'research_runs'/NEW).exists()
binding=load(F/'real-data-pilot-full26-entry01-2026-10-09/BINDING01.json');evidence={}
def bound(k):
 ref=binding[k];p=ROOT/ref['path'];assert sha(p)==ref['sha256'];evidence[k]=ref;return load(p)
prepared=bound('preparation');prior_public=bound('public_manifest');docs=move(copy.deepcopy(prepared['builder03_result']['inputs']));docs['archive_policy']=move(bound('unbound_archive'))
assert docs['archive_transport']['connection'] is None
oldnumerical=docs['pair_policy']['numerical_source'];names=set(oldnumerical['files'])
package=ROOT/'tradingagents/research/onchain_replication';required={'tradingagents/research/onchain_replication/'+p.name for p in package.glob('*.py')}|{'tradingagents/research/'+p.name for p in package.parent.glob('*.py')}|{'tradingagents/__init__.py'}
assert names==required and len(names)==193
current={n:sha(ROOT/n) for n in sorted(names)};publicpins={n:sha(ROOT/n) for n in prior_public['source_pins']}
changed={n:dict(prior=oldnumerical['files'][n],current=current[n]) for n in names if oldnumerical['files'][n]!=current[n]}
expected={'tradingagents/research/onchain_replication/'+n for n in ('batched_driver.py','batched_numeric_execution.py','batched_numeric_reuse.py','batched_pair_executor.py','compact_mcm_batched.py','real_pilot_import_caller.py')};assert set(changed)==expected
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
# Exact committed bodies, one finite Git batch. Public source closure excludes secrets/data.
anchor_pins=dict(publicpins);anchor_pins.update(current);ordered=sorted(anchor_pins);response=subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,input=''.join(head+':'+n+'\n' for n in ordered).encode());offset=0;pending=[]
for n in ordered:
 end=response.index(b'\n',offset);header=response[offset:end].split();assert len(header)==3 and header[1]==b'blob';size=int(header[2]);offset=end+1;body=response[offset:offset+size];offset+=size;assert response[offset:offset+1]==b'\n';offset+=1
 if hashlib.sha256(body).hexdigest()!=anchor_pins[n]:pending.append(n)
assert offset==len(response)
anchor=None if pending else head
docs['pair_policy']['numerical_source']={'commit':anchor,'files':current}
selected=docs['execution_job']['payload']['representation_jobs']['original32'];producer=docs['producer_plan']['producers']['original32']
for role,key in [('pair_policy','pair_execution'),('compact_policy','compact_execution'),('archive_policy','compact_archive_execution')]:
 pin=hashlib.sha256(raw(docs[role])).hexdigest()
 for value in (selected,producer):value['descriptor'][key]['policy_sha256']=pin
destination=HERE/('public'+EDITION);destination.mkdir(exist_ok=False);public_refs={}
for role,value in docs.items():
 ref=save(destination/(role+'.json'),value);public_refs[role]={k:ref[k] for k in ('path','sha256')};public_refs[role]['dataset']='eth'
refs=copy.deepcopy(bound('public_refs'));refs.update(public_refs);scratch=move(load(ROOT/refs['matching_ordered_edge_scratch']['path']));scratchref=save(HERE/('MATCHING_SCRATCH_RESERVATION'+EDITION+'.json'),scratch);refs['matching_ordered_edge_scratch']={k:scratchref[k] for k in ('path','sha256')};refs['matching_ordered_edge_scratch']['dataset']='eth'
assert len(refs)==64 and len(docs)==12;save(HERE/('PUBLIC_INPUT_REFS'+EDITION+'.json'),refs)
public=move(copy.deepcopy(prior_public));public.update(status='DRAFT_NOT_RELEASED',source_anchor=anchor,source_pins=publicpins,builder_sha256=sha(Path(__file__)),public_inputs=public_refs)
public['qualification']='Complete unchanged seven-graph science; added sampled Target authority polls and omitted discarded eager preparation only on selected schema6 lease route. Later-graph refusal may follow earlier graph work. Indivisible operations exceeding remaining60s freshness still refuse. No admission, currentness, remote reservation, recovery or runtime capacity assertion.'
publicref=save(HERE/('PUBLIC_MANIFEST'+EDITION+'.json'),public)
core=bound('core_manifest');core['builder_sha256']=sha(Path(__file__));core['source']={n:sha(ROOT/n) for n in core['source']};core['status']='DRAFT_NOT_RELEASED'
for role in core['inputs']:
 core['inputs'][role]={k:public_refs[role][k] for k in ('path','sha256')};core['inputs'][role]['bytes']=(ROOT/public_refs[role]['path']).stat().st_size
save(HERE/('CORE_MANIFEST'+EDITION+'.json'),core)
capacity=move(bound('capacity_observation'));capacity.update(decision='DRAFT_NOT_REVIEWED',decision_scope='Inherited prospective budget numbers only; Root adoption and fresh eligibility/review pending.',source_anchor=anchor,source_body_pins=publicpins)
capacity['basis']['public_source_manifest']=publicref;capacity['basis']['currentness_sample']=None;capacity['basis']['remote_storage_sample']=None
capacity['qualification']+=' Successor27 draft: prior timestamp and source baseline are historical provenance only; fresh union baseline must include failed26. Polling/eager-sweep timing changes require separate source/entry review. Currentness and remote reservation are unset.'
save(HERE/('CAPACITY_DECLARATION'+EDITION+'.json'),capacity)
record={'status':'DRAFT_NOT_RELEASED','identity':NEW,'terminal_parent':OLD,'inputs':64,'public_documents':12,'numerical_source_files':193,'source_anchor':anchor,'observed_head':head,'pending_source_paths':pending,'source_changes':changed,'original_model_training_refs':public['model_training_original_refs'],'prior_binding':binding['gate'],'inherited_evidence':evidence,'pending_requirements':['Root committed exact source anchor' if pending else 'Root registration of exact committed source closure','Genuine new transport binding/private dispatch outside this builder','Independent capacity/source/entry review, actual currentness/union/native/resource checks and external recovery','Root cumulative allowance and final gate; no claim created'],'builder03_result':{'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','inputs':docs},'qualification':public['qualification']}
save(HERE/('PREPARATION'+EDITION+'.json'),record)
print(json.dumps({k:record[k] for k in ('status','identity','inputs','public_documents','numerical_source_files','source_anchor','pending_source_paths')}))
