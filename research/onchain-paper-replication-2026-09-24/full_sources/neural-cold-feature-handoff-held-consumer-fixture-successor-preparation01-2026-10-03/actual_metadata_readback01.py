"""Read-only genuine source objects; no admission or numerical input generation."""
import hashlib,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-02/source')
ref=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-consumer-root-source-composition02-2026-10-03/SOURCE_COMPOSITION02.json'
r=json.loads(ref.read_bytes());rows=[{'path':x['target'],'sha256':x['sha256'],'bytes':x['bytes']} for x in r['source_entries']];rows.sort(key=lambda x:x['path'])
b=runpy.run_path(str(P/'capsule_builder01.py'));g=runpy.run_path(str(P/'generate_inputs01.py'))
s=b['held_source_plan'](C,r['actual_199_source_execution_commit'],r['actual_148_package_anchor'],rows)
plan=g['held_input_plan']({},s)
result={'status':'PASS_ACTUAL_SOURCE_METADATA_ONLY','source':s,'input_plan':plan,'source_composition_reference':{'path':str(ref),'sha256':hashlib.sha256(ref.read_bytes()).hexdigest()},'candidate_not_installed':True,'actual_runtime_and_empirical_input_reads':False}
(P/'ACTUAL_METADATA_READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'sources':s['source_count'],'package':s['package_count'],'source_bytes':s['logical_bytes'],'source_commit':s['source'],'anchor':s['anchor'],'missing_metadata_roles':plan['remaining_roles'],'execution_admitted':False}))
