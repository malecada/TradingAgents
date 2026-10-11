"""Independent serialized-metadata capacity probe. No native loading or claim."""
import json
from pathlib import Path
from types import SimpleNamespace
from tradingagents.research.onchain_replication import phase_timing as pt, geometry_summary as gs, geometry_publication as gp, matching_owner as mo, batched_numeric_execution as ne
from tests.research.onchain_replication.test_pilot_efficiency_selection import test_complete_compute_retains_commits_and_joins_numeric_score_bodies
from tests.research.onchain_replication.test_matching_reference import graph
root=Path(__file__).parent;fixture=root/'size-fixture';fixture.mkdir()
test_complete_compute_retains_commits_and_joins_numeric_score_bodies(fixture,False,False)
summary=json.loads((fixture/'stream/numeric-batches/000000000000.json').read_bytes())
reference=json.loads((root.parent/'pilot-efficiency-solver-qualification-2026-10-11/RESULTS01.json').read_bytes())
summary.update(compiled_edge_policy=reference['native_policy'],compiled_normalization_policy=reference['normalization_policy'],numeric_kernel_policy=reference['numeric_policy'],edge_cache_policy=dict(format='adaptive-lazy-edge-cache-v1',max_edge_products=16384,chunk_entries=256,max_scratch_bytes=262144))
collector=pt.PhaseTotals()
for name in pt.PHASES:
    collector._phases[name]=dict(calls=10000,failures=0,wall_seconds=123.12345678901234,cpu_seconds=120.12345678901234,bytes=100000)
for name in pt.NUMERIC_COUNTS:collector.add_count(name,100000)
summary['phase_totals']=collector.snapshot();ne.validate_phase_totals(summary['phase_totals'])
timing={'binding_timing_closed':0}|{'binding_'+p+'_'+x:(0 if x=='failures' else 10000) for p in mo._LEASE_TIMING_PHASES for x in ('calls','ns','failures')}
mo.binding_timing_counters(timing);summary['counters'].update(timing)
g=graph([[0.],[1.],[2.]],[]);geometry=gs.Geometry(1536);geometry.begin(0)
for i in range(32):geometry.add(g,g,dict(ordinal=i,mode='computed'))
summary['geometry']=gp.completed(geometry.finish(32,32,0),gp.POLICY,0,32,32,0)
raw=ne.raw(summary)
report=dict(summary_bytes=len(raw),limit=ne.SUMMARY_LIMIT,phase_bytes=len(ne.raw(summary['phase_totals'])),without_phases_bytes=len(ne.raw({k:v for k,v in summary.items() if k!='phase_totals'})),over_limit=len(raw)>ne.SUMMARY_LIMIT)
(root/'SUMMARY_SIZE01.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'SYNTHETIC_SUMMARY01.json').write_bytes(raw)
print(json.dumps(report))
