"""Offline exchange-state counterexamples for September execution corrections."""
import importlib
import io
import json
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from tradingagents.predlab.binance_client import BinanceAPIError, FuturesClient
from tradingagents.predlab.live_exec import check_caps as PRODUCTION_CAPS

NOW = datetime(2026, 8, 23, 0, 5, tzinfo=timezone.utc)

class Exchange:
    def __init__(self, positions=None, reject=(), unknown=False, partial=False, hedge=False):
        self.pos = dict(positions or {})
        self.reject = set(reject)
        self.unknown = unknown
        self.partial = partial
        self.hedge = hedge
        self.orders = []
        self.states = {}
        self.quote_time = int(NOW.timestamp()*1000)
    def position_mode(self): return self.hedge
    def equity(self): return 3000.0
    def positions(self): return {s:q for s,q in self.pos.items() if q}
    def exchange_info(self):
        return {'symbols':[{'symbol':s,'status':'TRADING','filters':[
            {'filterType':'MIN_NOTIONAL','notional':'5'},
            {'filterType':'LOT_SIZE','stepSize':'1'}]} for s in ('AAAUSDT','BBBUSDT','OLDUSDT')]}
    def book_ticker(self):
        return [{'symbol':s,'bidPrice':str(p),'askPrice':str(p),'time':self.quote_time}
                for s,p in [('AAAUSDT',2),('BBBUSDT',10),('OLDUSDT',100)]]
    def set_leverage(self,*args): pass
    def market_order(self,symbol,side,qty,reduce_only,client_order_id=None):
        self.orders.append((symbol, side, qty, reduce_only, client_order_id))
        if symbol in self.reject: raise BinanceAPIError(-2019,'rejected')
        fill_qty = qty/2 if self.partial else qty
        self.pos[symbol] = self.pos.get(symbol,0)+(fill_qty if side=='BUY' else -fill_qty)
        r={'orderId':len(self.orders),'status':'PARTIALLY_FILLED' if self.partial else 'FILLED',
           'executedQty':str(fill_qty),'avgPrice':'2','cumQuote':str(fill_qty*2)}
        self.states[client_order_id] = r
        if self.unknown: raise urllib.error.URLError('response lost after fill')
        return r
    def order_status(self,symbol,client_order_id):
        if client_order_id not in self.states: raise BinanceAPIError(-2013,'not found')
        return self.states[client_order_id]
    def user_trades(self,*args): return []

@pytest.fixture
def live(tmp_path,monkeypatch):
    monkeypatch.setenv('TRADINGAGENTS_DATA_ROOT',str(tmp_path))
    import predlab_s1_live
    mod=importlib.reload(predlab_s1_live)
    class Clock(datetime):
        @classmethod
        def now(cls,tz=None): return NOW
    monkeypatch.setattr(mod,'datetime',Clock)
    monkeypatch.setattr(mod.time,'sleep',lambda *_:None)
    # Two-symbol exchange tests isolate execution under an explicit toy cap.
    # Production concentration policy is tested below without this override.
    monkeypatch.setattr(mod.live_exec, 'check_caps',
        lambda tn, equity: PRODUCTION_CAPS(tn, equity, per_symbol_cap=1.))
    mod.CH_JOURNAL.parent.mkdir(parents=True)
    row={'journal_version':2,'asof':'2026-08-22','trade_day':'2026-08-23',
         'vt15_b100_scale':1.0,'weights':{'AAAUSDT':.025,'BBBUSDT':-.025},
         'mark_px':{'AAAUSDT':2.,'BBBUSDT':10.},'mark_ts':NOW.isoformat()}
    mod.CH_JOURNAL.write_text(json.dumps(row)+'\n')
    return mod,row

def latest(mod): return json.loads(mod.LIVE_JOURNAL.read_text().splitlines()[-1])

def test_rejected_batch_remains_retryable_and_never_claims_fills(live):
    mod,_=live
    c=Exchange(reject={'AAAUSDT','BBBUSDT'})
    assert 'incomplete' in mod.run(c,False)
    assert latest(mod)['status']=='incomplete'
    assert latest(mod)['orders_placed']==0
    c.reject.clear()
    assert mod.run(c,False).startswith('done')
    assert c.positions()=={'AAAUSDT':37.,'BBBUSDT':-7.}
    assert latest(mod)['status']=='reconciled'

def test_partial_batch_retries_only_residual_leg(live):
    mod,_=live
    c=Exchange(reject={'BBBUSDT'})
    mod.run(c,False)
    c.reject.clear()
    mod.run(c,False)
    assert [o[0] for o in c.orders]==['AAAUSDT','BBBUSDT','BBBUSDT']
    assert c.positions()=={'AAAUSDT':37.,'BBBUSDT':-7.}

def test_failed_emergency_is_incomplete_until_actual_flatten(live):
    mod,_=live
    c=Exchange({'AAAUSDT':37},reject={'AAAUSDT'})
    assert 'incomplete' in mod.close_all(c)
    assert c.positions()=={'AAAUSDT':37}
    assert mod.HALT_FLAG.exists()
    c.reject.clear()
    assert 'flattened' in mod.close_all(c)
    assert c.positions()=={}

def test_dry_run_does_not_consume_live_state(live):
    mod,_=live
    c=Exchange()
    assert mod.run(c,True).startswith('dry-run')
    assert not mod.DAY_EQUITY.exists()
    assert not c.orders
    assert mod.run(c,False).startswith('done')
    assert c.positions()=={'AAAUSDT':37.,'BBBUSDT':-7.}

def test_missing_desired_mark_never_becomes_exit(live):
    mod,row=live
    row['mark_px'].pop('AAAUSDT')
    mod.CH_JOURNAL.write_text(json.dumps(row)+'\n')
    c=Exchange({'AAAUSDT':37})
    assert mod.run(c,False).startswith('WAIT')
    assert c.positions()=={'AAAUSDT':37}
    assert not c.orders

@pytest.mark.parametrize('field,value',[('asof','2026-08-01'),('mark_ts','2026-08-22T00:05:00+00:00')])
def test_stale_decision_or_marks_refuse_orders(live,field,value):
    mod,row=live
    row[field]=value
    mod.CH_JOURNAL.write_text(json.dumps(row)+'\n')
    c=Exchange()
    assert mod.run(c,False).startswith('WAIT')
    assert not c.orders

def test_stale_current_quote_blocks_sizing(live):
    mod,_=live
    c=Exchange(); c.quote_time -= 3600_000
    assert mod.run(c,False).startswith('WAIT')
    assert not c.orders

def test_unknown_post_reconciles_fill_without_resubmitting(live):
    mod,_=live
    c=Exchange(unknown=True)
    mod.run(c,False)
    mod.run(c,False)
    assert c.positions()=={'AAAUSDT':37.,'BBBUSDT':-7.}
    assert len(c.orders)==2
    assert all(o[4] for o in c.orders)
    assert latest(mod)['status']=='reconciled'

def test_unresolved_partial_fill_does_not_start_duplicate_order(live):
    mod,_=live
    c=Exchange(partial=True)
    assert 'incomplete' in mod.run(c,False)
    n=len(c.orders)
    assert 'incomplete' in mod.run(c,False)
    assert len(c.orders)==n

def test_hedge_mode_blocks_daily_loss_and_manual_flatten(live):
    mod,_=live
    c=Exchange({'AAAUSDT':37},hedge=True)
    mod.LDIR.mkdir(parents=True)
    mod.DAY_EQUITY.write_text(json.dumps({'date':'2026-08-23','equity':4000}))
    assert 'hedge' in mod.run(c,False).lower()
    assert 'hedge' in mod.close_all(c).lower()
    assert not c.orders

def test_held_exposure_counts_in_risk_when_departing_close_can_fail(live):
    mod,_=live
    c=Exchange({'OLDUSDT':70},reject={'OLDUSDT'})
    mod.run(c,False)
    assert not any(not o[3] for o in c.orders)
    assert c.positions().get('OLDUSDT')==70

def test_unknown_503_post_is_never_blindly_retried(monkeypatch):
    c=FuturesClient(api_key='fake',api_secret='fake',base='https://offline.invalid')
    calls=[]
    def fail(req,timeout):
        calls.append(req)
        raise urllib.error.HTTPError(req.full_url,503,'unknown',{},io.BytesIO(b'{"code":-1000,"msg":"Unknown execution"}'))
    monkeypatch.setattr('urllib.request.urlopen',fail)
    monkeypatch.setattr('time.sleep',lambda *_:None)
    with pytest.raises(Exception): c.market_order('AAAUSDT','BUY',10,False)
    assert len(calls)==1


def test_status_warns_incomplete_reconciliation_and_compare_missing_fees(live):
    mod,_=live
    c=Exchange(reject={'BBBUSDT'})
    mod.run(c,False)
    assert 'incomplete' in mod.status(c).lower()
    mod.compare()
    report=json.loads((mod.LDIR/'compare_report.json').read_text())
    assert report['total_fees_usdt'] is None
    assert report['fee_coverage']=='incomplete'


def test_missing_position_mode_never_assumed_one_way(monkeypatch):
    c=FuturesClient(api_key='fake',api_secret='fake')
    monkeypatch.setattr(c,'_http',lambda *a,**k:{})
    with pytest.raises(ValueError): c.position_mode()


def test_small_live_book_cannot_bypass_per_symbol_cap(live,monkeypatch):
    mod,_=live
    c=Exchange()
    monkeypatch.setattr(mod.live_exec,'check_caps',PRODUCTION_CAPS)
    assert 'cap violation' in mod.run(c,False)
    assert not c.orders


def test_frozen_unfilled_target_remains_in_quote_and_risk_universe(live):
    mod,row=live
    c=Exchange(reject={'BBBUSDT'})
    mod.run(c,False)
    row['weights'].pop('BBBUSDT')
    row['mark_px'].pop('BBBUSDT')
    mod.CH_JOURNAL.write_text(json.dumps(row)+'\n')
    c.reject.clear()
    assert mod.run(c,False).startswith('done')
    assert c.positions()=={'AAAUSDT':37.,'BBBUSDT':-7.}


def test_frozen_residual_retries_after_paper_quote_expires(live, monkeypatch):
    from datetime import timedelta
    mod,_=live
    c=Exchange(reject={'BBBUSDT'})
    assert 'incomplete' in mod.run(c,False)
    later=NOW+timedelta(minutes=11)
    class Later(datetime):
        @classmethod
        def now(cls,tz=None): return later
    monkeypatch.setattr(mod,'datetime',Later)
    c.quote_time=int(later.timestamp()*1000)
    c.reject.clear()
    assert mod.run(c,False).startswith('done')
    assert c.positions()=={'AAAUSDT':37.,'BBBUSDT':-7.}


def test_partial_cancel_is_counted_and_cumulative_snapshots_not_double_counted(live):
    mod,_=live
    class Commissions(Exchange):
        def user_trades(self,*args):
            return [{'commissionAsset':'USDT','commission':'0.01','qty':'1'}]
    c=Commissions()
    one={'asof':'2026-08-22','symbol':'AAAUSDT','side':'BUY','qty':2.,'reduce_only':False,'client_order_id':'first'}
    response={'orderId':1,'status':'PARTIALLY_FILLED','executedQty':'1','avgPrice':'2','cumQuote':'2'}
    mod._observe(c,one,response)
    mod._observe(c,one,dict(response,status='CANCELED'))
    mod._observe(c,dict(one,client_order_id='second'),dict(response,status='FILLED',orderId=2))
    mod.compare()
    report=json.loads((mod.LDIR/'compare_report.json').read_text())
    assert report['n_fills']==2
    assert report['total_fees_usdt']==pytest.approx(.02)
