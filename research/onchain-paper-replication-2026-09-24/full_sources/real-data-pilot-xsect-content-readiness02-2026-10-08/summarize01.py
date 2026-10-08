import hashlib,json,math,os
from pathlib import Path
H=Path(__file__).resolve().parent
rows=json.loads((H/'CONTENT_ROWS01.json').read_text());batches=json.loads((H/'BATCHES01.json').read_text())['batches'];result=json.loads((H/'RESULT01.json').read_text());start=json.loads((H/'EXECUTION_START01.json').read_text());dirs=json.loads((H/'DIRECTORIES01.json').read_text())
assert len(rows)==3783 and sum(x['bytes'] for x in rows)==6915716585 and len(dirs)==14 and len(batches)==29
assert [r['relative_path'] for r in rows]==sorted(r['relative_path'] for r in rows)
stop=0;bounds=[]
for b in batches:
 assert b['start']==stop and b['stop']>b['start'];selected=rows[b['start']:b['stop']];stop=b['stop'];assert sum(x['bytes'] for x in selected)==b['raw_bytes']<=256*1024**2
 size=10240*math.ceil((sum(512+512*math.ceil(x['bytes']/512) for x in selected)+1024)/10240)
 # Existing build_bundle adds only member names and top-level extent/hash fields.
 manifest={'members':[{**r,'member':f'files/{i:08d}'} for i,r in enumerate(selected,start=b['start'])],'files':len(selected),'raw_bytes':b['raw_bytes'],'archive_bytes':size,'archive_sha256':'0'*64}
 metadata=len((json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
 bounds.append({'index':b['index'],'raw_bytes':b['raw_bytes'],'members':len(selected),'ustar_archive_bytes':size,'manifest_serialized_bytes_estimate':metadata,'two_archives_two_manifests_plus32KiB':2*size+2*metadata+32768})
assert stop==len(rows)
maximum=max(x['two_archives_two_manifests_plus32KiB'] for x in bounds)
(H/'STAGING_REQUIREMENTS01.json').write_text(json.dumps({'kind':'metadata-derived-local-staging-estimate-not-reservation','existing_tool':'preservation.transfer_bundle','one_batch_at_a_time':True,'max_additional_local_staging_bytes':maximum,'pilot_growth_plus10GiB_floor_plus128MiB_slack':start['disk_required_bytes'],'concurrent_free_requirement_bytes':start['disk_required_bytes']+maximum,'batches':bounds,'qualification':'Two generated archives coexist until successful completion; two manifests and32KiB control allowance modeled separately. Directory/inode/filesystem allocation, failure partials, further receipts and concurrent writers require fresh exact selection/space check; no reservation or remote quota proof. Original files remain throughout.'},indent=2)+'\n')
(H/'EXECUTION_EXIT01.json').write_text(json.dumps({'session_id':76302,'final_tool_chunk_id':'6ef308','exit_code':0,'stdout_sha256':hashlib.sha256((H/'HASH01.stdout').read_bytes()).hexdigest(),'stderr_bytes':(H/'HASH01.stderr').stat().st_size,'qualification':'Actual ordinary engineering execution; no native resource unit or pilot attachment.'},indent=2)+'\n')
files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(H.iterdir()) if p.is_file() and p.name!='MANIFEST01.json'}
(H/'MANIFEST01.json').write_text(json.dumps({'status':'CONTENT_PREPARATION_ONLY','files':files,'limitations':['No writer exclusion, provenance/vintage validation, remote backup, restore test or deletion permission.','No archive staging, network, scientific imports, source edits or active pilot changes.']},indent=2)+'\n')
print(json.dumps({'staging_bytes':maximum,'concurrent_required_bytes':start['disk_required_bytes']+maximum,'manifest_sha256':hashlib.sha256((H/'MANIFEST01.json').read_bytes()).hexdigest()}))
