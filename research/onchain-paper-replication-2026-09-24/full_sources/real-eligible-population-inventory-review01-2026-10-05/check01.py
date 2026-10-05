"""Scoped file metadata and independent UTC calendar reconstruction only."""
import ast,collections,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
from datetime import datetime,timedelta
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
P=BASE/'real-eligible-population-inventory01-2026-10-05';CODE=ROOT/'tradingagents/research/onchain_replication'
def sha(b):return hashlib.sha256(b).hexdigest()
raw=(P/'MANIFEST01.json').read_bytes();assert sha(raw)=='23b3b5bd8a86d798c726e6b417dfcb7bd60803f19ff8bc54529d9128e53f3e6e'
for n,r in json.loads(raw)['files'].items():
 b=(P/n).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
x=json.loads((P/'INVENTORY01.json').read_bytes());scope=Path(x['scope']);assert scope==ROOT/'research_artifacts/onchain-paper-replication-2026-09-24'
entries=0;manifests=[]
for directory,dirs,files in os.walk(scope,followlinks=False):
 for n in dirs+files:entries+=1;assert not (Path(directory)/n).is_symlink()
 manifests.extend(Path(directory)/n for n in files if n=='manifest.json')
assert entries==x['scope_entries']==14430 and len(manifests)==x['manifest_count']==13
assert sum(f.stat().st_size for f in manifests)==x['metadata_bytes_read']==17347
assert {str(f.relative_to(ROOT)) for f in manifests}=={g['manifest_path'] for g in x['graphs']}|set(x['non_graph_manifests'])
# Four price-capture manifest paths/stat extents only; do not read their bodies.
physical=[];count=0
for g in x['graphs']:
 p=ROOT/g['manifest_path'];raw=p.read_bytes();assert sha(raw)==g['manifest_sha256'];v=json.loads(raw)
 s=p.stat();assert [s.st_dev,s.st_ino]==g['manifest_physical_identity']
 assert v['graph_hash']==g['graph_hash'] and all(v['metadata'][k]==g[k] for k in ['asset','start_utc','end_utc','available_at','graph_config_hash','source_hashes'])
 assert len(v['arrays'])==len(g['members'])==5
 for m in g['members']:
  r=v['arrays'][m['name']];q=ROOT/m['path'];s=q.lstat()
  assert q.parent==p.parent and q==q.resolve() and q==p.parent/r['path'] and stat.S_ISREG(s.st_mode)
  assert r['sha256']==m['declared_sha256'] and r['bytes']==m['declared_bytes']==m['observed_bytes']==s.st_size
  assert [s.st_dev,s.st_ino]==m['physical_identity'] and m['present'] is True and m['extent_matches'] is True and m['array_body_rehashed_or_decoded'] is False
  physical.append((s.st_dev,s.st_ino));count+=1
assert count==45 and len(set(physical))==45 and len({g['graph_hash'] for g in x['graphs']})==9
assert collections.Counter(g['asset'] for g in x['graphs'])=={'ETH':9} and x['graph_counts']=={'BTC':0,'ETH':9}
for n,h in x['source_pins'].items():assert sha((CODE/n).read_bytes())==h
calraw=(ROOT/'research/onchain-paper-replication-2026-09-24/config/calendar-coinmetrics-v5.json').read_bytes();assert sha(calraw)==x['calendar_sha256'];cal=json.loads(calraw)
assert sha((BASE/'neural-batch-graph-census-preparation-2026-10-03/source-metadata01.json').read_bytes())==x['accepted_census_sha256']
def utc(s):
 d=datetime.fromisoformat(s.replace('Z','+00:00'));assert d.utcoffset()==timedelta(0);return d
def stamp(d):return d.isoformat().replace('+00:00','Z')
def required_week(step):
 # Independent reconstruction of one-day publication delay, then closed Monday week.
 lagged=step-timedelta(days=1);monday=(lagged-timedelta(days=lagged.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
 return stamp(monday-timedelta(days=7))
summary={}
for asset in ['BTC','ETH']:
 byweek={stamp(utc(g['start_utc'])):g for g in x['graphs'] if g['asset']==asset};summaries=[]
 for fold,saved in zip(cal['folds'],x['fold_graph_support'][asset],strict=True):
  begin=utc(fold['train_start']);end=utc(fold['test_end']);t=begin-timedelta(days=27);required=set()
  while t<end:required.add(required_week(t));t+=timedelta(days=1)
  assert len(required)==saved['required_week_count'] and sorted(required-set(byweek))==saved['missing_required_weeks'] and sorted(required&set(byweek))==saved['observed_required_weeks']
  counts=collections.Counter();t=begin
  while t<end:
   label_end=t+timedelta(days=1);train=t<utc(fold['train_end']);reason=None
   if train and label_end>=utc(fold['test_start']):reason='purged_training_label'
   elif not train and t<utc(fold['test_start']):reason='outside_fold'
   elif not train and label_end>end:reason='test_label_boundary'
   missing=late=False
   for k in range(28,0,-1):
    step=t-timedelta(days=k)+timedelta(days=1);g=byweek.get(required_week(step))
    if g is None:missing=True
    elif utc(g['available_at'])>step:late=True
   counts[reason or ('missing_graph_metadata' if missing else 'late_graph_metadata' if late else 'graph_metadata_supported_price_join_unresolved')]+=1;t+=timedelta(days=1)
  assert dict(counts)==saved['status_counts'] and sum(counts.values())==saved['daily_candidate_count'] and not saved['graph_supported_rows'] and saved['true_eligible_rows'] is None
  summaries.append({'fold':fold['id'],'required_weeks':len(required),'observed':len(required&set(byweek)),'graph_supported_daily_rows':0})
 summary[asset]=summaries
# Two focused source-semantics counterexamples; pure metadata, no financial run.
spec=importlib.util.spec_from_file_location('inventory_candidate',P/'inventory01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fold={'id':'mechanical','train_start':'2024-02-01T00:00:00Z','train_end':'2024-02-03T00:00:00Z','test_start':'2024-02-03T00:00:00Z','test_end':'2024-02-06T00:00:00Z'}
weeks=m.F['required_weeks'](m.SimpleNamespace(**fold),28)
graphs=[dict(start_utc=w,available_at=stamp(utc(w)+timedelta(days=8)),graph_hash=str(i).zfill(64),manifest_path=str(i)) for i,w in enumerate(weeks)]
duplicate=dict(graphs[0],start_utc=graphs[0]['start_utc'].replace('Z','+00:00'),graph_hash='f'*64)
r=m.graph_support(fold,graphs+[duplicate]);assert len(r['graph_supported_rows'])==4
assert stamp(utc(graphs[0]['start_utc']))==stamp(utc(duplicate['start_utc']))
selected=[n for n in ast.parse((CODE/'provenance.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='utc'];ns={'datetime':datetime,'timedelta':timedelta};exec(compile(ast.Module(body=selected,type_ignores=[]),'original_utc','exec'),ns)
offset='2024-01-01T01:00:00+01:00';assert m.F['stamp'](offset)==offset
try:ns['utc'](offset)
except ValueError:pass
else:raise AssertionError('original UTC validator unexpectedly admitted offset')
assert not {'numpy','torch','scipy','pandas'}&set(sys.modules)
print(json.dumps({'schema_version':1,'decision':'ACCEPT_SCOPED_SAVED_INVENTORY_WITH_SOURCE_REUSE_FINDINGS','scope_entries':entries,'manifests':13,'manifest_metadata_bytes':17347,'graph_manifest_bodies_read':9,'price_manifest_bodies_read':0,'graph_members_stat_only':count,'folds':summary,'counterexamples':{'equivalent_Z_offset_week_duplicate_not_rejected':True,'nonUTC_offset_accepted_by_substitute_utc_original_refuses':True},'numerical_imports':False,'array_bodies_read':False,'true_eligible_population_known':False},sort_keys=True,indent=2))
