from pathlib import Path
D=Path(__file__).resolve().parent;p=D/'verify01.py';s=p.read_text()
s=s.replace(" actual=r.tree(CAP,('.git',));", " require(stat.S_IMODE(CAP.lstat().st_mode)==basis['current589_manifest']['root_mode'],'literal current source root mode')\n actual=r.tree(CAP,('.git',));")
needle=" require(len(newbodies['delta'])==33 and len(newbodies['failed_delta'])==31,'both complete body denominators')"
addition="""
 failedcap=r.j(P['failed_delta']/'CAPTURE01.json');failedscope=r.j(P['failed_delta']/'ORIGINAL_FAILED_ROOT_SCOPE43.json');failedroot=Path(failedscope['root'])
 require(len(failedscope['members'])==43 and set(r.tree(failedroot))=={x['path'] for x in failedscope['members'] if x['path']!='.'},'complete original failedRoot43')
 for x in failedscope['members']:
  p=failedroot if x['path']=='.' else failedroot/safe(x['path']);st=p.lstat();require(stat.S_IMODE(st.st_mode)==x['mode'],'original failedRoot modes')
  if x['kind']=='file':require(r.read(p,x['sha256'])==newbodies['failed_delta'][x['path']],'actual failed original/recovered bytes')
  else:require(stat.S_ISDIR(st.st_mode),'failed original directory')
 require(failedcap['Root_outer_exit']==1 and failedcap['original_init_observed_exit'] is None and failedcap['separate_init_actual_reaped_exit']==0 and failedcap['historical_changed_directory_path_or_field'] is None and failedcap['actual_external_or_flat_receipt'] is None,'failed historical unknowns remain')
 require(failedcap['actual_FAILED_sha256']==h(newbodies['failed_delta']['FAILED01.json'])=='7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a','actual original failure pin')
"""
assert needle in s;s=s.replace(needle,needle+addition)
s=s.replace(" r.finish();report.update(status=", " for o in newflat['whole_tree_observations']+[post['observation']]:require(o['free_bytes']>=10*1024**3 and o['elapsed_seconds']<180 and o['seconds']<5 and 1<=o['complete_attempts']<=3,'actual finite floor/deadline samples')\n for role,names in [('policy',['POLICY01.json','SOURCE_CLOSURE01.json']),('delta',['CAPTURE01.json','ORIGIN_MAP01.json','PAYLOAD_MANIFEST01.json','operational-delta01.tar.gz']),('failed_delta',['CAPTURE01.json','FAILED_PAYLOAD_MANIFEST01.json','ORIGINAL_FAILED_ROOT_SCOPE43.json','failed-remote02.tar.gz']),('entry_review',['MACHINE01.json','MANIFEST01.json','REPORT01.md']),('receiver',['ROOT_FLAT04_INSTALLATION_DRAFT01.json','COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json'])]:\n  for n in names:receipts.append({'path':str(P[role]/n),'sha256':h(r.read(P[role]/n))})\n r.finish();report.update(status=")
p.write_text(s)
