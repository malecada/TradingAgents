"""Terminal-only retained-source/first-owner preparation for the new F1 recipe.

Read-only reconstruction. Does not request sources or calculate economic results.
The caller must register exact resulting context and evidence references.
"""
import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

S=module('f1_context_source_policy','financial_source_policy.py')
F2=module('f1_context_frozen_f2','f2_source.py')
A=module('f1_context_terminal_audit','f2_closure_audit.py')
O=module('f1_context_field_ownership','source_ownership.py')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def verify_registered_evidence(packet,read_input):
    """Bind embedded receipt/proof values to the separately registered raw files."""
    evidence={}
    for i,ref in enumerate(packet['evidence_refs']):
        raw=read_input(f'ownership_evidence_{i:04d}')
        if sha(raw)!=ref['sha256']:raise ValueError('registered ownership evidence hash differs')
        if ref['path'] in evidence:raise ValueError('duplicate ownership evidence path')
        evidence[ref['path']]=json.loads(raw)
    for item in packet['days'].values():
        for name,refname in (('header_receipt','header_ref'),('price_receipt','price_ref'),
                             ('suppressed_header_intent','header_intent_ref'),('suppressed_price_intent','price_intent_ref')):
            if name in item and item[name]!=evidence[item[refname]['path']]:
                raise ValueError('embedded ownership evidence differs from registered raw file')
    claim=packet['f2_claim_ref'];terminal=packet['f2_terminal_ref'];audit=packet['f2_audit']
    if claim['sha256']!=audit['claim_sha256'] or terminal['sha256']!=audit['terminal_sha256']:
        raise ValueError('audited terminal provenance differs')
    if evidence[terminal['path']]['claim_sha256']!=claim['sha256']:
        raise ValueError('registered F2 terminal belongs to another claim')
    if 'f2_contract' in packet:
        original=evidence[claim['path']]
        if packet['f2_contract']!=original['experiment']:
            raise ValueError('embedded F2 contract differs from registered claim')
        design_ref=original['inputs']['design']
        if packet['f2_design']!=evidence[design_ref['path']]:
            raise ValueError('embedded F2 design differs from registered raw design')


def header_from_receipt(day,receipt):
    request=receipt['request']
    if receipt['attempted'] is not True or receipt['url']!='https://mainnet.base.org':raise ValueError('retained header not actually acquired from fixed endpoint')
    if request['method']!='eth_getBlockByNumber' or request['params']!=[hex(day['candidate_block']),False]:
        raise ValueError('retained header request differs from fixed left height')
    raw=S.Q._raw_envelopes(receipt)[request['id']]['result']
    return S.actual_clock_header(raw,day,datetime.fromisoformat(receipt['retrieval_utc']).timestamp())


def prices_from_receipt(day,header,receipt):
    if receipt['attempted'] is not True or receipt['url']!='https://mainnet.base.org':raise ValueError('retained oracle request not actually acquired')
    request=receipt['request'];assets=['ETH','USDC'] if day['date'] in F2.RETAINED else ['WST','ETH','USDC']
    expected=[{'to':F2.ORACLE,'data':F2.encode_prices(assets)},{'blockHash':header['hash'],'requireCanonical':True}]
    if request['method']!='eth_call' or request['params']!=expected:raise ValueError('retained F2 oracle action/block/vector differs')
    value=F2.parse_prices(S.Q._raw_envelopes(receipt)[request['id']]['result'],assets)
    return {'block_hash':header['hash'],'prices_atoms_1e8':{a:value[a] for a in ('ETH','USDC')}}


def verify_packet(packet,design):
    """Reparse raw retained bodies before F1 use; no caller true flag substitutes."""
    previous=set(packet['prior_request_keys'])
    if sorted(previous)!=design['prior_request_keys']:raise ValueError('source exclusion inventory differs')
    if O.price_fields(previous)!=design['price_field_history']:raise ValueError('source semantic exclusion inventory differs')
    null_mapping=None
    if any(item.get(key,{}).get('request','absent') is None for item in packet['days'].values()
           for key in ('suppressed_header_intent','suppressed_price_intent')):
        if not isinstance(packet.get('f2_design'),dict) or not isinstance(packet.get('f2_contract'),dict):
            raise ValueError('null suppression needs frozen F2 contract provenance')
        frozen=packet['f2_design'];contract=packet['f2_contract']
        cells,outputs=F2.manifests(frozen)
        if cells!=contract['cells'] or outputs!=contract['outputs']:
            raise ValueError('F2 frozen suppression manifest differs')
        for name in ('f2_source.py','q3_protocol.py'):
            path='research/defi-depth-2026-09-15/'+name
            if sha((HERE/name).read_bytes())!=contract['source_files'][path]:
                raise ValueError('F2 frozen null-suppression source mapping differs')
        null_mapping={d['date']:d for d in frozen['days']}
    def null_proved(proof,day):
        return (null_mapping is not None and null_mapping.get(day['date'])==day
                and proof['id']+'-attempt.json' in packet['f2_contract']['outputs']
                and proof['id']+'-receipt.json' in packet['f2_contract']['outputs']
                and proof.get('request','absent') is None and isinstance(proof.get('reason'),str)
                and bool(proof['reason']))
    context={}
    for day in design['days']:
        d=day['date'];item=packet['days'][d];owner=design['ownership'][d];out={}
        if owner['header']=='retained':
            out['header']=header_from_receipt(day,item['header_receipt'])
            if out['header']!=item['header']:raise ValueError('raw/derived retained header differs')
        elif owner['header']=='new':
            proof=item['suppressed_header_intent']
            expected=F2.q.member(d+'-header-left','eth_getBlockByNumber',[hex(day['candidate_block']),False])
            expected_key=S.Q.request_key(expected['method'],expected['params'])
            if (proof.get('attempted') is not False or proof.get('id')!=expected['id']
                or proof.get('url')!='https://mainnet.base.org'
                or (proof.get('request')!=expected and not null_proved(proof,day)) or expected_key in previous):
                raise ValueError('new-header first-acquisition proof differs')
        elif owner['header']!='unavailable':raise ValueError('invalid header owner')
        if owner['prices']=='retained':
            out['prices']=prices_from_receipt(day,out['header'],item['price_receipt'])
            if out['prices']!=item['prices']:raise ValueError('raw/derived retained prices differ')
        elif owner['prices']=='new':
            proof=item['suppressed_price_intent']
            assets=['ETH','USDC'] if d in F2.RETAINED else ['WST','ETH','USDC']
            action={'to':F2.ORACLE,'data':F2.encode_prices(assets)}
            tags=[None]
            if 'header' in out:tags.append({'blockHash':out['header']['hash'],'requireCanonical':True})
            expected=[F2.q.member(d+'-oracle-prices','eth_call',[action,tag]) for tag in tags]
            if (proof.get('attempted') is not False or proof.get('id')!=d+'-oracle-prices'
                or proof.get('url')!='https://mainnet.base.org'
                or (proof.get('request') not in expected and not null_proved(proof,day))):
                raise ValueError('new-price first-acquisition proof differs')
            if 'header' in out:O.assert_new_price_fields(out['header']['hash'],[F2.TOKENS[a] for a in ('ETH','USDC')],design['price_field_history'])
        elif owner['prices']!='unavailable':raise ValueError('invalid price owner')
        context[d]=out
    return context


def prepare(root,days):
    root=Path(root).resolve();audit=A.audit(root)
    if audit['terminal_status']!='complete':raise ValueError('F1 preparation requires independently reconcilable terminal F2 publication')
    run=root/'research_runs/defi-depth-f2-20260915';terminal=json.loads((run/'complete.json').read_text())
    claim=json.loads((run/'claim.json').read_text())
    evidence={}
    def read_ref(path):
        raw=(root/path).read_bytes()
        evidence[path]=sha(raw)
        return json.loads(raw),{'path':path,'sha256':sha(raw)}
    prior,prior_ref=read_ref('research/defi-depth-2026-09-15/f2-attempt-history.json')
    prior_keys=set(prior['all_base_request_keys']);attempt_refs=[]
    # The original F2 metadata inventory itself was frozen as a registered input.
    if claim['experiment']['inputs']['attempt_history']['sha256']!=prior_ref['sha256']:
        raise ValueError('F2 inherited attempted-key inventory changed')
    reconstructed=set()
    for ref in prior['attempt_files']:
        obj,actual=read_ref(ref['path'])
        if actual['sha256']!=ref['sha256']:raise ValueError('inherited actual/uncertain attempt metadata changed')
        requests=obj['request'] if isinstance(obj['request'],list) else [obj['request']]
        keys=[S.Q.request_key(r['method'],r['params']) for r in requests]
        if keys!=ref['request_keys']:raise ValueError('inherited intent key mapping differs')
        if obj.get('url')!='https://mainnet.base.org':raise ValueError('prior Base exclusion came from another endpoint')
        reconstructed.update(keys)
    if reconstructed!=prior_keys:raise ValueError('inherited global request exclusion union differs')
    headers={key for key in reconstructed if json.loads(key)[0]=='eth_getBlockByNumber'}
    if not set(prior['base_header_keys'])<=headers:raise ValueError('inherited narrower header inventory differs')
    for path in sorted((run/'outputs').glob('*-attempt.json')):
        obj=json.loads(path.read_text())
        if not obj.get('url'):continue
        if obj['attempted']:
            request=obj['request'];prior_keys.add(S.Q.request_key(request['method'],request['params']))
        attempt_refs.append({'path':str(path.relative_to(root)),'sha256':sha(path.read_bytes())})
        evidence[str(path.relative_to(root))]=sha(path.read_bytes())
    packet={'f2_audit':audit,'f2_claim_ref':{'path':str((run/'claim.json').relative_to(root)),'sha256':sha((run/'claim.json').read_bytes())},
            'f2_terminal_ref':{'path':str((run/'complete.json').relative_to(root)),'sha256':sha((run/'complete.json').read_bytes())},
            'prior_history_ref':prior_ref,'f2_source_attempt_refs':attempt_refs,'prior_request_keys':sorted(prior_keys),
            'inherited_endpoint_stop':json.loads((run/'outputs/source-summary.json').read_text())['stopped'],
            'days':{}}
    frozen,frozen_ref=read_ref(claim['inputs']['design']['path'])
    if frozen_ref['sha256']!=claim['inputs']['design']['sha256']:raise ValueError('original F2 design hash differs')
    packet.update(f2_contract=claim['experiment'],f2_design=frozen)
    owners={}
    for day in days:
        d=day['date'];item={};owner={}
        if d in F2.RETAINED:
            path=f'research_runs/defi-depth-q3-20260915/outputs/base-{d}-header-left-receipt.json'
            receipt,ref=read_ref(path)
            if claim['experiment']['inputs'][d+'-header-left']['sha256']!=ref['sha256']:raise ValueError('F2 retained Q3 raw header changed')
            item.update(header_receipt=receipt,header_ref=ref,header=header_from_receipt(day,receipt));owner['header']='retained'
        else:
            intent,intent_ref=read_ref(f'research_runs/defi-depth-f2-20260915/outputs/{d}-header-left-attempt.json')
            item['header_intent_ref']=intent_ref
            if intent['attempted']:
                receipt,ref=read_ref(f'research_runs/defi-depth-f2-20260915/outputs/{d}-header-left-receipt.json')
                try:
                    header=header_from_receipt(day,receipt)
                    item.update(header_receipt=receipt,header_ref=ref,header=header);owner['header']='retained'
                except (ValueError,TypeError,KeyError) as exc:
                    owner.update(header='unavailable',header_unavailable_reason='Inherited actual header unavailable: '+str(exc))
            else:
                item['suppressed_header_intent']=intent;owner.update(header='new',first_header_acquisition_proved=True)
        intent,intent_ref=read_ref(f'research_runs/defi-depth-f2-20260915/outputs/{d}-oracle-prices-attempt.json')
        item['price_intent_ref']=intent_ref
        if intent['attempted']:
            receipt,ref=read_ref(f'research_runs/defi-depth-f2-20260915/outputs/{d}-oracle-prices-receipt.json')
            try:
                values=prices_from_receipt(day,item['header'],receipt)
                item.update(price_receipt=receipt,price_ref=ref,prices=values);owner['prices']='retained'
            except (ValueError,TypeError,KeyError) as exc:
                owner.update(prices='unavailable',prices_unavailable_reason='Inherited actual price field unavailable: '+str(exc))
        else:
            item['suppressed_price_intent']=intent;owner.update(prices='new',first_overlapping_price_fields_proved=True)
        owners[d]=owner;packet['days'][d]=item
    for path in ('research_runs/defi-depth-f2-20260915/claim.json',
                 'research_runs/defi-depth-f2-20260915/complete.json',
                 'research_runs/defi-depth-f2-20260915/outputs/source-summary.json'):
        read_ref(path)
    packet['evidence_refs']=[{'path':p,'sha256':h} for p,h in sorted(evidence.items())]
    return packet,owners
