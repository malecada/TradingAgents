from pathlib import Path
import hashlib,json,ast,difflib
P=Path(__file__).resolve().parent;R=P.parents[3];source=R/'tradingagents/research/onchain_replication/compact_mcm_batched.py';old=source.read_text();s=old;changes=[]
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));changes.append(dict(before=a,after=b));s=s.replace(a,b,1)
change('from . import adaptive_edge_policy','from . import adaptive_edge_policy\nfrom . import compiled_normalization_policy')
change(" | ({'edge_cache_policy'} if 'edge_cache_policy' in execution else set()),'explicit numeric execution schema required')", " | ({'edge_cache_policy'} if 'edge_cache_policy' in execution else set()) | ({'compiled_normalization_policy','compiled_normalization_inputs'} if 'compiled_normalization_policy' in execution else set()),'explicit numeric execution schema required')")
change("    if 'edge_cache_policy' in execution:require", "    _compiled_policy(execution)\n    if 'edge_cache_policy' in execution:require")
helper='''def _compiled_policy(execution):
    if 'compiled_normalization_policy' not in execution:
        require('compiled_normalization_inputs' not in execution,'normalization roles without selection')
        return None
    value=compiled_normalization_policy.freeze(execution['compiled_normalization_policy'])
    require(value is not None,'explicit compiled normalization selection required')
    roles=execution.get('compiled_normalization_inputs')
    require(type(roles) is dict and set(roles)=={'source','library','runtime'},'exact registered normalization roles required')
    require(all(type(role) is str and 0<len(role)<=128 and role.isascii() and all(c.isalnum() or c in '_-' for c in role) for role in roles.values()) and len(set(roles.values()))==3 and 'environment' not in roles.values(),'distinct finite registered normalization roles required')
    return value


def _compiled_inputs(execution,run):
    value=_compiled_policy(execution)
    if value is None:return None
    policy=dict(value);ad=run.admission;runtime=None
    for kind in ('source','library','runtime'):
        role=execution['compiled_normalization_inputs'][kind]
        require(role in ad.inputs,'normalization role not admitted')
        info=ad.inputs[role];path=ad.root/info['path']
        require(str(path)==policy[kind+'_path'] and path.resolve()==path and info['sha256']==policy[kind+'_sha256'],'normalization registered path/hash differs')
        limit=4096 if kind=='runtime' else 65536
        bounded=compiled_normalization_policy.read_reference(path,info['sha256'],limit,policy['runtime_bytes'] if kind=='runtime' else None,owned=kind=='library')
        require(run.read_input(role)==bounded,'normalization genuine input bytes differ')
        if kind=='runtime':runtime=compiled_normalization_policy.runtime_metadata(bounded)
    require('environment' in ad.inputs and runtime['runtime_inventory_sha256']==ad.inputs['environment']['sha256'],'normalization inventory not joined to genuine environment input')
    environment=ad.inputs['environment'];path=ad.root/environment['path']
    bounded=compiled_normalization_policy.read_reference(path,environment['sha256'],1024**2)
    require(run.read_input('environment')==bounded,'normalization environment input changed')
    return value


'''
change('def _modules(root, admission=None, *, grouped=False, geometry=False, binding_timing=False):',helper+'def _modules(root, admission=None, *, grouped=False, geometry=False, binding_timing=False, compiled=False):')
change("        if binding_timing:names+=('matching_owner','compact_owner','imported_authority_lease')", "        if binding_timing:names+=('matching_owner','compact_owner','imported_authority_lease')\n        if compiled:names+=('compiled_normalization_policy','compiled_small_lse','matching_annealing','matching_checkpoint')")
change("        numeric=modules['numeric_execution'].verify(root/'stream',binding['numeric_execution'])", "        require(compiled_normalization_policy.freeze(binding.get('compiled_normalization_policy'))==compiled_normalization_policy.freeze(binding['numeric_execution'].get('compiled_normalization_policy')),'batched/numeric normalization selection differs')\n        numeric=modules['numeric_execution'].verify(root/'stream',binding['numeric_execution'])")
change("    require(info['sha256']==binding['mcm_policy_sha256'],'batched policy admission pin differs')", "    require(info['sha256']==binding['mcm_policy_sha256'],'batched policy admission pin differs')\n    if 'compiled_normalization_policy' in binding:\n        policy=json.loads(stage.owner.bound._run.read_input(binding['mcm_policy_input']))\n        execution=validate(policy,binding['cells'])['execution']\n        require(_compiled_inputs(execution,stage.owner.bound._run)==compiled_normalization_policy.freeze(binding['compiled_normalization_policy']),'closed normalization policy differs from admitted input')")
change("**({'edge_cache_policy':execution['edge_cache_policy']} if 'edge_cache_policy' in execution else {}))", "**({'edge_cache_policy':execution['edge_cache_policy']} if 'edge_cache_policy' in execution else {}),**({'compiled_normalization_policy_value':dict(_compiled_policy(execution))} if 'compiled_normalization_policy' in execution else {}))")
change("binding_timing='binding_timing' in b['execution'])", "binding_timing='binding_timing' in b['execution'],compiled='compiled_normalization_policy' in b['execution'])")
change("        owner.boundary();target.check()", "        normalization=_compiled_inputs(b['execution'],owner.bound._run)\n        owner.boundary();target.check()")
change("            held.check(owner);target.check();owner.boundary();stage.lease();target.final();io._root(root,fd)", "            held.check(owner);target.check();owner.boundary();stage.lease();target.final();io._root(root,fd)\n            require(_compiled_policy(b['execution'])==normalization,'batched normalization selection changed')")
change("        binding.update(mcm_policy_input=input_name,mcm_policy_sha256=start['policy_sha256'])", "        require(compiled_normalization_policy.freeze(binding['numeric_execution'].get('compiled_normalization_policy'))==normalization,'completed numeric normalization selection differs')\n        if normalization is not None:binding['compiled_normalization_policy']=dict(normalization)\n        binding.update(mcm_policy_input=input_name,mcm_policy_sha256=start['policy_sha256'])")
ast.parse(s);(P/'compact_mcm_batched.py').write_text(s)
restored=s
for c in reversed(changes):assert restored.count(c['after'])==1;restored=restored.replace(c['after'],c['before'],1)
assert restored==old
(P/'LITERAL_INVERSE01.json').write_text(json.dumps(dict(baseline_path=str(source.relative_to(R)),baseline_sha256=hashlib.sha256(old.encode()).hexdigest(),changes=changes),indent=2)+'\n')
(P/'compact_mcm_batched.py.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='installed/compact_mcm_batched.py',tofile='candidate/compact_mcm_batched.py')))
