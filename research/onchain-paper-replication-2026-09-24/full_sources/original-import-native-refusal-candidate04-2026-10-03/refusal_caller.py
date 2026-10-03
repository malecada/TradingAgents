"""Source-only actual entrypoint interfaces; the reviewed outer guard must call.

No runtime CLI and no default execution. Root must bind and review the native
release, complete source closure, registrations, watched tree and final parser.
"""
from pathlib import Path
from types import SimpleNamespace
import json
from refusal_cases import PRECLAIM,NAMES,identity,FRAGMENTS

def preclaim(*,root,registration,source,variant):
    """Call real job._admitted without constructing any ResearchRun or fake Binding."""
    if variant not in PRECLAIM:raise ValueError('exact preclaim case required')
    root=Path(root);name=identity(variant)
    paths=[root/'research_runs'/name,root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name]
    if any(p.exists() for p in paths):raise ValueError('preclaim identity already exists')
    from tradingagents.research.onchain_replication import job
    args=SimpleNamespace(root=root,registration=registration,experiment=name,source=source)
    observed=None
    try:job._admitted(args)
    except ValueError as error:
        if type(error) is not ValueError or FRAGMENTS[variant] not in str(error):raise
        observed={'variant':variant,'identity':name,'boundary':'actual job._admitted','exception':'ValueError','message_fragment':FRAGMENTS[variant],'claim_created':False}
    if observed is None:raise AssertionError('registered invalid admission unexpectedly accepted')
    if any(p.exists() for p in paths):raise AssertionError('negative admission created forbidden namespace')
    return observed

def worker_command(*,interpreter,root,registration,source,variant):
    """Actual job launch→monitor→worker vector; no alternate authority command."""
    if variant not in NAMES or variant in PRECLAIM:raise ValueError('exact after-claim case required')
    return [interpreter,'-B','-m','tradingagents.research.onchain_replication.job','--mode','launch','--root',str(root),'--registration',registration,'--experiment',identity(variant),'--source',source]

def terminal(*,root,variant):
    """Supplement to—not replacement for—the selected outer native raw parser."""
    if variant in PRECLAIM or variant not in NAMES:raise ValueError('genuine failed-claim case required')
    from raw_receipts01 import metadata,body,digest,require
    root=Path(root);name=identity(variant);path='research_runs/'+name
    claim=body(root,path+'/claim.json');failed=metadata(root,path+'/failed.json')
    require(not (root/path/'complete.json').exists() and failed['status']=='failed' and failed['experiment_id']==name and failed['claim_sha256']==digest(claim),'negative lifecycle differs')
    require('RefusalObserved' in failed['reason'] and ('registered original-import refusal observed: '+variant) in failed['reason'],'wrong negative terminal cause')
    claim_value=json.loads(claim);expected=set(claim_value['experiment']['outputs'])
    require(expected=={'resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json'} and {p.name for p in (root/path/'outputs').iterdir()}==expected,'negative output membership differs')
    require({name:digest(body(root,path+'/outputs/'+name)) for name in expected}==failed['output_sha256'],'negative lifecycle output hashes differ')
    rows=metadata(root,path+'/outputs/cell-ledger.json');require([r['id'] for r in rows]==['import-target-01','import-target-02'] and all(r['status']=='unavailable' for r in rows),'negative cell disposition differs')
    summary=metadata(root,path+'/outputs/resource-summary.json')
    require(metadata(root,path+'/outputs/resource-binding.json')==summary==metadata(root,path+'/outputs/resource-journal.json'),'negative resource outputs differ')
    require(summary['case']==variant and summary['identity']==name and summary['status']=='observed' and summary['boundary']=={'exception':'ValueError','expected_message_fragment':FRAGMENTS[variant],'observed':True},'negative boundary receipt differs')
    from refusal_evidence import authenticate
    evidence=authenticate(root,variant,claim)
    return {'variant':variant,'claim_sha256':digest(claim),'observed':True,'evidence':evidence,'native_parser_still_required':True}
