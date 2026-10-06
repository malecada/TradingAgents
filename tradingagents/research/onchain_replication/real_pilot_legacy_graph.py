"""Fixed June13 legacy-component joins inside the genuine resource pilot.

No capability factory, data loader, new graph publication or parent-status upgrade.
"""
import hashlib
import json
from .graph_legacy_coverage import EVIDENCE, KIND, verify_legacy_coverage

GRAPH_KEY='0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba'
COVERAGE_ROLE='legacy_graph_evidence'
COVERAGE_PATH='research/onchain-paper-replication-2026-09-24/full_sources/real-data-end-to-end-pilot-preparation01-2026-10-05/LEGACY_GRAPH_EVIDENCE_DRAFT01.json'
COVERAGE_SHA='3153c0bb910cef6a47caa5e00cd52ea0efed25ce970981cdd0090ccbd6cd7dfa'

def require(value,message):
    if not value:raise ValueError('June13 protected component: '+message)

def registered(inputs,mapping):
    """Pure selection validation; neither admission nor Owner authority."""
    require(type(mapping) is dict and GRAPH_KEY in mapping,'fixed graph absent')
    role=mapping[GRAPH_KEY]
    require(type(role) is str and role in inputs,'target manifest role missing')
    expected={**{'legacy_'+name:ref for name,ref in EVIDENCE.items()},
              COVERAGE_ROLE:{'path':COVERAGE_PATH,'sha256':COVERAGE_SHA}}
    for name,ref in expected.items():
        require(name in inputs and all(inputs[name].get(k)==v for k,v in ref.items()),
                'original registered role differs: '+name)
    require(all(inputs[role].get(k)==v for k,v in EVIDENCE['graph_manifest'].items()),
            'target manifest is not the original completed component')
    return set(expected)

def verify(run,graph,manifest_role):
    """Existing legacy validator consumes actual run.read_input before Owner birth."""
    from tradingagents.research.lifecycle import ResearchRun
    require(type(run) is ResearchRun,'genuine ResearchRun required')
    run._active();run._check_source()
    from .contracts import GraphSnapshot
    require(type(graph) is GraphSnapshot,'actual loaded GraphSnapshot required')
    registered(run.admission.inputs,{GRAPH_KEY:manifest_role})
    raw=run.read_input(manifest_role)
    require(hashlib.sha256(raw).hexdigest()==EVIDENCE['graph_manifest']['sha256']
            and json.loads(raw)['graph_hash']==GRAPH_KEY,'original graph identity differs')
    proof=json.loads(run.read_input(COVERAGE_ROLE))
    require(proof=={'schema_version':2,'kind':KIND,'roles':{k:'legacy_'+k for k in EVIDENCE}},
            'fixed coverage selection differs')
    result=verify_legacy_coverage(proof,graph,EVIDENCE['graph_manifest']['sha256'],run.read_input)
    require(result['parent_status']=='failed' and result['graph_cell_status']=='complete'
            and result['modern_producer_plan_present'] is False,'legacy distinctions differ')
    run._active();run._check_source()
    return result
