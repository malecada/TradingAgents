"""Offline graph-metadata support inventory; never declares scientific eligibility."""
import ast,hashlib,json,os,stat,time
from datetime import datetime,timedelta
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'tradingagents/research/onchain_replication/calendar.py').is_file())
SCOPE=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24'
CALENDAR=ROOT/'research/onchain-paper-replication-2026-09-24/config/calendar-coinmetrics-v5.json'
CODE=ROOT/'tradingagents/research/onchain_replication'
def sha(b):return hashlib.sha256(b).hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
def source_functions():
 ns={'datetime':datetime,'timedelta':timedelta}
 pins={}
 for file,names in [('provenance.py',{'utc'}),('calendar.py',{'stamp','eligible','expected_week'}),('population_assembly.py',{'required_weeks'})]:
  raw=(CODE/file).read_bytes();pins[file]=sha(raw);tree=ast.parse(raw)
  selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
  require(len(selected)==len(names),'source function denominator');exec(compile(ast.Module(body=selected,type_ignores=[]),file,'exec'),ns)
 return ns,pins
F,SOURCE_PINS=source_functions()
utc=F['utc']
SOURCE_PINS['dataset.py']=sha((CODE/'dataset.py').read_bytes())
def regular(path,limit=262144):
 s=path.lstat();require(stat.S_ISREG(s.st_mode) and not path.is_symlink() and s.st_size<=limit,'bounded regular metadata required');raw=path.read_bytes();t=path.lstat()
 require((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns) and len(raw)==s.st_size,'metadata changed')
 return raw,s
def graph_support(fold,graphs):
 """Whitelist-only support before price/label/fold-source admission; no true eligible claim."""
 require(len(graphs)<=2048,'graph population bound');by_week={}
 for g in graphs:
  w=F['stamp'](g['start_utc']);require(w not in by_week,'ambiguous graph for same asset/week');by_week[w]=g
 required=F['required_weeks'](SimpleNamespace(**fold),28);decision=utc(fold['train_start']);end=utc(fold['test_end']);rows=[];counts={};supported=[]
 require(0<(end-decision).days<=4096,'fixed bounded fold')
 while decision<end:
  d=F['stamp'](decision);label_end=decision+timedelta(days=1);train=decision<utc(fold['train_end']);reason=None
  if train and label_end>=utc(fold['test_start']):reason='purged_training_label'
  elif not train and decision<utc(fold['test_start']):reason='outside_fold'
  elif not train and label_end>end:reason='test_label_boundary'
  dates=[(decision-timedelta(days=i)).date().isoformat() for i in range(28,0,-1)];uses=[];missing=[];late=[]
  for date in dates:
   step=F['stamp'](utc(date+'T00:00:00Z')+timedelta(days=1));week=F['expected_week'](step);g=by_week.get(week)
   if g is None:
    if week not in missing:missing.append(week)
   elif not F['eligible'](g['available_at'],step):
    if week not in late:late.append(week)
   else:uses.append({'week':week,'graph_hash':g['graph_hash'],'manifest_path':g['manifest_path']})
  status=reason or ('missing_graph_metadata' if missing else 'late_graph_metadata' if late else 'graph_metadata_supported_price_join_unresolved')
  counts[status]=counts.get(status,0)+1
  if status=='graph_metadata_supported_price_join_unresolved':supported.append({'decision_at':d,'partition':'train' if train else 'test','input_dates':dates,'uses':uses})
  rows.append({'decision_at':d,'partition':'train' if train else 'test','status':status,'missing_weeks':missing,'late_weeks':late});decision+=timedelta(days=1)
 return {'fold':fold['id'],'required_week_count':len(required),'missing_required_weeks':[w for w in required if w not in by_week],'observed_required_weeks':[w for w in required if w in by_week],'daily_candidate_count':len(rows),'status_counts':counts,'graph_supported_rows':supported,'true_eligible_rows':None,'exclusion_precedence_qualification':'Price lookup is intentionally not read; missing/late graph diagnostics are independent necessary conditions, not original final exclusion labels.'}
def inventory():
 start=time.monotonic();paths=[];entries=0
 for current,dirs,files in os.walk(SCOPE,followlinks=False):
  require(time.monotonic()-start<60,'scan deadline');dirs.sort();files.sort()
  for name in dirs+files:
   entries+=1;require(entries<=32768,'scan entry bound');p=Path(current)/name;require(not p.is_symlink(),'scoped symlink requires explicit disposition')
  for name in files:
   if name=='manifest.json':paths.append(Path(current)/name)
 require(len(paths)<=2048,'manifest count bound');graphs=[];non_graph=[];bodies=0
 for p in paths:
  raw,s=regular(p);bodies+=len(raw);require(bodies<=8*1024**2,'metadata aggregate bound');v=json.loads(raw)
  if not {'graph_hash','metadata','arrays'}<=set(v):non_graph.append(str(p.relative_to(ROOT)));continue
  m=v['metadata'];require(m['asset'] in ('BTC','ETH'),'graph asset');require(utc(m['end_utc'])-utc(m['start_utc'])==timedelta(days=7) and utc(m['start_utc']).weekday()==0 and utc(m['start_utc']).time().isoformat()=='00:00:00','whole graph week');require(utc(m['available_at'])>=utc(m['end_utc'])+timedelta(days=1),'graph availability precedes fixed lag')
  members=[]
  for name,r in sorted(v['arrays'].items()):
   q=p.parent/r['path'];require(q.parent==p.parent and q.resolve()==q,'direct graph member path');t=q.lstat() if q.exists() else None
   members.append({'name':name,'path':str(q.relative_to(ROOT)),'declared_sha256':r['sha256'],'declared_bytes':r['bytes'],'present':t is not None,'observed_bytes':None if t is None else t.st_size,'extent_matches':None if t is None else stat.S_ISREG(t.st_mode) and t.st_size==r['bytes'],'physical_identity':None if t is None else [t.st_dev,t.st_ino],'array_body_rehashed_or_decoded':False})
  graphs.append({'asset':m['asset'],'start_utc':m['start_utc'],'end_utc':m['end_utc'],'available_at':m['available_at'],'graph_hash':v['graph_hash'],'graph_config_hash':m['graph_config_hash'],'source_hashes':m['source_hashes'],'manifest_path':str(p.relative_to(ROOT)),'manifest_sha256':sha(raw),'manifest_physical_identity':[s.st_dev,s.st_ino],'members':members})
 calendar_raw,_=regular(CALENDAR);require(sha(calendar_raw)=='21bb348b9c779238b212d0e4074cf806f6a54d0ce3b7713d97bc3ad65d57ef22','fixed calendar differs');calendar=json.loads(calendar_raw)
 census=HERE.parent/'neural-batch-graph-census-preparation-2026-10-03/source-metadata01.json';require(sha(census.read_bytes())=='5a7f0dd2ce2af033244e3b4491fba3f316fb42d8d5512fc384c26f496417400d','accepted census pin')
 summaries={asset:[graph_support(fold,[g for g in graphs if g['asset']==asset]) for fold in calendar['folds']] for asset in ('BTC','ETH')}
 physical={};hashes={}
 for g in graphs:
  hashes.setdefault(g['graph_hash'],[]).append(g['manifest_path'])
  for member in g['members']:
   if member['physical_identity'] is not None:physical.setdefault(str(member['physical_identity']),[]).append(member['path'])
 return {'schema_version':1,'scope':str(SCOPE),'scope_entries':entries,'manifest_count':len(paths),'metadata_bytes_read':bodies,'non_graph_manifests':non_graph,'graphs':graphs,'graph_counts':{a:sum(g['asset']==a for g in graphs) for a in ('BTC','ETH')},'repeated_graph_hash_paths':{h:p for h,p in hashes.items() if len(p)>1},'shared_physical_member_paths':{h:p for h,p in physical.items() if len(p)>1},'runtime_graph_object_identity':None,'fold_graph_support':summaries,'calendar_sha256':sha(calendar_raw),'source_pins':SOURCE_PINS,'accepted_census_sha256':sha(census.read_bytes()),'true_eligible_population_available':False,'missing_required_evidence':['admitted complete graph/unavailable population for each asset/fold','price-date membership and availability without values, bound to original source','genuine original population train/fold/test membership hashes and ordered whitelist/exclusions','complete original representation/terminal/component joins for all required graph hashes'],'qualification':'Current scoped metadata/file-extent census only. No array body authentication, labels/prices, numerical import, true eligible batch, global raw-store absence, runtime alias census or capacity claim.'}
if __name__=='__main__':print(json.dumps(inventory(),sort_keys=True,indent=2))
