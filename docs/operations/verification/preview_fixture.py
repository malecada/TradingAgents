from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
DIST=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/tradingagents/monitor/frontend/dist')
points=[{'ts':'2026-09-07','value':100.},{'ts':'2026-09-08','value':110.},{'ts':'2026-09-09','value':None}]
reason='Synthetic fixture: funding missing on 2026-09-09'
measurement={'status':'incomplete','note':reason,'books':{'champion':{'status':'incomplete','reason':reason,'journal':'journal_champion_v2.jsonl'},'vt10':{'status':'missing','reason':'Synthetic fixture: no VT10 journal','journal':None}}}
book={'measurement_status':'incomplete','measurement_reason':reason,'equity':points,'drawdown':[dict(p,value=0 if p['value'] else None) for p in points], 'rolling_sharpe':[], 'slippage':None,'cards':{'cum_return':None,'sharpe':None,'max_drawdown':None,'scale':None,'warmup':{'n':1,'required':20},'avg_turnover':None,'cum_cost':None,'last_asof':'2026-09-09','n_days':3}}
perf={'books':{'champion':book,'vt10':None},'nav':{'champion':None,'vt10':None},'account':{'testnet':None,'live':None},'reference':None,'backtest_yearly':None,'measurement':measurement}
health={'books':{'champion':{'last_asof':'2026-09-09','written_utc':'2026-09-10T00:20:00Z','stale':False,'rows':3,'malformed':0,'gaps':[],'journal_version':2,'measurement_status':'incomplete','measurement_reason':reason,'legacy_rows':38},'vt10':None},'heartbeat_note':'Synthetic fixture; no network or account access'}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(DIST),**kwargs)
 def do_GET(self):
  if self.path.startswith('/api/'):
   data={'/api/predlab/performance':perf,'/api/predlab/health':health,'/api/predlab/gate':{'status':'suspended_after_audit','reason':'Historical comparisons withdrawn after accounting audit.'}}.get(self.path,{})
   body=json.dumps(data).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  else:super().do_GET()
 def log_message(self,*args):pass
ThreadingHTTPServer(('127.0.0.1',8766),Handler).serve_forever()
