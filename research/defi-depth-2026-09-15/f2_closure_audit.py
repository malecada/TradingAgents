"""Read-only terminal F2 reconciliation; never fills sources or computes PnL."""
import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(root):
    root=Path(root).resolve();run=root/'research_runs/defi-depth-f2-20260915'
    terminal_paths=[run/n for n in ('complete.json','failed.json') if (run/n).exists()]
    if len(terminal_paths)!=1:raise ValueError('exactly one terminal receipt required; never audit active ownership')
    claim_raw=(run/'claim.json').read_bytes();claim=json.loads(claim_raw)
    raw=terminal_paths[0].read_bytes();terminal=json.loads(raw)
    if terminal['claim_sha256']!=sha(claim_raw):raise ValueError('terminal claim hash mismatch')
    outputs={};intents={};receipts={};financial_attempts={};counts=Counter();http=Counter();errors=Counter();keys=set()
    for path in sorted((run/'outputs').iterdir()):
        if not path.is_file():raise ValueError('unexpected output directory')
        raw=path.read_bytes()
        if terminal['output_sha256'].get(path.name)!=sha(raw):raise ValueError('terminal output hash differs')
        obj=json.loads(raw);outputs[path.name]=obj
        if path.name.endswith('-attempt.json'):
            (intents if 'url' in obj else financial_attempts)[obj['id']]=obj
        if path.name.endswith('-receipt.json'):
            receipts[obj['id']]=obj;body=base64.b64decode(obj['body_base64'],validate=True)
            if sha(body)!=obj['body_sha256'] or len(body)!=obj['body_bytes']:raise ValueError('raw body hash/length differs')
            counts['retained_raw_bytes']+=len(body)
            counts['actual_source_requests' if obj['attempted'] else 'suppressed_source_slots']+=1
            if obj['attempted']:
                request=obj['request'];key=json.dumps([request['method'],request['params']],sort_keys=True,separators=(',',':'),allow_nan=False)
                if key in keys:raise ValueError('actual logical request repeated')
                keys.add(key);http[str(obj['http_status'])]+=1
                try:
                    decoded=json.loads(body)
                    if not isinstance(decoded,dict) or decoded.get('id')!=request['id']:
                        counts['invalid_rpc_envelopes']+=1
                    elif 'error' in decoded:errors[json.dumps(decoded['error'],sort_keys=True)]+=1
                except (json.JSONDecodeError,UnicodeDecodeError):counts['non_json_bodies']+=1
    if set(outputs)!=set(terminal['output_sha256']):raise ValueError('terminal output inventory mismatch')
    if set(intents)!=set(receipts):raise ValueError('actual/uncertain attempt has no paired receipt')
    for rid,intent in intents.items():
        receipt=receipts[rid]
        for field in ('id','attempted','request','url','request_utc'):
            if intent[field]!=receipt[field]:raise ValueError('intent/receipt identity mismatch')
    expected=set(claim['experiment']['cells']);cells=terminal.get('cells',[])
    if terminal['status']=='complete':
        if set(outputs)!=set(claim['experiment']['outputs']):raise ValueError('complete run missing declared output')
        if len(cells)!=len(expected) or {r['id'] for r in cells}!=expected:raise ValueError('complete run cell denominator differs')
        counts.update({'complete_cells':sum(r['status']=='complete' for r in cells),
                       'unavailable_cells':sum(r['status']=='unavailable' for r in cells)})
    summary=outputs.get('source-summary.json')
    if summary:
        if summary['rpc_requests']!=counts['actual_source_requests'] or summary['raw_bytes']!=counts['retained_raw_bytes']:
            raise ValueError('source summary resource totals differ from raw receipts')
        dates=[r['date'] for r in summary['price_rows']]
        if len(set(dates))!=len(dates):raise ValueError('duplicate qualified price date')
        counts['qualified_price_dates']=len(dates)
        if summary['status']!='complete' and any(a['attempted'] for a in financial_attempts.values()):
            raise ValueError('financial calculation attempted despite incomplete frozen panel')
    counts.update(outputs=len(outputs),registered_cells=len(expected),source_intent_receipt_pairs=len(intents),
                  financial_attempt_slots=len(financial_attempts),financial_books_attempted=sum(a['attempted'] for a in financial_attempts.values()))
    return {'experiment':claim['experiment_id'],'source':claim['source'],'terminal_status':terminal['status'],
            'started_at':claim['started_at'],'ended_at':terminal['ended_at'],'claim_sha256':sha(claim_raw),
            'terminal_file':terminal_paths[0].name,'terminal_sha256':sha(terminal_paths[0].read_bytes()),
            'counts':dict(counts),'http_status_counts':dict(http),'raw_rpc_errors':dict(errors),
            'source_panel_status':summary['status'] if summary else 'unavailable',
            'source_stop_reason':summary.get('reason') if summary else 'source summary absent',
            'scope':'Terminal hash/raw/request/denominator audit only; no recovered or recomputed financial outcomes'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=audit(args.root);path=Path(args.output)
    with path.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps(result))
