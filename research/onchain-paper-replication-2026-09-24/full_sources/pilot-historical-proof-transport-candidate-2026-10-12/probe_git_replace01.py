"""Synthetic temporary-Git replacement currentness control, no real history."""
import json
from pathlib import Path
from test_transport import ProofTests,v,old,P
ProofTests.setUpClass()
try:
 root=ProofTests.root;commit=ProofTests.commit;p=root/'source00.txt';oldbody=p.read_bytes()
 with v._SweepGitReader(root) as reader:
  v._verify_sources(root,ProofTests.pins,{commit},_source_reader=reader)
  p.write_bytes(b'changed synthetic');ProofTests.git('add','source00.txt');ProofTests.git('commit','-qm','synthetic replacement');new=ProofTests.git('rev-parse','HEAD').decode().strip();ProofTests.git('replace',commit,new)
  def outcome(fn):
   try:fn();return {'accepted':True}
   except Exception as e:return {'accepted':False,'type':type(e).__name__,'message':str(e)}
  expected=outcome(lambda:old._verify_sources(root,ProofTests.pins,{commit}))
  observed=outcome(lambda:v._verify_sources(root,ProofTests.pins,{commit},_source_reader=reader))
 (P/'REPLACE_CURRENTNESS01.json').write_text(json.dumps({'synthetic_only':True,'legacy_fresh_child':expected,'persistent_child':observed,'same':expected==observed},indent=2)+'\n');print(expected,observed)
finally:ProofTests.tearDownClass()
