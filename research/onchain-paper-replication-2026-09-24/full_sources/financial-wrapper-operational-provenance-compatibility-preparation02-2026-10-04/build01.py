import ast,difflib,hashlib,json,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;P=B/'financial-wrapper-operational-provenance-compatibility-preparation01-2026-10-04';V=B/'financial-wrapper-operational-provenance-compatibility-review01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((P/'MANIFEST01.json').read_bytes())=='ac15b2501dc1ca44b8f1505eed49039672e074ac536bf6a26bfde402e3576786'
assert sha((V/'MANIFEST01.json').read_bytes()).startswith('6f808520')
shutil.copytree(P,H/'predecessor01',symlinks=True)
(H/'independent_finding01').mkdir()
for n in ('MANIFEST01.json','MACHINE01.json','REPORT01.md','WITNESS01.json','independent01.py'):(H/'independent_finding01'/n).write_bytes((V/n).read_bytes())
for n in ('financial_wrapper_fixture.py','training.py','workflow_storage.py','operational_source_compatibility.py','original_financial_wrapper_fixture.py','original_training.py'):(H/n).write_bytes((P/n).read_bytes())
wrapper=H/'financial_wrapper_fixture.py';old=wrapper.read_text()
a=" info=run.admission.inputs[value['checkpoint_input']];run.read_input(value['checkpoint_input']);checkpoint=run.admission.root/info['path']"
b=" if 'operational_source_compatibility' in run.admission.inputs and p['phase']=='predict':\n  from .operational_source_compatibility import require_prediction_policy\n  require_prediction_policy(run,claim)\n"+a
assert old.count(a)==1;new=old.replace(a,b);wrapper.write_text(new)
helper=H/'operational_source_compatibility.py';base=helper.read_text();oldpin=sha(old.encode());newpin=sha(new.encode());assert base.count(oldpin)==1;s=base.replace(oldpin,newpin)
addition='''\n\ndef validate_prediction_parent(policy,policy_sha256,closure_sha256,parent_identity,parent_inputs,parent_sources,parent_cells):
 """Pure metadata predicate; it neither verifies nor creates a genuine claim.
 The runtime caller supplies fields from the original verified COMPLETE parent.
 """
 require(digest(policy_sha256) and digest(closure_sha256),'exact current policy/closure hashes unavailable')
 expected=policy['consumers']['continue100']
 require(parent_identity==expected['experiment'] and parent_cells==[expected['cell_id']],'prediction parent must be the fixed continuation consumer/cell')
 require(type(parent_inputs)is dict and parent_inputs.get(ROLE,{}).get('sha256')==policy_sha256,'completed parent used a different or missing compatibility policy')
 target=policy['target']
 require(parent_inputs.get(target['closure_input'],{}).get('sha256')==closure_sha256,'completed parent full implementation closure differs')
 require(type(parent_sources)is dict and all(parent_sources.get(p)==h for p,h in target['installed'].items()),'completed parent target implementation map differs')
 return {'policy_sha256':policy_sha256,'parent_experiment':parent_identity,'target_map_sha256':sha(canonical(target['installed']))}


def require_prediction_policy(run,claim):
 policy,plan,read,budget,pin=_context(run,_registered_normal)
 require(plan['phase']=='predict','prediction policy join is unavailable outside prediction')
 # financial_wrapper_fixture._parent already verified this exact claim and its
 # actual COMPLETE lifecycle, and preserved the strict scientific comparison.
 return validate_prediction_parent(policy,pin,sha(read(policy['target']['closure_input'])),claim['experiment_id'],claim['inputs'],claim['experiment']['source_files'],claim['experiment']['cells'])
'''
s+=addition;helper.write_text(s)
for n in ('financial_wrapper_fixture.py','operational_source_compatibility.py'):ast.parse((H/n).read_text())
assert new.replace(b,a)==old;assert s.removesuffix(addition).replace(newpin,oldpin)==base
# Existing methods, numerical bodies, readers and fatal cleanup remain identical.
a1=ast.parse(base);a2=ast.parse(s);a1.body=[n for n in a1.body if not isinstance(n,ast.Assign) or not any(isinstance(t,ast.Name) and t.id=='CONTROL_TARGETS' for t in n.targets)];a2.body=[n for n in a2.body if getattr(n,'name',None) not in ('validate_prediction_parent','require_prediction_policy') and (not isinstance(n,ast.Assign) or not any(isinstance(t,ast.Name) and t.id=='CONTROL_TARGETS' for t in n.targets))];assert ast.dump(a1)==ast.dump(a2)
changes={'financial_wrapper_fixture.py':[{'old':a,'new':b}],'operational_source_compatibility.py':[{'old':oldpin,'new':newpin},{'old':'','new':addition,'operation':'append'}]}
(H/'SUCCESSOR_INVERSE01.json').write_text(json.dumps({'changes':changes,'original_sources':{n:sha((P/n).read_bytes()) for n in changes},'successor_sources':{n:sha((H/n).read_bytes()) for n in changes},'full_literal_and_AST_inverse':True},indent=2,sort_keys=True)+'\n')
inv=json.loads((P/'SOURCE_INVERSES02.json').read_text());inv['changes']['financial_wrapper_fixture.py'].append({'old':a,'new':b});inv['sources']['financial_wrapper_fixture.py']['new_sha256']=newpin
(H/'SOURCE_INVERSES02.json').write_text(json.dumps(inv,indent=2,sort_keys=True)+'\n')
for n in changes:(H/(n+'.patch')).write_text(''.join(difflib.unified_diff((P/n).read_text().splitlines(True),(H/n).read_text().splitlines(True),fromfile='predecessor01/'+n,tofile=n)))
print(json.dumps({'status':'SOURCE_CANDIDATE_BUILT_NO_RUNTIME','wrapper':newpin,'helper':sha(s.encode()),'retained01_manifest':sha((P/'MANIFEST01.json').read_bytes()),'review01_manifest':sha((V/'MANIFEST01.json').read_bytes()),'witness01_sha256':sha((V/'WITNESS01.json').read_bytes())}))
