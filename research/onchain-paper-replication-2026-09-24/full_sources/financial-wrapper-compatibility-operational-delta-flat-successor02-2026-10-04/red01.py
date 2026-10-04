from pathlib import Path
import importlib.util,json
O=Path(__file__).resolve().parent;F=O.parent;T=F/'financial-wrapper-compatibility-operational-delta-flat-tooling01-2026-10-04';s=importlib.util.spec_from_file_location('oldflat',T/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
failed=F/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04'
try:M.load_capture(failed)
except ValueError as e:print('EXPECTED_OLD_REFUSAL',str(e))
else:raise AssertionError('old caller unexpectedly covers new failed scope')
assert hasattr(M,'load_failed_capture'), 'RED missing exact failed-root capture loader/two-target restoration'
