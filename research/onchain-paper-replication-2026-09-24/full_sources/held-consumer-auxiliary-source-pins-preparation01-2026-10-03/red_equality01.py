"""Actual old helper; synthetic source maps, never an admission invocation."""
import runpy
from test_auxiliary01 import P,fixture
old=runpy.run_path(str(P/'generate_inputs01.py.baseline04.txt'))
source,roles=fixture();roles={k:v for k,v in roles.items() if k in old['HELD_ROLES']}
old['held_input_plan'](roles,source)
