import hashlib,json,stat
from pathlib import Path
P=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,j):
    with (P/n).open('x') as f:json.dump(j,f,sort_keys=True,indent=2);f.write('\n')
r=json.loads((P/'READBACK01.json').read_bytes())
def ref(suffix,funcs):
    matches=[x for x in r['sources'] if x['path'].endswith(suffix)]
    assert len(matches)==1
    x=matches[0]
    return {'path':x['path'],'sha256':x['sha256'],'functions':[d for d in x['definitions'] if d['name'] in funcs]}
stages=[
 {'role':'current genuine production','state':'implemented_in_current_source_no_execution_observed','source':ref('/source/tradingagents/research/onchain_replication/compact_mcm.py',['produce_imported','_produce_locked','Produced._check']),'handoff':'Actual ImportedExecution + GraphSnapshot -> Target -> held Owner/Stage -> completed stream -> closed Stage -> publication -> genuine Produced; current source has no codec consumer'},
 {'role':'f64 original ranges','state':'prepared_source_not_installed','source':ref('held-score-reader-preparation01-2026-10-03/held_score_reader.py',['HeldBatches','HeldBatches._authority','HeldBatches.read_part','open_held']),'handoff':'Only while original Stage active and actual stream completed; exact original f64 member bytes, aligned <=1MiB, retain metadata/terminal and full Target.check'},
 {'role':'completed raw-f32 original ranges','state':'prepared_source_not_installed','source':ref('adapter-preparation02-2026-10-03/completed_f32.py',['CompletedF32','CompletedF32._authority','CompletedF32.read_part','completed_worker','consume_if_selected']),'handoff':'Actual Produced and original held token after Stage close, current Owner before close, original matrix.f32 plus manifest; no NPY/scientific lineage substitution'},
 {'role':'durable original non-tail accounting','state':'prepared_source_not_installed','source':ref('adapter-preparation02-2026-10-03/archive_non_tail.py',['Context','Ledger','Operation','Operation.reserve_next','Operation.verify_local_recovery']),'handoff':'Actual ResearchRun -> Context -> exact typed original source -> Ledger -> one-use Operation; independent original population and no-refund reservations'},
 {'role':'selected original transport','state':'prepared_source_not_installed_no_actual_transfer','source':ref('adapter-preparation02-2026-10-03/selected_non_tail_transport.py',['Session._reserve','Session._command','Session.run','dispatch']),'handoff':'Real source-derived operation, fixed registered bounded SSH roundtrip, full original container recovery, no disposition authority or wire-metering claim'},
 {'role':'engineering router','state':'candidate_source_only','source':ref('integration-preparation01-2026-10-04/router04.py',['inspect','route','estimate','Router.run','production','Router.release']),'handoff':'Already complete codec directories -> unchanged partitions -> callback engineering acknowledgments -> retained recovered LocalStore; production and release refuse'},
 {'role':'current target boundary','state':'implemented_in_current_source_no_execution_observed','source':ref('/source/tradingagents/research/onchain_replication/imported_mcm_identity.py',['Target.derive_scope','Target.lease','Target.check','Target.final']),'handoff':'Original graph/node-order/dictionary/ordered-motif/matching/workflow six hashes plus full actual source/input/import ancestry; full checks cannot be replaced with caller callback'},
]
requirements=[
 {'id':'P1','missing':'actual current-code integration and coherent new admitted source closure','evidence':'four prepared modules absent; current financial_wrapper differs from prepared compact_resource and two-tiny-target closure'},
 {'id':'P2','missing':'genuine original-source to codec cursor','evidence':'router inspect requires complete codec source; neither genuine range adapter emits codec frames; preserve every original companion and derived whole hash'},
 {'id':'P3','missing':'production route capacity and complete per-target inputs','evidence':'prepared two tiny targets and 8KiB ledger; router16 targets/20000members/2048plans/4MiB intent; actual input-derived node/chunk/member population unobserved'},
 {'id':'P4','missing':'common cumulative original+codec+spool+recovery storage lease and finite outer guard','evidence':'current Owner, publication reservation, sampled whole watch and router engineering ledger are separate; all physical duplicates still retained'},
 {'id':'P5','missing':'typed actual codec transport/recovery receipt and current authority bridge','evidence':'prepared Session handles original member containers; engineering RoutedAck/Recovery callbacks do not verify remote origin or genuine ownership'},
 {'id':'P6','missing':'separately admitted retirement and cold/external-backed readers','evidence':'current original checks require local complete membership/inodes; every prepared non-tail receipt says no disposal and zero bytes retired'},
 {'id':'P7','missing':'complete graph-artifact companion handling and scientific lineage','evidence':'f32 raw route is not graph NPY/edges/component context and imported resource output is not completed scientific cold publication'},
 {'id':'P8','missing':'genuine whole-method resource and agreement evidence','evidence':'resident kernel matrix, fixed tensors, graph activations, joint gradients/Adam/RNG/checkpoint, all registered examples retained; no numeric execution performed'},
]
for x in r['sources']:
    p=Path(x['path']);assert sha(p.read_bytes())==x['sha256'] and stat.S_IMODE(p.lstat().st_mode)==x['mode']
write('HANDOFF01.json',{'status':'BOUNDED_SOURCE_INVESTIGATION_COMPLETE_PRODUCTION_UNAVAILABLE','readback_sha256':sha((P/'READBACK01.json').read_bytes()),'report_sha256':sha((P/'REPORT01.md').read_bytes()),'calls':stages,'requirements':requirements,'future_actual_pins':{'production_source':None,'registration':None,'transport_release':None,'complete_per_target_inventory':None,'remote_recovery':None,'retirement':None,'measured_capacity':None},'unperformed':r['unperformed'],'late_source_hashes_unchanged':len(r['sources']),'no_new_claim_or_budget':True})
rows=[]
for p in sorted(P.rglob('*')):
    s=p.lstat();row={'path':p.relative_to(P).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
    if stat.S_ISDIR(s.st_mode):row['kind']='directory'
    elif stat.S_ISREG(s.st_mode):row.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()))
    else:raise AssertionError('unexpected own type')
    rows.append(row)
write('MANIFEST01.json',{'schema_version':1,'kind':'complete-owned-source-investigation','self_excluded':'MANIFEST01.json','members':rows,'regular_files':sum(x['kind']=='file' for x in rows),'regular_bytes':sum(x.get('bytes',0) for x in rows),'count':len(rows)})
print(json.dumps({'manifest':sha((P/'MANIFEST01.json').read_bytes()),'handoff':sha((P/'HANDOFF01.json').read_bytes()),'report':sha((P/'REPORT01.md').read_bytes()),'regular_files':len(rows),'regular_bytes':sum(x.get('bytes',0) for x in rows)}))
