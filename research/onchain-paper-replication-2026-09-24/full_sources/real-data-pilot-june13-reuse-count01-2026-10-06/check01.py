import datetime,hashlib,json,stat
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;F=HERE.parent
B=ROOT/'research/onchain-paper-replication-2026-09-24'
def raw(p):
 assert p.stat().st_size<=4*1024**2 and p.resolve(strict=True)==p
 return p.read_bytes()
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def doc(p):return json.loads(raw(p))
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def put(name,v):(HERE/name).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
legacy=F/'real-data-end-to-end-pilot-preparation01-2026-10-05/LEGACY_GRAPH_INPUTS_DRAFT01.json'
inputs=doc(legacy)['inputs'];assert len(inputs)==19
for r in inputs.values():assert sha(ROOT/r['path'])==r['sha256']
mref=inputs['legacy_graph_manifest'];mp=ROOT/mref['path'];m=doc(mp)
assert mref['sha256']=='a7599cb4dce5a3d7b01614fe097026e70d48ecd63bb1c25518ccb05f41204d59'
assert m['graph_hash']=='0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba'
claim=doc(ROOT/inputs['legacy_claim']['path']);terminal=doc(ROOT/inputs['legacy_terminal']['path']);result=doc(ROOT/inputs['legacy_result']['path']);cell=doc(ROOT/inputs['legacy_cell']['path'])
assert terminal['status']=='failed' and terminal['claim_sha256']==inputs['legacy_claim']['sha256']
assert terminal['experiment_id']==claim['experiment_id']=='eth-paper-resource-pilot-20260924-02'
assert claim['source']==claim['design_source']=='c6b568d4b1c177ab94ac37fbad462c2decc721c0'
assert cell['status']==result['status']=='complete' and cell['details']==result['details']
assert result['details']['graph_manifest_sha256']==mref['sha256']
index=doc(ROOT/inputs['legacy_artifact_index']['path']);rows=[]
for name,a in sorted(m['arrays'].items()):
 p=mp.parent/a['path'];assert a['path']==name+'.npy' and p.resolve(strict=True)==p
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==a['bytes']
 assert index[str(p)]['sha256']==a['sha256'] and index[str(p)]['bytes']==a['bytes']
 rows.append({'name':name,'path':str(p.relative_to(ROOT)),'bytes':s.st_size,'expected_original_sha256':a['sha256'],'mode':stat.S_IMODE(s.st_mode),'current_stat_identity':[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns],'body_read_or_hash':False,'historical_complete_hash_stat_join_available':False})
assert sum(r['bytes'] for r in rows)==474534176
closed=F/'legacy-array-checker-2026-09-30';closure=doc(closed/'closure01.json');receiptp=closed/'verification01/payload/2022-06-13.json';receipt=doc(receiptp)
assert closure['receipt_sha256'][str(receiptp.relative_to(ROOT))]==sha(receiptp)
assert receipt['graph_hash']==m['graph_hash'] and receipt['manifest_sha256']==mref['sha256'] and receipt['nodes']==1768268 and receipt['directed_edges']==2518332 and receipt['array_bytes']==474534176
assert not any(k in receipt for k in ('files','stat_identity','signatures'))
put('CURRENT_METADATA01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'metadata-joins-pass-current-body-authentication-unavailable','manifest':ref(mp),'graph_hash':m['graph_hash'],'rows':rows,'total_bytes':474534176,'historical_count':1768268,'historical_edges':2518332,'historical_parent_status':'failed','graph_component_status':'complete','historical_array_verification_status':'complete','nineteen_original_metadata_hashes_joined':True,'array_payload_bytes_read':0,'array_header_bytes_read':0,'qualification':'Current stats/extents do not retroactively attach to historical completed full hashes. No body or header currently read.'})
refs={'original_legacy_inputs':ref(legacy),'original_graph_manifest':ref(mp),'original_array_checker_closure':ref(closed/'closure01.json'),'original_array_checker_june13':ref(receiptp),'original_checker_source':ref(closed/'arrays.py'),'accepted_legacy_source_metadata_check':ref(F/'real-data-pilot-legacy-graph-review01-2026-10-05/CHECK01.json'),'accepted_header_utility':ref(F/'real-data-pilot-graph-count-header-preparation01-2026-10-06/header_counts01.py'),'builder_protected_roster':ref(F/'real-data-pilot-resource-input-builder02-2026-10-06/PROTECTED_JUNE13_ROSTER02.json'),'later_header_only_arithmetic':ref(F/'real-data-pilot-resource-scope01-2026-10-05/KNOWN_JUNE13_STORAGE_ARITHMETIC01.json')}
put('REUSE_REFERENCES01.json',{'status':'DRAFT_NOT_ADMITTED','references':refs,'exact_original_inputs':inputs,'authority':'Original failed parent and complete component stay distinct. Accepted legacy metadata route consumes genuine future run.read_input; no historical modern producer plan/Owner/Binding is synthesized, and this document grants no capability.'})
put('REQUIRED_BODY_PASS01.json',{'status':'REQUIRED_NOT_EXECUTED','scope':'One opaque streaming SHA-256 pass across these five exact retained original arrays, total474534176 bytes; no numerical decode, rerun or graph reconstruction.','manifest':ref(mp),'files':rows,'required_checks':['Canonical no-symlink regular single-link descriptors; exact expected extents and original hashes.','Capture before/after descriptor and path device/inode/nlink/size/mtime_ns/ctime_ns/mode, refusing any mismatch.','Capture only bounded NPY node_features/node_ids headers during that same pass; use accepted parser and verify matching row dimensions/dtypes/extents.','Preserve actual tool/exit and explicit failures; independent exact metadata/body proof review before builder count adoption.'],'minimal_count_only_subset_bytes':353653856,'qualification':'Two files suffice for count-only authentication, but all five are the smallest complete graph-reuse body scope. Root may perform one five-file pass to resolve both without repetition.'})
put('COUNT_DRAFT_WITHHELD01.json',{'status':'WITHHELD_MISSING_CURRENT_FULL_BODY_STAT_JOIN','graph_manifest_sha256':mref['sha256'],'node_features_sha256':m['arrays']['node_features']['sha256'],'historical_rows':1768268,'current_retained_header_rows':None,'builder_compatible_count_wrapper_emitted':False,'reason':'Historical full verification did not persist file signatures; later stat/header records explicitly did not hash bodies. No current header/body inference is manufactured.','next_action_reference':ref(HERE/'REQUIRED_BODY_PASS01.json')})
print(json.dumps({'decision':'bounded metadata complete; current count wrapper withheld','metadata_refs':19,'arrays_stat_only':5,'total_bytes':474534176,'historical_rows':1768268,'payload_or_header_reads':0}))
