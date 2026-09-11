"""Independent actual source, representative selection and Fraction fee audit."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from datetime import datetime,timezone
from collections import Counter
from urllib.parse import urlencode
import base64,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[3];REV=Path(__file__).resolve().parent;RUN=ROOT/'research_runs/options-entry-20260911';OUT=RUN/'outputs';DAY=86400000

def sha(raw):return hashlib.sha256(raw).hexdigest()
def pairs(rows):
 d={}
 for k,v in rows:assert k not in d;d[k]=v
 return d

def loads(raw):return json.loads(raw,object_pairs_hook=pairs,parse_float=Decimal,parse_constant=lambda _:(_ for _ in ()).throw(AssertionError('nonfinite JSON')))
def read(path):return loads(path.read_bytes())
def dec(value,positive=True):
 assert not isinstance(value,bool) and isinstance(value,(str,int,Decimal)) and len(str(value))<=64
 v=Decimal(str(value));assert v.is_finite() and -32<=v.adjusted()<=32 and (v>0 if positive else v>=0);return Fraction(v)
def clock(value):assert type(value) is int and 0<value<=2**63-1;return value

def payload(r):
 raw=base64.b64decode(r['body_base64'],validate=True);assert len(raw)==r['body_bytes'] and sha(raw)==r['body_sha256']
 assert r['attempted'] is True and r['body_complete'] is True and type(r['http_status']) is int and r['http_status']==200 and r['error'] is None
 return loads(raw)

claim=read(RUN/'claim.json');done=read(RUN/'complete.json');capture=read(OUT/'capture.json');entry=read(OUT/'entry.json');summary=read(OUT/'summary.json')
assert claim['source']=='b46f06a095ab7c8bbf712372780c884abec2663c'
assert done['claim_sha256']==sha((RUN/'claim.json').read_bytes()) and done['cell_count']==15 and done['unavailable_count']==0
assert claim['experiment']['cells']==[x['id'] for x in done['cells']] and all(x['status']=='complete' for x in done['cells'])
assert set(done['output_sha256'])==set(claim['experiment']['outputs'])=={p.name for p in OUT.iterdir()} and len(done['output_sha256'])==10
outputbytes=0
for name,h in done['output_sha256'].items():raw=(OUT/name).read_bytes();assert sha(raw)==h;outputbytes+=len(raw)
assert outputbytes<12*1024**2
for item in claim['inputs'].values():assert sha((ROOT/item['path']).read_bytes())==item['sha256']
for path,h in claim['experiment']['source_files'].items():assert sha(subprocess.check_output(['git','show',claim['source']+':'+path],cwd=ROOT))==h
assert sha(subprocess.check_output(['git','show',claim['source']+':'+claim['registration']],cwd=ROOT))==claim['registration_sha256']
parent=read(ROOT/claim['inputs']['metadata_receipt']['path']);aggregate=read(ROOT/claim['inputs']['metadata_capture']['path']);admit=read(ROOT/claim['inputs']['metadata_admission']['path'])
assert [x for x in aggregate['requests'] if x['id']==parent['id']]==[parent]
meta=payload(parent);norm=next(x for x in admit['cells'] if x['id']==parent['id'])
assert len(meta['optionSymbols'])==norm['symbol_count']==len(norm['normalized_symbol_rows'])
assert all(r['row_index']==i and r['raw_fields']==meta['optionSymbols'][i] for i,r in enumerate(norm['normalized_symbol_rows']))
assert norm['optionContracts']['literal_value']==meta['optionContracts']
spec=read(ROOT/claim['inputs']['request_spec']['path']);assert spec==capture['request_spec']
raws={};receipts={};previous=None;clockreport={}
assert len(capture['receipts'])==7
for template,ref in zip(spec['requests'],capture['receipts']):
 r=read(OUT/ref['path']);assert r['id']==template['id']==ref['id'] and sha((OUT/ref['path']).read_bytes())==ref['receipt_sha256']
 for k in ('body_sha256','body_bytes','request_url','request_utc','retrieval_utc','attempted'):assert r[k]==ref[k]
 assert r['endpoint']==template['endpoint'] and r['kind']==template['kind']
 if template['kind'] in ('time','index'):
  assert r['parameters']==template['parameters'] and r['request_url']==r['endpoint']+('?' + urlencode(template['parameters']) if template['parameters'] else '')
 begin=datetime.fromisoformat(r['request_utc']);end=datetime.fromisoformat(r['retrieval_utc']);assert end>=begin and (previous is None or begin>=previous);previous=end
 assert r['elapsed_seconds']>=0 and r['elapsed_seconds']<=20 and r['body_bytes']<=262144
 clockreport[r['id']]={'request_utc':r['request_utc'],'retrieval_utc':r['retrieval_utc'],'elapsed_seconds':float(r['elapsed_seconds'])}
 raws[r['id']]=payload(r);receipts[r['id']]=r
assert datetime.fromisoformat(capture['capture_closed_utc'])>=previous
reference=clock(raws['options-time']['serverTime']);r=receipts['options-time'];lo=int(datetime.fromisoformat(r['request_utc']).timestamp()*1000)-5000;hi=int(datetime.fromisoformat(r['retrieval_utc']).timestamp()*1000)+5000;assert lo<=reference<=hi
assert capture['source_admission']['options-time']['serverTime']==reference and capture['source_admission']['options-time']['clock_bounds_ms']==[lo,hi]
identities=Counter(r['symbol'] for r in meta['optionSymbols']);chosen={};selectionreport={}
for asset in ('BTC','ETH'):
 indexrow=raws[asset.lower()+'-index'];assert isinstance(indexrow['indexPrice'],str);index=dec(indexrow['indexPrice']);clock(indexrow['time'])
 assert 'underlying' not in indexrow or indexrow['underlying']==asset+'USDT'
 assert dec(capture['source_admission'][asset.lower()+'-index']['indexPrice'])==index and capture['source_admission'][asset.lower()+'-index']['time']==indexrow['time']
 parents=[r for r in meta['optionContracts'] if r['underlying']==asset+'USDT'];assert len(parents)==1
 assert [parents[0][k] for k in ('baseAsset','quoteAsset','settleAsset')]==[asset,'USDT','USDT']
 eligible=[];excluded=0;calls=0
 for r in meta['optionSymbols']:
  if r.get('underlying')!=asset+'USDT' or r.get('side')!='CALL':continue
  calls+=1
  try:
   symbol=r['symbol'];expiry=r['expiryDate'];assert identities[symbol]==1 and isinstance(symbol,str) and len(symbol)<=128
   assert r['quoteAsset']=='USDT' and ('status' not in r or r['status']=='TRADING')
   clock(expiry);assert 7*DAY<=expiry-reference<=45*DAY
   strike=dec(r['strikePrice']);unit=dec(r['unit']);q=dec(r['minQty']);maximum=dec(r['maxQty'])
   m=re.fullmatch(asset+r'-(\d{6})-(\d+(?:\.\d+)?)-C',symbol);assert m and m[1]==datetime.fromtimestamp(expiry/1000,timezone.utc).strftime('%y%m%d') and dec(m[2])==strike
   lots=[v for v in r['filters'] if v['filterType']=='LOT_SIZE'];assert len(lots)==1
   step=dec(lots[0]['stepSize']);assert dec(lots[0]['minQty'])==q and dec(lots[0]['maxQty'])==maximum and q<=maximum and (q/step).denominator==1
   eligible.append(r)
  except (AssertionError,ValueError,KeyError,TypeError):excluded+=1
 assert eligible
 expires=sorted({r['expiryDate'] for r in eligible});expiry=min(expires,key=lambda x:(abs(x-reference-30*DAY),x))
 selected=min([r for r in eligible if r['expiryDate']==expiry],key=lambda x:(abs(dec(x['strikePrice'])-index),dec(x['strikePrice']),x['symbol']))
 expected=capture['selections'][asset]
 assert expected['reference_ms']==reference and dec(expected['index'])==index and expected['eligible_count']==len(eligible)
 assert expected['excluded_counts']=={'structurally_or_temporally_ineligible':excluded}
 assert [v['symbol'] for v in expected['eligible']]==[r['symbol'] for r in eligible]
 for projection,r in zip(expected['eligible'],eligible):
  assert projection['expiry_ms']==r['expiryDate'] and projection['metadata_status']==r.get('status','unverified')
  for output,raw in [('strike','strikePrice'),('unit','unit'),('minQty','minQty'),('maxQty','maxQty')]:assert dec(projection[output])==dec(r[raw])
  assert projection['underlyingType']==r.get('underlyingType') and projection['contractType']==r.get('contractType')
 assert expected['selected']['symbol']==selected['symbol'];chosen[asset]=(selected,index)
 selectionreport[asset]={'symbol':selected['symbol'],'eligible_count':len(eligible),'excluded_matching_calls':excluded,'matching_call_rows':calls,'expiry_choices_utc':[datetime.fromtimestamp(t/1000,timezone.utc).isoformat() for t in expires],'selected_expiry_utc':datetime.fromtimestamp(expiry/1000,timezone.utc).isoformat(),'days_after_reference':(expiry-reference)/DAY,'index':indexrow['indexPrice'],'minQty':selected['minQty'],'unit':str(selected['unit'])}
 for kind in ('depth','mark'):
  key=asset.lower()+'-'+kind;r=receipts[key];params={'symbol':selected['symbol'],**({'limit':10} if kind=='depth' else {})}
  assert r['parameters']==params and r['request_url']==r['endpoint']+'?'+urlencode(params)
 depth=raws[asset.lower()+'-depth'];admitted=capture['source_admission'][asset.lower()+'-depth'];clock(depth['T']);assert type(depth['lastUpdateId']) is int and 0<=depth['lastUpdateId']<=2**63-1
 assert 'symbol' not in depth or depth['symbol']==selected['symbol']
 for side in ('bids','asks'):
  rows=depth[side];assert 1<=len(rows)<=10
  for pair in rows:assert len(pair)==2 and all(isinstance(v,str) for v in pair);dec(pair[0]);dec(pair[1],False)
  prices=[dec(v[0]) for v in rows];assert all((x>y if side=='bids' else x<y) for x,y in zip(prices,prices[1:]));assert admitted[side]==rows
 assert dec(depth['bids'][0][0])<=dec(depth['asks'][0][0]) and admitted['T']==depth['T'] and admitted['lastUpdateId']==depth['lastUpdateId']
 marks=raws[asset.lower()+'-mark'];assert isinstance(marks,list) and len(marks)==1 and marks[0]['symbol']==selected['symbol'];mark=marks[0];ma=capture['source_admission'][asset.lower()+'-mark'];assert dec(ma['markPrice'])==dec(mark['markPrice'])
 for field,status in ma['model_fields'].items():
  assert status['status']=='complete' and isinstance(mark[field],str) and len(mark[field])<=64
  value=Decimal(mark[field]);assert value.is_finite() and -32<=value.adjusted()<=32 and Decimal(status['value'])==value
 assert ma['event_time'].startswith('unavailable')
 clockreport[asset.lower()+'-index']['source_time_ms']=indexrow['time'];clockreport[asset.lower()+'-depth']['source_time_ms']=depth['T']

case_report={};exact_checks=0
for asset,(selected,index) in chosen.items():
 q=dec(selected['minQty']);unit=dec(selected['unit']);ask=dec(raws[asset.lower()+'-depth']['asks'][0][0]);size=dec(raws[asset.lower()+'-depth']['asks'][0][1],False)
 for capital in (1000,10000):
  for rate in ('0.00024','0.00030'):
   name=f'{asset.lower()}-{capital}-{rate}';got=entry['cases'][name]
   premium=ask*q;fee=min(Fraction(Decimal(rate))*index*unit,Fraction(1,10)*ask)*q;total=premium+fee
   for k,v in [('quantity',q),('unit',unit),('ask',ask),('index',index),('premium_usdt',premium),('fee_usdt',fee),('entry_component_usdt',total),('visible_ask_size',size)]:assert dec(got[k],False)==v;exact_checks+=1
   assert got['symbol']==selected['symbol'] and got['fee_rate']==rate and got['capital_usdt']==capital and got['status']=='complete'
   assert got['component_fits_capital']==(total<=capital) and got['visible_ask_size_sufficient']==(size>=q);exact_checks+=2
   case_report[name]={'premium_usdt':got['premium_usdt'],'fee_usdt':got['fee_usdt'],'entry_component_usdt':got['entry_component_usdt'],'capital':capital,'fits':total<=capital,'visible_size_sufficient':size>=q,'fee_cap_binds':fee==Fraction(1,10)*premium}
assert len(case_report)==8 and summary['component_counts']=={'complete':8} and summary['graduation'] is False
resource=read(REV/'options-entry-resource-execution.json');assert resource['child_exit_code']==0 and resource['limit_reason'] is None and resource['peak_sampled_tree_rss_bytes']<536870912 and resource['elapsed_seconds']<240
from tradingagents.research.verify import verify_run
structural=verify_run(RUN)
result={'disposition':'PASS within buyer-entry-component scope; no strategy validation','source':claim['source'],'gate_sha256':claim['registration_sha256'],'outputs':done['output_sha256'],'output_bytes':outputbytes,'source_cells':7,'component_cells':8,'unavailable':0,'source_receipts':7,'prior_metadata_rows':len(meta['optionSymbols']),'exact_cash_assertions':exact_checks,'selection':selectionreport,'cases':case_report,'clock_evidence':clockreport,'capture_closed_utc':capture['capture_closed_utc'],'structural_verification':structural,'resource':{k:float(v) if isinstance(v,Decimal) else v for k,v in resource.items()},'limitations':summary['unavailable']}
(REV/'options-entry-actual-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'selection':selectionreport,'cases':case_report,'output_bytes':outputbytes,'exact_cash_assertions':exact_checks},indent=2))
