"""Fixed invented funded-book examples; no historical financial inputs."""
import argparse
from decimal import Decimal as D
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from tradingagents.research import ResearchRun
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('engine_admission_book',HERE/'spot_book.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
EXPERIMENT='allocation-spot-engine-20260915'
REGISTRATION='research/broader-allocation-2026-09-15/gates-spot-engine.json'
SPEC_HASH='855584e605ca2316e4f55ae1af202557c8cd001559d8fd6df5ef08dff5b7f380'


def rejected(call,exception=ValueError):
    try:call()
    except exception:return True
    return False


def evaluate(raw):
    if hashlib.sha256(raw).hexdigest()!=SPEC_HASH:raise ValueError('unregistered invented examples')
    spec=json.loads(raw);rows=[]
    def keep(name,actual,expected):
        if actual!=expected:raise AssertionError((name,actual,expected))
        rows.append({'id':name,'status':'complete','actual':str(actual),'literal_expected':str(expected),'scope':'invented example'})
    book=b.SpotBook({('cex','USDC'):'10000'})
    book.trade('b','cex','BTC','USDC','buy','2','100',fee_asset='USDC',fee='0.2')
    book.trade('s','cex','BTC','USDC','sell','2','110',fee_asset='USDC',fee='0.22')
    nav=book.liquidation_nav({('cex','USDC'):'1'},exit_cost_usd='5',pending_marks={})
    keep('round-trip',nav,D('10014.58'))
    keep('full-capital-profit',b.cash_profit(nav,'10000')['simple_net_return'],D('0.001458'))
    book=b.SpotBook({('cex','USDC'):'1000',('cex','GAS'):'1'})
    book.trade('b','cex','BTC','USDC','buy','2','100',fee_asset='BTC',fee='0.002')
    keep('base-fee',book.balances[('cex','BTC')],D('1.998'))
    book.trade('s','cex','BTC','USDC','sell','1','100',fee_asset='GAS',fee='0.1')
    keep('third-asset-fee',book.liquidation_nav({('cex','USDC'):'1',('cex','BTC'):'100',('cex','GAS'):'10'},exit_cost_usd='0',pending_marks={}),D('1008.8'))
    book=b.SpotBook({('cex','USDC'):'100'})
    keep('insufficient-cash',rejected(lambda:book.trade('b','cex','BTC','USDC','buy','1','100',fee_asset='USDC',fee='0.1')) and not book.events and book.balances=={('cex','USDC'):D('100')},True)
    book=b.SpotBook({('cex','USDC'):'10000'})
    for i in range(4):book.trade(str(i),'cex','BTC','USDC','buy',b.floor_quantity(D('624')/100,'0.1'),'100',fee_asset='USDC',fee='1')
    keep('phased-entry-idle-cash',book.balances[('cex','USDC')],D('7516'))
    keep('lot-dust-nav',book.liquidation_nav({('cex','USDC'):'1',('cex','BTC'):'100'},exit_cost_usd='0',pending_marks={}),D('9996'))
    book=b.SpotBook({('source','USDC'):'10000'})
    book.begin_transfer('t','source','destination','USDC','1000',fee_asset='USDC',fee='2')
    keep('unvalued-transfer',rejected(lambda:book.liquidation_nav({('source','USDC'):'1'},exit_cost_usd='0',pending_marks={}),b.MissingValuation),True)
    keep('pending-transfer-nav',book.liquidation_nav({('source','USDC'):'1'},exit_cost_usd='0',pending_marks={'t':'0.98'}),D('9978'))
    keep('pending-not-spendable',rejected(lambda:book.trade('early','destination','BTC','USDC','buy','1','100',fee_asset='USDC',fee='0')),True)
    book.settle_transfer('settle','t')
    keep('settlement-no-double-count',book.liquidation_nav({('source','USDC'):'1',('destination','USDC'):'0.98'},exit_cost_usd='0',pending_marks={}),D('9978'))
    book=b.SpotBook({('cex','USDC'):'7500',('wallet','chain:token'):'25'})
    keep('missing-held',rejected(lambda:book.liquidation_nav({('cex','USDC'):'0.8'},exit_cost_usd='0',pending_marks={}),b.MissingValuation),True)
    keep('depeg-token-total-loss',book.liquidation_nav({('cex','USDC'):'0.8',('wallet','chain:token'):'0'},exit_cost_usd='10',pending_marks={}),D('5990'))
    keep('unknown-exit-fee',rejected(lambda:book.liquidation_nav({('cex','USDC'):'0.8',('wallet','chain:token'):'0'},exit_cost_usd=None,pending_marks={}),b.MissingValuation),True)
    close='2025-09-01T00:00:00Z'; decision='2025-09-01T00:05:00Z'; fill='2025-09-02T00:00:00Z'
    keep('causal-next-bar',b.check_action_clock(close,close,decision,fill,'86100'),True)
    keep('future-information-rejected',rejected(lambda:b.check_action_clock(close,'2025-09-01T00:06:00Z',decision,fill,'86100')),True)
    keep('pre-decision-fill-rejected',rejected(lambda:b.check_action_clock(close,close,decision,close,'86100')),True)
    keep('late-fill-rejected',rejected(lambda:b.check_action_clock(close,close,decision,fill,'86099')),True)
    # Convention diagnostic only: the log number is never entered in inventory.
    keep('simple-versus-log-convention',b.cash_profit('200','100')['net_cash_profit_usd']==D('100') and 69<100*math.log(2)<70,True)
    if [r['id'] for r in rows]!=spec['cells']:raise ValueError('case identity/order mismatch')
    return {'scope':'Invented ledger/clock examples only; not financial evidence','cells':rows,'implementation_admitted':False,'new_requests':0,'not_implemented':['actual quote/filter admission','historical publication witness','identity-changing transfer','LP/lending/staking','strategy scheduler','return inference']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);args=p.parse_args()
    with ResearchRun.start(root=HERE.parents[1],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        run.read_input('cash_result');run.read_input('ancestry')
        result=evaluate(run.read_input('spec'));run.write_json('engine-cases.json',result)
        run.finish([{'id':r['id'],'status':r['status']} for r in result['cells']])

if __name__=='__main__':main()
