exec(compile((__import__('pathlib').Path(__file__).parent/'check04.py').read_text(),'check04.py','exec'))
FINAL=F/'real-data-pilot-final20-2026-10-08'
draft=json.loads(pin(FINAL/'INPUT_DRAFT02.json'));result=json.loads(pin(FINAL/'PREPARATION_RESULT05.json'));pin(FINAL/'PREPARATION04.stderr');pin(FINAL/'ACTUAL_STORAGE_REFUSAL01.json')
class Captured(Exception):pass
capture={};real_load=new.load
def capture_load(name):
 m=real_load(name)
 if name=='controls':
  def take(s):capture['input']=copy.deepcopy(s);raise Captured()
  m.calculate=take
 return m
new.load=capture_load
try:new.prepare(R,draft)
except Captured:pass
finally:new.load=real_load
s=capture['input'];controls4=new.load('controls');controls3=old.load('controls')
actual=controls4.calculate(s)
check('actual_diagnostic_inventory_matches_root',actual==result['inventory'])
check('all_seven_graphs_preserved',len(actual['by_week'])==7)
check('one_matrix_reserved',actual['categories']['retained_original_matrices']['regular_files']==1)
check('caps_unchanged',actual['storage_budget_unchanged']==s['storage_budget'] and actual['transport_caps_unchanged']==s['transport'] and actual['filesystem_assumption']==s['filesystem'])
# Synthetic control-path equivalence only: same supplied one-stage declarations,
# diagnostic selector removed. This does not represent full-run admission.
synthetic=copy.deepcopy(s);synthetic.pop('diagnostic')
check('actual_controls_default_output_equal_on_identical_metadata',controls4.calculate(synthetic)==controls3.calculate(synthetic))
full=copy.deepcopy(synthetic);full['residual_domains']=r4.resolve(stage,**(kwargs|{'runtime_reservation':draft['protocol']['runtime_reservation'],'lifecycle_reservation':draft['protocol'].get('lifecycle_reservation')}))['residual_domains']
errors=[]
for module in (controls3,controls4):
 try:module.calculate(full)
 except ValueError as e:errors.append(str(e))
 else:raise AssertionError('full unexpectedly fits')
check('full_original_capacity_refusal_preserved',errors==['aggregate writable scope underfunded: logical_bytes']*2)
# Compare category bodies excluding the two explicitly changed domains.
for k,v in controls4.calculate(synthetic)['categories'].items():
 if k!='retained_original_matrices':check('category_unchanged_'+k,v==actual['categories'][k])
check('native_1GiB_preserved',s['filesystem']['max_native_file_bytes']==1073741824)
check('limits_preserved',s['storage_budget']['limits']['max_logical_bytes']==16*1024**3 and s['storage_budget']['limits']['max_allocated_bytes']==20*1024**3)
(H/'INTEGRATION04.json').write_text(json.dumps({'status':'NARROW_DIAGNOSTIC_METADATA_ACCEPTED_NOT_ENTRY','checks':checks,'source_sha256':hashes,'full_refusals':errors,'actual_diagnostic_totals':actual['total_with_declared_baseline'],'qualification':'Explicit separately registered diagnostic reservation only; full seven-stage capacity remains refused. Synthetic default control equality is not full capacity admission.'},indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks)}))
