import pathlib,json,hashlib,copy,stat,os
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();C=F/'real-data-pilot-full24-transport-binding01-2026-10-09';P=F/'real-data-pilot-full24-input-binding01-2026-10-09'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
check=j(C/'BINDING_CHECK01.json');bound=j(C/'BOUND01.json');prep=j(C/'PREPARED01.json');request=j(C/'REQUEST01.json');unbound=j(C/'UNBOUND_ARCHIVE01.json');refs=j(C/'ALL_INPUT_REFS01.json');prior=j(P/'PUBLIC_INPUT_REFS04.json');manifest=j(P/'PUBLIC_MANIFEST04.json')
for role in ('binder','prepared','request','bound'):
 ref=check[role];assert h(ROOT/ref['path'])==ref['sha256'] and (ROOT/ref['path']).stat().st_size==ref['bytes']
assert check['binder']['sha256']=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
assert bound['source_request']==request and bound['status']=='BOUND_DRAFT_NOT_REGISTERED_NOT_ADMITTED' and bound['independent_approval'] is False
assert prep['independent_approval'] is False and prep['builder03_spec']['template_roles']=={'job':'execution_job','producer_plan':'producer_plan','archive':'archive_policy'}
assert prep['builder03_spec']['references']['archive_policy']==request['archive_policy']
assert h(C/'UNBOUND_ARCHIVE01.json')==request['archive_policy']['sha256']
public={role:j(ROOT/ref['path']) for role,ref in manifest['public_inputs'].items()}
for role,ref in manifest['public_inputs'].items():assert h(ROOT/ref['path'])==ref['sha256']
a=copy.deepcopy(unbound);assert a['transport_identity'] is None;a['transport_identity']=public['archive_policy']['transport_identity'];assert a==public['archive_policy']
expected=copy.deepcopy(public);expected.pop('archive_policy')
for x in (expected['execution_job']['payload']['representation_jobs']['original32'],expected['producer_plan']['producers']['original32']):x['descriptor']['compact_archive_execution']['policy_sha256']=request['archive_policy']['sha256']
assert prep['builder03_result']['inputs']==expected
actual=bound['inputs'];assert len(actual)==11
expected.pop('archive_transport');expected['archive_policy']=copy.deepcopy(unbound);expected['archive_policy']['transport_identity']=bound['binding']['transport_identity']
assert actual['archive_policy']==expected['archive_policy']
archref=refs['archive_policy'];assert bound['binding']['archive_policy_sha256']==archref['sha256']
for x in (expected['execution_job']['payload']['representation_jobs']['original32'],expected['producer_plan']['producers']['original32']):x['descriptor']['compact_archive_execution']={'backend':unbound['backend'],'policy_sha256':archref['sha256']}
assert actual==expected
assert len(refs)==64 and set(refs)==set(prior)
for role,body in actual.items():
 p=C/'inputs01'/(role+'.json');assert j(p)==body and h(p)==refs[role]['sha256'] and refs[role]['path']==str(p.relative_to(ROOT))
private=bound['private_input'];assert set(private)=={'archive_transport'} and private==check['actual_opaque_input']
ref=private['archive_transport'];p=ROOT/ref['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==ref['bytes']==930
# Opaque bytes hashed only, never decoded/printed; no connection/key files opened.
assert h(p)==ref['sha256'] and refs['archive_transport']['path']==ref['path'] and refs['archive_transport']['sha256']==ref['sha256']
for role in set(refs)-set(actual)-{'archive_transport'}:assert refs[role]==prior[role]
assert not (ROOT/'research_runs'/check['experiment']).exists()
receipt={'decision':'accepted_transport_interface_supplement_only','evidence':{str(p.relative_to(ROOT)):h(p) for p in [C/'bind_actual01.py',C/'BINDING_CHECK01.json',C/'BOUND01.json',C/'PREPARED01.json',C/'REQUEST01.json',C/'UNBOUND_ARCHIVE01.json',C/'ALL_INPUT_REFS01.json',F/'mcm-batched-full24-core-review01-2026-10-09/SOURCE_REVIEW03.json']},'all_input_roles':64,'actual_public_docs':11,'opaque_private_ref':ref,'checks':['Public04 to prepared exact inverse except unbound archive identity/descriptor SHA.','Bound public docs exact inverse except actual opaque connection identity/descriptor SHA; all11 actual body pins verified.','All64 roles retained; unchanged inherited inputs reference-identical without scientific payload reads.','Exact accepted binder bcca source; actual publication reference hash/size/type/nlink/mode verified without decoding.','Prior accepted full science/fixed native/storage limits unchanged by binding transform.'],'pending':['Concrete gate and complete committed source/input closure.','Final binding/review/release and exact preflight/root caller joins.','Current resource/namespace/capacity eligibility and actual incremental preservation/recovery.'],'qualification':'Offline binding-interface review only. No opaque connection decoding, credentials, arrays, transport/network, Owner/Run, native launch or admission. Final entry review remains pending.'}
(R/'TRANSPORT_REVIEW01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(h(R/'TRANSPORT_REVIEW01.json'))
