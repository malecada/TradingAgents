import ast,copy,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD='eth-paper-real-data-end-to-end-resource-20261008-21';NEW='eth-paper-real-data-end-to-end-resource-20261009-22'
def module(path):
 spec=importlib.util.spec_from_file_location('metadata_candidate',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
s=module(HERE/'successor04.py');c=s.load('controls');b=s.load('builder');h=s.load('handoff')
def budget(name):return {'schema_version':2,'kind':'real-pilot-writable-union','authority_root':'/toy','experiment':name,'roots':['/toy/research_artifacts','/toy/research_runs/'+name],'shared_files':['/toy/research_runs/.lock'],'limits':{'max_logical_bytes':10**15,'max_allocated_bytes':10**15,'max_entries':10**12,'max_depth':64,'max_scan_seconds':5}}
def inventory(name):
 alloc=c.allocation()['graph'](2,64,560,512,168*2)
 g={'rows':2,'tail_part_bytes':560,'output_part_bytes':512,'allowances':alloc['required_typed_allowances'],'count_evidence_sha256':'a'*64}
 residual={'logical_bytes':8*1024**2,'regular_files':4,'directories':2,'max_file_bytes':4*1024**2,'additional_scratch_bytes':0,'scratch_files':0,'scratch_max_file_bytes':0,'evidence_sha256':'b'*64,'bound_basis':'Synthetic declared bound, no evidence/admission claim'}
 return {'schema_version':1,'graphs':{w:copy.deepcopy(g) for w in c.WEEKS},'chunk_cells':64,'typed_control_bytes':10**9,'stage':{'max_events':2,'chunk_events':2,'max_total_checkpoints':1},'archive':{'max_stage_verifications':1,'max_writer_metadata_bytes':10**8,'max_read_metadata_bytes':10**8,'max_stage_bytes':10**9,'max_workflow_metadata_bytes':10**12},'transport':{'max_commands':1000,'max_payload_bytes':10**8,'max_diagnostic_bytes':10**12,'max_control_bytes':10**12},'residual_domains':{k:dict(residual) for k in c.REQUIRED},'filesystem':{'allocation_unit_bytes':4096,'per_regular_inode_overhead_bytes':512,'per_directory_allocated_bytes':4096,'extra_allocated_bytes':0,'extra_entries':0,'max_native_file_bytes':10**13,'evidence_sha256':'c'*64},'baseline':{'logical_bytes':0,'allocated_bytes':0,'entries':0,'evidence_sha256':'d'*64},'storage_budget':budget(name)}
class Tests(unittest.TestCase):
 def test_controls_full_toy(self):
  self.assertEqual(c.calculate(inventory(OLD)),c.calculate(inventory(OLD),experiment=OLD))
  c.calculate(inventory(NEW),experiment=NEW)
  with self.assertRaises(ValueError):c.calculate(inventory(NEW))
  for field in ('experiment','roots','shared_files'):
   v=inventory(NEW);v['storage_budget'][field]=budget(OLD)[field] if field!='shared_files' else ['/toy/wrong']
   with self.assertRaises(ValueError):c.calculate(v,experiment=NEW)
 def test_all_name_refusals_before_metadata(self):
  for func,args in [(c.calculate,({},)),(b.build,('/toy',{})),(h.prepare,('/toy',{})),(s.prepare,('/toy',{}))]:
   for name in (None,False,22,'../x',NEW+'/x',NEW+'\n',NEW.replace('-22','-022')):
    with self.subTest(func=func.__name__,name=name),self.assertRaisesRegex(ValueError,'canonical bounded'):func(*args,experiment=name)
 def test_builder_actual_storage_join(self):
  t=ast.parse((HERE/'candidate/build_inputs04.py').read_text());fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='build')
  start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='budget' for x in n.targets))
  nodes=fn.body[start:start+3] # budget, limits, exact join
  for name in (OLD,NEW):
   ns={'resource':{'storage_budget':budget(name)},'root':Path('/toy'),'experiment':name,'need':b.need}
   exec(compile(ast.Module(body=nodes,type_ignores=[]),'storage-seam','exec'),ns)
   ns['experiment']=OLD if name==NEW else NEW
   with self.assertRaises(ValueError):exec(compile(ast.Module(body=nodes,type_ignores=[]),'storage-seam','exec'),ns)
 def test_threading_and_no_numerical_import(self):
  for path,fun,calls in [(HERE/'candidate/prepare_builder04.py','prepare',['c.calculate','b.build']),(HERE/'successor04.py','prepare',['m.prepare'])]:
   fn=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==fun)
   for target in calls:
    call=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and ast.unparse(n.func)==target)
    self.assertEqual([(k.arg,ast.unparse(k.value)) for k in call.keywords],[('experiment','experiment')])
  self.assertFalse({'numpy','torch','tradingagents.research.onchain_replication'} & set(sys.modules))
 def test_literal_inverse(self):
  helper="def experiment_name(value):\n    if type(value) is not str or re.fullmatch(r'eth-paper-real-data-end-to-end-resource-[0-9]{8}-[1-9][0-9]{0,5}',value) is None:\n        raise ValueError('canonical bounded real ETH pilot experiment required')\n    return value\n\n"
  for name in ['controls02.py','build_inputs04.py','prepare_builder04.py','successor04.py']:
   original=(HERE/('baseline_'+name)).read_text();path=HERE/name if name=='successor04.py' else HERE/'candidate'/name
   text=path.read_text();self.assertEqual(text.count('import re\n'),1);text=text.replace('import re\n','',1).replace(helper,'',1)
   text=text.replace('    experiment=experiment_name(experiment)\n','',1)
   if name=='controls02.py':text=text.replace('def calculate(s,*,experiment=EXPERIMENT):','def calculate(s):',1).replace("budget['experiment']==experiment","budget['experiment']==EXPERIMENT").replace("root+'/research_runs/'+experiment","root+'/research_runs/'+EXPERIMENT")
   elif name=='build_inputs04.py':text=text.replace(f'def build(root,spec,*,experiment={OLD!r}):','def build(root,spec):',1).replace("budget=resource['storage_budget'];limits=budget['limits']", "budget=resource['storage_budget'];limits=budget['limits'];experiment="+repr(OLD),1)
   else:
    text=text.replace(f'def prepare(root,draft,*,experiment={OLD!r}):','def prepare(root,draft):',1).replace('c.calculate(inventory,experiment=experiment)','c.calculate(inventory)').replace('b.build(root,spec,experiment=experiment)','b.build(root,spec)').replace('m.prepare(root,draft,experiment=experiment)','m.prepare(root,draft)')
    if name=='prepare_builder04.py':
     start=text.index('PINS=');end=text.index('\n\ndef need',start);a=original.index('PINS=');z=original.index('\n\ndef need',a);text=text[:start]+original[a:z]+text[end:]
   self.assertEqual(text,original,name)
if __name__=='__main__':unittest.main(verbosity=2)
