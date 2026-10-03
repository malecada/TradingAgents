"""Opaque synthetic metadata only; no genuine authority or financial credit."""
import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
D=Path(__file__).parent
p=D/'overlay/tradingagents/research/onchain_replication/treatment_admission.py'
spec=importlib.util.spec_from_file_location('isolated_treatment_admission',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def ok(label,f):
 f();checks.append({'name':label,'passed':True})
def refuse(label,f):
 try:f()
 except (ValueError,KeyError,TypeError,StopIteration):checks.append({'name':label,'passed':True});return
 raise AssertionError(label)
def equal(a,b):assert a==b,(a,b)
H=lambda v:hashlib.sha256(v.encode()).hexdigest()
w='2024-01-01T00:00:00Z';end='2024-01-08T00:00:00Z';avail='2024-01-09T00:00:00Z'
weekref={'status':'complete','claim_input':'claim','terminal_input':'terminal','ledger_input':'ledger','job_input':'job','plan_input':'plan','disposition_input':'cell','receipt_input':'receipt','coverage_input':'coverage','manifest_input':'manifest','components':{'node_ids.npy':'nodes'},'aliases':{}}
bundle={'schema_version':1,'asset':'ETH','variant':'whale','expected_weeks':[w],'weeks':{w:weekref}}
ok('exact bounded weekly role schema',lambda:m.schema(bundle,'ETH','whale',[w]))
for label,edit in [('extraweek',lambda x:x['weeks'].update({'2024-01-08T00:00:00Z':weekref})),('asset',lambda x:x.update(asset='BTC')),('variant',lambda x:x.update(variant='fund')),('emptycomponents',lambda x:x['weeks'][w].update(components={})),('absoluteinput',lambda x:x['weeks'][w].update(claim_input='/tmp/x')),('unknownmember',lambda x:x['weeks'][w].update(components={'../manifest.json':'x'})),('boolversion',lambda x:x.update(schema_version=True)),('missingrole',lambda x:x['weeks'][w].pop('claim_input'))]:
 b=copy.deepcopy(bundle);edit(b);refuse('schema '+label,lambda b=b:m.schema(b,'ETH','whale',[w]))
u=copy.deepcopy(bundle);u['weeks'][w].update(status='unavailable',receipt_input=None,coverage_input=None,manifest_input=None,components={},disposition_input=None)
ok('explicit unavailable absence remains in denominator',lambda:m.schema(u,'ETH','whale',[w]))
cell='treatment-eth-whale-2024-01-01';claim={'source':'1'*40,'experiment_id':'opaque-test-only','registration_sha256':H('reg'),'experiment':{'cells':[cell]}}
ledger=[{'id':cell,'status':'complete','asset':'ETH','week':w,'manifest_sha256':H('manifest'),'coverage_sha256':H('coverage'),'treatment_receipt_sha256':H('receipt')}]
terminal={'claim_sha256':H('claim'),'experiment_id':claim['experiment_id'],'status':'complete','source':claim['source'],'registration_sha256':claim['registration_sha256'],'cells':ledger,'output_sha256':{'cell-ledger.json':H('ledger')},'cell_count':1,'unavailable_count':0}
plan={'expected_weeks':[w]}
args=[claim,terminal,ledger,H('claim'),H('ledger'),plan,w,'whale','ETH']
ok('pure closed source/cell/ledger join',lambda:equal(m.disposition(*args),ledger[0]))
for field,val in [('claim_sha256',H('wrong')),('source','2'*40),('status','running'),('cell_count',2),('unavailable_count',1),('cells',[]),('output_sha256',{})]:
 a=copy.deepcopy(args);a[1][field]=val;refuse('terminal '+field,lambda a=a:m.disposition(*a))
a=copy.deepcopy(args);a[1]['status']='failed';refuse('failed cannot grant completed treatment',lambda:m.disposition(*a))
a=copy.deepcopy(args);a[1]['status']='failed';a[2][0].update(status='unavailable',reason='opaque interrupted failure');ok('failed unavailable retained',lambda:m.disposition(*a))
meta={'asset':'ETH','start_utc':w,'end_utc':end,'available_at':avail,'source_hashes':[H('source')],'graph_config_hash':H('config'),'raw_count':9,'admitted_count':8,'exclusion_counts':{'opaque':1}}
parent={'metadata':copy.deepcopy(meta),'graph_hash':H('parentgraph'),'arrays':{}}
decision={'schema_version':2,'variant':'whale','parent_graph_hash':parent['graph_hash'],'decision':{'threshold':.9,'strict':True}}
graph={'metadata':copy.deepcopy(meta),'graph_hash':H('treatedgraph'),'arrays':{}}
graph['metadata']['graph_config_hash']=m.sha(m.canonical({'parent_config':meta['graph_config_hash'],'variant':decision}))
coverage={'graph_config_hash':graph['metadata']['graph_config_hash'],'graph_manifest_sha256':H('manifest'),'claim_sha256':H('claim'),'plan_sha256':H('plan'),'asset':'ETH','week':w,'end_utc':end}
receipt={'schema_version':1,'kind':'registered-graph-treatment-receipt','asset':'ETH','variant':'whale','week':w,'end_utc':end,'available_at':avail,'claim_sha256':H('claim'),'plan_sha256':H('plan'),'source':claim['source'],'manifest_sha256':H('manifest'),'parent_manifest_sha256':H('parentmanifest'),'graph_hash':graph['graph_hash'],'parent_graph_hash':parent['graph_hash'],'decision':decision,'cohort_sha256':None,'cohort_review_sha256':None}
ga=[receipt,ledger[0],graph,H('manifest'),coverage,H('coverage'),H('receipt'),claim,H('claim'),H('plan'),parent,H('parentmanifest'),w,'ETH','whale']
ok('pure original whale config/clock/raw lineage',lambda:m.graph_join(*ga))
for field in ('asset','variant','week','end_utc','available_at','claim_sha256','plan_sha256','source','manifest_sha256','parent_manifest_sha256','graph_hash','parent_graph_hash','cohort_sha256'):
 a=copy.deepcopy(ga);a[0][field]='corrupt';refuse('receipt '+field,lambda a=a:m.graph_join(*a))
for field,val in [('graph_config_hash',H('wrong')),('raw_count',10),('source_hashes',[H('wrong')]),('available_at','2024-01-08T00:00:00Z')]:
 a=copy.deepcopy(ga);a[2]['metadata'][field]=val;refuse('graph '+field,lambda a=a:m.graph_join(*a))
a=copy.deepcopy(ga);a[0]['decision']['decision']['threshold']=.8;refuse('filter threshold cannot drift',lambda:m.graph_join(*a))
a=copy.deepcopy(ga);a[14]='fund';a[0]['variant']='fund';a[0]['decision']['variant']='fund';a[2]['metadata']['graph_config_hash']=m.sha(m.canonical({'parent_config':meta['graph_config_hash'],'variant':a[0]['decision']}));a[4]['graph_config_hash']=a[2]['metadata']['graph_config_hash'];refuse('fund policy remains unadmitted despite self-consistent hashes',lambda:m.graph_join(*a))
admitted={w:m.graph_join(*ga)}
rows=[(['2024-01-08'],[graph['graph_hash']],[avail])]
ok('exact causal example graph membership',lambda:m.verify_example_metadata(rows,admitted))
for date,h,a in [('2024-01-07',graph['graph_hash'],avail),('2024-01-08',H('other'),avail),('2024-01-08',graph['graph_hash'],'2024-01-10T00:00:00Z')]:refuse('example date/hash/availability '+date+h[:4]+a,lambda date=date,h=h,a=a:m.verify_example_metadata([([date],[h],[a])],admitted))
a=copy.deepcopy(admitted);a[w]['status']='unavailable';refuse('unavailable graph cannot enter example',lambda:m.verify_example_metadata(rows,a))
refuse('missing treatment input fails before run access',lambda:m.preflight_treatment(None,{}, {'variant':'whale'},None))
ok('untreated legacy bypass unchanged',lambda:m.preflight_treatment(None,{}, {'variant':'whole'},None))
# AST-based wiring checks and exact inverse; no numeric-containing imports.
changes=json.loads((D/'DELTA_INVERSE01.json').read_text())
for r in changes:
 current=(D/'overlay'/r['path']).read_text();ast.parse(current)
 for e in reversed(r['edits']):assert current.count(e['new'])==1;current=current.replace(e['new'],e['old'])
 ok('exact full byte inverse '+r['path'],lambda current=current,r=r:equal(hashlib.sha256(current.encode()).hexdigest(),r['original_sha256']))
old=(D/'origins/run.py').read_text();new=(D/'overlay/tradingagents/research/onchain_replication/run.py').read_text()
ok('RED original lacked mandatory treatment call',lambda:equal('preflight_treatment(run, reference, cell, examples)' in old,False))
ok('GREEN treatment call precedes graph representation dispatch',lambda:equal(new.index('preflight_treatment(run, reference, cell, examples)')<new.index("if cell['arm'] in PRICE_ARMS"),True))
ok('new dependency is not falsely released',lambda:equal(m.PRODUCER_SOURCE_PINS,None))
ok('no numerical import executed',lambda:equal(any(x in sys.modules for x in ('numpy','torch','scipy')),False))
(D/'CHECKS01.json').write_text(json.dumps({'scope':'pure opaque metadata/AST only; no genuine run, graph, claim or financial authority','checks':checks,'count':len(checks),'failures':[]},indent=2)+'\n')
print(len(checks),'checks passed')
