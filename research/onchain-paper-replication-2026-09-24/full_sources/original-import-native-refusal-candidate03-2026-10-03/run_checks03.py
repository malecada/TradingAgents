"""Finite stdlib-only source/retained-format suite; no numerical runtime import."""
import os,sys,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
os.environ['MCM_SOURCE']=str(D/'compact_mcm.py');os.environ['REFUSAL_PARSER_DIR']=str(D)
sys.path.insert(0,str(D))
names=['test_cleanup03','test_cleanup_actual03','test_evidence03','test_format03','test_review03']
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
result=unittest.TextTestRunner(verbosity=2).run(suite)
forbidden=[name for name in sys.modules if name.split('.')[0] in ('numpy','torch','scipy','tradingagents')]
if forbidden:raise RuntimeError('numerical/package import outside proof: '+','.join(forbidden))
print('Numerical/package imports: none. Actual claims/Owners/guards: zero.')
sys.exit(not result.wasSuccessful())
