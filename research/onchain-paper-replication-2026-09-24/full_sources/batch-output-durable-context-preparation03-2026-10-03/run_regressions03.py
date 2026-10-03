import importlib.util,unittest
from pathlib import Path
H=Path(__file__).parent
spec=importlib.util.spec_from_file_location('retained_source_tests02',H/'test_corrections02.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Original ten behavioral controls remain exact; two old parity expectations are
# superseded by test_bounds03's full inverse-to02 proof for the declared change.
names=[n for n in unittest.defaultTestLoader.getTestCaseNames(m.Tests) if n not in ('test_inverse_complete_module_bytes','test_whole_other_sources_and_inverse_ast')]
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(m.Tests(n) for n in names));raise SystemExit(not result.wasSuccessful())
