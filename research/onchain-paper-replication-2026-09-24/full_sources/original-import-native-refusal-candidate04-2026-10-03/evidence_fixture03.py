"""Parser tests on explicitly fake JSON/files only, not Owner construction."""
import hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent
sys.path.insert(0,str(F/'original-import-fixture-native-preparation03-2026-10-03'))
sys.path.insert(0,str(D))
import refusal_cases as cases
from stage_fixture03 import POLICY
from refusal_evidence import canonical,key
S=D;spec=importlib.util.spec_from_file_location('selected_caller',S/'refusal_caller.py');caller=importlib.util.module_from_spec(spec);spec.loader.exec_module(caller)
def fixture(root,variant):
 name=cases.identity(variant);run=root/'research_runs'/name;source='a'*40;registration='b'*64;inputs={}
 def write(path,value):
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value if isinstance(value,bytes) else canonical(value));return path
 def put(name,value):
  path='inputs/'+name+'.json';raw=canonical(value);write(root/path,raw);inputs[name]={'path':path,'sha256':hashlib.sha256(raw).hexdigest()}
 from synthetic_original import fixture as original_fixture
 from original_semantics import expected_numeric
 original,blobs=original_fixture();matching=json.loads(blobs['matching_config'])
 from synthetic_targets04 import graphs
 targets,target_files=graphs()
 required=[t['graph_hash'] for t in targets];original['required_graphs']=required;numeric=expected_numeric(original,blobs);descriptor={'required_graphs':required,'configs':{'matching':matching},'resource_graph_inputs':{required[0]:'target0',required[1]:'target1'},'resource_fixture':{'case':'refusal-'+variant}};workflow=key(descriptor)
 selected={'plan_input':'plan','producer':'p','pair_checkpoint_input':'pair','descriptor':descriptor,'compact_policy_input':'compact','original_dictionary_input':'original','original_dictionary_stage_input':'import-policy'}
 put('plan',{'producers':{'p':selected|{'binding_output':'resource-binding.json','journal_output':'resource-journal.json'}}});put('pair',{'backend':{'fixed':True},'numerical_source':{'commit':'e'*40,'files':{}}});put('compact',{'backend':'fixture','max_workflow_retained_logical_bytes':1000000,'stage_policy':POLICY});put('original',original);put('import-policy',{'max_stage_bytes':262144});put('environment',{'fake_runtime':True});put('execution_job',{'kind':'compact_resource','environment_input':'environment','payload':{'representation_jobs':{'r':selected}}})
 for i,(path,raw) in enumerate(target_files.items()):
  write(root/path,raw);inputs['tiny_'+str(i)]={'path':path,'sha256':hashlib.sha256(raw).hexdigest()}
 for i,t in enumerate(targets):inputs['target'+str(i)]={'path':t['manifest'],'sha256':t['sha256']}
 source_rows=json.loads((F/'original-import-native-refusal-candidate03-2026-10-03/source_inventory03.json').read_bytes())['source_inventory']
 from refusal_pair_identity import FORMULA_SOURCE
 source_pins={}
 for r in source_rows:
  if r['target'] in FORMULA_SOURCE:
   raw=(D.parents[3]/r['origin']).read_bytes();write(root/r['target'],raw);source_pins[r['target']]=r['sha256']
 for role,raw in blobs.items():
  write(root/('inputs/'+role+'.json'),raw);inputs[role]={'path':'inputs/'+role+'.json','sha256':hashlib.sha256(raw).hexdigest()}
 outputs=['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json'];claim={'experiment_id':name,'source':source,'registration_sha256':registration,'inputs':inputs,'experiment':{'inputs':inputs,'outputs':outputs,'source_files':source_pins|{'tradingagents/research/onchain_replication/'+n+'.py':'a'*64 for n in ('original_import_preparation','original_dictionary')}}};claim_raw=canonical(claim);write(run/'claim.json',claim_raw)
 summary={'schema_version':1,'case':variant,'identity':name,'status':'observed','boundary':{'exception':'ValueError','expected_message_fragment':cases.FRAGMENTS[variant],'observed':True}}
 rows=[{'id':'import-target-01','status':'unavailable'},{'id':'import-target-02','status':'unavailable'}]
 for output in outputs:write(run/'outputs'/output,rows if output=='cell-ledger.json' else summary)
 write(run/'failed.json',{'status':'failed','experiment_id':name,'claim_sha256':hashlib.sha256(claim_raw).hexdigest(),'reason':'RefusalObserved: registered original-import refusal observed: '+variant,'output_sha256':{n:hashlib.sha256((run/'outputs'/n).read_bytes()).hexdigest() for n in outputs}})
 journal=root/'research_artifacts/onchain_representations'/workflow/name
 if variant not in cases.NO_JOURNAL:
  owner={'experiment':name,'source_commit':source,'producer':'p','workflow_identity':workflow};write(journal/'owner.json',owner);write(journal/'start.json',{'schema_version':1,'owner':owner,'required_graphs':required,'parent':None,'workflow_identity':None})
  write(journal/'claim.json',{'owner':owner,'descriptor':descriptor,'plan_input':'plan','binding_output':'resource-binding.json','registration_sha256':registration,'pair_checkpoint_input':'pair','pair_checkpoint_policy_sha256':inputs['pair']['sha256'],'continuation_input':None,'death_input':None,'job_input':'execution_job','job_sha256':inputs['execution_job']['sha256'],'resource_only':True})
  write(journal/'failed.json',{'schema_version':1,'status':'failed','reason':{'owner-death':'registered negative owner terminal boundary','lease-terminal':'registered negative lease-terminal boundary'}.get(variant,'registered negative fixture; no retry'),'owner':owner,'workflow_identity':None,'events':[],'parent':None,'required_graphs':required})
 if variant not in cases.NO_OWNER:
  compact=journal/'compact';binding={'experiment':name,'source_commit':source,'claim_sha256':hashlib.sha256(claim_raw).hexdigest(),'registration_sha256':registration,'representation':'r','producer':'p','workflow_identity':workflow,'policy_sha256':inputs['pair']['sha256'],'journal_directory':str(journal),'numerical_source':{'commit':'e'*40,'files':{}},'job_input':'execution_job','job_sha256':inputs['execution_job']['sha256'],'resource_only':True}
  contract={'kind':'dictionary-import','required_stages':['dictionary-import']+['mcm-'+k for k in required],'current_binding':key(binding),'control_input':'original','control_sha256':inputs['original']['sha256'],'job_input':'execution_job','job_sha256':inputs['execution_job']['sha256'],'descriptor_sha256':workflow}
  current={'schema_version':1,'backend':'fixture','binding':binding,'context':{'namespace':workflow,'source_commit':'e'*40,'runtime_hash':key({'fake_runtime':True})},'policy_input':'compact','policy_sha256':inputs['compact']['sha256'],'required_stages':contract['required_stages'],'maximum_retained_logical_bytes':1000000,'original_import':contract};write(compact/'owner.json',current);ownerid=key(current)
  execution={'original_dictionary':original['dictionary_identity'],'original_matching':key(matching),'execution_matching':key({'config':matching,'backend':{'fixed':True}}),'current_binding':key(binding),'current_source':source,'runtime_hash':key({'fake_runtime':True}),'stage_contract':contract,'backend':{'fixed':True},'mcm_execution_admitted':False,'source_modules':{'tradingagents/research/onchain_replication/'+n+'.py':'a'*64 for n in ('original_import_preparation','original_dictionary')}}
  intent={'owner':ownerid,'stage':'dictionary-import','kind':'dictionary-import','binding_sha256':key(binding),'prebirth_contract':contract,'policy':{'max_stage_bytes':262144},'reserved_logical_bytes':262144,'execution':execution};write(compact/'dictionary-import/intent.json',intent)
  receipt={'schema_version':1,'kind':'dictionary-import-complete','owner':ownerid,'intent_sha256':key(intent),'execution':execution,'current_matching_pairs':0,'historical_work_recomputed':False,'numeric':numeric};write(compact/'dictionary-import/import-complete.json',receipt)
  if variant in ('wrong-count','wrong-matrix','wrong-purpose','wrong-ack'):
   stage=compact/('mcm-'+required[0]);stage.mkdir();producer=root/'research_artifacts/onchain_compact_mcm'/workflow/name/stage.name
   write(producer/'start.json',{'owner':ownerid,'graph_hash':required[0],'rows':2,'motifs':32,'cells':64});write(producer/'failed.json',{'schema_version':1,'status':'failed','owner':ownerid})
 return journal,write
