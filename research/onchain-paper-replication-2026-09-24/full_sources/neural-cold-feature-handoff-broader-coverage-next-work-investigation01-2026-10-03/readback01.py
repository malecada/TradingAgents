"""Only explicit hash-pinned source/metadata reads. No acquisition or admission."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
refs=json.loads((HERE/'source_refs01.json').read_bytes());assert refs['count']<=40 and refs['total_bytes']<=4194304
bodies={}
for row in refs['files']:
 p=ROOT/row['path'];raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];bodies[row['path']]=raw
R='research/onchain-paper-replication-2026-09-24/';H='research_runs/paper-full-source-metadata-20260924/'
def doc(name):return json.loads(bodies[name])
coverage=doc(H+'outputs/source-coverage.json');term=doc(H+'complete.json');claim=doc(H+'claim.json');grid=doc(R+'full_sources/required-grid-v3.json');storage=doc(H+'outputs/storage-summary.json')
assert term['status']=='complete' and term['claim_sha256']==hashlib.sha256(bodies[H+'claim.json']).hexdigest()
for n in ('source-coverage.json','storage-summary.json'):assert term['output_sha256'][n]==hashlib.sha256(bodies[H+'outputs/'+n]).hexdigest()
assert claim['registration']==R+'full_sources/metadata-01/gate-v3.json';assert claim['registration_sha256']==hashlib.sha256(bodies[claim['registration']]).hexdigest()
assert len(coverage['catalogues'])==18 and all(x['listing_complete'] and x['listed_dates']==len(x['dates'])==x['required_dates'] for x in coverage['catalogues'].values());assert coverage['required_cells']==85488 and not coverage['transaction_data_admitted']
assert grid['counts']=={'complete_price_cells':6576,'pending_transaction_field_cells':82200,'total':88776}
candidates=[]
for asset in ('BTC','ETH'):
 for year in range(2016,2025 if asset=='BTC' else 2022):
  key=f'{asset}-{year}';c=coverage['catalogues'][key];objects=[o for d in c['dates'].values() for o in d['objects']]
  candidates.append({'asset_year':key,'dates':len(c['dates']),'objects':len(objects),'listed_complete_object_bytes':sum(o['bytes'] for o in objects),'maximum_object_bytes':max(o['bytes'] for o in objects),'historical_catalogue_path':f'research_artifacts/onchain-paper-replication-2026-09-24/sources/paper-full-source-metadata-20260924/{key}-catalogue.json','selected_column_bytes':'unknown until actual footer plan','current_ETag_available':'not probed','source_body_status':'not established by metadata','action':'source-contract preparation only; no identity assigned'})
assert len(candidates)==15
for path,name in [('tradingagents/research/onchain_replication/range_source.py','capture_ranges'),('tradingagents/research/onchain_replication/job.py','execute_source_job')]:assert any(isinstance(n,ast.FunctionDef) and n.name==name for n in ast.parse(bodies[path]).body)
out={'scope':'metadata-only; historical listings authenticated through closed complete output hashes','historical_metadata_claim':'CLOSED_COMPLETE_NEVER_REPLAY','historical_field_denominator':85488,'current_required_grid':grid['counts'],'listed_asset_years':18,'listed_asset_dates':sum(x['listed_dates'] for x in coverage['catalogues'].values()),'listed_BTC_bytes':sum(v for k,v in storage['listed_object_bytes'].items() if k.startswith('BTC')),'listed_ETH_bytes':sum(v for k,v in storage['listed_object_bytes'].items() if k.startswith('ETH')),'prospective_missing_asset_year_contracts':candidates,'new_acquisition_performed':False,'financial_fit_or_fund_cohort_admitted':False}
(HERE/'readback01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('PASS30 pinned bodies / metadata COMPLETE joins /18 catalogues /6576listed asset-dates /15 prospective contracts. No acquisition or data admission.')
