import ast,json,hashlib
from pathlib import Path
from datetime import datetime,timedelta,timezone
R=Path.cwd();D=Path(__file__).resolve().parent;F=D.parent;S=R/'tradingagents/research/onchain_replication'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); evidence={}
def read(p,digest=None):
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert digest is None or h==digest;evidence[str(p.relative_to(R))]=h;return json.loads(b)
gatepath=F/'real-data-pilot-full29-entry01-2026-10-09/gate04.json';g=read(gatepath);entry=g['experiments']['eth-paper-real-data-end-to-end-resource-20261009-29'];refs=entry['inputs']
def role(n):x=refs[n];return read(R/x['path'],x['sha256'])
p=role('pilot');model=role('model');training=role('training');calendar=role('calendar');plan=role('resource_population_plan')
ns={'datetime':datetime,'timedelta':timedelta,'timezone':timezone}
for name,functions in [('provenance.py',{'utc'}),('calendar.py',{'stamp','eligible','expected_week'})]:
 t=ast.parse((S/name).read_text());exec(compile(ast.Module(body=[z for z in t.body if isinstance(z,ast.FunctionDef) and z.name in functions],type_ignores=[]),name,'exec'),ns)
constants={z.targets[0].id:ast.literal_eval(z.value) for z in ast.parse((S/'real_pilot_training.py').read_text()).body if isinstance(z,ast.Assign) and isinstance(z.targets[0],ast.Name) and z.targets[0].id in ('MODEL_SHA','TRAINING_SHA')}
for value,key in [(model,'MODEL_SHA'),(training,'TRAINING_SHA')]:assert hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==constants[key]
graphs={};headers=[]
for key,rol in p['graph_inputs'].items():
 m=role(rol);meta=m['metadata'];assert m['graph_hash']==key;graphs[meta['start_utc']]=(key,meta)
 out={'graph':key}
 for name in ('node_features','edge_index'):
  a=m['arrays'][name];path=(R/refs[rol]['path']).parent/a['path'];assert path.stat().st_size==a['bytes']
  with path.open('rb') as stream:
   lead=stream.read(8);assert lead[:6]==b'\x93NUMPY';width=2 if lead[6]==1 else 4;n=int.from_bytes(stream.read(width),'little');assert 0<n<=65536;h=stream.read(n);v=ast.literal_eval(h.decode('latin1'))
  out[name]={'shape':v['shape'],'dtype':v['descr'],'header_sha256':hashlib.sha256(h).hexdigest()}
 headers.append(out)
rows=[];dates=set()
for decision,expected in zip(p['decisions'],p['graph_sequences'],strict=True):
 d=ns['utc'](decision);selected=[]
 for i in range(28,0,-1):
  date=d-timedelta(days=i);dates.add(date.date().isoformat());step=ns['stamp'](date+timedelta(days=1));key,meta=graphs[ns['expected_week'](step)];assert ns['eligible'](meta['available_at'],step);selected.append(key)
 assert selected==expected;dates.add(d.date().isoformat());rows.append({'decision':decision,'distinct_graphs':len(set(selected))})
assert len(rows)==16 and len({k for row in p['graph_sequences'] for k in row})==7
fold=next(x for x in calendar['folds'] if x['id']==plan['fold'])
for row in rows:
 d=ns['utc'](row['decision']);assert ns['utc'](fold['train_start'])<=d<ns['utc'](fold['train_end']) and d+timedelta(days=1)<ns['utc'](fold['test_start'])
for name in ['real_pilot_import_caller.py','real_pilot_population.py','real_pilot_training.py','dataset.py','calendar.py','model.py','streamed_gat.py','evaluation.py','temporal.py','feature_residency.py']:
 path=S/name
 if path.exists():evidence[str(path.relative_to(R))]=sha(path);assert entry['source_files'][str(path.relative_to(R))]==sha(path)
out={'decision':'PASS_METADATA_ONLY','rows':rows,'graph_references':448,'union_graphs':7,'required_price_dates_count':len(dates),'required_price_date_start':min(dates),'required_price_date_end':max(dates),'price_payload_read':False,'price_finiteness_and_membership_proved':False,'graph_headers':headers,'model_execution':p['model_execution'],'model_config':model,'training_config':training,'checkpoint_cap':p['max_checkpoint_bytes'],'fold_membership_and_graph_sequences_match':True,'source_pins':evidence,'qualification':'No numerical import, price/testlabel/array payload, Owner, Run, fitting or claim. Availability/header/source compatibility only; genuine eligible population remains runtime-derived.'}
(D/'CHECK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('source_pins','graph_headers','model_config','training_config','rows')}))
