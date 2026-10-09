from pathlib import Path
import ast,json,hashlib,os
R=Path.cwd();D=Path(__file__).resolve().parent;F=D.parent;P=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';O=P/'outcome13';N=P/'full29increment14'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(65536),b''):h.update(b)
 return h.hexdigest()
m=json.loads((N/'HELPERS_MANIFEST01.json').read_text())
for n,h in m['helpers'].items():assert sha(N/n)==h;ast.parse((N/n).read_text())
a=(O/'capture13.py').read_text().replace('13','14').replace('failed-outcome-increment14.tar','full29-preparation-increment14.tar').replace('full28 failed outcome and functional source increment','final full29 preparation increment');assert a==(N/'capture14.py').read_text()
a=(O/'recover13.py').read_text().replace('13','14').replace('full28-outcome','full29-preparation').replace('full28 failed outcome and source public increment','final full29 preparation public increment').replace('fresh-git-recovered-outcome14.tar','fresh-git-recovered-full29increment14.tar');assert a==(N/'recover14.py').read_text()
def norm(s):
 return ''.join(x for x in s.splitlines(True) if not x.startswith(('prior =','owned =','N=','scopes=','prior_selection=','assert sha(prior.parent/','    \'selection_rule\':','with (HERE/','# Original failed28'))).replace("('capture13.py', 'recover13.py', 'select13.py')","('capture14.py', 'recover14.py', 'select14.py', 'HELPERS_MANIFEST01.json')")
assert norm((O/'select13.py').read_text())==norm((N/'select14.py').read_text())
t=ast.parse((N/'select14.py').read_text());assign={n.targets[0].id:n.value for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)};assert ast.literal_eval(assign['scopes'])==m['raw_scopes']==[];owned=ast.literal_eval(assign['owned']);assert owned==m['owned_directories'] and len(set(owned))==6 and all((F/x).is_dir() for x in owned)
v=json.loads((O/'FRESH_GIT_RECOVERY13.json').read_text());cap=R/v['capture']['path'];assert sha(cap)==v['capture']['sha256'];c=json.loads(cap.read_text());assert sha(O/'SELECTION13.json')==c['selection']['sha256'];assert v['source']==v['actual_remote_head']==v['actual_fetch_head'] and v['no_alternates'] is True;assert len(v['operations'])==13 and all(x['exit_code']==0 for x in v['operations'])
ex=[R/c['archive']['path'],R/v['returned_archive']['path'],O/'actual_external_archive_blob_return.stdout'];assert all(sha(p)==v['returned_archive']['sha256'] for p in ex)
review=F/'pilot-full28-outcome-increment-tools-review01-2026-10-09/TOOLS_REVIEW01.json';recovery=review.parent/'returned13/RECOVERY_REVIEW01.json';assert json.loads(review.read_text())['decision']=='accepted' and json.loads(recovery.read_text())['decision']=='accepted';assert json.loads(recovery.read_text())['source']==v['source']
absent=[N/x for x in ('SELECTION14.json','CAPTURE14.json','FRESH_GIT_RECOVERY14.json','GIT_OPERATIONS14.json','full29-preparation-increment14.tar','fresh-git-recovered-full29increment14.tar')]+[R.parent/'onchain-pilot-recovery/real-pilot-full29-preparation-20261009-14.git'];assert all(not os.path.lexists(p) for p in absent)
(D/'RESULT01.json').write_text(json.dumps({'literal_capture_recover_inverse':True,'literal_selector_remaining_logic_inverse':True,'six_owned_directories':owned,'raw_scopes':[],'baseline_source':v['source'],'baseline_return_sha256':sha(O/'FRESH_GIT_RECOVERY13.json'),'baseline_selection_sha256':sha(O/'SELECTION13.json'),'baseline_tool_review_sha256':sha(review),'baseline_recovery_review_sha256':sha(recovery),'three_exact_duplicate_hashes':v['returned_archive']['sha256'],'fresh_namespaces_absent':[str(p) for p in absent],'helpers':m['helpers']},indent=2)+'\n');print('PASS')
