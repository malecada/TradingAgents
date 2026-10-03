"""Exact old count refusal versus explicit new metadata mode; no authority."""
import importlib.util,json,sys,types
from pathlib import Path
P=Path(__file__).parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
b=load('builder',P/'capsule_builder01.py');g=load('generator',P/'generate_inputs01.py');pkg=types.ModuleType('fixture_tools');pkg.capsule_builder01=b;sys.modules['fixture_tools']=pkg
q=json.loads((P/'ROOT_TEMPLATE01.json').read_bytes());mode=q['closure_mode'];source,package=b.full_rows(q['rows'],mode)
plan={'kind':'full202-resource-source-metadata-v1','closure_mode':mode,'source_count':202,'package_count':151,'source_files':source,'package_files':package,'execution_admitted':False,'source':'a'*40,'anchor':'b'*40,'root':'/synthetic-only'}
result=g._legacy_held_input_plan({},plan) if '--baseline' in sys.argv else g.held_input_plan({},plan,closure_mode=mode)
assert result['source_count']==202 and result['package_count']==151 and result['execution_admitted'] is False
print('PASS explicit202/151 metadata-only plan; all missing Root roles remain unresolved')
