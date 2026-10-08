import importlib.util,pathlib,sys,unittest,json
HERE=pathlib.Path(__file__).resolve().parent
C=HERE.parent/'real-data-pilot-advance-validation-correction01-2026-10-08'
s=importlib.util.spec_from_file_location('candidate_checks',C/'checks.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
import tradingagents.research.onchain_replication as package
package.matching_checkpoint=h.new
sys.modules['tradingagents.research.onchain_replication.matching_checkpoint']=h.new
from tests.research.onchain_replication import test_matching_pair_checkpoints as suite
suite.engine=h.new
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(suite))
(HERE/'EXISTING_SUITE02.json').write_text(json.dumps({'tests':r.testsRun,'passed':r.wasSuccessful(),'candidate_package_and_function_local_imports_bound':True,'supersedes_only_reviewer_harness_binding':True},indent=2)+'\n')
sys.exit(0 if r.wasSuccessful() else 1)
