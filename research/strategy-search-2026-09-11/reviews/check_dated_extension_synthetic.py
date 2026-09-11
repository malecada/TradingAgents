"""Independent adversarial preservation checks in disposable invented repositories."""
from pathlib import Path
import hashlib,importlib.util,inspect,json,tempfile
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('extension_fixture_review',ROOT/'tests/research/test_extended_lifecycle.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
# Retain an explicit unrun ancestor and another family in every historical gate.
# This alters only invented fixture construction, never a real registry/ledger.
source=inspect.getsource(fixture.build_extension).replace("    previous=None", "    spec['experiments']['unrun-ancestor']=deepcopy(exp)\n    spec['families']['unrelated']={'mechanism_id':'invented-unrelated','attempt_budget':2,'prior_attempts':0,'history_reference':'preserved unrelated history'}\n    previous=None",1)
namespace=dict(fixture.__dict__);exec(source,namespace)
results=[]
for change in ('remove_unrun_ancestor','rewrite_unrelated_family'):
 with tempfile.TemporaryDirectory(prefix='dated-extension-independent-') as directory:
  root,gate,certificate,commit=namespace['build_extension'](Path(directory))
  if change=='remove_unrun_ancestor':del gate['experiments']['unrun-ancestor']
  else:gate['families']['unrelated']['history_reference']='rewritten history'
  commit=fixture.rebind_extension(root,gate,certificate)
  try:
   run=fixture.start(root,commit)
  except (ValueError,KeyError) as error:
   results.append({'change':change,'rejected_before_claim':not (root/'research_runs'/fixture.TARGET).exists(),'error':type(error).__name__+': '+str(error)})
  else:
   results.append({'change':change,'rejected_before_claim':False,'error':'altered historical gate was admitted'})
   run.fail('invented adversarial review completed; no source call')
report={'passed':all(x['rejected_before_claim'] for x in results),'cases':results,'scope':'Disposable invented history and [1] input only. No real source/financial run, registry mutation or network.','source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tradingagents/research_extended').glob('*.py')}}
(Path(__file__).parent/'dated-extension-synthetic-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
