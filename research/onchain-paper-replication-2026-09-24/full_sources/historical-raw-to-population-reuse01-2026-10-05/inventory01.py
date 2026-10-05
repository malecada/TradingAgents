"""Declared historical metadata only; reuse exact existing adapter, never raw bodies."""
import ast, hashlib, json, re, stat
from pathlib import Path
from datetime import date, datetime, timedelta
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
STUDY=ROOT/'research/onchain-paper-replication-2026-09-24'
ADAPTER=STUDY/'prepare_pilot_sources.py'
PLAN=ROOT/'research/onchain-graph-2026-09-16/fullpanel/plan.json'
PLAN_SHA='19f3716454216afc172aec2939a9908ba3b57921e99249951e1860b995d1d691'
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(b):return json.dumps(b,sort_keys=True,separators=(',',':')).encode()+b'\n'
def load(path,expected=None):
 p=Path(path);s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_size>16*1024**2 or p.suffix!='.json':raise ValueError('bounded JSON metadata required: '+str(p))
 raw=p.read_bytes();t=p.lstat()
 if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns):raise ValueError('metadata changed')
 if expected is not None and sha(raw)!=expected:raise ValueError('metadata hash mismatch '+str(p))
 return json.loads(raw)
def metadata_hash(p):
 load(p);return sha(Path(p).read_bytes())
def functions():
 raw=ADAPTER.read_bytes();tree=ast.parse(raw);selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'span','ordinary','special'}]
 assert len(selected)==3
 ns=dict(ROOT=ROOT,Path=Path,re=re,load=load,file_hash=metadata_hash)
 exec(compile(ast.Module(body=selected,type_ignores=[]),str(ADAPTER),'exec'),ns)
 return ns,sha(raw)
def week_days(w):return [(w+timedelta(days=i)).isoformat() for i in range(7)]
def full_weeks(days):
 available=set(days);result=[]
 for d in sorted(available):
  w=date.fromisoformat(d)
  if w.weekday()==0 and set(week_days(w))<=available:result.append(d)
 return result

def run():
 plan=load(PLAN,PLAN_SHA);fn,adapter_sha=functions();days={};failures={};physical={};objects={}
 assert len(plan['dates'])==1096 and len(plan['captures'])==1095
 target=HERE/'daily-maps';target.mkdir(exist_ok=False)
 for day in plan['dates']:
  try:
   rows=plan['expected_rows'][day]
   mapping=fn['special'](rows) if day=='2024-01-01' else fn['ordinary'](plan['captures'][day],day,rows)
   for sp in mapping['spans']:
    p=Path(sp['path']);s=p.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_size!=sp['stored_bytes']:raise ValueError('nonregular/mismatched retained span '+str(p))
    physical.setdefault(str((s.st_dev,s.st_ino)),set()).add(str(p))
   obj=mapping['object'];objects.setdefault(str((obj['key'],obj['etag'])),[]).append(day)
   body=canonical(mapping);p=target/(day+'.json');p.write_bytes(body)
   days[day]={'path':str(p),'sha256':sha(body),'format':'projected_zstd','expected_rows':rows,'start_utc':day+'T00:00:00Z','end_utc':(date.fromisoformat(day)+timedelta(days=1)).isoformat()+'T00:00:00Z'}
  except (OSError,ValueError,KeyError,AssertionError) as e:failures[day]={'type':type(e).__name__,'message':str(e)}
 weeks={}
 weekly=HERE/'weekly-inputs';weekly.mkdir(exist_ok=False)
 for w in full_weeks(days):
  members=[days[d] for d in week_days(date.fromisoformat(w))]
  v={'start_utc':w+'T00:00:00Z','end_utc':(date.fromisoformat(w)+timedelta(days=7)).isoformat()+'T00:00:00Z','status':'complete','expected_members':7,'expected_rows':sum(m['expected_rows'] for m in members),'members':members}
  p=weekly/(w+'.json');body=canonical(v);p.write_bytes(body);weeks[w]={'path':str(p),'sha256':sha(body),'expected_rows':v['expected_rows']}
 calpath=STUDY/'config/calendar-coinmetrics-v5.json';cal=load(calpath,'21bb348b9c779238b212d0e4074cf806f6a54d0ce3b7713d97bc3ad65d57ef22')
 # Reuse exact pure fixed-calendar required-week logic, without package imports.
 from types import SimpleNamespace
 ns={'datetime':datetime,'timedelta':timedelta,'utc':lambda s:datetime.fromisoformat(s.replace('Z','+00:00'))}
 pins={}
 for f,names in [('calendar.py',{'stamp','expected_week'}),('population_assembly.py',{'required_weeks'})]:
  p=ROOT/'tradingagents/research/onchain_replication'/f;raw=p.read_bytes();pins[f]=sha(raw)
  nodes=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),ns)
 folds=[]
 for fold in cal['folds']:
  req=ns['required_weeks'](SimpleNamespace(**fold),28)
  folds.append({'fold':fold['id'],'required_week_count':len(req),'raw_supported_weeks':[w for w in req if w[:10] in weeks],'missing_raw_weeks':[w for w in req if w[:10] not in weeks],'produced_graphs_or_eligible_rows':None})
 result={'schema_version':1,'scope':'exact pinned historical ETH fullpanel plan; no global absence inference','plan':{'path':str(PLAN),'sha256':PLAN_SHA},'adapter':{'path':str(ADAPTER),'sha256':adapter_sha,'functions_reused_unchanged':['span','ordinary','special']},'calendar_sha256':metadata_hash(calpath),'source_pins':pins,'declared_days':1096,'metadata_supported_days':len(days),'declared_rows_supported':sum(d['expected_rows'] for d in days.values()),'failures':failures,'weeks':weeks,'complete_week_count':len(weeks),'weekly_declared_rows':sum(w['expected_rows'] for w in weeks.values()),'partial_boundary_days':[d for d in days if not any(d in week_days(date.fromisoformat(w)) for w in weeks)],'folds':folds,'repeated_physical_span_paths':{k:sorted(v) for k,v in physical.items() if len(v)>1},'reused_object_key_etag_dates':{k:v for k,v in objects.items() if len(v)>1},'unique_span_physical_count':len(physical),'raw_payload_rehashed':False,'raw_payload_decoded':False,'eligible_original_population':None,'scratch_path':None,'qualification':'Authenticated historical JSON pins and current regular-file extents only. Raw hashes are original declarations; decoder must reauthenticate/decode within later admitted graph production. No raw copies, numerical execution, price join, fresh sample, availability or capacity claim.'}
 (HERE/'INVENTORY01.json').write_bytes(canonical(result));print(json.dumps({k:result[k] for k in ['metadata_supported_days','declared_rows_supported','complete_week_count','unique_span_physical_count','failures']}))
if __name__=='__main__':run()
