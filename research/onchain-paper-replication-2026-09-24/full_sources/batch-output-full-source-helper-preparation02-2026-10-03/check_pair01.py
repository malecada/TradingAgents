import importlib.util,json,sys
from pathlib import Path
P=Path(__file__).parent;old=P.parent/'batch-output-full-source-helper-preparation01-2026-10-03';combined=P.parent/'batch-output-combined-worker-preparation01-2026-10-03'
f=old/'capsule_builder01.py' if '--old' in sys.argv else P/'capsule_builder01.py'
s=importlib.util.spec_from_file_location('builder_pair',f);b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
q=json.loads((old/'ROOT_TEMPLATE01.json').read_bytes());rows=[{'path':r['target'],'sha256':r['sha256'],'bytes':r['bytes']} for r in json.loads((combined/'SOURCE_INVENTORY01.json').read_bytes())['entries']]
# Accepted combined inventory retains original three helpers; test only worker pair.
b.full_rows(rows,q['closure_mode']);print('PASS exact accepted combined worker pair accepted in explicit202 map')
