"""Tiny files / synthetic metadata only; no genuine ResearchRun or Owner fabricated."""
import ast,hashlib,json,os,pathlib,shutil,tempfile,time,types,unittest
from unittest.mock import patch
import archive01 as a
import collector01 as c
import closed_comparison01 as cc
P=pathlib.Path(__file__).parent
class Tests(unittest.TestCase):
 def test_copy_fatal_close_once(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/'a';src.write_bytes(b'abc');row=a.census(root,65536,time.monotonic()+10)[0];first=MemoryError('first');closed=[];realclose=os.close
   def close(fd):
    closed.append(fd);realclose(fd);raise OSError('later')
   with patch.object(a.os,'read',side_effect=first),patch.object(a.os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as got:a.copy_file(src,root/'out',row,time.monotonic()+10)
   self.assertIs(got.exception,first);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_member_replaced_same_bytes_refused(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/'a';src.write_bytes(b'abc');row=a.census(root,65536,time.monotonic()+10)[0];tmp=root/'b';tmp.write_bytes(b'abc');tmp.replace(src)
   with self.assertRaises(ValueError):a.copy_file(src,root/'out',row,time.monotonic()+10)
 def test_empty_directory_allocations_count(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'x').mkdir()
   with self.assertRaises(ValueError):a.census(root,1,time.monotonic()+10)
 def test_missing_terminal_is_not_complete(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);v=c.observed_phase(root,'compare',None);self.assertEqual(v['original_lifecycle_observation'],'not_observed');self.assertIsNone(v['registered_outputs']);self.assertFalse(v['numerical_results_synthesized'])
   dest=root/'research_runs'/c.IDS['compare'];dest.mkdir(parents=True);(dest/'claim.json').write_text('{}');v=c.observed_phase(root,'compare',None);self.assertEqual(v['original_lifecycle_observation'],'claimed_partial_no_terminal')
   (dest/'complete.json').write_text('{}');(dest/'failed.json').write_text('{}');v=c.observed_phase(root,'compare',None);self.assertEqual(v['original_lifecycle_observation'],'conflicting_original_terminals')
 def test_missing_registered_outputs_retained(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'r.json').write_text(json.dumps({'experiments':{c.IDS['compare']:{'outputs':c.OUTPUTS['compare']}}}));v=c.observed_phase(root,'compare',{'registration':{'path':'r.json'}});self.assertEqual(v['absent_registered_outputs'],sorted(c.OUTPUTS['compare']));self.assertIsNone(v['present_output_names'])
 def test_closed_adapter_refuses_false_prior_before_any_context(self):
  fake=types.SimpleNamespace(require=a.require,deref=lambda root,ref:{'status':'failed'},metadata=None,ref=None,module=None,authenticate=None,closure=None,IDENTITIES=c.IDS,OUTER='proof_outer/',MAX=a.MAX,GIB=a.GIB)
  identity=c.IDS['compare'];refs=[{'path':'proof_outer/'+identity+'/accepted.json'},{'path':'proof_supervise/'+identity+'/exit.json'}]
  with self.assertRaises(ValueError):cc.authenticate_closed_comparison(pathlib.Path('/not-read'),{},*refs,fake)
 def test_closed_adapter_missing_prior_refuses(self):
  fake=types.SimpleNamespace(require=a.require,deref=lambda *_:(_ for _ in ()).throw(FileNotFoundError()),metadata=None,ref=None,module=None,authenticate=None,closure=None,IDENTITIES=c.IDS,OUTER='proof_outer/',MAX=a.MAX,GIB=a.GIB)
  identity=c.IDS['compare']
  with self.assertRaises(FileNotFoundError):cc.authenticate_closed_comparison(pathlib.Path('/not-read'),{}, {'path':'proof_outer/'+identity+'/accepted.json'},{'path':'proof_supervise/'+identity+'/exit.json'},fake)
 def test_external_refs_recursively_retained_and_rechecked(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);b=root/'b';b.write_bytes(b'actual opaque raw');rb={'path':str(b),'sha256':c.digest(b.read_bytes())};x=root/'a';x.write_text(json.dumps({'original':rb}));ra={'path':str(x),'sha256':c.digest(x.read_bytes())};rows=c.capture_external({'ref':ra},root/'retained');self.assertEqual(len(rows),2);self.assertEqual((root/'retained'/rows[1]['retained']).read_bytes(),b.read_bytes())
   b.write_bytes(b'changed')
   with self.assertRaises(ValueError):c.capture_external({'ref':ra},root/'refused')
 def test_recovery_metadata_extras_and_failure_revoke(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);original=root/'original';original.mkdir();data=original/'data';data.mkdir();src=root/'source';src.mkdir();(src/'binary').write_bytes(bytes(range(256)));rows=a.snapshot(src,data/'capsule',limit=65536);members=original/'members';members.mkdir();refs=a.pages(members/'capsule',rows);report={'byte_retention_status':'complete-original-byte-copy','member_pages':{'capsule':refs},'tree_root_modes':{'capsule':(data/'capsule').stat().st_mode&0o777},'outcomes':{'materialize':{'strict_scientific_disposition':'FAILED_OR_UNVERIFIED'}}};a.write(original,'collection.json',report);sha=c.digest((original/'collection.json').read_bytes());recovered=root/'recovered';shutil.copytree(original,recovered)
   got=c.verify_recovery(original,recovered,sha);self.assertEqual(got['scientific_dispositions']['materialize'],'FAILED_OR_UNVERIFIED')
   (recovered/'extra').write_bytes(b'x')
   with self.assertRaises(ValueError):c.verify_recovery(original,recovered,sha)
   (recovered/'extra').unlink();(original/'collection-failed.json').write_bytes(b'{}');shutil.copyfile(original/'collection-failed.json',recovered/'collection-failed.json')
   with self.assertRaises(ValueError):c.verify_recovery(original,recovered,sha)
 def test_source_refusal_still_retains_bytes_without_positive_authority(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/'source';src.mkdir();(src/'raw').write_bytes(b'failed original bytes')
   q={'root':str(src),'destination':str(root/'saved'),'source':'unverified','wrappers':dict.fromkeys(c.IDS),'wrapper_waits':dict.fromkeys(c.IDS)}
   result=c.retain_unverified(q,ValueError('source refused'));self.assertEqual((root/'saved/data/capsule/raw').read_bytes(),b'failed original bytes');self.assertEqual(result['source_authentication'],'refused');self.assertTrue(all(v['strict_scientific_disposition']=='FAILED_OR_UNVERIFIED' for v in result['outcomes'].values()))
 def test_empty_born_namespace_is_partial_not_unattempted(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'research_runs'/c.IDS['compare']).mkdir(parents=True)
   self.assertEqual(c.observed_phase(root,'compare',None)['original_lifecycle_observation'],'unclaimed_partial')
 def test_root_parent_failure_revokes_wrapper_success(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);wrapper=root/'wrapper';wrapper.mkdir();parent=root/'parent';parent.mkdir();source=root/'parent.py';source.write_text('# source-only fixture')
   pid=2147483640;identity=c.IDS['materialize'];wait={'schema_version':1,'identity':identity,'source':'a'*40,'wrapper_pid':pid,'wrapper_exit_code':0,'command':[],'request':{},'output_root':str(wrapper)}
   (parent/'wait.json').write_text(json.dumps(wait));(parent/'intent.json').write_text('{}');(parent/'child.json').write_text('{}');(parent/'failure.json').write_text('{}');(wrapper/'intent.json').write_text(json.dumps({'parent_pid':pid}));(wrapper/'tail-complete.json').write_text('{}');(wrapper/'observation.json').write_text('{}')
   ref=lambda p:{'path':str(p),'sha256':c.digest(p.read_bytes())}
   q={'wrapper_waits':{'materialize':ref(parent/'wait.json')},'parent_sources':{'materialize':ref(source)}}
   with self.assertRaisesRegex(ValueError,'parent failure'):c.wrapper_authentication(q,root,'materialize',wrapper,{'source':'a'*40})
 def test_readonly_sources_no_start_admit_or_numeric_import(self):
  for name in ('collector01.py','closed_comparison01.py','archive01.py'):
   tree=ast.parse((P/name).read_text())
   for n in ast.walk(tree):
    if isinstance(n,ast.Import):self.assertFalse(any(x.name.split('.')[0] in ('torch','numpy','scipy') for x in n.names))
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):self.assertNotIn(n.func.attr,('start','admit','guarded_run','finish'))
 def test_closed_context_exact_inverse_source(self):
  original=ast.parse((P/'closed-context-baseline01.py').read_text()).body[0];selected=next(n for n in ast.parse((P/'closed_comparison01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='closed_comparison_context')
  # Every inherited statement outside explicitly changed mode/origin/namespace
  # boundary must remain an exact AST statement in the new context.
  selected_dumps=[ast.dump(n,include_attributes=False) for n in selected.body]
  ignored=[]
  for n in original.body:
   text=ast.unparse(n)
   if 'historical context is materialization-only and read-only' in text or 'phase identity already reserved/terminal' in text:ignored.append(text);continue
   if 'Path(__file__)' in text:ignored.append(text);continue
   self.assertIn(ast.dump(n,include_attributes=False),selected_dumps,text)
  self.assertEqual(len(ignored),3)
if __name__=='__main__':unittest.main(verbosity=2)
