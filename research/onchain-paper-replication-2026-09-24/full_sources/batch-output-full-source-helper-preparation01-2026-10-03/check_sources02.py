"""All source origins and current Git are read-only; no future anchor made."""
import ast,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('builder',P/'capsule_builder01.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
v=json.loads((P/'SOURCE_INVENTORY01.json').read_bytes());q=json.loads((P/'ROOT_TEMPLATE01.json').read_bytes());baseline=json.loads((P/'ORIGIN_ROWS_INITIAL01.json').read_bytes())
checked=[]
for row in v['entries']:
 path=Path(row['origin']);reader=b.Reader(path.parent);raw=reader.body(path.name)
 assert len(raw)==row['bytes'] and b.sha(raw)==row['sha256'];checked.append(row['target'])
assert len(checked)==len(set(checked))==202
cap=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');r=b.Reader(cap)
# Exact actual current199 roots, independently of prospective replacements.
reg=b.parse(r.body('held-fixture-registration01.json'));exp=reg['experiments']['original-import-held-success-20261003-01'];current={n:h for n,h in exp['source_files'].items() if n not in baseline['baseline_auxiliary_paths']};assert len(current)==199
rows=[]
for name,h in sorted(current.items()):
 raw=r.body(name);assert b.sha(raw)==h;rows.append({'path':name,'sha256':h,'bytes':len(raw)})
b.full_git_bodies(r,baseline['baseline_source'],rows);r.recheck()
# Static inverse source-specialization checks: only names/counts/error labels
# differ within copies; baseline methods and default prefixes remain intact.
old=ast.parse((P/'generate_inputs01.py.baseline.txt').read_bytes());new=ast.parse((P/'generate_inputs01.py').read_bytes());nodes={n.name:n for n in new.body if isinstance(n,ast.FunctionDef)}
names={'render_held_auxiliary_declaration','held_auxiliary_metadata','held_input_plan'}
class Undo(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  if n.name.startswith('full_') and n.name[5:] in names:n.name=n.name[5:]
  return self.generic_visit(n)
 def visit_Name(self,n):
  if n.id.startswith('full_') and n.id[5:] in names:n.id=n.id[5:]
  return n
 def visit_Constant(self,n):
  if type(n.value) is int and n.value in (202,151,207):n.value={202:199,151:148,207:204}[n.value]
  elif type(n.value) is str:
   for a,z in [('202','199'),('151','148'),('207','204')]:n.value=n.value.replace(a,z)
  return n
for n in old.body:
 if isinstance(n,ast.FunctionDef) and n.name in names:assert ast.dump(n)==ast.dump(Undo().visit(nodes['full_'+n.name]))
# Original code/package paths plus exactly three additions, helpers replaced.
newpaths=set(checked)-set(current);assert newpaths=={'tradingagents/research/onchain_replication/'+n for n in ('archive_non_tail.py','selected_non_tail_transport.py','completed_f32.py')}
result={'status':'source_origins_and_actual_baseline_checked','actual_baseline_source':baseline['baseline_source'],'actual_current_code':199,'prospective_implementation_count':202,'prospective_package_count':151,'prospective_admission_count':207,'actual_future_source':None,'actual_future_anchor':None,'new_paths':sorted(newpaths),'helper_replacements':list(q['closure_mode']['helper_source_files']),'origin_count':len(checked),'metadata_only_inverse_ast':True,'execution_admitted':False}
(P/'READBACK02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print('PASS202 origins, actual199 original current/Git joins, exact3new packagepaths, selected generator count-only inverse AST')
