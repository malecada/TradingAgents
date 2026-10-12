"""Root-only once-use metadata preparation. No claim, release, or numerical imports.
Origin slices are bounded provenance bytes, never score/numerical recomputation.
"""
from pathlib import Path
import argparse,json,hashlib,stat
P=Path(__file__).resolve().parent;R=P.parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def body(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def checked(path,expected):
 p=Path(path);s=p.lstat()
 if p.resolve(strict=True)!=p or not stat.S_ISREG(s.st_mode) or s.st_size>32*1024**2:raise ValueError('bounded canonical regular metadata required')
 b=p.read_bytes()
 if sha(b)!=expected:raise ValueError('source bytes differ: '+str(p))
 return b

def build(output):
 output=Path(output).absolute()
 if output.exists() or output.is_symlink():raise ValueError('unused metadata destination required')
 if not output.is_relative_to(R) or output.parent.resolve(strict=True)!=output.parent:raise ValueError('existing canonical repository parent required')
 contract=json.loads(checked(P/'EXACT_CONTRACT03.json','a132758a85f14f2da164230e07b19fbf09028a2c0dac638fd5a19a471952e878'))
 parent=contract['parent'];D=R/'research_runs'/parent
 graph='0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba';workflow='ada9fbd6764c8dc113bf837ff9cc71296dd9c09e6af2a9da4d7a841a2e91329f'
 G=R/'research_artifacts/onchain_representations'/workflow/parent/('compact/mcm-'+graph)
 roles={};evidence={};sources={};batches=[];generated={}
 def register(role,path,expected):
  raw=checked(path,expected);roles[role]={'path':str(path.relative_to(R)),'sha256':expected,'bytes':len(raw)};return {'role':role,'sha256':expected}
 parent_claim=register('cont39_parent_claim',D/'claim.json',contract['claim_sha256']);parent_failed=register('cont39_parent_failed',D/'failed.json',contract['failed_sha256'])
 for key,pin in contract['evidence'].items():evidence[key]=register('cont39_'+key.replace(':','_').replace('.','_').replace('-','_'),R/pin['path'],pin['sha256'])
 for path,expected in contract['sources'].items():sources[path]=register('cont39_source_'+Path(path).stem,P/'original_source'/Path(path).name,expected)
 selection=json.loads(checked(R/contract['evidence']['selection']['path'],contract['evidence']['selection']['sha256']))
 rows={r['path']:r for r in selection['rows'] if r['type']=='regular'}
 origin_path=G/'stream/numeric-origins.bin';origin_info=rows[str(origin_path.relative_to(R))];origins=checked(origin_path,origin_info['sha256'])
 if len(origins)!=65536*9:raise ValueError('exact full origin extent required')
 for i,hashes in enumerate(contract['batches']):
  refs=[]
  paths=[G/f'matching/{i:08d}.pending.json',G/f'matching/{i:08d}.records.bin',G/f'matching/{i:08d}.complete.json',None,G/f'stream/numeric-batches/{i:012d}.json',G/f'matching/{i:08d}.prefix.json']
  for j,(path,expected) in enumerate(zip(paths,hashes,strict=True)):
   role=f'cont39_batch_{i:02d}_{j}'
   if j==3:
    raw=origins[i*4096*9:(i+1)*4096*9]
    if sha(raw)!=expected:raise ValueError('origin slice differs')
    name=f'origin-{i:02d}.bin';generated[name]=raw;roles[role]={'path':str((output/name).relative_to(R)),'sha256':expected,'bytes':len(raw)};refs.append({'role':role,'sha256':expected})
   else:refs.append(register(role,path,expected))
  batches.append(refs)
 # Exact descriptor bytes are joined to all recovered pending commitments.
 descriptor={'rows':1768268,'cells':56584576,'motifs':32,'graph_hash':graph,'node_order_hash':'5dc2a871dd496f582043fab005688c0a3ac765abac45120cb158de30bf0ab575','workload_sha256':'78ac070814d3146bf1a9c711b979ae7184d2ae38880bacf969705ee8d3308edc','purpose_schema_version':2}
 descriptor_sha=sha(body(descriptor))
 for i,refs in enumerate(batches):
  pending=json.loads(checked(G/f'matching/{i:08d}.pending.json',refs[0]['sha256']))
  if pending['workload_sha256']!=descriptor_sha:raise ValueError('original descriptor join differs')
 accounting={'format':contract['format'],'parent_experiment':parent,'parent_claim_sha256':contract['claim_sha256'],'parent_failed_sha256':contract['failed_sha256'],'evidence':evidence,'source_bodies':sources,'spent_counters':contract['costs'],'retained_partial_work':{k:0 for k in contract['costs']},'preserved_unknowns':['telemetry','cache','transport','outer_disposition']}
 raw=body(accounting);generated['DERIVED_ACCOUNTING.json']=raw;roles['cont39_accounting']={'path':str((output/'DERIVED_ACCOUNTING.json').relative_to(R)),'sha256':sha(raw),'bytes':len(raw)}
 if len(roles)!=127:raise ValueError('finite role cardinality differs')
 draft={'status':'UNREVIEWED_NOT_RELEASED','parent_claim':parent_claim,'parent_failed':parent_failed,'parent_accounting_mode':contract['format'],'parent_accounting':{'role':'cont39_accounting','sha256':sha(raw)},'batches':batches,'descriptors':{descriptor_sha:descriptor},'spent_counters':contract['costs'],'ready_roles':127,'additional_required_roles':{'continuation_manifest':None,'independent_continuation_review':None,'normalized_score_offload_recovery':None,'normalized_numeric_origin_recovery':None},'total_distinct_roles_if_no_existing_aliases':131,'requires_actual_successor_contract_and_allowance':True,'independent_review_required':True,'original_outputs_modified':False,'full_graph_completion_proved':False}
 generated['REGISTERED_ROLE_MAP.json']=body(roles);generated['MANIFEST_FIELDS_DRAFT.json']=body(draft)
 output.mkdir()
 for name,raw in generated.items():
  with (output/name).open('xb') as f:f.write(raw)
 return {'status':'UNREVIEWED_METADATA_ONLY','files':len(generated),'ready_roles':len(roles),'output':str(output)}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();print(json.dumps(build(args.output),sort_keys=True))
