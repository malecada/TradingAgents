"""Stdlib source/assembly tests. Synthetic metadata is never public authority."""
import ast,copy,hashlib,importlib.util,json,tempfile,unittest,sys
from pathlib import Path
P=Path(__file__).parent
spec=importlib.util.spec_from_file_location('generator02',P/'generate02.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def fixture():
 material={'inputs':{n:{'path':'raw/'+n+'.json','sha256':g.digest(n.encode()),'dataset':'synthetic-cold'} for n in g.MATERIAL_INPUTS}}
 env={'path':'environment.json','sha256':g.digest(b'env'),'dataset':'synthetic-cold'}
 family={'mechanism_id':g.FAMILY,'attempt_budget':2,'prior_attempts':0,'history_reference':'history.md'}
 first={'family':g.FAMILY,'parent':None,'question':'materialize','stage':'development','reuse':'exploratory','runtime_hashes':{'admission.py':g.digest(b'body')},'source_files':{str(i):g.digest(str(i).encode()) for i in range(195)},'inputs':{'environment':env},'charter':{'path':'charterA','sha256':g.digest(b'charter')},'cells':[g.CELL['materialize']],'outputs':['proof-materialize.json'],'windows':[{'dataset':'synthetic-cold','start':'2023-12-04T00:00:00Z','end':'2024-05-13T00:00:00Z','availability':'existing'}]}
 original={'schema_version':1,'program_id':g.PROGRAM,'families':{g.FAMILY:family},'datasets':{'synthetic-cold':{'identity':'s','history_reference':'history.md','exposures':[]}},'experiments':{g.IDS['materialize']:first}}
 release={'source':'1234567890'*4,'registration':{'path':'oldreg.json','sha256':g.digest(b'oldreg'),'bytes':20,'kind':'document'},'root':'/qualified-fixture','sources':{'path':'sources.json'},'runtime':{'path':'runtime.json'},'native_environment':{'path':'env.json'},'cpus':[0,1]}
 return {'context':{'release':release},'registration':original,'material':material},dict(registration='new/reg.json',charter='new/charter.md',evolution='new/evolution.json',phase_contract='new/contract.json')
class Tests(unittest.TestCase):
 def test_actual_pure_assembly_full44_and_noncyclic_evolution(self):
  retained,paths=fixture();before=copy.deepcopy(retained);out=g.compare_documents(retained,paths,{'path':'accepted'},{'path':'wait'},(P/'CHARTER_COMPARE02.md').read_bytes())
  self.assertEqual(retained,before);reg=out['registration'];self.assertEqual(reg['experiments'][g.IDS['materialize']],retained['registration']['experiments'][g.IDS['materialize']]);self.assertEqual(len(out['experiment']['inputs']),44)
  evo=json.loads(out['files'][paths['evolution']]);self.assertEqual(len(evo['additions']),3);self.assertNotIn(paths['evolution'],[x['path'] for x in evo['additions']]);self.assertNotIn('source',evo);self.assertIsNone(out['gate_template']['source']);self.assertFalse(out['gate_template']['execution_authorized'])
  for row in evo['additions']:self.assertEqual(g.digest(out['files'][row['path']]),row['sha256'])
  self.assertEqual(out['gate_template']['prior_materialization']['evolution']['sha256'],g.digest(out['files'][paths['evolution']]))
 def test_partial_wrongname_and_prior_history_refuse(self):
  for case in ('missing','same_count_wrong_name','prior','budget','charter','overlap'):
   r,p=fixture();charter=(P/'CHARTER_COMPARE02.md').read_bytes()
   if case=='missing':r['material']['inputs'].pop('graph-00')
   if case=='same_count_wrong_name':r['material']['inputs']['wrong']=r['material']['inputs'].pop('graph-00')
   if case=='prior':r['registration']['families'][g.FAMILY]['prior_attempts']=True
   if case=='budget':r['registration']['families'][g.FAMILY]['attempt_budget']=3
   if case=='charter':charter+=b'changed'
   if case=='overlap':p['charter']=p['registration']
   with self.subTest(case=case),self.assertRaises(ValueError):g.compare_documents(r,p,{}, {},charter)
 def test_public_missing_fake_summary_refuses_before_write(self):
  for r in ({},{'schema_version':1,'phase':'compare','accepted':True},{'schema_version':1,'phase':'materialize'}):
   with self.assertRaises(ValueError):g.prepare_compare(Path('/nonexistent'),r)
 def test_actual_public_order_and_source_pins(self):
  t=ast.parse((P/'generate02.py').read_text());fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_compare');text=ast.unparse(fn)
  self.assertLess(text.index('release.authenticated_materialization'),text.index('compare_documents('));self.assertIn('release._registration_evolution',text);self.assertIn("original['source'] == request['source']",text)
  self.assertEqual(g.PINNED_INVENTORY,'8576e2baba60576818ee4def16fcfad32cc69bd197c4ff1b727808d9695786d2');self.assertEqual(g.RELEASE_SHA,'53c2294b7b38f340e9160e4484a6b7506942ce36e2dff12694a47f9b72206812')
 def test_actual_fatal_writer_preserved_and_fd_closed_once(self):
  original={n:getattr(g.os,n) for n in ('open','write','fsync','close')};calls=[];fatal=MemoryError('first')
  g.os.open=lambda *a,**k:9
  def fail(*a):raise fatal
  g.os.write=fail
  def close(fd):calls.append(fd);raise OSError('uncertain close')
  g.os.close=close
  try:
   with self.assertRaises(MemoryError) as caught:g.write_exclusive(Path('/unused'),b'x')
   self.assertIs(caught.exception,fatal);self.assertEqual(calls,[9])
  finally:
   for n,v in original.items():setattr(g.os,n,v)
 def test_real_tiny_exclusive_draft_and_refusal(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'draft.json';g.write_exclusive(p,b'{}\n');self.assertEqual(p.read_bytes(),b'{}\n')
   with self.assertRaises(FileExistsError):g.write_exclusive(p,b'changed')
   with self.assertRaises(ValueError):g.new_path(Path(d),'draft.json')
 def test_no_numerical_imports(self):self.assertFalse(any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
