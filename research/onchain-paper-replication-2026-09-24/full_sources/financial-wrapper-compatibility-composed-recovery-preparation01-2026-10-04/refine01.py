from pathlib import Path
import hashlib,re
D=Path(__file__).resolve().parent;p=D/'verify01.py';s=p.read_text();s=re.sub("INPUTS_PIN='[0-9a-f]+'","INPUTS_PIN='"+hashlib.sha256((D/'INPUTS01.json').read_bytes()).hexdigest()+"'",s)
for a,b in [('ROOT_FLAT04_INTENT','ROOT_FLAT05_INTENT'),('ROOT_FLAT04_SPAWN','ROOT_FLAT05_SPAWN'),('ROOT_FLAT04_EXIT','ROOT_FLAT05_EXIT'),('ROOT_FLAT04.','ROOT_FLAT05.'),('root_operational_flat04.py','root_operational_flat05.py')]:s=s.replace(a,b)
pos=" if prerequisites_only:r.finish();report.update(bytes_read=r.total,files_read=len(r.cache));return report"
insert="""
 # Actual completed external transfer and its exact preserved input modes remain separate from new flat modes.
 D=P['receiver'];remote=receipt(D/'REMOTE_RECOVERY01.json');rm=seal(r,P['remote_review']);profile=r.j(D/'COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json');selected=D/'selected'
 require(profile['actual_receiver_root']==str(D) and profile['actual_selected_root']==str(selected),'fixed receiver profile')
 require(profile['actual_remote_receipt_sha256']==h(r.read(D/'REMOTE_RECOVERY01.json')) and profile['selection_sha256']==h(r.read(D/'SELECTED_BODIES01.json')),'profile actual receipt selection')
 require(profile['actual_remote_outcome_review_sha256']==h(r.read(P['remote_review']/'MACHINE01.json')) and profile['actual_remote_outcome_review_manifest_sha256']==h(r.read(P['remote_review']/'MANIFEST01.json')),'profile genuine review bodies')
 require(rm['decision']=='ACCEPTED_ACTUAL_REMOTE_BYTES_WITHHELD_FLAT_ENTRY_RM1','original byte-only acceptance')
 require(set(r.tree(selected))==set(manifest_rows(profile['full_manifest'])),'actual selected full namespace')
 for n,m in profile['directory_modes'].items():
  p=selected if n=='.' else selected/safe(n);st=p.lstat();require(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==m and st.st_uid==profile['expected_owner_uid'],'original directory mode owner')
 require(len(profile['files'])==15 and len(profile['directory_modes'])==7,'exact original7dirs15files')
 for n,x in profile['files'].items():require(len(r.read(selected/safe(n),x['sha256'],x['mode']))==x['bytes'] and (selected/n).lstat().st_uid==profile['expected_owner_uid'],'actual selected extent owner')
 require(remote['expected_operations']==55 and len(remote['operations'])==55 and remote['selected_count']==15 and remote['selected_logical_bytes']==507946,'actual denominator15/55/507946')
 for x in remote['selected_blobs']:
  b=r.read(selected/safe(x['path']),x['sha256']);require(len(b)==x['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest()==x['git_object'],'actual selected logical GitOID')
 for x in remote['operations']:require(x['exit']==x['actual_reaped_exit']==0 and x['cleanup_failures']==[] and x['actual_child_limits']=={'fsize':[FILE,FILE],'pid':x['pid']},'original actual child success bounds')
 require(remote['free_bytes']>=10*1024**3,'actual remote floor')
 report['selected_original_modes_preserved']=True
"""
assert pos in s;s=s.replace(pos,insert+pos)
s=s.replace(" require(ex['native_or_claim_started']", " require(entry['owned_root']==str(D) and entry['installation_draft_sha256']==h(r.read(D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json')) and entry['flat_helper_sha256']==draft['source_sha256'] and entry['flat_execution_released'] is True and entry['remote_execution_released'] is False and entry['numerical_authority'] is False,'exact entry release scope')\n require(not os.path.lexists(D/'FLAT_FAILED01.json'),'no contradictory failure terminal')\n require(ex['native_or_claim_started']")
s=s.replace(" require(newflat['status']", " require(newflat['capture_sha256']==h(r.read(P['delta']/'CAPTURE01.json')) and newflat['failed_capture_sha256']==h(r.read(P['failed_delta']/'CAPTURE01.json')) and newflat['original_mapping_sha256']==h(r.read(P['delta']/'ORIGIN_MAP01.json')),'both actual capture origins')\n require(newflat['actual_root_exit'] is None and newflat['posix_tree_restored'] is False and newflat['whole_fit_capacity'] is None and newflat['numerical_release'] is None and newflat['native_or_claim_started'] is False,'retain original unknowns/exclusions')\n require(newflat['status']")
s=s.replace(" for o in ex['whole_owned_observations']+[post['observation']]", " require(1<=len(newflat['whole_tree_observations'])<=64 and 1<=len(ex['whole_owned_observations'])<=128,'fixed observation denominators')\n require(newflat['whole_tree_policy']=={'allocation':100663296,'deadline':5.0,'depth':32,'file':4194304,'floor':10737418240,'logical':67108864,'members':32768,'samples':8192},'fixed policy')\n for o in ex['whole_owned_observations']+newflat['whole_tree_observations']+[post['observation']]")
p.write_text(s)
