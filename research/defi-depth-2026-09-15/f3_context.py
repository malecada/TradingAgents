"""Terminal-only F1 evidence reuse for F3. No acquisition or financial arithmetic.

Embedded original file bytes are bound to separately registered F1 claim/terminal
hashes. This avoids thousands of redundant runtime input-admission calls without
discarding any original request identity or raw observation.
"""
import base64
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PREFIX='research_runs/defi-depth-f1-20260915/'


def module(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


C=module('f3_prior_f1_context','f1_context.py')
S=module('f3_shared_source','protocol_financial_source.py')
A=module('f3_prior_terminal_audit','protocol_closure_audit.py')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def decode_evidence(packet,claim_raw,terminal_raw):
    if sha(claim_raw)!=packet['f1_claim_sha256'] or sha(terminal_raw)!=packet['f1_terminal_sha256']:
        raise ValueError('F1 registered parent provenance differs')
    if (packet['f1_audit']['claim_sha256']!=sha(claim_raw)
        or packet['f1_audit']['terminal_sha256']!=sha(terminal_raw)):
        raise ValueError('F1 terminal audit provenance differs')
    claim=json.loads(claim_raw);terminal=json.loads(terminal_raw)
    if terminal['status']!='complete' or terminal['claim_sha256']!=sha(claim_raw):
        raise ValueError('F1 complete terminal required')
    expected={i['path']:i['sha256'] for i in claim['inputs'].values()}
    expected.update({PREFIX+'outputs/'+name:h for name,h in terminal['output_sha256'].items()})
    result={}
    for path,encoded in packet['evidence_base64'].items():
        raw=base64.b64decode(encoded,validate=True)
        if path not in expected or sha(raw)!=expected[path]:raise ValueError('embedded bytes not bound to F1 provenance')
        result[path]=json.loads(raw)
    return claim,terminal,result


def reconstruct(packet,claim_raw,terminal_raw,daily_actions,boundary_actions):
    claim,terminal,evidence=decode_evidence(packet,claim_raw,terminal_raw)
    old_design=evidence[claim['inputs']['design']['path']]
    old_packet=evidence[claim['inputs']['source_context']['path']]
    old_context=C.verify_packet(old_packet,old_design)
    prior=set(old_design['prior_request_keys'])
    # Require every declared physical source intent, including suppressed slots.
    attempts=[n for n in claim['experiment']['outputs'] if n.endswith(tuple(f'-try{i}-attempt.json' for i in (1,2,3)))]
    for name in attempts:
        item=evidence[PREFIX+'outputs/'+name];request=item['request']
        key=S.P.Q.request_key(request['method'],request['params'])
        if key!=item['logical_key'] or name!=item['id']+'-attempt.json' or type(item['attempted']) is not bool:
            raise ValueError('F1 attempt key or identity differs')
        if item['attempted']:prior.add(key)
    summary=evidence[PREFIX+'outputs/source-summary.json']
    if summary['endpoint_stop']:raise ValueError('inherited F1 endpoint stop cannot be bypassed')
    reported=packet['f1_audit']['counts']
    if reported['actual_physical_requests']!=summary['physical_requests'] or reported['retained_raw_bytes']!=summary['raw_bytes']:
        raise ValueError('F1 audit/source resource totals differ')
    context={};owners={}
    def receipt(logical,row):
        slot=row['successful_physical_slot'];rid=f'{logical}-try{slot}'
        value=evidence[PREFIX+'outputs/'+rid+'-receipt.json']
        if value['id']!=rid or value['logical_id']!=logical or value['attempted'] is not True:
            raise ValueError('retained successful physical receipt identity differs')
        return value
    for day in old_design['days']:
        date=day['date'];saved=evidence[PREFIX+'outputs/'+date+'-source.json']
        cells={r['id']:r for r in saved['cells']};out={};owner={};old_owner=old_design['ownership'][date]
        h=cells[date+'-actual-clock']
        if h['status']=='complete':
            if old_owner['header']=='retained':header=old_context[date]['header']
            else:header=C.header_from_receipt(day,receipt(date+'-header',h))
            if header!=h['value']:raise ValueError('F1 raw/derived shared header differs')
            out['header']=header;owner['header']='retained'
        else:owner.update(header='unavailable',header_unavailable_reason='Inherited F1 actual-clock source unavailable')
        p=cells[date+'-oracle-prices']
        if p['status']=='complete':
            if 'header' not in out:raise ValueError('retained price has no qualified shared header')
            if old_owner['prices']=='retained':prices=old_context[date]['prices']
            else:
                r=receipt(date+'-oracle-prices',p);request=r['request']
                expected=[{'to':S.F2.ORACLE,'data':S.F2.encode_prices(['ETH','USDC'])},
                          {'blockHash':out['header']['hash'],'requireCanonical':True}]
                if r['url']!='https://mainnet.base.org' or request['method']!='eth_call' or request['params']!=expected:
                    raise ValueError('retained F1 oracle action differs')
                value=S.F2.parse_prices(S.P.Q._raw_envelopes(r)[request['id']]['result'],['ETH','USDC'])
                prices={'block_hash':out['header']['hash'],'prices_atoms_1e8':value}
            if prices['prices_atoms_1e8']!=p['value']:raise ValueError('F1 raw/derived shared prices differ')
            out['prices']=prices;owner['prices']='retained'
        else:owner.update(prices='unavailable',prices_unavailable_reason='Inherited F1 overlapping prices unavailable')
        owner['fields']={};actions=daily_actions+(boundary_actions if date in S.BOUNDARIES else [])
        for action in actions:
            key=action['key']
            if key not in ('usdc-decimals','usdc-code'):
                if 'header' in out:
                    tag={'blockHash':out['header']['hash'],'requireCanonical':True}
                    params=[{'to':action['to'],'data':action['data']},tag] if action['method']=='eth_call' else [action['to'],tag]
                    if S.P.Q.request_key(action['method'],params) in prior:
                        raise ValueError('purported new LP action overlaps prior actual/uncertain key')
                owner['fields'][key]='new';continue
            row=cells[date+'-'+key]
            if row['status']!='complete':owner['fields'][key]='unavailable';continue
            r=receipt(date+'-'+key,row);request=r['request'];tag={'blockHash':out['header']['hash'],'requireCanonical':True}
            params=[{'to':action['to'],'data':action['data']},tag] if action['method']=='eth_call' else [action['to'],tag]
            if r['url']!='https://mainnet.base.org' or request['method']!=action['method'] or request['params']!=params:
                raise ValueError('retained F1 USDC witness action differs')
            parsed=S.P.Q.old.parse_action(S.P.Q._raw_envelopes(r)[request['id']]['result'],action)
            if parsed!=row['value']:raise ValueError('F1 raw/derived USDC witness differs')
            out.setdefault('fields',{})[key]={'block_hash':out['header']['hash'],'action':action,'value':parsed}
            owner['fields'][key]='retained'
        context[date]=out;owners[date]=owner
    return context,owners,sorted(prior),old_design


def prepare(root,daily_actions,boundary_actions):
    root=Path(root).resolve();audit=A.audit(root,'defi-depth-f1-20260915')
    if audit['structural']['status']!='complete':raise ValueError('complete terminal F1 publication required')
    claim_raw=(root/PREFIX/'claim.json').read_bytes();terminal_raw=(root/PREFIX/'complete.json').read_bytes()
    claim=json.loads(claim_raw)
    paths={claim['inputs'][key]['path'] for key in ('design','source_context')}
    paths.add(PREFIX+'outputs/source-summary.json')
    for name in claim['experiment']['outputs']:
        if name.endswith(tuple(f'-try{i}-attempt.json' for i in (1,2,3))) or name.endswith('-source.json'):
            paths.add(PREFIX+'outputs/'+name)
    # Only successful shared getters need raw-response reuse; all intents still
    # enter the exclusion union. Unavailable source observations stay unavailable.
    for path in sorted(paths):
        if not path.endswith('-source.json'):continue
        obj=json.loads((root/path).read_bytes())
        for row in obj['cells']:
            cid=row['id']
            if row['status']!='complete' or 'successful_physical_slot' not in row:continue
            if cid.endswith(('-actual-clock','-oracle-prices','-usdc-decimals','-usdc-code')):
                logical=cid.removesuffix('-actual-clock')+'-header' if cid.endswith('-actual-clock') else cid
                paths.add(PREFIX+'outputs/'+logical+f"-try{row['successful_physical_slot']}-receipt.json")
    packet={'f1_claim_sha256':sha(claim_raw),'f1_terminal_sha256':sha(terminal_raw),'f1_audit':audit,
            'evidence_base64':{p:base64.b64encode((root/p).read_bytes()).decode() for p in sorted(paths)}}
    context,owners,prior,old_design=reconstruct(packet,claim_raw,terminal_raw,daily_actions,boundary_actions)
    return packet,context,owners,prior,old_design


def verify_packet(packet,design,claim_raw,terminal_raw):
    context,owners,prior,old_design=reconstruct(packet,claim_raw,terminal_raw,design['daily_actions'],design['boundary_actions'])
    if owners!=design['ownership'] or prior!=design['prior_request_keys'] or old_design['days']!=design['days']:
        raise ValueError('F3 ownership/calendar/exclusion differs from terminal reconstruction')
    if S.O.price_fields(prior)!=design['price_field_history']:raise ValueError('F3 semantic price history differs')
    return context
