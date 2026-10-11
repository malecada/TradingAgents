"""Exact final binding metadata checks; no admission, Git or native execution."""
import ast,copy,hashlib,json,os,stat
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];E=F/'real-data-pilot-full36-entry-preparation01-2026-10-11';NAME='eth-paper-real-data-end-to-end-resource-20261011-36'
sha=lambda b:hashlib.sha256(b).hexdigest();js=lambda p:json.loads(p.read_bytes())
request_path=E/'BINDING_REQUEST01.json';request_bytes=request_path.read_bytes();assert sha(request_bytes)=='00078de430149f95350d8db96288540f2936f5f1d342a453cd35f5e9942c135e'
request=json.loads(request_bytes);draft=js(E/'BINDING_DRAFT01.json');changed={k for k in request.keys()|draft.keys() if request.get(k)!=draft.get(k)}
assert changed=={'status','complete_increment_recovery','new_increment_recovery_review'} and request['binding_review'] is None
gate_path=E/'gate01.json';gate=js(gate_path);experiment=gate['experiments'][NAME];actual={role:{k:value[k] for k in ('path','sha256')} for role,value in experiment['inputs'].items()}
assert request['identity']==NAME and request['input_refs']==actual and len(actual)==73 and len(set(experiment['outputs']))==9
assert experiment['parent']==NAME[:-2]+'35' and request['gate']['sha256']==sha(gate_path.read_bytes())=='20f769eea62240230e8353cf35988d2b58cbcbf25a91bdfcf32a59a4e4e6e228'
opaque=request['transport']['path'];evidence={};references={}
def authenticate(ref):
    path=R/ref['path'];assert path.resolve()==path and not path.is_symlink() and path.is_file()
    s=path.stat();assert s.st_nlink==1 and s.st_size<=4*1024**2
    b=path.read_bytes();t=path.stat();assert all(getattr(s,k)==getattr(t,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
    assert sha(b)==ref['sha256']
    if 'bytes' in ref:assert len(b)==ref['bytes']
    assert ref['path'] not in evidence or evidence[ref['path']]==ref['sha256']
    evidence[ref['path']]=ref['sha256'];references[ref['path']]={'bytes':len(b),'sha256':ref['sha256']};return b
for path,pin in experiment['source_files'].items():authenticate({'path':path,'sha256':pin})
for role,ref in actual.items():authenticate(ref) # opaque body is hashed, never decoded
for role,ref in request.items():
    if isinstance(ref,dict) and {'path','sha256'}<=set(ref):authenticate(ref)
recovery_ref=request['complete_increment_recovery'];return_ref=request['new_increment_recovery_review']
assert recovery_ref['path']==str((F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full36increment32/FRESH_GIT_RECOVERY32.json').relative_to(R))
assert return_ref['path']==str((P/'RETURN_REVIEW01.json').relative_to(R)) and return_ref['sha256']=='230a939c4ed35ed09d0fc3dda5ad9328f7920c4686769d6f3e6a852a557ec1f8'
recovery=json.loads(authenticate(recovery_ref));returned=json.loads(authenticate(return_ref));assert returned['decision']=='accepted' and returned['source']==recovery['source']=='4c9029af4e35d508c02254f91081d56bea15b28c' and returned['archive']==recovery['returned_archive']
for name in ('ADMISSION01.json','ROOT_ADMISSION_OPERATIONS01.json'):
    path=E/name;authenticate({'path':str(path.relative_to(R)),'sha256':sha(path.read_bytes())})
admission_record=js(E/'ADMISSION01.json');assert admission_record==json.loads(js(E/'ROOT_ADMISSION_OPERATIONS01.json')['output']) and admission_record['ready'] is True and admission_record['empirical_inputs_opened'] is admission_record['run_started'] is False
body={'schema_version':1,'decision':'accepted','reviewer':'Independent increment32 return and exact pilot36 binding reviewer','identity':NAME,'input_refs':actual,'evidence':evidence,'references':references,'binding_request':{'path':str(request_path.relative_to(R)),'sha256':sha(request_bytes)},'counts':{'source_pins':len(experiment['source_files']),'inputs':73,'outputs':9,'capacity_source_bodies':428},'scope':'Exact actual73-role binding and new complete increment32 recovery references; prior accepted source/entry/cumulative checks reused. No admission, native launch or scientific completion. Final BINDING01 and exact source/entry release remain separate.','limits':['Opaque envelope authenticated only by hash, never decoded; no referenced connection or credential target opened.','All gate source/input and non-self binding references independently match current bytes. Git commitment and fresh runtime/capacity/namespace/process eligibility remain Root final preflight obligations.','Capture32 covers its exact frozen289bodies; subsequent admission/operation/review/binding/release metadata is separately pinned, not falsely claimed inside that tar.','Full37 capacity and scientific/whole-runtime/POSIX/deletion authority excluded.']}
encoded=(json.dumps(body,indent=2,sort_keys=True)+'\n').encode();review_path=P/'BINDING_REVIEW01.json';review_ref={'path':str(review_path.relative_to(R)),'sha256':sha(encoded),'bytes':len(encoded)}
# Exercise existing prepared_inputs on metadata containers, not genuine Admission/Run.
source=(E/'preflight36_01.py').read_bytes();assert sha(source)=='b00449135a348f5393afef09acadda02bab0cc2c60cf00f5abaa75f92ae72138'
tree=ast.parse(source);names={'need','reference','inverse_binding','_encoded','_path_envelope','prepared_inputs'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
ns=dict(Path=Path,ROOT=R,json=json,copy=copy,hashlib=hashlib,OPAQUE_ROLE='archive_transport',NAME=NAME)
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        try:ns[node.targets[0].id]=ast.literal_eval(node.value)
        except (ValueError,TypeError):pass
def metadata_read(ref):
    if ref==review_ref:return body
    assert ref['path']!=opaque,'opaque body decoding forbidden'
    return json.loads(authenticate(ref))
ns['read']=metadata_read;ns['read_path']=lambda path:path.read_bytes()
def capacity_metadata_join(capacity,public,admitted,current_source):
    pins=capacity['source_body_pins'];assert len(pins)==428 and pins==public['source_pins'] and all(admitted[p]==h for p,h in pins.items())
    assert capacity['source_anchor']=='f450f11cc44f5287d0daf1bcfcaea469d9347613' and 'source' not in capacity and 'max_age_seconds' not in capacity
ns['_capacity_source']=capacity_metadata_join # accepted Git ancestry reused; no Git in this review
exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual_prepared_inputs_metadata_only','exec'),ns)
bound_request=copy.deepcopy(request);bound_request['binding_review']=review_ref
release={'evidence':dict(evidence)|{review_ref['path']:review_ref['sha256']}}
metadata=SimpleNamespace(inputs=experiment['inputs'],experiment=experiment,source=recovery['source'])
job=metadata_read(actual['execution_job']);capacity=ns['prepared_inputs'](bound_request,release,metadata,job)
assert capacity['entry_qualification_only']['experiment_id']==NAME and capacity['full_pilot_capacity_admitted'] is False
# Validation only added refs already in the finite evidence closure; bytes remain exact.
assert encoded==(json.dumps(body,indent=2,sort_keys=True)+'\n').encode()
with review_path.open('xb') as h:h.write(encoded)
check={'status':'PASS_EXACT_BINDING_METADATA','request_sha256':sha(request_bytes),'binding_review':review_ref,'actual_prepared_inputs_metadata_control':True,'genuine_admission':False,'git':False,'native':False,'source_count':len(experiment['source_files']),'input_count':73,'evidence_count':len(evidence)}
with (P/'BINDING_CHECK01.json').open('x') as h:json.dump(check,h,sort_keys=True,indent=2);h.write('\n')
print(json.dumps(check))
