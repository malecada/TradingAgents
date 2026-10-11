"""Actual-source AST/metadata checks only; never execute admission or launcher."""
import ast,hashlib,json
from pathlib import Path
ROOT=Path.cwd().resolve();H=Path(__file__).resolve().parent;F=H.parent;OLD=F/'real-data-pilot-full29-entry01-2026-10-09'
def load(p):return json.loads(p.read_bytes())
def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
def main():
 old=funcs(OLD/'preflight29_02.py');new=funcs(H/'preflight30_01.py');changed=[k for k in old if old[k]!=new[k]]
 assert changed==['prepared_inputs','check']
 assert funcs(OLD/'root_io29_02.py')==funcs(H/'root_io30_01.py')
 assert (H/'root_io30_01.py').read_text().replace('from preflight30_01 import check','from preflight29_02 import check')==(OLD/'root_io29_02.py').read_text()
 tree=ast.parse((H/'preflight30_01.py').read_text());constants={}
 for n in tree.body:
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name):
   try:constants[n.targets[0].id]=ast.literal_eval(n.value)
   except (ValueError,TypeError):pass
 assert constants['NAME']=='eth-paper-real-data-end-to-end-resource-20261011-30'
 job=load(F/'real-data-pilot-full30-binding-preparation01-2026-10-11/public01/execution_job.json');assert constants['EXPECTED_RESOURCES']==job['resources']
 core=load(H/'CORE_MANIFEST01.json');oldcore=load(OLD/'CORE_MANIFEST01.json')
 for role in ('compact_policy','typed_payload','mcm_output_policy'):assert core['inputs'][role]['sha256']==oldcore['inputs'][role]['sha256']
 mcm=load(ROOT/core['inputs']['mcm_policy']['path'])['batched']['execution'];assert mcm['compiled_normalization_policy']==constants['COMPILED_POLICY'] and mcm['compiled_normalization_inputs']==constants['COMPILED_INPUTS']
 # Extract only actual stdlib entry helpers; missing references refuse without imports.
 scope={'Path':Path,'ROOT':ROOT}
 selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('need','reference','read_path')]
 exec(compile(ast.Module(body=selected,type_ignores=[]),'<entry-helpers>','exec'),scope)
 refused=0
 for value in (None,{}, {'path':'../bad','sha256':'0'*64},{'path':'valid.json','sha256':None}):
  try:scope['reference'](value)
  except (ValueError,TypeError):refused+=1
 assert refused==4
 try:scope['read_path'](H/'BINDING01.json')
 except FileNotFoundError:pass
 else:raise AssertionError('missing genuine binding must refuse')
 ancestry=load(H/'CAPACITY_SOURCE_MAP01.json')['source_files'];assert len(ancestry)>=365
 pins=load(F/'real-data-pilot-full30-preparation01-2026-10-11/gate.draft01.json')['experiments'][constants['NAME']]['source_files'];pins.update(load(H/'INSTALLED_SOURCE_PINS01.json'))
 assert all(pins.get(path)==digest for path,digest in ancestry.items())
 for path,digest in load(H/'INSTALLED_SOURCE_PINS01.json').items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
 for p in H.glob('*.py'):ast.parse(p.read_text())
 print(json.dumps({'status':'PASS_SOURCE_ONLY','changed_preflight_functions':changed,'launcher_function_bodies_unchanged':True,'malformed_ref_refusals':refused,'missing_actual_binding_refused':True,'capacity_ancestry_sources':len(ancestry),'authority_or_launch_executed':False}))
if __name__=='__main__':main()
