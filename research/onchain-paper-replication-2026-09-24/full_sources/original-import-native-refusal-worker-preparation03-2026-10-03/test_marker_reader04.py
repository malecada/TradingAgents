"""Real raw post-tail parser refuses additive marker; tiny metadata only."""
import hashlib,importlib.util,json,pathlib,tempfile,unittest
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
rows=json.loads((D/'source_inventory03.json').read_text())['source_inventory'];row=next(r for r in rows if r['target']=='fixture_tools/raw_receipts01.py');path=ROOT/row['origin'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];spec=importlib.util.spec_from_file_location('selected_raw_source_reader',path);raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
class Tests(unittest.TestCase):
 def test_original_parser_refuses_marker_before_accepting_old_tail(self):
  with tempfile.TemporaryDirectory() as folder:
   root=pathlib.Path(folder);outer=root/'fixture_outer'/'synthetic-unclaimed';outer.mkdir(parents=True);(outer/'terminal.json').write_text('{"status":"passed"}');(outer/'post-tail-storage.json').write_text('{"synthetic":"not a native observation"}');(outer/'post-terminal-failure.json').write_text('{"status":"failed","error_type":"OSError"}')
   with self.assertRaisesRegex(ValueError,'outer finalization failed'):raw.authenticate_post_tail(root,'synthetic-unclaimed',{})
if __name__=='__main__':unittest.main(verbosity=2)
