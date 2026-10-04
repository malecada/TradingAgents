import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
load=lambda p:json.loads(p.read_bytes());raw=load(H/'CANDIDATE_ROWS01.json')['rows'];core=load(H/'CURRENT_CORE_ROWS01.json')['rows'];summary=load(H/'SUMMARY01.json');by={r['path']:r for r in raw};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
caller=B/'financial-genuine-wrapper-root-claimedrun-final-capture02-2026-10-04';vm=load(caller/'union-manifest.json');index=load(caller/'SHARD_INDEX01.json');assert sha(caller/'union-manifest.json')=='c72030b48f422bcfa52b1bbb2ca3202b9c8a8447387330f818edd20a58fb8b5d';assert sha(caller/'SHARD_INDEX01.json')=='da1aa342283473a8d47e0101f90bd0b25ed093c6f88f5abd183374326885f25a';archive_for={n:r for r in index['shards'] for n in r['regular_paths']};donors={}
for r in core:donors.setdefault((r['bytes'],r['sha256']),{'kind':'selected_current_core_exact_body','path':r['path'],'mode':r['mode']})
for r in vm['members']:
 if r['kind']=='file':
  shard=archive_for[r['path']];donors.setdefault((r['bytes'],r['sha256']),{'kind':'actual_accepted_final_canonical_shard_member','virtual_path':r['path'],'virtual_mode':r['mode'],'index_sha256':sha(caller/'SHARD_INDEX01.json'),'archive_ref':shard['archive'],'archive_member_path':r['path'],'actual_external_recovery':None})
src=B/'financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04';sm=load(src/'source-manifest.json');assert sha(src/'source-manifest.json')=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8'
for r in sm['members']:
 if r['kind']=='file':donors.setdefault((r['bytes'],r['sha256']),{'kind':'genuine_previously_external_and_flat_recovered_Source339_archive_member','path':r['path'],'mode':r['mode'],'source_manifest_sha256':sha(src/'source-manifest.json'),'source_archive_sha256':'b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24','accepted_full_source_proof_sha256':'468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825'})
wanted={'complete_witness_exporter_preparation02','current_witness_exporter_independent_review02'};targets=[r for r in raw if set(r['roles'])&wanted];mapping=[];additional=[]
for r in targets:
 key=(r['bytes'],r['sha256']);donor=donors.get(key)
 if donor is None:
  donor={'kind':'additional_raw_exact_body_representative','path':r['path'],'mode':r['mode'],'actual_external_recovery':None};donors[key]=donor;additional.append(r)
 mapping.append({'original_path':r['path'],'original_mode':r['mode'],'bytes':r['bytes'],'sha256':r['sha256'],'roles':r['roles'],'exact_byte_source':donor})
rows=sorted(core+additional,key=lambda r:r['path']);assert len({r['path'] for r in rows})==len(rows)
stats={'direct_core_count':len(core),'additional_unique_raw_body_representatives':len(additional),'all_original_exporter_regular_paths':len(mapping),'candidate_rows':len(rows),'candidate_bytes':sum(r['bytes'] for r in rows),'remaining_paths_to506':506-len(rows),'remaining_bytes_to64MiB':67108864-sum(r['bytes'] for r in rows),'estimated_git_calls':11+2*len(rows),'not_a_frozen_Root_selection':True,'no_path_omitted_from_mapping':True,'requires_reviewed_mapping_and_actual_fresh_recovery_before_claim':True,'actualfuture_witness_capture':None}
for n,o in [('EXPLICIT_REUSE_CANDIDATES01.json',{'qualification':'Exact byte equality only. All original paths/modes remain represented. This is not adopted and supplies no current recovery claim. No symlink is instantiated; typed tree census preserves literal links.','mapping':mapping}),('REUSE_ROW_CANDIDATE01.json',{'rows':rows,'not_a_Root_selection':True}),('REUSE_ACCOUNTING01.json',stats)]: (H/n).write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
print(json.dumps(stats,indent=2))
