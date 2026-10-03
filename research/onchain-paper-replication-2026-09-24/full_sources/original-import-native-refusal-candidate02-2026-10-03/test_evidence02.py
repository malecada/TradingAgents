"""Parser tests on explicitly fake JSON/files only, not Owner construction."""
import hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent
sys.path.insert(0,str(F/'original-import-fixture-native-preparation03-2026-10-03'))
sys.path.insert(0,str(D))
import refusal_cases as cases
from refusal_evidence import canonical,key
S=Path(os.environ.get('REFUSAL_SOURCE_DIR',D));spec=importlib.util.spec_from_file_location('selected_caller',S/'refusal_caller.py');caller=importlib.util.module_from_spec(spec);spec.loader.exec_module(caller)
def fixture(root,variant):
 name=cases.identity(variant);run=root/'research_runs'/name;source='a'*40;registration='b'*64;inputs={}
 def write(path,value):
  path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value if isinstance(value,bytes) else canonical(value));return path
 def put(name,value):
  path='inputs/'+name+'.json';raw=canonical(value);write(root/path,raw);inputs[name]={'path':path,'sha256':hashlib.sha256(raw).hexdigest()}
 required=['c'*64,'d'*64];descriptor={'required_graphs':required,'configs':{'matching':{'fixed':True}},'resource_fixture':{'case':'refusal-'+variant}};workflow=key(descriptor)
 selected={'plan_input':'plan','producer':'p','pair_checkpoint_input':'pair','descriptor':descriptor,'compact_policy_input':'compact','original_dictionary_input':'original','original_dictionary_stage_input':'import-policy'}
 put('plan',{'producers':{'p':selected|{'binding_output':'resource-binding.json','journal_output':'resource-journal.json'}}});put('pair',{'backend':{'fixed':True},'numerical_source':{'commit':'e'*40,'files':{}}});put('compact',{'backend':'fixture','max_workflow_retained_logical_bytes':1000000});put('original',{'dictionary_identity':'f'*64});put('import-policy',{'max_stage_bytes':262144});put('environment',{'fake_runtime':True});put('execution_job',{'kind':'compact_resource','environment_input':'environment','payload':{'representation_jobs':{'r':selected}}})
 outputs=['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json'];claim={'experiment_id':name,'source':source,'registration_sha256':registration,'inputs':inputs,'experiment':{'inputs':inputs,'outputs':outputs}};claim_raw=canonical(claim);write(run/'claim.json',claim_raw)
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
  execution={'original_dictionary':'f'*64,'original_matching':key({'fixed':True}),'execution_matching':key({'config':{'fixed':True},'backend':{'fixed':True}}),'current_binding':key(binding),'current_source':source,'runtime_hash':key({'fake_runtime':True}),'stage_contract':contract,'backend':{'fixed':True}}
  intent={'owner':ownerid,'stage':'dictionary-import','kind':'dictionary-import','binding_sha256':key(binding),'prebirth_contract':contract,'policy':{'max_stage_bytes':262144},'reserved_logical_bytes':262144,'execution':execution};write(compact/'dictionary-import/intent.json',intent)
  receipt={'schema_version':1,'kind':'dictionary-import-complete','owner':ownerid,'intent_sha256':key(intent),'execution':execution,'current_matching_pairs':0,'historical_work_recomputed':False,'numeric':{'original_dictionary':'f'*64,'original_matching':key({'fixed':True}),'ordered_motifs':['0'*64]*32,'representative_sample_indices':list(range(32)),'owner_stage_completed':False,'mcm_execution_admitted':False}};write(compact/'dictionary-import/import-complete.json',receipt)
  if variant in ('wrong-count','wrong-matrix','wrong-purpose','wrong-ack'):
   stage=compact/('mcm-'+required[0]);stage.mkdir();producer=root/'research_artifacts/onchain_compact_mcm'/workflow/name/stage.name
   write(producer/'start.json',{'owner':ownerid,'graph_hash':required[0],'rows':2,'motifs':32,'cells':64});write(producer/'failed.json',{'schema_version':1,'status':'failed','owner':ownerid})
 return journal,write
class Evidence(unittest.TestCase):
 def test_qualified_valid_zero_journal_journal_only_owner_and_failed_producer(self):
  for variant in ('policy-bool','job-input','lease-terminal','wrong-count'):
   with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);fixture(root,variant);record=caller.terminal(root=root,variant=variant)
    self.assertEqual(record['evidence']['journal_count'],int(variant not in cases.NO_JOURNAL));self.assertEqual(record['evidence']['owner_count'],int(variant not in cases.NO_OWNER))
 def test_missing_or_wrong_original_journal_and_owner_refuse(self):
  for change in ('missing-terminal','wrong-owner','wrong-compact','extra-journal','owner-complete','import-receipt'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);journal,write=fixture(root,'lease-terminal')
    if change=='missing-terminal':(journal/'failed.json').unlink()
    elif change=='wrong-owner':write(journal/'owner.json',{'fake':True})
    elif change=='wrong-compact':write(journal/'compact/owner.json',{'fake':True})
    elif change=='extra-journal':(root/'research_artifacts/onchain_representations'/('1'*64)/journal.name).mkdir(parents=True)
    elif change=='owner-complete':write(journal/'compact/complete.json',{})
    else:write(journal/'compact/dictionary-import/import-complete.json',{})
    with self.assertRaises((ValueError,KeyError,FileNotFoundError)):caller.terminal(root=root,variant='lease-terminal')
 def test_unexpected_actual_producer_complete_name_refuses(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);journal,write=fixture(root,'wrong-count');producer=next((root/'research_artifacts/onchain_compact_mcm').glob('*/*/*'));write(producer/'complete.json',{'unexpected':True})
   with self.assertRaises(ValueError):caller.terminal(root=root,variant='wrong-count')
if __name__=='__main__':unittest.main()
