"""Deterministic Q2 registration assembly; no source capture or financial data."""
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
loader=importlib.util.spec_from_file_location('register_q2_source',HERE/'q2_source.py')
q2=importlib.util.module_from_spec(loader);loader.loader.exec_module(q2)
def digest(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def ref(p):return {'path':p,'sha256':digest(p)}
base='research/defi-depth-2026-09-15/'
gate=json.loads((HERE/'gates-q1.json').read_text())
spec=json.loads((HERE/'q2-spec.json').read_text())
dataset='defi-base-daily-history'
gate['datasets'][dataset]={'identity':'base-fixed-daily-protocol-accounting-source-20230902-20260901',
'history_reference':'Q1 source raw states and overlapping core/DeFi ancestry; full daily panel becomes exposed development on capture. All dates/cohorts retained including absent deployments; no confirmation or oracle execution claim.',
'exposures':[{'start':'2023-09-02T00:00:00Z','end':'2026-09-15T16:33:00Z','state':'exposed'}]}
inputs={'spec':base+'q2-spec.json','phase':base+'phase-grant.json',
'q1_claim':'research_runs/defi-depth-q1-20260915/claim.json',
'q1_source':'research_runs/defi-depth-q1-20260915/outputs/summary.json',
'q1_review':base+'reviews/q1-postexecution-review.md',
'aave_base':base+'documents/aave-base.json',
'core_ancestry':'research/broader-allocation-2026-09-15/ancestry-crosswalk.json',
'defi_ancestry':'research/broader-allocation-2026-09-15/defi-ancestry-crosswalk.json',
'old_closure':'research/broader-allocation-2026-09-15/RESULTS.md'}
sources=[base+'q2_source.py',base+'q2_transport.py',base+'q1_source.py',
'research/broader-allocation-2026-09-15/dex_source.py','research/broader-allocation-2026-09-15/dex_transport.py','uv.lock']
gate['experiments'][q2.EXPERIMENT]={'family':'protocol-state-source','parent':'defi-depth-q1-20260915',
'question':'Does the fixed Base endpoint supply all chronological daily lending/LP state and proxy valuation fields for three fixed365-day cohorts while preserving missing dates and unproved execution/version terms?',
'charter':ref(base+'q2-charter.md'),'stage':'discovery','reuse':'exploratory','selection':None,
'source_files':{p:digest(p) for p in sources},'runtime_hashes':gate['experiments']['defi-depth-q1-20260915']['runtime_hashes'],
'inputs':{k:{**ref(p),'dataset':dataset} for k,p in inputs.items()},
'windows':[{'dataset':dataset,'start':'2023-09-02T00:00:00Z','end':'2026-09-15T16:33:00Z','availability':'existing'}],
'cells':q2.cells_for(spec),'outputs':q2.outputs_for(spec)}
(HERE/'gates-q2.json').write_text(json.dumps(gate,indent=2)+'\n')
print({'cells':len(q2.cells_for(spec)),'outputs':len(q2.outputs_for(spec)),'registered':q2.EXPERIMENT})
