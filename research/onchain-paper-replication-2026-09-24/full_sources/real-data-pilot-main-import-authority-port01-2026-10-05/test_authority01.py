"""Offline source and metadata algorithms only: no Run/Binding/Owner or arrays."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,sys,types,unittest,uuid
from tempfile import TemporaryDirectory
D=Path(__file__).resolve().parent;M=D.parents[3];P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P
SHA=lambda b:hashlib.sha256(b).hexdigest()
def extract(path,names,env):
 tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
 return env

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

# Isolated package: only actual stdlib bodies plus extracted pure I/O routines.
pkg=types.ModuleType('authority_offline');pkg.__path__=[str(T)];sys.modules[pkg.__name__]=pkg
owned=load('authority_offline.owned_io',T/'owned_io.py')
original=load('authority_offline.original_dictionary',T/'original_dictionary.py')
io=types.ModuleType('authority_offline.score_batches');sys.modules[io.__name__]=io
for n in ('CleanupFailure','_fatal','_flatten','_cleanup','_close_after_failure','_release','_closing','_opened','_read_path'):setattr(io,n,getattr(owned,n))
import stat,re
io.__dict__.update(os=os,stat=stat,re=re,Path=Path,hashlib=hashlib,json=json)
extract(T/'score_batches.py',['_require','_hash','_json','_signature','_write','_read'],io.__dict__)
metadata=load('authority_offline.import_metadata',T/'import_metadata.py')
prov=load('authority_offline.provenance',M/P/'provenance.py')
life={'Path':Path,'os':os,'json':json,'uuid':uuid,'current_metadata_scope':lambda:None}
extract(M/'tradingagents/research/lifecycle.py',['_encode','_fsync_dir','_immutable'],life)

def journal(path):
 env={'__name__':'journal_metadata_algorithm','Path':Path,'json':json,'checked_io':metadata,'_RESOURCE_METADATA':object(),**{n:getattr(prov,n) for n in ['file_hash','durable_mkdir','sync_directory','canonical_bytes','require_hash','utc']},'_immutable':life['_immutable']}
 extract(path,['required_set','FeatureJournal'],env);return env

def symbols(path):
 tree=ast.parse(path.read_text());out=set()
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef)):out.add(n.name)
  elif isinstance(n,(ast.Import,ast.ImportFrom)):
   out.update(a.asname or a.name.split('.')[0] for a in n.names)
  elif isinstance(n,(ast.Assign,ast.AnnAssign)):
   for t in (n.targets if isinstance(n,ast.Assign) else [n.target]):out.update(v.id for v in ast.walk(t) if isinstance(v,ast.Name))
 return out

class Checks(unittest.TestCase):
 def test_01_exact_inverse_and_protected_main(self):
  d=json.loads((D/'SOURCE_DELTA01.json').read_text())
  for row in d['changed']:
   p=Path(row['path']);raw=(D/'candidate'/p).read_bytes();self.assertEqual(SHA(raw),row['cap_sha256']);lines=raw.decode().splitlines(True)
   for e in reversed(row['edits']):self.assertEqual(lines[e['new_start']:e['new_end']],e['new']);lines[e['new_start']:e['new_end']]=e['old']
   self.assertEqual(''.join(lines).encode(),(D/'baseline'/p.name).read_bytes())
   self.assertEqual(SHA((M/p).read_bytes()),row['baseline_sha256'])
  for row in d['reused']:self.assertEqual(SHA((D/'candidate'/row['path']).read_bytes()),row['sha256'])
  for p,h in d['main_unchanged_package'].items():self.assertEqual(SHA((M/p).read_bytes()),h)
 def test_02_candidate_syntax_and_direct_relative_symbols(self):
  files={p.stem:p for p in (M/P).glob('*.py')};files.update({p.stem:p for p in T.glob('*.py')})
  for path in T.glob('*.py'):
   tree=ast.parse(path.read_text());compile(tree,str(path),'exec')
   for n in ast.walk(tree):
    if isinstance(n,ast.ImportFrom) and n.level==1:
     if n.module is None:
      for a in n.names:self.assertIn(a.name,files,(path.name,a.name))
     elif '.' not in n.module and n.module in files:
      exposed=symbols(files[n.module])
      for a in n.names:self.assertIn(a.name,exposed,(path.name,n.module,a.name))
 def test_03_coupled_interfaces_and_original_guards(self):
  tree=ast.parse((T/'matching_owner.py').read_text());bind=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bind')
  self.assertTrue({'job_input','_resource'}<=set(a.arg for a in bind.args.kwonlyargs))
  before=(D/'baseline/matching_owner.py').read_text();after=(T/'matching_owner.py').read_text()
  for name in ['_source','_anchor_read','_anchor_blobs','_guard','open_first','open_successor']:
   pick=lambda s:ast.dump(next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
   self.assertEqual(pick(before),pick(after),name)
  for filename,cls,method,key in [('compact_owner.py','Owner','__init__','imported'),('mcm_score_stream.py','MCMScoreStream','__init__','_imported')]:
   c=next(n for n in ast.parse((T/filename).read_text()).body if isinstance(n,ast.ClassDef) and n.name==cls)
   f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==method)
   self.assertIn(key,{a.arg for a in f.args.kwonlyargs})
  self.assertIn('produce_imported',symbols(T/'compact_mcm.py'));self.assertIn('completed_evidence',symbols(T/'mcm_score_stream.py'))
  self.assertIn("record.get('job_input','execution_job')",(T/'compact_mcm_publication.py').read_text())
  # ResearchRun type check is the first effectful statement; no duck authority.
  self.assertIn('isinstance(run, ResearchRun)',ast.unparse(bind.body[0]))
  # Main payload/population/model/financial/graph interfaces are inherited, not replaced.
  for n in ['job_payload','run','population_assembly','model_registry','compact_native_features','compact_native_producer','graph_production','graph_store']:
   self.assertFalse((T/(n+'.py')).exists())
 def test_04_real_metadata_exclusive_and_hardlink_refusal(self):
  with TemporaryDirectory(dir=D) as tmp:
   root=Path(tmp);raw=b'{"synthetic_metadata":true}'
   self.assertEqual(metadata.write(root,'test.json',raw),SHA(raw));self.assertEqual(metadata.read(root,'test.json'),raw)
   with self.assertRaises(FileExistsError):metadata.write(root,'test.json',b'changed')
   os.link(root/'test.json',root/'alias')
   with self.assertRaises(ValueError):metadata.read(root,'test.json')
   self.assertEqual((root/'test.json').read_bytes(),raw)
 def test_05_selected_journal_algorithms_and_unknown_role(self):
  e=journal(T/'feature_journal.py');J=e['FeatureJournal'];h='a'*64
  with TemporaryDirectory(dir=D) as tmp:
   root=Path(tmp);owner={'experiment':'synthetic-metadata-only','source_commit':'b'*40,'producer':'synthetic','workflow_identity':h}
   with self.assertRaises(ValueError):J(root/'bad',owner,required_graphs=[h],_metadata_role=object())
   self.assertFalse((root/'bad').exists())
   j=J(root/'journal',owner,required_graphs=[h],_metadata_role=e['_RESOURCE_METADATA'])
   j._resource_check()
   with self.assertRaises(AttributeError):j.directory=root/'elsewhere'
   with self.assertRaises(ValueError):j('mcm_progress',{},None)
   with self.assertRaises(ValueError):j.seal('complete')
   j.seal('failed',reason='synthetic metadata check');self.assertTrue(j.sealed)
   self.assertTrue((root/'journal/failed.json').exists());self.assertFalse((root/'journal/complete.json').exists())
 def test_06_legacy_journal_metadata_identical(self):
  old=journal(D/'baseline/feature_journal.py');new=journal(T/'feature_journal.py');h='a'*64
  with TemporaryDirectory(dir=D) as tmp:
   root=Path(tmp);owner={'synthetic':'legacy'}
   for name,e in [('old',old),('new',new)]:e['FeatureJournal'](root/name,owner,required_graphs=[h]).seal('failed',reason='same')
   for name in ['owner.json','start.json','failed.json']:self.assertEqual((root/'old'/name).read_bytes(),(root/'new'/name).read_bytes())
 def test_07_exact_stage_population_and_no_new_dictionary(self):
  e={};extract(T/'original_import_preparation.py',['require','required_stages'],e)
  h=[f'{i:064x}' for i in range(7)];d={'dictionary_origin':'imported-original-v1','required_graphs':h}
  self.assertEqual(e['required_stages'](d),('dictionary-import',)+tuple('mcm-'+x for x in h))
  for bad in [h+h[:1],h[::-1],[],['x'*64]]:
   with self.assertRaises(ValueError):e['required_stages'](dict(d,required_graphs=bad))
  self.assertNotIn('dictionary',e['required_stages'](d))
 def test_08_cleanup_preserves_fatal_and_attempts_each_close(self):
  seen=[];primary=MemoryError('synthetic')
  def fail():seen.append(1);raise OSError('synthetic close')
  with self.assertRaises(MemoryError) as caught:
   try:raise primary
   finally:owned._cleanup((fail,lambda:seen.append(2)))
  self.assertIs(caught.exception,primary);self.assertEqual(seen,[1,2])
 def test_09_no_numerical_imports(self):
  self.assertFalse({'numpy','torch','scipy','networkx'}&set(sys.modules))

if __name__=='__main__':unittest.main(verbosity=2)
