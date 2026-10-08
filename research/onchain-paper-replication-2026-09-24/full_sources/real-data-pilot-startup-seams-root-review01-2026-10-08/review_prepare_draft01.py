"""Different-author changed-seam review; metadata fixtures only, no authority."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
F = HERE.parent
C = F / 'real-data-pilot-prepare-bracket01-2026-10-08'
ROOT = HERE.parents[3]
checks = []

def check(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def nodes(path):
    return {n.name: n for n in ast.parse(path.read_text()).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))}

check(sha(C/'compact_mcm.py') == 'd8435b5bc2e2067065969ad73629914d45bed5d30272a176579b4d9024c35294', 'exact_compact_candidate')
check(sha(C/'imported_mcm_identity.py') == '75d4e269ad4e87a34061e8331381af417b3c850346d71711902fcd5bbf322c82', 'exact_target_candidate')
check(sha(C/'baseline_compact_mcm.py') == sha(ROOT/'tradingagents/research/onchain_replication/compact_mcm.py'), 'frozen_main_baseline')
check(sha(C/'baseline_imported_mcm_identity.py') == '39304277c2a0c6278a7524102f15bcfb0f8f9d73f691b51e0cd7a554a65bd7eb', 'accepted_constructor_baseline')
old, new = nodes(C/'baseline_compact_mcm.py'), nodes(C/'compact_mcm.py')
check(old.keys() == new.keys(), 'compact_definition_roster')
for name in old:
    if name != '_prepare':
        check(ast.dump(old[name]) == ast.dump(new[name]), 'unchanged_compact_'+name)
old_t, new_t = nodes(C/'baseline_imported_mcm_identity.py'), nodes(C/'imported_mcm_identity.py')
for name in old_t:
    if name != 'Target':
        check(ast.dump(old_t[name]) == ast.dump(new_t[name]), 'unchanged_target_module_'+name)
old_methods = {n.name:n for n in old_t['Target'].body if isinstance(n, ast.FunctionDef)}
new_methods = {n.name:n for n in new_t['Target'].body if isinstance(n, ast.FunctionDef)}
check(set(new_methods) - set(old_methods) == {'_prepare_sources','_prepare_graph'}, 'only_two_private_getters')
for name in old_methods:
    if name != 'sources':
        check(ast.dump(old_methods[name]) == ast.dump(new_methods[name]), 'unchanged_target_'+name)
old_scan = old_methods['sources'].body[1:]
new_scan = new_methods['_prepare_sources'].body[2:]
check([ast.dump(n) for n in old_scan] == [ast.dump(n) for n in new_scan], 'exact_source_hash_loop')
old_text=(C/'baseline_compact_mcm.py').read_text(); new_text=(C/'compact_mcm.py').read_text()
check(old_text[old_text.index('    rows = len(graph.node_ids)'):old_text.index('    io._json(start); return')] == new_text[new_text.index('    rows = len(graph.node_ids)'):new_text.index('    io._json(start)\n')], 'unchanged_numeric_policy_preparation')

# Reuse only fixture construction, then inject independently chosen callbacks.
# The fixture does not instantiate Target, Owner, Binding, Run, or graph arrays.
spec=importlib.util.spec_from_file_location('prepare_metadata_fixtures', C/'test02.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def fixture():
    t=m.Checks(); t.setUp(); return t

t=fixture()
t.ns['_sources']=lambda d:(d.check(), {'source':'a'*64})[1]
t.ns['_graph']=lambda d,k:(d.check(),d.graph)[1]
before=t.invoke('baseline_compact_mcm.py'); check(t.calls==3,'baseline_three_target_checks')
t.calls=0;t.events=[]
after=t.invoke();check(t.calls==2,'candidate_entry_final_checks')
check(before==after,'unchanged_imported_metadata_result')
t=fixture();t.imported=False
before=t.invoke('baseline_compact_mcm.py');t.calls=0;t.events=[];after=t.invoke()
check(before==after and t.calls==1,'legacy_result_and_entry_inverse')

for seam in ('sources','read_input','kernel','output_policy','json','final'):
    t=fixture()
    def revoke(): t.revoked=True
    if seam=='sources':
        original=t.target._prepare_sources
        def callback():
            result=original();revoke();return result
        t.target._prepare_sources=callback
    elif seam=='read_input':
        run=t.target.owner.bound._run;original=run.read_input
        def callback(name):
            result=original(name);revoke();return result
        run.read_input=callback
    elif seam=='kernel': t.kernel.validate_policy=lambda *args:revoke()
    elif seam=='output_policy':
        t.ns['publication']._output_policy=lambda *args:(revoke(),({},1))[1]
    elif seam=='json': t.ns['io']._json=lambda value:revoke()
    else: t.mutation=revoke
    try: t.invoke()
    except ValueError as error: check(str(error)=='revoked','late_revocation_refused_'+seam)
    else: raise AssertionError('accepted late revocation '+seam)

for seam in ('sources','read_input','kernel','output_policy','json'):
    t=fixture(); expected=OSError('original '+seam)
    def fatal(*args): raise expected
    if seam=='sources':t.target._prepare_sources=fatal
    elif seam=='read_input':t.target.owner.bound._run.read_input=fatal
    elif seam=='kernel':t.kernel.validate_policy=fatal
    elif seam=='output_policy':t.ns['publication']._output_policy=fatal
    else:t.ns['io']._json=fatal
    try:t.invoke()
    except OSError as error:check(error is expected,'original_error_preserved_'+seam)
    else:raise AssertionError('lost original error '+seam)

result={'decision':'accepted-source-only','checks':checks,
    'sources':{str(p.relative_to(ROOT)):sha(p) for p in (C/'compact_mcm.py',C/'imported_mcm_identity.py',C/'baseline_compact_mcm.py',C/'baseline_imported_mcm_identity.py')},
    'scope':'Different-author source/AST and metadata-callback checks only. No genuine authority, arrays, graph, neural, admission, performance or live integration. Imported preparation reduces three Target.check calls to entry+final two, retaining source-hash scans and public checked getters; seven eager preparations remove seven Target.check calls (static at least21 execution checks). Constructor acceptance reused, not re-reviewed. Full final check remains genuine in source; its runtime behavior is inherited unchanged, not proved by callback stubs. Sampled boundaries are not atomic concurrent-writer exclusion; kernel pins do not prove transitive global immutability.'}
out=HERE/'PREPARE_REVIEW01.json'
with out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':result['decision'],'checks':len(checks),'review_sha256':sha(out)}))
