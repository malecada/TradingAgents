"""Actual source/registration metadata only; no claims or package imports."""
import ast,importlib.util,json
from pathlib import Path
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('helper',P/'held_failure01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
template=P.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json';release=m.parse(template.read_bytes());r=m.Reader(release['capsule_root']);reg=m.sources(r,release);exp=reg['experiments'][m.IDENTITY]
assert len(exp['inputs'])==33 and len(exp['outputs'])==6
inputs={name:{'path':ref['path'],'sha256':m.sha(m.input_body(r,exp,name))} for name,ref in sorted(exp['inputs'].items())}
sources={}
for name in ('compact_mcm','compact_mcm_publication','resource_fixture','held_score_consumer','feature_journal'):
 path='tradingagents/research/onchain_replication/'+name+'.py';raw=r.body(path);sources[path]={'sha256':m.sha(raw),'bytes':len(raw)}
 if name=='compact_mcm':
  text=raw.decode();assert text.index('stream_terminal = stream.finish()')<text.index('held_score_consumer.consume(')<text.index('stage_ref = owner._finish_stage(')<text.index('ticket = publication._publish(')
 if name=='compact_mcm_publication':
  text=raw.decode();assert text.index('publication_boundary(owner,stage)')<text.index('attempt.mkdir()')
 if name=='held_score_consumer':assert "run.write_json(output,observation)" in raw.decode()
try:r.body('research_runs/'+m.IDENTITY+'/failed.json')
except FileNotFoundError:actual_outcome='absent'
else:raise ValueError('Unexpected actual outcome; stop metadata-only preparation')
r.recheck()
result={'status':'readonly-source-order-and-registration-checked','current_source':m.SOURCE,'actual_outcome':actual_outcome,'inputs':inputs,'source_evidence':sources,'registered_outputs':exp['outputs'],'helper_sha256':m.sha((P/'held_failure01.py').read_bytes()),'source_order':'both held receipts and both stages precede second publication boundary; second Produced complete and output namespace absent','authority_granted':False}
(P/'METADATA_READBACK04.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print('PASS: actual205 Git/source bodies,33 opaque inputs,6 outputs and source call order; actual failure absent')
