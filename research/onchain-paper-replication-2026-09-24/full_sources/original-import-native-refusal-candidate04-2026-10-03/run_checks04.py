"""Finite metadata/formula suite only; all numerical packages forbidden."""
import os,sys,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));os.environ['FIXTURE_DIR']=str(D)
if 'PARSER_DIR' in os.environ:raise RuntimeError('final corpus requires selected04 parser')
suite=unittest.defaultTestLoader.loadTestsFromNames(['test_resealed04','test_formulas04','test_evidence04'])
result=unittest.TextTestRunner(verbosity=2).run(suite)
forbidden=[n for n in sys.modules if n.split('.')[0] in ('numpy','scipy','torch','tradingagents')]
if forbidden:raise RuntimeError('unexpected numerical/package import: '+repr(forbidden))
print('No numerical/package imports, claims, Owners, native guards or matching executions.')
sys.exit(not result.wasSuccessful())
