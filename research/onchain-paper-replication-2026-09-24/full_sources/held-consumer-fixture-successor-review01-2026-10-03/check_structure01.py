from pathlib import Path
import json,hashlib,ast,runpy,subprocess,os
D=Path(__file__).parent;F=D.parent;R=F.parents[2];P=F/'neural-cold-feature-handoff-held-consumer-fixture-successor-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((P/'MANIFEST01.json').read_bytes())=='ae5245a5b857bfb4f9a279e39bb4d1ef162185a88fb663c78a5eff7d2214ef5f';m=json.loads((P/'MANIFEST01.json').read_bytes())
for row in m['files']:b=(P/row['path']).read_bytes();assert H(b)==row['sha256'] and len(b)==row['bytes']
sm=json.loads((P/'SOURCE_MAP01.json').read_bytes());assert H((P/'SOURCE_MAP01.json').read_bytes())=='fca3fb5a6db95630e20fce79ae45745fe3d5c485298f8257128333b01d475093'
for row in sm['install_map']:
 old=(P/(row['candidate']+'.baseline')).read_bytes();new=(P/row['candidate']).read_bytes();assert new.startswith(old) and H(old)==row['baseline_sha256'] and H(new)==row['sha256'] and len(new)==row['bytes']
 ot=ast.parse(old);nt=ast.parse(new)
 for n in ot.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef)):assert ast.dump(n)==ast.dump(next(x for x in nt.body if type(x) is type(n) and x.name==n.name))
inv=json.loads((P/'prospective-source-inventory01.json').read_bytes());rows=inv['source_inventory'];assert len(rows)==199 and sum(r['target'].startswith('tradingagents/') for r in rows)==148 and sum(r['bytes'] for r in rows)==3347707
for row in rows:b=(R/row['origin']).read_bytes();assert H(b)==row['sha256'] and len(b)==row['bytes']
comp=json.loads((F/'neural-cold-feature-handoff-held-consumer-root-source-composition02-2026-10-03/SOURCE_COMPOSITION02.json').read_bytes());prior={r['target']:r for r in comp['source_entries']};assert set(prior)=={r['target'] for r in rows};changed={r['target'] for r in rows if r['sha256']!=prior[r['target']]['sha256']};assert changed=={r['target'] for r in sm['install_map']}
B=runpy.run_path(str(P/'capsule_builder01.py'));G=runpy.run_path(str(P/'generate_inputs01.py'));C=Path(comp['source_root']);oldrows=sorted([{'path':r['target'],'sha256':r['sha256'],'bytes':r['bytes']} for r in comp['source_entries']],key=lambda r:r['path'])
actual=B['held_source_plan'](C,comp['actual_199_source_execution_commit'],comp['actual_148_package_anchor'],oldrows);assert actual['source_count']==199 and actual['package_count']==148 and actual['logical_bytes']==3323180
empty=G['held_input_plan']({},actual);assert len(empty['remaining_roles'])==13 and empty['experiment_id'] is None and empty['execution_admitted'] is False and empty['arrays_generated'] is False
try:G['generate_held_arrays']()
except ValueError as e:assert 'guarded' in str(e)
else:raise AssertionError('arrays allowed')
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
tracked=subprocess.check_output(['git','-C',str(C),'ls-tree','-rz',actual['source']],env=env).split(b'\0');assert len([x for x in tracked if x])==204
out={'decision':'WITHHELD_HFS1_HFS2','manifest_bodies':len(m['files']),'original_helpers_full_prefix_and_definition_AST_unchanged':True,'changed_targets':sorted(changed),'prospective_199_source_148_package_bytes':3347707,'actual_existing_source_199_package_148_bytes':actual['logical_bytes'],'actual_existing_Git_tracked':204,'actual_source':actual['source'],'actual_anchor':actual['anchor'],'source_origins':actual['source_origins'],'missing_roles':empty['remaining_roles'],'runtime_readback_performed':False,'no_legacy_graphs_inputs_registration_or_numerical_or_authority_execution':True};(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='source_origins'},indent=2))
