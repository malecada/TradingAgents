"""Metadata-only June13 handoff generator; no array opens or runtime authority."""
from pathlib import Path
import hashlib,json,stat,types
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];F=HERE.parent
COUNT_DIR=F/'real-data-pilot-june13-reuse-count01-2026-10-06'
LEGACY=ROOT/'tradingagents/research/onchain_replication/graph_legacy_coverage.py'
LEGACY_SHA='da4bccabb15f69ce55024cc291f963498ffdc473c30d1d69d7d8e4ea7a7c20e7'
COUNT_MANIFEST_SHA='58ecb227b0d0b126045f227d4681e829ce811b827c910824bdc1266d283ff6ef'
KEY='0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba'
def need(v,m):
 if not v:raise ValueError(m)
def read(path,expected=None):
 path=Path(path);info=path.lstat()
 need(path.resolve(strict=True)==path and stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=2*1024**2,'bounded original metadata required')
 raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 need(expected is None or sha==expected,'metadata pin differs: '+str(path))
 return raw,{'path':str(path.relative_to(ROOT)),'sha256':sha,'bytes':len(raw)}
def generate(out):
 out=out.resolve();need(out.parent==HERE and not out.exists(),'fresh direct-child output required')
 raw,_=read(LEGACY,LEGACY_SHA);legacy=types.ModuleType('fixed_legacy_metadata');exec(compile(raw,str(LEGACY),'exec'),legacy.__dict__)
 raw,count_manifest_ref=read(COUNT_DIR/'MANIFEST01.json',COUNT_MANIFEST_SHA);members=json.loads(raw)['members']
 def accepted(name):
  raw,ref=read(COUNT_DIR/name,members[name]['sha256']);need(len(raw)==members[name]['bytes'],'accepted metadata size differs');return json.loads(raw),ref
 count,count_ref=accepted('COUNT_DRAFT02.json');body,body_ref=accepted('ORIGINAL_BODY_HASH02.json');header,header_ref=accepted('HEADER_OBSERVATION02.json')
 need(count['rows']==1768268 and count['graph_manifest_sha256']==legacy.EVIDENCE['graph_manifest']['sha256'] and count['evidence']==header_ref,'accepted count/header chain differs')
 inputs={};raws={}
 for name,ref in legacy.EVIDENCE.items():
  raw,_=read(ROOT/ref['path'],ref['sha256']);role='legacy_'+name;inputs[role]={'dataset':'eth',**ref};raws[role]=raw
 manifest=json.loads(raws['legacy_graph_manifest']);need(manifest['graph_hash']==KEY,'fixed graph differs')
 coverage_path=F/'real-data-end-to-end-pilot-preparation01-2026-10-05/LEGACY_GRAPH_EVIDENCE_DRAFT01.json'
 raw,coverage_ref=read(coverage_path,'3153c0bb910cef6a47caa5e00cd52ea0efed25ce970981cdd0090ccbd6cd7dfa');coverage=json.loads(raw)
 # Existing pure validator only, using authentic metadata carrier; no fake Run.
 result=legacy.verify_legacy_coverage(coverage,types.SimpleNamespace(**manifest['metadata']),legacy.EVIDENCE['graph_manifest']['sha256'],raws.__getitem__)
 need(result['parent_status']=='failed' and result['graph_cell_status']=='complete','historical distinction differs')
 need(body['decision']=='pass' and len(body['files'])==5,'accepted five-body denominator differs')
 observed=[]
 for row in body['files']:
  p=ROOT/row['path'];info=p.lstat();sig=[info.st_dev,info.st_ino,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns]
  need(p.resolve(strict=True)==p and stat.S_ISREG(info.st_mode) and info.st_nlink==1 and stat.S_IMODE(info.st_mode)==row['mode'] and sig==row['stat_identity'],'accepted array stat changed: '+row['path'])
  key=p.stem;item=manifest['arrays'][key]
  need(p.parent==ROOT/legacy.EVIDENCE['graph_manifest']['path'].rsplit('/',1)[0] and item['path']==p.name and item['bytes']==row['bytes'] and item['sha256']==row['sha256'],'original array/accepted body join differs')
  observed.append({'path':row['path'],'mode':row['mode'],'stat_identity':sig,'inherited_sha256':row['sha256']})
 need({Path(x['path']).stem for x in observed}==set(manifest['arrays']),'whole original array roster differs')
 inputs['legacy_graph_evidence']={'dataset':'eth','path':coverage_ref['path'],'sha256':coverage_ref['sha256']}
 inputs['graph_20220613']=dict(inputs['legacy_graph_manifest'])
 handoff={'schema_version':1,'status':'DRAFT_NOT_ADMITTED','week':'2022-06-13T00:00:00Z','graph_hash':KEY,'graph_input_role':'graph_20220613','registered_input_templates':inputs,'count_ref':count_ref,'reuse_evidence':{'accepted_count_manifest':count_manifest_ref,'five_body_proof':body_ref,'header_observation':header_ref},'original_parent_status':'failed','original_graph_component_status':'complete','modern_original_producer_plan':None,'future_root_bindings':{'current_source':None,'registration':None,'genuine_resource_admission':None,'independent_entry_review':None},'authority':'No new claim, Owner, Binding, source-worker execution, representation_complete or budget transfer. Existing genuine pilot establishes its own current authority.'}
 current={'scope':'five closed June13 arrays: stat-only currentness join to accepted one-pass body proof','arrays':observed,'array_body_bytes_read':0,'writer_exclusion':False,'qualification':'Observed signatures are not immutable writer exclusion. Genuine future load_graph and Target still verify complete content/currentness; no hash skip is added.'}
 out.mkdir()
 for name,value in [('HANDOFF_DRAFT01.json',handoff),('CURRENT_STAT_JOIN01.json',current),('METADATA_CHECK01.json',{'decision':'pass-metadata-only','existing_validator_result':result,'actual_original_roles':19,'arrays_stat_joined':5,'array_payload_reads':0,'genuine_authority_called':False})]:
  with (out/name).open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
 return handoff
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();generate(args.output)
