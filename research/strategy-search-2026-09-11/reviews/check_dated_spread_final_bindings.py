"""Independent final metadata/source binding check; no admission or financial inputs parsed."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));P=ROOT/'research/strategy-search-2026-09-11'
from tradingagents.research_spread import runtime_hashes
def read(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
gate=read(P/'gates-dated-spread.json');name='dated-spread-book-20260911';exp={k:v for k,v in gate['experiments'][name].items()if k!='budget_book_grant'}
parent=read(ROOT/'research_runs/dated-mark-20260911/claim.json');before=parent['experiment'];manifest=read(P/'dated-spread-change-manifest.json')
changes={key:{side:{'present':key in value,**({'value':value[key]}if key in value else {})}for side,value in [('before',before),('after',exp)]}for key in set(before)|set(exp)if key not in before or key not in exp or canon(before[key])!=canon(exp[key])}
assert manifest=={'schema_version':1,'baseline_experiment':parent['experiment_id'],'target_experiment':name,'baseline_contract_sha256':sha(canon(before)),'target_contract_sha256':sha(canon(exp)),'changes':changes}
assert sha(canon(exp))=='61691a3fc2ede27a1d4f41c23b0436ce43fad918c88a4c076cc9fa4db2d32ec1'
assert exp['runtime_hashes']==runtime_hashes()
for path,digest in exp['source_files'].items():assert sha((ROOT/path).read_bytes())==digest
for item in [exp['charter'],*exp['inputs'].values()]:assert sha((ROOT/item['path']).read_bytes())==item['sha256']
assert len(exp['inputs'])==8 and exp['cells']==[f'{a}-{c}-{s}'for a in ['btc','eth']for c in [1000,10000]for s in ['base','stress']]
assert exp['outputs']==['books.json','summary.json','source-audit.json']
assert [(w['start'],w['end'])for w in exp['windows']]==[('2026-05-01T00:00:00Z','2026-06-26T00:00:00Z')]*2
assert exp['stage']=='development' and exp['reuse']=='exploratory'
inventory={};family=gate['families'][exp['family']]
for folder in sorted((ROOT/'research_runs').iterdir()):
 if folder.name.startswith('.'):continue
 claim=read(folder/'claim.json')
 if claim['family']['mechanism_id']!=family['mechanism_id']:continue
 assert folder.name!=name and claim['family']==family
 terminal=[p for p in [folder/'complete.json',folder/'failed.json']if p.exists()];assert len(terminal)==1
 inventory[folder.name]={'claim_sha256':sha((folder/'claim.json').read_bytes()),'terminal':terminal[0].name,'terminal_sha256':sha(terminal[0].read_bytes())}
 old=json.loads(subprocess.check_output(['git','show',claim['source']+':'+claim['registration']],cwd=ROOT))
 for collection in ['families','experiments','datasets']:
  for key,value in old[collection].items():assert gate[collection][key]==value
 physical=subprocess.check_output(['git','show',parent['source']+':'+claim['registration']],cwd=ROOT);assert (ROOT/claim['registration']).read_bytes()==physical
assert len(inventory)==5 and family['attempt_budget']==4 and family['prior_attempts']==1
latest=read(P/'gates-dated-mark.json')
for collection in ['families','experiments','datasets']:
 for key,value in latest[collection].items():assert gate[collection][key]==value
reports=[]
for mode in ['full','partial','unavailable']:
 resultpath=P/f'reviews/dated-spread-cli-preflight-{mode}-result.json';guardpath=P/f'reviews/dated-spread-cli-preflight-{mode}-guard.json';r=read(resultpath);g=read(guardpath)
 assert r['runtime_hashes']==runtime_hashes() and r['complete_primary']=={'full':8,'partial':4,'unavailable':0}[mode]
 assert r['complete_primary']+r['unavailable_primary']==8 and (r['scalars'],r['stresses'],r['output_files'],r['cpu_count'])==(16,72,3,2)
 assert r['output_bytes']<=8*1024**2 and g['child_exit_code']==0 and g['limit_reason']is None and g['wall_limit_seconds']==120 and g['rss_limit_bytes']==512*1024**2
 for key,value in r['source_sha256'].items():
  if key.startswith('research/'):assert sha((ROOT/key).read_bytes())==value
  elif key.startswith('test_'):assert sha((ROOT/'tests/research'/key).read_bytes())==value
  elif key=='resource_guard_v2.py':assert sha((P/key).read_bytes())==value
 for path in [guardpath,resultpath]:reports.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path.read_bytes())})
for prefix in ['dated-spread-lifecycle-preflight','dated-v2-actual-snapshot']:
 for kind in ['guard','result']:
  path=P/f'reviews/{prefix}-{kind}.json';value=read(path)
  if kind=='guard':assert value['child_exit_code']==0 and value['limit_reason']is None
  elif prefix=='dated-v2-actual-snapshot':
   assert value['status']=='PASS' and value['runtime_hashes']==runtime_hashes()
   for key,item in inventory.items():assert {k:value['current_same_mechanism_inventory'][key][k]for k in item}==item
  reports.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path.read_bytes())})
report={'passed':True,'target_contract_sha256':sha(canon(exp)),'change_manifest_sha256':sha((P/'dated-spread-change-manifest.json').read_bytes()),'prior_claims_sha256':sha(canon(inventory)),'prior_claims':inventory,'source_pin_count':len(exp['source_files']),'runtime_pin_count':len(exp['runtime_hashes']),'input_byte_total':sum((ROOT/x['path']).stat().st_size for x in exp['inputs'].values()),'preflight_reports':reports,'scope':'Read-only final target/source/raw byte hashes and prior claim metadata. Actual input payloads are hashed but not parsed or financially evaluated. No new claim, network or financial calculation. Commit/design equality and exact certificate reference remain final execution prerequisites.'}
(Path(__file__).parent/'dated-spread-final-bindings-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['prior_claims','preflight_reports']},indent=2))
