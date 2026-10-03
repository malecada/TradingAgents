"""Exact inverse candidate edits; all other full AST and bytes must match."""
import ast,hashlib
from pathlib import Path
b=Path(__file__).parent
old=(b/'population_assembly.before.py').read_text();new=(b/'population_assembly.py').read_text()
new=new.replace("    projection = type(plan.get('schema_version')) is int and plan['schema_version'] == 2\n",'')
new=new.replace("    if set(plan) != ({'schema_version','graphs','price_input','fold','calendar_input',\n                     'expected_weeks','admission_input','outputs'} | ({'projection_input'} if projection else set())) or (not projection and plan['schema_version'] != 1):\n", "    if set(plan) != {'schema_version','graphs','price_input','fold','calendar_input',\n                     'expected_weeks','admission_input','outputs'} or plan['schema_version'] != 1:\n")
new=new.replace("    if (set(outputs) != ({'population','binding','assembly'} | ({'projection'} if projection else set())) or len(set(outputs.values())) != (4 if projection else 3)\n", "    if (set(outputs) != {'population','binding','assembly'} or len(set(outputs.values())) != 3\n")
new=new.replace("    if projection:\n        from .population_batch_projection import publish_projection\n        publish_projection(run, plan_input, plan, result)\n",'')
assert new==old
assert ast.dump(ast.parse(new))==ast.dump(ast.parse(old))
print('PASS complete inverse bytes/AST; only schema2/output selector and fourth publication hook differ.')
print('Baseline SHA256',hashlib.sha256(old.encode()).hexdigest())
