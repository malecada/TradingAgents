"""Finite source-only metadata. Synthetic references are never approval/claims."""
import ast,copy,hashlib,json,pathlib,runpy,sys,unittest
P=pathlib.Path(__file__).parent
G=runpy.run_path(str(P/('generate_inputs01.py.baseline04.txt' if '--baseline' in sys.argv else 'generate_inputs01.py')));sys.argv=[a for a in sys.argv if a!='--baseline']
def role(path,doc):
 b=doc.encode() if isinstance(doc,str) else G['canonical'](doc)
 return {'reference':{'path':path,'sha256':G['sha'](b),'bytes':len(b)},'document':doc}
def fixture():
 files={**{'tradingagents/synthetic_%03d.py'%i:'a'*64 for i in range(148)},**{'synthetic_helpers/%03d.txt'%i:'b'*64 for i in range(51)}}
 source={'source_count':199,'package_count':148,'source_files':dict(sorted(files.items())),'package_files':{k:v for k,v in files.items() if k.startswith('tradingagents/')},'execution_admitted':False,'source':'1'*40,'anchor':'2'*40,'root':'/synthetic-only'}
 case={'schema_version':1,'kind':'root-selected-imported-held-resource-v1','program_id':'synthetic-program','experiment_id':'future-held-fixture','job_input':'job','plan_input':'plan','representation':'rep','producer':'prod','held_policy_input':'held','readback_outputs':{},'additional_inputs':{}}
 family={'mechanism_id':'synthetic-only','attempt_budget':2,'prior_attempts':0,'history_reference':'synthetic'}
 allocation=role('metadata/allocation.json',{'scope':'synthetic-reference-only'})
 extension=role('metadata/extension.json',{'schema_version':1,'program_id':case['program_id'],'base_family':family,'cumulative_ceiling':6,'consumed_before':4,'initial_experiment':case['experiment_id'],'allocation':{k:allocation['reference'][k] for k in ('path','sha256')},'claims':[],'reason':'synthetic metadata, deliberately no genuine history'})
 review=role('metadata/review.json',{'schema_version':1,'decision':'accepted','extension_sha256':extension['reference']['sha256'],'reviewer':'synthetic-test-only','scope':'not a genuine independent approval'})
 charter=role('metadata/charter.md','Synthetic test charter; not research authority.')
 refs={'budget_allocation':allocation['reference'],'budget_extension':extension['reference'],'budget_review':review['reference'],'charter':charter['reference']}
 declaration={'schema_version':1,'kind':'held-auxiliary-source-metadata-v1','program_id':case['program_id'],'experiment_id':case['experiment_id'],'implementation_source_count':199,'package_count':148,'implementation_map_sha256':G['sha'](G['canonical'](source['source_files'])),'entry_count':4,'entries':[{'role':n,'reference':refs[n]} for n in sorted(refs)]}
 auxiliary=role('metadata/auxiliary.json',declaration)
 src={**source['source_files'],**{r['path']:r['sha256'] for r in [*refs.values(),auxiliary['reference']]}}
 exp={'family':'test','stage':'development','selection':None,'source_files':dict(sorted(src.items())),'outputs':['summary.json'],'charter':{k:charter['reference'][k] for k in ('path','sha256')},'cumulative_budget_extension':{'extension':{k:extension['reference'][k] for k in ('path','sha256')},'review':{k:review['reference'][k] for k in ('path','sha256')}}}
 roles={'case_contract':role('metadata/case.json',case),'budget_allocation':allocation,'budget_extension':extension,'budget_review':review,'charter':charter,'auxiliary_sources':auxiliary,'registration':role('metadata/registration.json',{'program_id':case['program_id'],'families':{'test':family},'experiments':{case['experiment_id']:exp}})}
 return source,roles
class Tests(unittest.TestCase):
 def test_explicit_199_plus_five_auxiliary_pins(self):
  s,r=fixture();out=G['held_input_plan'](r,s);self.assertEqual(out['source_count'],199);self.assertEqual(out['package_count'],148);self.assertEqual(out['auxiliary_metadata']['auxiliary_count'],5);self.assertEqual(out['auxiliary_metadata']['admission_source_count'],204);self.assertFalse(out['execution_admitted'])
 def test_null_template_no_authority(self):
  s,r=fixture();out=G['held_input_plan']({},s);self.assertIsNone(out['auxiliary_metadata']);self.assertIn('budget_allocation',out['remaining_roles']);self.assertIn('auxiliary_sources',out['remaining_roles'])
 def test_legacy_array_entry_and_unknown_count_remain_refused(self):
  with self.assertRaises(ValueError):G['generate_held_arrays']()
  s,r=fixture();s['source_count']=204
  with self.assertRaises(ValueError):G['held_input_plan']({},s)
  s,r=fixture();s['source_files']['extra.py']='a'*64
  with self.assertRaises(ValueError):G['held_input_plan']({},s)
  s,r=fixture();r['unexpected_auxiliary_flag']=None
  with self.assertRaises(ValueError):G['held_input_plan'](r,s)
 def test_missing_extra_hash_and_count(self):
  for change in ('missing','extra','hash','count','collision','outside','unbound','registration-cycle','declaration-count','declaration-order','family','charter'):
   s,r=fixture();exp=r['registration']['document']['experiments']['future-held-fixture'];decl=r['auxiliary_sources']['document']
   if change=='missing':r['budget_allocation']=None
   if change=='extra':exp['source_files']['metadata/extra.json']='f'*64
   if change=='hash':exp['source_files']['metadata/review.json']='f'*64
   if change=='count':s['source_files'].pop(next(iter(s['source_files'])))
   if change=='collision':r['charter']['reference']['path']=next(iter(s['source_files']))
   if change=='outside':decl['entries'][0]['reference']['path']='../escape.json'
   if change=='unbound':exp['cumulative_budget_extension']['extension']['sha256']='e'*64
   if change=='registration-cycle':r['auxiliary_sources']['reference']['path']=r['registration']['reference']['path']
   if change=='declaration-count':decl['entry_count']=True
   if change=='declaration-order':decl['entries'].reverse()
   if change=='family':r['budget_extension']['document']['base_family']={}
   if change=='charter':exp['charter']['path']='metadata/other.md'
   with self.subTest(change=change),self.assertRaises(ValueError):G['held_input_plan'](r,s)
if __name__=='__main__':unittest.main(verbosity=2)
