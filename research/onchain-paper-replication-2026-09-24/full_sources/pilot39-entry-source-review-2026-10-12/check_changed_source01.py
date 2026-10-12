"""Finite static controls only. Does not import or execute entry controls."""
import ast, hashlib, json, difflib
from pathlib import Path
ROOT=Path.cwd();F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
C=F/'pilot39-entry-preparation-candidate-2026-10-12';O=F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
s=(C/'prepare_entry01.py').read_text();tree=ast.parse(s);pre=(C/'preflight39_01.py').read_text()
# Inspect the authored statement creating the private reference, never a private body.
prep=function(tree,'prepare')
transport=[n for n in ast.walk(prep) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='binding' and isinstance(t.slice,ast.Constant) and t.slice.value=='transport' for t in n.targets)]
assert len(transport)==1
transport_source=ast.get_source_segment(s,transport[0])
assert "'bytes'" in transport_source or 'private_input' in transport_source or 'transport_reference' in transport_source,transport_source
observe=function(tree,'observe');first_work=min(n.lineno for n in ast.walk(observe) if isinstance(n,ast.ImportFrom))
guards=[n for n in observe.body if isinstance(n,ast.Assert) and 'BASELINE_STORAGE_OBSERVATION01.json' in ast.get_source_segment(s,n)]
assert guards and guards[0].lineno<first_work,'observation existing-output refusal must precede imports/scan'
assert "need('entry_qualification' not in mcm" in pre
assert "capacity.get('whole_cells')==415968128" in pre and "capacity.get('whole_graphs')==7" in pre
assert "capacity.get('memory_fit_proven') is False" in pre
assert "len(pins)==428" in pre and 'authenticate_committed(anchor,pins)' in pre
for token in ["len(gate['experiments'])==15","len(experiment['source_files'])==1036","len(pins)==428","sourcefiles[path]==digest","parent=None","actual_new_recovery':None","final_release':None"]:assert token in s,token
assert "full_training_memory_fit_proven':False" in s and "physical_reservation':False" in s
rootio=(C/'root_io39_01.py').read_text();assert rootio.replace('preflight39_01','preflight38_01')==(O/'root_io38_01.py').read_text()
for oldname,newname in [('preflight38_01.py','preflight39_01.py'),('root_io38_01.py','root_io39_01.py')]:
 before=(O/oldname).read_text();after=(C/newname).read_text();ast.parse(after)
 diff=(C/(newname+'.diff')).read_text();inverse=(C/(newname+'.inverse.diff')).read_text()
 assert diff==''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str((O/oldname).relative_to(ROOT)),tofile='full39/'+newname))
 assert inverse==''.join(difflib.unified_diff(after.splitlines(True),before.splitlines(True),fromfile='full39/'+newname,tofile=str((O/oldname).relative_to(ROOT))))
print(json.dumps({'status':'STATIC_CHANGED_SOURCE_PASS','candidate_sha256':sha(C/'prepare_entry01.py'),'preflight_sha256':sha(C/'preflight39_01.py'),'root_io_sha256':sha(C/'root_io39_01.py'),'transport_statement':transport_source,'candidate_controls_executed':False,'actual_scan_admission_numerical_execution':False},indent=2))
