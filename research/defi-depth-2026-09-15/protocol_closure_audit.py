"""Terminal-only physical-request reconciliation for F1/F3; no recomputed PnL."""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
from tradingagents.research.verify import verify_run


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(root,experiment):
    if experiment not in ('defi-depth-f1-20260915','defi-depth-f3-20260915'):
        raise ValueError('fixed financial experiment required')
    root=Path(root).resolve();run=root/'research_runs'/experiment
    structural=verify_run(run)
    terminal_name='complete.json' if structural['status']=='complete' else 'failed.json'
    terminal=json.loads((run/terminal_name).read_text());claim=json.loads((run/'claim.json').read_text())
    intents={};receipts={};financial={};logical={};keys={};counts=Counter();statuses=Counter()
    for path in sorted((run/'outputs').iterdir()):
        if path.name.endswith('-attempt.json'):
            obj=json.loads(path.read_bytes())
            target=intents if 'url' in obj else financial
            if obj['id'] in target:raise ValueError('duplicate attempt identity')
            target[obj['id']]=obj
        elif path.name.endswith('-receipt.json'):
            obj=json.loads(path.read_bytes())
            if obj['id'] in receipts:raise ValueError('duplicate receipt identity')
            receipts[obj['id']]=obj
    for rid,intent in intents.items():
        request=intent['request'];key=json.dumps([request['method'],request['params']],sort_keys=True,separators=(',',':'),allow_nan=False)
        if key!=intent['logical_key']:raise ValueError('literal logical key differs')
        slot=intent['physical_slot'];lid=intent['logical_id']
        if type(slot) is not int or slot not in (1,2,3) or rid!=f'{lid}-try{slot}':raise ValueError('physical slot identity differs')
        if request.get('id')!=rid or request.get('jsonrpc')!='2.0':raise ValueError('request envelope identity differs')
        if type(intent['attempted']) is not bool:raise ValueError('literal attempted Boolean required')
        if lid in logical and logical[lid]['key']!=key:raise ValueError('retry changed logical request')
        item=logical.setdefault(lid,{'key':key,'slots':set(),'actual':[]})
        if slot in item['slots']:raise ValueError('duplicate physical slot')
        item['slots'].add(slot)
        if intent['attempted']:
            if key in keys and keys[key]!=lid:raise ValueError('same actual/uncertain key repeated under another logical ID')
            keys[key]=lid;item['actual'].append(slot);counts['actual_or_uncertain_physical_requests']+=1
        if rid not in receipts:
            if structural['status']=='complete':raise ValueError('complete source intent has no receipt')
            counts['uncertain_actual_requests' if intent['attempted'] else 'unpaired_suppressed_intents']+=1
            continue
        receipt=receipts[rid]
        for field in ('id','logical_id','logical_key','physical_slot','attempted','request','url','request_utc','max_response_bytes'):
            if receipt[field]!=intent[field]:raise ValueError('intent/receipt identity mismatch')
        body=base64.b64decode(receipt['body_base64'],validate=True)
        if sha(body)!=receipt['body_sha256'] or len(body)!=receipt['body_bytes']:raise ValueError('raw body hash/length differs')
        if len(body)>intent['max_response_bytes']:raise ValueError('retained raw prefix exceeds registered bound')
        counts['retained_raw_bytes']+=len(body)
        if intent['attempted']:
            counts['actual_physical_requests']+=1
            statuses[str(receipt['http_status'])]+=1
        else:
            counts['suppressed_physical_slots']+=1
            if body:raise ValueError('unattempted slot contains network response bytes')
    if set(receipts)-set(intents):raise ValueError('receipt lacks durable intent')
    if structural['status']=='complete' and any(v['slots']!={1,2,3} for v in logical.values()):
        raise ValueError('complete run missing physical slots')
    for item in logical.values():
        if sorted(item['actual'])!=list(range(1,len(item['actual'])+1)):
            raise ValueError('actual retry slots are not a consecutive prefix')
    source_path=run/'outputs/source-summary.json'
    source=json.loads(source_path.read_bytes()) if source_path.exists() else None
    if source:
        if source['physical_requests']!=counts['actual_physical_requests'] or source['raw_bytes']!=counts['retained_raw_bytes']:
            raise ValueError('source totals differ from physical receipts')
        dates=[r['date'] for r in source['rows']]
        if len(set(dates))!=len(dates):raise ValueError('duplicate source calendar date')
        counts['qualified_daily_rows']=sum(r['daily_source_complete'] for r in source['rows'])
        counts['qualified_price_rows']=sum(r['block'] is not None and r['oracle_prices']['status']=='complete' for r in source['rows'])
    counts.update(logical_source_slots=len(logical),actual_unique_logical_keys=len(keys),
                  physical_intents=len(intents),physical_receipts=len(receipts),
                  financial_attempt_slots=len(financial),financial_attempts=sum(x['attempted'] for x in financial.values()))
    registered=claim['experiment'];published={p.name for p in (run/'outputs').iterdir()}
    declared_slots={name for name in registered['outputs'] if name.endswith(tuple(f'-try{i}-attempt.json' for i in (1,2,3)))}
    counts.update(registered_cells=len(registered['cells']),registered_outputs=len(registered['outputs']),
                  registered_physical_slots=len(declared_slots),unpublished_outputs=len(set(registered['outputs'])-published),
                  physical_slots_without_intent=len(declared_slots-published))
    return {'experiment':experiment,'structural':structural,'source':claim['source'],
            'started_at':claim['started_at'],'ended_at':terminal['ended_at'],
            'claim_sha256':sha((run/'claim.json').read_bytes()),'terminal_sha256':sha((run/terminal_name).read_bytes()),
            'counts':dict(counts),'http_status_counts':dict(statuses),
            'actual_or_uncertain_request_keys':sorted(keys),
            'source_panel_status':source['status'] if source else 'unavailable',
            'endpoint_stop':source['endpoint_stop'] if source else 'terminal source summary absent',
            'scope':'Hash, raw, physical retry and denominator reconciliation only; no financial recomputation'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--experiment',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();result=audit(a.root,a.experiment)
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
