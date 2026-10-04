import ast,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];rows={};trees={};roles={};missing=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size<=4194304 and st.st_nlink==1 and p.resolve()==p
 body=p.read_bytes();end=p.lstat();assert (st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==(end.st_dev,end.st_ino,end.st_mode,end.st_size,end.st_mtime_ns,end.st_ctime_ns);return body

def add(p,role):
 body=read(p);name=p.relative_to(MAIN).as_posix();r={'path':name,'bytes':len(body),'sha256':sha(body),'mode':stat.S_IMODE(p.lstat().st_mode),'roles':[]}
 if name in rows:assert {k:v for k,v in rows[name].items() if k!='roles'}=={k:v for k,v in r.items() if k!='roles'}
 else:rows[name]=r
 rows[name]['roles']=sorted(set(rows[name]['roles']+[role]));roles.setdefault(role,set()).add(name)

def tree(root,role):
 typed=[]
 def visit(p,name):
  st=p.lstat();before=(st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns);r={'path':name,'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p));typed.append(r)
  elif stat.S_ISDIR(st.st_mode):
   assert p.resolve()==p;r['kind']='directory';typed.append(r)
   for c in sorted(p.iterdir()):visit(c,c.name if name=='.' else name+'/'+c.name)
  else:
   body=read(p);r.update(kind='file',bytes=len(body),sha256=sha(body));typed.append(r);add(p,role)
  z=p.lstat();assert before==(z.st_dev,z.st_ino,z.st_mode,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 visit(root,'.');trees[role]={'root':str(root),'members':sorted(typed,key=lambda r:r['path'])}

def top(root,role):
 for p in sorted(root.iterdir()):
  if stat.S_ISREG(p.lstat().st_mode):add(p,role)

def emit(name,v):
 p=H/name;assert not os.path.lexists(p);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
# Actual core is never silently rehashed into a changed selection.
core=json.loads(read(B/'financial-genuine-wrapper-claimedrun-final-preservation-selection-census01-2026-10-04/CURRENT_CORE_ROWS01.json'))['rows'];assert len(core)==117 and sum(r['bytes'] for r in core)==22672976
for r in core:
 p=MAIN/r['path'];body=read(p);assert len(body)==r['bytes'] and sha(body)==r['sha256'] and stat.S_IMODE(p.stat().st_mode)==r['mode'];add(p,'original_exact_CORE117')
witness=B/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04';top(witness,'actual_witness57_capture_top');tree(witness/'shards','actual_witness57_archive_manifest_pairs')
tree(B/'financial-genuine-wrapper-claimedrun-actual-sharded-witness-capture-review02-2026-10-04','complete_actual_witness57_review_and_original_PAX_refusal')
for kind in ('witness-tooling','recovery-helper-witness'):
 root=B/('financial-genuine-wrapper-root-claimedrun-'+kind+'-capture01-2026-10-04');top(root,'actual_'+kind+'_capture_top');add(root/'union-bytes01/ORIGINAL_TREES01.json','actual_'+kind+'_complete_original_mapping')
tree(B/'financial-genuine-wrapper-claimedrun-actual-witness-tooling-capture-review01-2026-10-04','complete_actual_tooling_capture_review')
# Root will supply this final actual review seal; never infer it from a partial file.
helper_review=B/'financial-genuine-wrapper-claimedrun-actual-recovery-helper-witness-capture-review01-2026-10-04'
if (H/'ACTUAL_HELPER_REVIEW_BINDING01.json').exists():
 binding=json.loads(read(H/'ACTUAL_HELPER_REVIEW_BINDING01.json'));helper_review=Path(binding['root']);assert sha(read(helper_review/binding['manifest_name']))==binding['manifest_sha256'];tree(helper_review,'complete_actual_six_helper_capture_review')
else:missing.append({'role':'complete_actual_six_helper_capture_review','root':str(helper_review),'manifest_sha256':None,'not_closed':True})
for name,role in [('financial-genuine-wrapper-root-claimedrun-final-sharded-flat01-2026-10-04','complete_installed_final11_flat_caller'),('financial-genuine-wrapper-root-claimedrun-witness-sharded-flat01-2026-10-04','complete_installed_witness57_direct_flat_caller')]:tree(B/name,role)
for name,role,pin in [('financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-preparation01-2026-10-04','complete_six_capture_exporter_own_source','73cea960c32019158961df0dcfa6f42032697d6da682a7a199b3c592dfc84d51'),('financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-review01-2026-10-04','complete_six_capture_exporter_own_review','128cffb0c122368ba8731be9f849f49dab148beef61cd2447cf5c36936e8657c')]:
 root=B/name;assert sha(read(root/'MANIFEST01.json'))==pin;tree(root,role)
# Typed external mapping preserves ALL links/root/directory modes without asking transport to follow links.
emit('COMPLETE_TYPED_ROOTS01.json',trees);add(H/'COMPLETE_TYPED_ROOTS01.json','literal_link_directory_and_original_mode_metadata')
# Retain this exact census implementation in the proposed transport payload.
add(H/'census01.py','census_source')
regular=sorted(rows.values(),key=lambda r:r['path'])
assert len({r['path'] for r in regular})==len(regular)
remote=B/'financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04/recover01.py';node=next(n for n in ast.parse(read(remote)).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in n.targets));required=ast.literal_eval(node.value);anchors=[rows[p] for p in sorted(required)];assert len(anchors)==6
for r in anchors:assert r['bytes']==required[r['path']]['bytes'] and r['sha256']==required[r['path']]['sha256']
def metrics(xs):return {'paths':len(xs),'bytes':sum(r['bytes'] for r in xs),'largest_body':max((r['bytes'] for r in xs),default=0),'git_operations_11_plus2N':11+2*len(xs),'fits_506_64MiB_4MiB':len(xs)<=506 and sum(r['bytes'] for r in xs)<=67108864 and all(r['bytes']<=4194304 for r in xs)}
# Deterministic priority partition: archival/current core first, all complete own trees second.
own={'complete_six_capture_exporter_own_source','complete_six_capture_exporter_own_review'};anchor_paths={r['path'] for r in anchors};payload=[r for r in regular if r['path'] not in anchor_paths];payload.sort(key=lambda r:(bool(set(r['roles'])&own),r['path']))
batches=[];current=[]
for row in payload:
 if not metrics(anchors+current+[row])['fits_506_64MiB_4MiB']:
  assert current;batches.append(current);current=[]
 assert metrics(anchors+current+[row])['fits_506_64MiB_4MiB'];current.append(row)
if current:batches.append(current)
assert {r['path'] for batch in batches for r in batch}==set(rows)-anchor_paths and sum(len(b) for b in batches)==len(payload)
transport=[]
for i,body in enumerate(batches):
 selected=sorted(anchors+body,key=lambda r:r['path']);transport.append({'batch':'proposed-'+str(i+1).zfill(2),'metrics':metrics(selected),'rows':selected,'payload_disjoint_paths':[r['path'] for r in body],'mandatory_shared_anchors':[r['path'] for r in anchors],'actual_remote_namespace':None,'actual_commit':None,'actual_receipt':None})
summary={'decision':'EXACT_CURRENT_CANDIDATE_NOT_ROOT_SELECTION','current_complete_rows':metrics(regular),'original_CORE117_authenticated':True,'roles':{k:{'paths':len(v),'bytes':sum(rows[n]['bytes'] for n in v)} for k,v in sorted(roles.items())},'complete_typed_roots':len(trees),'literal_links':sum(r['kind']=='lexical-symlink' for t in trees.values() for r in t['members']),'future_missing_roles':missing,'transport_batches':len(batches),'mandatory_anchor_rows_repeated_per_batch':6,'payloads_disjoint':True,'whole_packets_disjoint':len(batches)==1,'qualification':'No omitted body or link. Original transport requires six identical anchor rows in every batch; strictly disjoint full packets are incompatible with unchanged REQUIRED. Payloads alone are disjoint. No actual transfer/recovery/authority follows.'}
emit('CANDIDATE_ROWS01.json',{'rows':regular});emit('TRANSPORT_BATCHES01.json',{'batches':transport,'genuine_future_reviews_must_be_added_before_Root_freeze':missing});emit('SUMMARY01.json',summary);print(json.dumps(summary,indent=2))
