import json,pathlib,hashlib,copy,subprocess,resource,signal,os
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();C=F/'real-data-pilot-full24-input-binding01-2026-10-09';O=F/'real-data-pilot-final23-2026-10-09'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
m=j(C/'PUBLIC_MANIFEST04.json');refs=j(C/'PUBLIC_INPUT_REFS04.json');oldname='eth-paper-real-data-end-to-end-resource-20261009-23';name='eth-paper-real-data-end-to-end-resource-20261009-24';old=j(O/'gate03.json')['experiments'][oldname]['inputs']
assert m['experiment']==name and m['public_input_count']==len(m['public_inputs'])==12
assert len(m['source_pins'])==365
for p,v in m['source_pins'].items():assert h(ROOT/p)==v,p
assert m['source_anchor']==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert m['source_anchor'].startswith('958')
assert h(C/'bind_public04.py')==m['builder_sha256']
docs={}
for role,ref in m['public_inputs'].items():
 assert refs[role]==ref and h(ROOT/ref['path'])==ref['sha256'];docs[role]=j(ROOT/ref['path'])
assert set(refs)==set(old)
for role in set(refs)-set(docs):assert refs[role]==old[role]
def original(role):
 ref=old[role];assert h(ROOT/ref['path'])==ref['sha256'];return j(ROOT/ref['path'])
for role in ('compact_policy','mcm_policy','mcm_output_policy','typed_payload'):assert docs[role]==j(C/'core03'/(role+'.json'))
for role in ('resource_population_plan','original_import'):assert docs[role]==original(role)
a=copy.deepcopy(docs['archive_policy']);a['remote_namespace']=original('archive_policy')['remote_namespace'];assert a==original('archive_policy')
pair=copy.deepcopy(docs['pair_policy']);ns=pair['numerical_source'];assert ns['commit']==m['source_anchor']
assert set(ns['files'])==set(original('pair_policy')['numerical_source']['files'])
for p,v in ns['files'].items():assert h(ROOT/p)==v
pair['numerical_source']=original('pair_policy')['numerical_source'];assert pair==original('pair_policy')
job=copy.deepcopy(docs['execution_job']);pilot=copy.deepcopy(docs['pilot']);plan=copy.deepcopy(docs['producer_plan'])
resource=copy.deepcopy(job['resources']);budget=resource['storage_budget'];assert budget['experiment']==name and budget['roots'][1]==str(ROOT/'research_runs'/name)
budget['experiment']=original('execution_job')['resources']['storage_budget']['experiment'];budget['roots'][1]=original('execution_job')['resources']['storage_budget']['roots'][1]
assert resource==original('execution_job')['resources'];assert pilot['resource_policy']==job['resources']
assert job['resources']['storage_budget']['limits']['max_logical_bytes']==16*1024**3 and job['resources']['storage_budget']['limits']['max_allocated_bytes']==20*1024**3
sel=job['payload']['representation_jobs']['original32'];item=plan['producers'][sel['producer']]
for value,oldvalue in ((sel,original('execution_job')['payload']['representation_jobs']['original32']),(item,original('producer_plan')['producers'][sel['producer']])):
 d=value['descriptor'];assert d['configs']['dictionary']['size']==32 and d['configs']['dictionary']['sample_count']==512
 assert d['required_graphs']==sorted(pilot['graph_inputs']) and len(d['required_graphs'])==7
 for key,role in (('compact_execution','compact_policy'),('compact_archive_execution','archive_policy'),('pair_execution','pair_policy')):
  assert d[key]['policy_sha256']==refs[role]['sha256'];d[key]['policy_sha256']=oldvalue['descriptor'][key]['policy_sha256']
 assert value==oldvalue
job['resources']=resource;assert job==original('execution_job');assert plan==original('producer_plan')
assert pilot['cell_id']=='real-eth-seven-graph-joint-update-resource24' and 'partial_progress' not in pilot and 'scoring_diagnostic' not in pilot and 'diagnostic' not in pilot['outputs']
op=original('pilot');op.pop('partial_progress',None);op.pop('scoring_diagnostic',None);op['outputs'].pop('diagnostic',None);op['cell_id']=pilot['cell_id'];op['resource_policy']=pilot['resource_policy'];assert pilot==op
for role in ('model','training'):assert refs[role]==old[role]==m['model_training_original_refs'][role]
t=docs['archive_transport'];assert t['connection'] is None
assert {k:v for k,v in t.items() if k not in ('schema_version','format','typed_payload_input','connection')}==j(C/'TRANSPORT_LIMITS03.json')
assert not (ROOT/'research_runs'/name).exists()
r={'decision':'accepted_public_core_supplement_only','prior_review_sha256':h(R/'SOURCE_REVIEW02.json'),'public_manifest_sha256':h(C/'PUBLIC_MANIFEST04.json'),'public_refs_sha256':h(C/'PUBLIC_INPUT_REFS04.json'),'builder_sha256':m['builder_sha256'],'source_anchor':m['source_anchor'],'current_source_pin_count':365,'numerical_source_pin_count':len(ns['files']),'public_inputs':m['public_inputs'],'checks':['All12 public body hashes and exact descriptor policy SHA joins.','Full inverses of job/producer/archive/pair/pilot changed fields; original decisions/config/model/training and512samples32motifs7graphs retained.','No partial progress/scoring diagnostic/1024 prefix stop; new full joint-update cell.','Native/storage resource inverse changes only experiment and corresponding existing root;16/20GiB caps unchanged.','Current365 sourcepins and declared numerical roster hashes joined to actual HEAD anchor.','Opaque connection is None; no private body read and no valid transport authority asserted.'],'qualification':'Partial public binding only. Actual opaque binder, registry, current namespace/resource/capacity facts, committed final source closure, preservation and release remain required. No execution/admission/claim.'}
(R/'SOURCE_REVIEW03.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'decision':r['decision'],'sha256':h(R/'SOURCE_REVIEW03.json'),'source_anchor':m['source_anchor']}))
