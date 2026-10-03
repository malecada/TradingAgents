"""Independent bounded source/typed metadata checks. No authority or numerics."""
import ast,copy,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((HERE/'MANIFEST03.json').read_bytes())
for r in m['files']:
 b=(ROOT/r['path']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes'],r['path']
inv=json.loads((HERE/'source_inventory03.json').read_bytes());rows=inv['source_inventory'];assert len(rows)==195
old=json.loads((HERE.parent/'neural-cold-feature-handoff-proof-source-composition02-2026-10-03/source_inventory02.json').read_bytes())
a={r['target']:r for r in old['source_inventory']};b={r['target']:r for r in rows};assert a.keys()==b.keys()
assert [k for k in a if a[k]['sha256']!=b[k]['sha256']]==['proof_tools/proof_release01.py']
for r in rows:
 p=ROOT/r.get('snapshot',r['origin']);assert sha(p.read_bytes())==r['sha256'],r['target']
import proof_release01 as module
first=module.IDENTITIES['materialize'];second=module.IDENTITIES['compare']
inputs={n:{'path':'emitted/'+n,'sha256':sha(n.encode()),'dataset':'synthetic-cold'} for n in module.MATERIAL_INPUTS}
oldexp={'family':'f','parent':None,'question':'input question','cells':[module.CELLS['materialize']],'outputs':['proof-materialize.json'],'charter':{'path':'old/charter','sha256':sha(b'oldcharter')},'inputs':{'environment':{'path':'env.json','sha256':sha(b'env'),'dataset':'synthetic-cold'}},'source_files':{r['target']:r['sha256'] for r in rows},'runtime_hashes':{'runtime.py':sha(b'runtime')},'reuse':'exploratory','stage':'development','windows':[{'dataset':'synthetic-cold','start':'2023-12-04T00:00:00Z','end':'2024-05-13T00:00:00Z','availability':'existing'}]}
oldreg={'schema_version':1,'program_id':module.PROGRAM,'families':{'f':{'mechanism_id':'f','attempt_budget':2,'prior_attempts':0,'history_reference':'history'}},'datasets':{'synthetic-cold':{'identity':'synthetic','history_reference':'history','exposures':[]}},'experiments':{first:oldexp}}
newexp=copy.deepcopy(oldexp);newexp.update(parent=first,question='compare question',cells=[module.CELLS['compare']],outputs=['binding.json','journal.json','cold-handoff.json','proof-compare.json'],charter={'path':'new/charter','sha256':sha(b'newcharter')},inputs={('execution_job' if n=='future_execution_job' else n):r for n,r in inputs.items()}|{'environment':oldexp['inputs']['environment']})
newreg=copy.deepcopy(oldreg);newreg['experiments'][second]=newexp
module._registration_evolution(oldreg,newreg,newexp,{'inputs':inputs})
mutators=[lambda d:d['experiments'][first].update(question='changed original'),lambda d:d['experiments'][second]['runtime_hashes'].update(x='changed'),lambda d:d['experiments'][second].update(stage='confirmation'),lambda d:d['experiments'][second]['windows'][0].update(end='2025-01-01T00:00:00Z'),lambda d:d['experiments'][second]['inputs'].pop('graph-00'),lambda d:d['experiments'][second]['inputs']['graph-00'].update(sha256=sha(b'wrong')),lambda d:d['experiments'][second]['inputs']['environment'].update(path='other'),lambda d:d['families']['f'].update(prior_attempts=1),lambda d:d['datasets']['synthetic-cold'].update(history_reference='erased'),lambda d:d['experiments'][second].update(parent=None)]
for mutate in mutators:
 changed=copy.deepcopy(newreg);mutate(changed)
 try:module._registration_evolution(oldreg,changed,changed['experiments'][second],{'inputs':inputs})
 except ValueError:pass
 else:raise AssertionError('mutation accepted')
# Reuse only fixture assembler for direct real verifier calls, not its expected verdicts.
from test_tree03 import Tests
fixture=Tests()
for mutate in [lambda s:s['diff'].append(('A','unlisted-metadata.json')),lambda s:s['diff'].append(('M','old/registration')),lambda s:s.update(parents='b'*40+' '+'a'*40+' '+'c'*40)]:
 try:fixture.exercise(mutate)
 except ValueError:pass
 else:raise AssertionError('bad tree accepted')
# Tiny helper must refuse missing genuine receipt before loading package or job.
try:module.authenticated_materialization(Path('/nonexistent'),{'path':'wrong'},{'path':'wrong'})
except ValueError:pass
else:raise AssertionError('wrong original receipt paths accepted')
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'status':'source-only-pass','manifest_bodies':len(m['files']),'selected_sources':len(rows),'unchanged_sources':194,'registration_corruptions_refused':len(mutators),'additional_tree_refusals':3,'historical_missing_receipt_refusal':True,'real_native_or_lifecycle_execution':False},indent=2))
