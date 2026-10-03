"""Registered guarded treatment production; numerical imports are execution-only.

Source candidate only. No permission to create historical cohort evidence.
"""
import json
from pathlib import Path
from types import SimpleNamespace
from .treatment_contract import schema,cohort,parent_receipts,require,stamp


def _metadata(run,name):
 raw=run.read_input(name);require(len(raw)<=4*1024**2,'bounded treatment metadata required');return json.loads(raw),raw

def _guard(run,plan_input):
 from ..lifecycle import ResearchRun
 from . import job,resources
 from .provenance import file_hash
 require(type(run)is ResearchRun,'genuine ResearchRun required');run._active();run._check_source()
 root=run.admission.root
 for name in ('treatment_contract.py','treatment_production.py','subsets.py','btc_subsets.py','graph_store.py','btc_store.py','graph_production.py'):
  path=Path(__file__).parent/name;relative=str(path.relative_to(root))
  require(run.admission.experiment['source_files'].get(relative)==file_hash(path),'unadmitted treatment dependency source')
 spec,_=_metadata(run,'execution_job')
 require(spec['kind']=='treatments' and spec['payload']=={'plan_input':plan_input},'genuine treatment job input required')
 args=SimpleNamespace(root=str(root),registration=run.admission.registration,experiment=run.admission.experiment_id,source=run.admission.source)
 policy=spec['resources'];base=job._base(args)
 live=resources.assert_guarded_worker(base/'guard',job._command(args,'worker'),required_paths=[Path(p) for p in policy['disk_paths']],wall_seconds=policy['wall_seconds'],memory_max_bytes=policy['memory_max_bytes'],memory_high_bytes=policy['memory_high_bytes'],disk_floor_bytes=policy['disk_floor_bytes'])
 owner=json.loads((base/'owner.json').read_bytes())
 require(live['owner_identity']==owner and owner['experiment']==args.experiment and owner['source_commit']==args.source and all(live[k]==v for k,v in policy.items()),'actual native owner/policy differs')
 return live

def _close(actions,primary):
 chosen=primary
 for action in actions:
  try:action()
  except BaseException as error:
   fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
   if chosen is None or (fatal(error) and not fatal(chosen)):chosen=error
 if chosen is not None:raise chosen

def produce_registered_treatments(run,plan_input):
 _guard(run,plan_input)
 from ..lifecycle import _immutable
 from ..admission import local_path
 from .provenance import digest,file_hash,durable_mkdir,sync_directory
 p,plan_raw=_metadata(run,plan_input);ids=schema(p)
 require(run.admission.experiment['cells']==ids,'registered complete treatment denominator differs')
 from datetime import timedelta
 windows=[(stamp(w['start']),stamp(w['end'])) for w in run.admission.experiment['windows']]
 for week in p['expected_weeks']:require(any(a<=stamp(week) and stamp(week)+timedelta(days=7)<=b for a,b in windows),'week outside admitted window')
 directory=run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/treatments'/run.admission.experiment_id
 durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent)
 _immutable(directory/'intent.json',{'plan_sha256':digest(plan_raw),'claim_sha256':run._claim_sha256,'source':run.admission.source,'cells':ids,'financial_credit':0})
 rows={};graphs={};primary=None
 def record(row):_immutable(directory/(row['id']+'.json'),row);rows[row['id']]=row
 try:
  for week,cell in zip(p['expected_weeks'],ids,strict=True):
   try:
    _guard(run,plan_input)
    if p['variant']=='fund' and p['cohort_input'] is None:
     record({'id':cell,'status':'unavailable','reason':'original historical65-entity address cohort and independent vintage evidence unavailable','asset':p['asset'],'week':week});continue
    ref=p['parents'][week];manifest,mraw=_metadata(run,ref['manifest_input']);proof,praw=_metadata(run,ref['coverage_input']);claim,craw=_metadata(run,ref['claim_input']);terminal,traw=_metadata(run,ref['terminal_input']);ledger,lraw=_metadata(run,ref['ledger_input'])
    parent_row=parent_receipts(claim,terminal,ledger,digest(craw),digest(mraw),week,p['asset'])
    require(parent_row.get('coverage_sha256')==digest(praw),'parent completed coverage output differs')
    require(terminal.get('source')==claim.get('source') and terminal.get('registration_sha256')==claim.get('registration_sha256') and terminal.get('output_sha256',{}).get('cell-ledger.json')==digest(lraw) and terminal.get('cells')==ledger,'parent terminal/claim/ledger joins differ')
    require(proof.get('claim_sha256')==digest(craw),'parent coverage claim differs')
    path=local_path(run.admission.root,run.admission.inputs[ref['manifest_input']]['path']);required={}
    if p['asset']=='BTC':
     inner_role=ref['components'].get('graph/manifest.json');require(inner_role is not None,'BTC inner graph manifest role required');inner,inner_raw=_metadata(run,inner_role)
     require(digest(inner_raw)==manifest['graph_manifest_sha256'],'BTC inner manifest differs');required['graph/manifest.json']=digest(inner_raw)
     required.update({'graph/'+v['path']:v['sha256'] for v in inner['arrays'].values()});required.update({k+'.hex':v['sha256'] for k,v in manifest['sidecars'].items()})
    else:required={v['path']:v['sha256'] for v in manifest['arrays'].values()}
    require(set(required)==set(ref['components']),'exact graph component membership required')
    for member,pin in required.items():
     role=ref['components'][member];admitted=run.admission.inputs[role];member_path=local_path(run.admission.root,admitted['path'])
     require(member_path==path.parent/member and admitted['sha256']==pin and file_hash(member_path)==pin,'parent component not exactly registered/contained')
    end=(stamp(week)+timedelta(days=7)).isoformat().replace('+00:00','Z');members=None;cohort_hash=None;cohort_doc=None;cohort_review_hash=None
    if p['variant']=='fund':
     cohort_doc,cohort_raw=_metadata(run,p['cohort_input']);review,review_raw=_metadata(run,p['cohort_review_input']);cohort_hash=digest(cohort_raw);members=cohort(cohort_doc,review,cohort_hash,week,end);cohort_review_hash=digest(review_raw)
     for role,pin in cohort_doc['evidence_inputs'].items():require(digest(run.read_input(role))==pin,'historical cohort evidence hash differs')
    # Only now import existing numerical graph loaders and exact treatments.
    from .graph_store import load_graph,save_graph
    from .btc_store import load_btc_graph,save_btc_graph
    from .subsets import filter_graph
    from .btc_subsets import filter_btc_graph
    from .graph_production import _verify_graph_coverage
    from .neighborhoods import graph_hash
    value=(load_graph if p['asset']=='ETH' else load_btc_graph)(path,digest(mraw));parent=value if p['asset']=='ETH' else value.graph
    require(parent.asset==p['asset'] and parent.start_utc==week and parent.end_utc==end,'parent graph date/asset differs')
    _verify_graph_coverage(proof,parent,digest(mraw))
    transformed,decision=(filter_graph if p['asset']=='ETH' else filter_btc_graph)(value,p['variant'],cohort=members,cohort_hash=cohort_hash)
    graph=transformed if p['asset']=='ETH' else transformed.graph
    if cohort_doc is not None and stamp(cohort_doc['known_at'])>stamp(graph.available_at):
     from dataclasses import replace
     graph=replace(graph,available_at=cohort_doc['known_at']);transformed=graph
    require(stamp(graph.available_at)>=stamp(parent.available_at),'treatment backdated availability')
    require(decision['parent_graph_hash']==graph_hash(parent),'transformation parent join differs')
    _guard(run,plan_input)
    output=(save_graph if p['asset']=='ETH' else save_btc_graph)(directory/cell,transformed)
    receipt={'schema_version':1,'kind':'registered-graph-treatment-receipt','asset':p['asset'],'variant':p['variant'],'week':week,'end_utc':end,'available_at':graph.available_at,'parent_graph_hash':graph_hash(parent),'parent_manifest_sha256':digest(mraw),'parent_coverage_sha256':digest(praw),'parent_claim_sha256':digest(craw),'parent_terminal_sha256':digest(traw),'parent_ledger_sha256':digest(lraw),'cohort_sha256':cohort_hash,'cohort_review_sha256':cohort_review_hash,'claim_sha256':run._claim_sha256,'plan_sha256':digest(plan_raw),'source':run.admission.source,'graph_hash':graph_hash(graph),'manifest_sha256':file_hash(output),'decision':decision,'raw_event_counters':'retained original; treatment deletions separately recorded'}
    _immutable(output.parent/'treatment.json',receipt)
    # Retain genuine raw coverage, joined to transformed config/manifest; treatment is a separate mandatory receipt.
    derived={**proof,'graph_config_hash':graph.graph_config_hash,'graph_manifest_sha256':file_hash(output),'claim_sha256':run._claim_sha256,'plan_sha256':digest(plan_raw)}
    _immutable(output.parent/'coverage.json',derived)
    row={'id':cell,'status':'complete','asset':p['asset'],'week':week,'manifest_path':str(output.relative_to(run.admission.root)),'manifest_sha256':file_hash(output),'treatment_receipt_sha256':file_hash(output.parent/'treatment.json'),'coverage_sha256':file_hash(output.parent/'coverage.json')};record(row);graphs[week]=row
    del value,parent,transformed,graph
   except Exception as error:
    if isinstance(error,MemoryError):raise
    record({'id':cell,'status':'unavailable','asset':p['asset'],'week':week,'reason':type(error).__name__+': '+str(error)})
 except BaseException as error:primary=error
 finally:
  def pending():
   for week,cell in zip(p['expected_weeks'],ids,strict=True):
    if cell not in rows:record({'id':cell,'status':'unavailable','asset':p['asset'],'week':week,'reason':'not completed after '+('unknown stop' if primary is None else type(primary).__name__)})
  def summary():_immutable(directory/'result.json',{'asset':p['asset'],'variant':p['variant'],'expected_weeks':p['expected_weeks'],'graphs':graphs,'cells':[rows[k] for k in ids],'financial_credit':0,'qualification':'source treatment only; explicit treatment-receipt admission and common-mask population still required'})
  _close((pending,summary),primary)
 return [rows[k] for k in ids],json.loads((directory/'result.json').read_bytes()),directory
