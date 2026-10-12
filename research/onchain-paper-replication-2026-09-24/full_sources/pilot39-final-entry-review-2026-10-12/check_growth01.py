"""Independent scalar reconstruction of supplied observation/terms; no helper imports or scans."""
import hashlib,json,stat
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];F=D.parent;E=F/'real-data-pilot-full39-entry-preparation01-2026-10-12';C=F/'pilot39-whole-capacity-candidate-2026-10-12';N='eth-paper-real-data-end-to-end-resource-20261012-39';evidence={};checks=[]
def pin(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink();b=p.read_bytes();v={'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};evidence[v['path']]=v['sha256'];return v
def load(p):pin(p);return json.loads(p.read_bytes())
def ck(name,v):assert v,name;checks.append(name)
o=load(E/'BASELINE_STORAGE_OBSERVATION01.json');t=load(E/'ROOT_GROWTH_TERMS01.json');p=load(E/'ROOT_GROWTH_PROJECTION01.json');m=load(C/'WHOLE_METADATA01.json');dep=load(E/'DEPENDENCY_PINS01.json');ops=load(E/'ROOT_OBSERVATION_OPERATION01.json')
ck('exact actual identity/source/block',o['experiment']==N and o['source']=='f0daad8bd480f4e28838424d0124480bff032af7' and o['filesystem_block_bytes']==4096 and o['kind']=='final-post38-whole39-writable-union')
ck('actual observation operation',ops['actual_exit']==0 and ops['claim'] is False and ops['numerical_execution'] is False and ops['source_anchor']==o['source'])
for n in ('ROOT_OBSERVE01.stdout','ROOT_OBSERVE01.stderr'):pin(E/n)
ck('terms exact original observation',t['observation_sha256']==pin(E/'BASELINE_STORAGE_OBSERVATION01.json')['sha256'])
ck('accepted scalar model exact hash',pin(C/'capacity.py')['sha256']==dep['capacity.py']=='c1d391d2b9d1decc734a4719a57c8e809b0b2ec68622383066c6dfb39cef1586')
for n in ('WHOLE_METADATA01.json','INPUT_SOURCE_PINS01.json'):ck('dependency '+n,pin(C/n)['sha256']==dep[n])
for name,v in load(C/'INPUT_SOURCE_PINS01.json').items():z=pin(R/name);ck('unchanged pinned storage evidence '+name,z['sha256']==v['sha256'] and z['bytes']==v['bytes'])
qualified=load(F/'pilot38-preparation-outcome-review-2026-10-12/OUTCOME_REVIEW01.json');rec=F/'real-data-pilot-full24-preparation-increment01-2026-10-09/full38outcome35/FRESH_GIT_RECOVERY35.json';review=load(F/'pilot38-outcome-increment35-review-2026-10-12/RETURN_REVIEW01.json')
ck('genuine38 closed failed component',qualified['original_outer_status']=='failed' and qualified['original_outer_attempt_spent'] and qualified['component_qualification']['accepted'] and qualified['closure']['accepted'])
ck('genuine35 accepted exact recovery',review['decision']=='accepted' and review['evidence'][str(rec.relative_to(R))]==pin(rec)['sha256'])
src_review=load(F/'pilot39-entry-source-review-2026-10-12/SOURCE_PUBLIC_REVIEW01.json');ck('independent actual73 public source review',src_review['decision']=='accepted' and src_review['identity']==N and src_review['all_input_roles']==73)
ck('fresh route no imported prefix',m['continuation_manifest_input'] is None and m['graph_manifest_inputs']=={} and m['batch_cells']==4096 and m['group_batches']==16)
cells=batches=groups=0
for g in p['graphs']:
 orig=m['graphs'][g['graph']];c=32*orig['nodes'];b=(c+4095)//4096;k=(b+15)//16
 ck('whole graph '+g['graph'],orig['motifs']==32 and (g['cells'],g['batches'],g['groups'])==(c,b,k) and g['prefix_bytes']==4096*b and g['retained_origins_bytes']==9*c and g['retained_summaries_bytes']==8192*b and g['spool_and_output_bytes']==8*c)
 cells+=c;batches+=b;groups+=k
ck('all7 exact cardinality',len(p['graphs'])==7 and (cells,batches,groups)==(415968128,101559,6352))
# Reuse immutable base-route terms; independently reconstruct changed residuals/additions and sums.
base={'scores_origins_summaries_spool_output_work_typed_receipts':(9086624428,9480953856),'checkpoint_one_fatal_live_attempt':(273838080,273838080),'temporary_group_archive_and_recovery_journal':(16090560,16352640),'retained_transport_controls_diagnostics_failure':(236017056,236283231),'owner_stage_publication_sidecars':(1089536,1343426),'current_metadata_headroom':(1048576,1048576)}
for dom,key,lc,ac in [('runtime_temp_cache','runtime_temp_cache_residual',268435456,288354304),('training_and_lifecycle','training_lifecycle_residual',33554432,33933244)]:
 a=o['storage_observation']['residual_domains'][dom];ck('actual residual caps '+dom,a['policy']['logical_bytes']==lc and a['allocated_threshold_bytes']==ac and a['logical_file_bytes']<=lc and a['allocated_bytes']<=ac);base[key]=(lc-a['logical_file_bytes'],ac-a['allocated_bytes'])
base['continuation_markers_and_conservative_live_delta']=(4096*batches+98304,)*2;base['directory_growth']=(0,t['directory_allocated_bytes']);base['other_writers']=(t['other_writer_logical_bytes'],t['other_writer_allocated_bytes']);base['additional_headers_edges']=(t['additional_headers_edges_logical_bytes'],t['additional_headers_edges_allocated_bytes']);base['other_new']=(t['other_new_logical_bytes'],t['other_new_allocated_bytes'])
ck('complete component decomposition',p['components']=={k:dict(zip(('logical_file_bytes','allocated_bytes'),v)) for k,v in base.items()})
ck('conservative declared directory/other-writer allowance',t['base_entry_bound']==650016 and t['directory_allocated_bytes']==2*1024**3+65536 and t['directory_entries']==101559 and t['other_writer_logical_bytes']==t['other_writer_allocated_bytes']==1024**3 and t['other_writer_entries']==0)
ck('zero added copies/new writers explicit',all(t[k]==0 for k in t if k.startswith(('additional_headers_edges_','other_new_')) and not k.endswith('evidence')))
growth={'logical_file_bytes':sum(v[0] for v in base.values()),'allocated_bytes':sum(v[1] for v in base.values()),'entries':650016+101559+t['directory_entries']+t['other_writer_entries']+t['additional_headers_edges_entries']+t['other_new_entries']};ck('reconstructed growth',growth==p['growth'])
projection={k:o['storage_observation'][k]+v for k,v in growth.items()};ck('reconstructed baseline plus growth',projection==p['projection'])
limits={'logical_file_bytes':17179869184,'allocated_bytes':21474836480,'entries':1000000,'disk_floor_bytes':10737418240,'memory_max_bytes':6442450944,'memory_high_bytes':5368709120,'swap_max_bytes':0,'cpus':2,'wall_seconds':28800,'startup_reserve_bytes':2684354560};ck('unchanged full caps',t['limits']==limits)
margins={k:limits[k]-v for k,v in projection.items()};margins.update(filesystem_free_after_growth_and_floor=o['disk_free_bytes']-growth['allocated_bytes']-limits['disk_floor_bytes'],startup_free_after_floor_and_reserve=o['disk_free_bytes']-limits['disk_floor_bytes']-limits['startup_reserve_bytes'],inodes_after_growth=o['free_inodes']-growth['entries']);ck('reconstructed physical/logical/inode margins',margins==p['margins'] and all(v>=0 for v in margins.values()))
ck('explicit limited result',p['storage_caps_and_floor_pass'] and p['memory_fit_proven'] is False and p['physical_reservation'] is False and p['missing_terms']==[])
# Freshness remains an observed sample, not permanently promoted into raw evidence.
ck('raw observation not rewritten as admission',all(k not in o for k in ('post38_closed_and_recovered','source_and_scope_current','observation_sha256')))
result={'decision':'accepted_prospective_guarded_storage_only','checks':checks,'evidence':evidence,'projection':projection,'margins':margins,'qualifications':['Independent arithmetic only; no observation/helper/admission or numerical execution.','Raw observation remains a dated non-atomic sample; derived closure/currentness flags supported by exact accepted receipts/current storage pins.','No physical reservation or proof of full forward/backward/Adam/checkpoint memory fit.','Other-writer and directory envelopes are conservative declared assumptions with sampled guard, not hard quotas; any added writer/copy/route requires recalculation.','Only191808016 logical bytes margin remains; actual source/input/runtime/namespace/resource checks and new entry recovery/release remain pending.']}
with (D/'GROWTH_CHECK01.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
review={'decision':'accepted','identity':N,'terms':pin(E/'ROOT_GROWTH_TERMS01.json'),'observation':pin(E/'BASELINE_STORAGE_OBSERVATION01.json')}
with (D/'GROWTH_REVIEW01.json').open('x') as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'checks':len(checks),'review':pin(D/'GROWTH_REVIEW01.json'),'projection':projection,'margins':margins}))
