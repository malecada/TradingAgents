"""Independent invented Fraction fee/cash comparisons and selection tie oracle."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];DIRECTORY=ROOT/'research/strategy-search-2026-09-11';sys.path.insert(0,str(DIRECTORY))
import options_entry as candidate
checks=[]
fixtures=[('1','2','10','100','1'),('1','1','997','12500','1'),('1','1','997.0000000000000000001','12500','0.999999999999999999999'),('0.1','2','1000','1000000000','0.1'),('0.001','0.1','1e-32','1e32','0'),('1e-32','1e32','1e32','1e32','1e-32'),('1.'+'1'*62,'1.'+'2'*62,'1.'+'3'*62,'1.'+'4'*62,'1.'+'1'*62)]
for q,unit,ask,index,size in fixtures:
 for fee in ('0.00024','0.00030'):
  for capital in (1000,10000):
   amount,U,A,S,visible,r=map(lambda v:Fraction(Decimal(v)),[q,unit,ask,index,size,fee])
   premium=A*amount;charge=min(r*S*U,Fraction(1,10)*A)*amount;cash=premium+charge
   got=candidate.component({'selected':{'symbol':'invented','minQty':q,'unit':unit}},{'asks':[[ask,size]]},Decimal(index),capital,fee)
   assert Fraction(Decimal(got['premium_usdt']))==premium
   assert Fraction(Decimal(got['fee_usdt']))==charge
   assert Fraction(Decimal(got['entry_component_usdt']))==cash
   assert got['component_fits_capital']==(cash<=capital)
   assert got['visible_ask_size_sufficient']==(visible>=amount)
   checks.append({'q':q,'unit':unit,'ask':ask,'index':index,'fee':fee,'capital':capital,'passed':True})
now=1800000000000;day=86400000

def row(days,strike,status='TRADING'):
 expiry=now+days*day
 result={'symbol':'BTC-'+datetime.fromtimestamp(expiry/1000,timezone.utc).strftime('%y%m%d')+'-'+strike+'-C','underlying':'BTCUSDT','quoteAsset':'USDT','side':'CALL','expiryDate':expiry,'strikePrice':strike,'unit':'1','minQty':'0.1','maxQty':'100','filters':[{'filterType':'LOT_SIZE','minQty':'0.1','maxQty':'100','stepSize':'0.1'}]}
 if status is not None:result['status']=status
 return result
rows=[row(31,'100'),row(29,'110'),row(29,'90',None),row(7,'100'),row(45,'100'),row(30,'99','BREAK')]
parent={'underlying':'BTCUSDT','baseAsset':'BTC','quoteAsset':'USDT','settleAsset':'USDT'}
data={'optionContracts':[parent],'optionSymbols':rows}
chosen=candidate.select(data,'BTC',now,Decimal(100));assert chosen['selected']['symbol']==rows[2]['symbol'] and chosen['selected']['metadata_status']=='unverified' and chosen['eligible_count']==5
rows[2]['filters'][0]['stepSize']='0.03';chosen=candidate.select(data,'BTC',now,Decimal(100));assert chosen['selected']['symbol']==rows[1]['symbol']
data['optionContracts'].append(dict(parent))
try:candidate.select(data,'BTC',now,Decimal(100));raise AssertionError('duplicate parent admitted')
except ValueError:pass
result={'passed':True,'cash_cases':len(checks),'exact_assertions':len(checks)*5,'selection_checks':['earlier expiry','lower strike','inclusive7/45days','non-TRADING exclusion','missing status unverified','exact lot-step exclusion','duplicate parent unavailable'],'source_sha256':hashlib.sha256((DIRECTORY/'options_entry.py').read_bytes()).hexdigest(),'scope':'Invented inputs only. Exact Fraction arithmetic independent of candidate Decimal implementation; no actual observations/network/run lifecycle.'}
(Path(__file__).parent/'options-entry-synthetic-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
