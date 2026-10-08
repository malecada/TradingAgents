import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=Path.cwd();name='eth-paper-real-data-end-to-end-resource-20261008-21';wf='db8a30b46d4a51935c063f6ab718cab337aca2e15be0d9c49460466aae02ca15';graph='0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba';rep=R/'research_artifacts/onchain_representations'/wf/name;stage=rep/'compact'/('mcm-'+graph);producer=R/'research_artifacts/onchain_compact_mcm'/wf/name/('mcm-'+graph);e={}
def load(p):
 b=p.read_bytes();e[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return json.loads(b)
f=load(rep/'failed.json');ret=load(stage/'checkpoints/failed.json');match=load(stage/'matching/failed.json');prod=load(producer/'failed.json');arc=load(rep/'archive-operations'/('writer-mcm-'+graph+'-0000')/'failed.json');imp=load(rep/'compact/dictionary-import/import-complete.json')
assert f['status']=='failed' and f['parent'] is None and f['workflow_identity'] is None and len(f['required_graphs'])==7
assert ret['error_type']=='PlannedScoringStop' and ret['execution_admitted'] is False and ret['restart_permitted'] is False
assert match['status']=='failed' and match['events']==2048 and match['archived_chunks']==0 and match['error_type']=='RuntimeError'
assert prod['status']=='failed' and arc['status']=='failed' and arc['reservations_retained'] is True
assert imp['kind']=='dictionary-import-complete' and imp['execution']['current_source']=='a4ae14412bffef123e1b2602bab023dcb1a4f616' and imp['historical_work_recomputed'] is False
assert not (rep/'complete.json').exists() and not (producer/'complete.json').exists() and not (stage/'stage-complete.json').exists()
x={'decision':'accepted-terminal-metadata-supplement','identity':name,'evidence':e,'representation_failure':f,'retention_failure':ret,'matching_failure':match,'producer_failure':prod,'archive_writer_failure':arc,'import_complete_metadata_present':True,'qualifications':['Matching failed marker original RuntimeError remains unchanged; primary outer reason is PlannedScoringStop.2048 events is retained metadata, not independently parsed binary-chain proof.','Dictionary import complete does not imply MCM/model completion. No full representation/stage/producer completion marker observed.','No numeric bodies opened or evaluated; retained binary artifacts require opaque preservation and separate recovery only.']}
(H/'ARTIFACT_JOIN02.json').write_text(json.dumps(x,indent=2)+'\n');print(hashlib.sha256((H/'ARTIFACT_JOIN02.json').read_bytes()).hexdigest())
