import ast,datetime,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];assert MAIN.name=='TradingAgents-audit-fixes'
rows={};trees={};roles={};events=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();t=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns);return b

def addfile(p,role):
 s=p.lstat();b=read(p);n=p.relative_to(MAIN).as_posix();r={'path':n,'mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':sha(b),'roles':[]}
 if n in rows:assert {k:v for k,v in rows[n].items() if k!='roles'}=={k:v for k,v in r.items() if k!='roles'}
 else:rows[n]=r
 rows[n]['roles'].append(role);roles.setdefault(role,[]).append(n)

def tree(p,role,closed=True):
 typed=[]
 def scan(q,n):
  s=q.lstat();before=(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns);r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):
   r['kind']='directory';typed.append(r)
   for c in sorted(q.iterdir()):scan(c,c.name if n=='.' else n+'/'+c.name)
  elif stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(q));typed.append(r)
  else:
   b=read(q);r.update(kind='file',bytes=len(b),sha256=sha(b));typed.append(r);addfile(q,role)
  t=q.lstat();assert before==(t.st_dev,t.st_ino,t.st_mode,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
 scan(p,'.');trees[role]={'root':str(p),'closed_at_assignment':closed,'members':sorted(typed,key=lambda r:r['path'])}

def top(p,role):
 for q in sorted(p.iterdir()):
  if stat.S_ISREG(q.lstat().st_mode):addfile(q,role)
remote=B/'financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04';required=ast.literal_eval(next(n.value for n in ast.parse(read(remote/'recover01.py')).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in n.targets)))
assert sha(read(remote/'recover01.py')).startswith('0b397')
for p,pin in required.items():assert len(read(MAIN/p))==pin['bytes'] and sha(read(MAIN/p))==pin['sha256'];addfile(MAIN/p,'required_transport_source325_supplement')
for role,name in [('actual_source339_capture','financial-genuine-wrapper-root-claimedrun-source339-capture01-2026-10-04'),('complete_actual_admission_review','financial-genuine-wrapper-claimedrun-actual-admission-review01-2026-10-04'),('original_actual_admission_receipts','financial-genuine-wrapper-root-claimedrun-actual-admission01-2026-10-04'),('source339_actual_remote_review','financial-genuine-wrapper-claimedrun-source339-actual-remote-review01-2026-10-04'),('source339_actual_flat_review','financial-genuine-wrapper-claimedrun-source339-actual-flat-review01-2026-10-04'),('source339_actual_flat_release','financial-genuine-wrapper-claimedrun-source339-flat-release-review01-2026-10-04'),('source339_root_flat_receipts','financial-genuine-wrapper-root-claimedrun-source339-flat01-2026-10-04')]:tree(B/name,role)
top(B/'financial-genuine-wrapper-root-claimedrun-source339-remote02-2026-10-04','source339_actual_remote_top');flat=B/'financial-genuine-wrapper-claimedrun-source339-flat-20261004-01';top(flat,'source339_actual_flat_top');addfile(flat/'flat-source01/body-metadata.json','source339_actual_flat_metadata')
actual=B/'financial-genuine-wrapper-root-claimedrun-final-capture02-2026-10-04';top(actual,'actual_final_capture_top');tree(actual/'shards','actual_final11_shards');old=B/'financial-genuine-wrapper-root-claimedrun-final-capture01-2026-10-04';requirements=json.loads(read(B/'financial-genuine-wrapper-claimedrun-actual-final-capture-review02-2026-10-04/FAILED_SCOPE_RECOVERY_REQUIREMENTS01.json'))
for r in requirements['must_select_exact_outside_union_files']:
 p=old/r['path'];assert len(read(p))==r['bytes'] and sha(read(p))==r['sha256'] and stat.S_IMODE(p.stat().st_mode)==r['mode'];addfile(p,'old_failed_exact8_outside_union')
rawbody=B/'financial-genuine-wrapper-claimedrun-actual-final-capture-review02-2026-10-04/READBACK01.json';assert len(read(rawbody))==2532973 and sha(read(rawbody))=='c47fcb6875375ecb8ea5c60926bae307955007751cdf52bec2473c44964e17e3';addfile(rawbody,'required_direct_original_readback')
tree(remote,'prospective_transport_source')
prep=B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-preparation02-2026-10-04';tree(prep,'complete_witness_exporter_preparation02');review=B/'financial-genuine-wrapper-claimedrun-sharded-witness-capture-review02-2026-10-04';tree(review,'current_witness_exporter_independent_review02',closed=False)
# The five source witness trees are existing raw evidence, not yet captured or recovered.
ns={'Path':Path}
for n in ast.parse(read(prep/'capture_witness02.py')).body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('MAIN','BASE','SCOPES'):exec(compile(ast.Module(body=[n],type_ignores=[]),'<fixed witness scope literals>','exec'),ns)
for role,root in sorted(ns['SCOPES'].items()):tree(root,'future_witness_source_'+role)
regular=sorted(rows.values(),key=lambda r:r['path'])
for r in regular:r['roles']=sorted(set(r['roles']))
role_summaries={}
for role,paths in sorted(roles.items()):
 names=sorted(set(paths));members=trees.get(role,{}).get('members',[]);role_summaries[role]={'regular_paths':len(names),'regular_bytes':sum(rows[n]['bytes'] for n in names),'max_body_bytes':max(rows[n]['bytes'] for n in names),'over4MiB':[n for n in names if rows[n]['bytes']>4194304],'literal_links':sum(r['kind']=='lexical-symlink' for r in members),'directories_including_root':sum(r['kind']=='directory' for r in members),'closed_at_assignment':trees.get(role,{}).get('closed_at_assignment',True),'paths':names}
core_roles={r for r in roles if not r.startswith('future_witness_source_') and r not in ('complete_witness_exporter_preparation02','current_witness_exporter_independent_review02')}
def subset(wanted):return [r for r in regular if set(r['roles'])&wanted]
def metrics(xs):return {'paths':len(xs),'bytes':sum(r['bytes'] for r in xs),'max_body':max(r['bytes'] for r in xs),'remaining_paths_to506':506-len(xs),'remaining_bytes_to64MiB':67108864-sum(r['bytes'] for r in xs),'estimated_transport_git_calls_11_plus_2N':11+2*len(xs),'fits_current_caps':len(xs)<=506 and sum(r['bytes'] for r in xs)<=67108864 and all(r['bytes']<=4194304 for r in xs)}
variants={}
for name,wanted in [('current_core',core_roles),('core_plus_complete_exporter_preparation',core_roles|{'complete_witness_exporter_preparation02'}),('core_plus_both_complete_exporter_trees',core_roles|{'complete_witness_exporter_preparation02','current_witness_exporter_independent_review02'}),('all_current_raw_source_and_future_witness_trees',set(roles))]:variants[name]=dict(metrics(subset(wanted)),roles=sorted(wanted))
# Exact-content reuse is reported separately, never silently applied to a selection.
groups={}
for r in subset(core_roles|{'complete_witness_exporter_preparation02','current_witness_exporter_independent_review02'}):groups.setdefault((r['bytes'],r['sha256']),[]).append(r)
duplicates=[{'bytes':k[0],'sha256':k[1],'paths':[{'path':r['path'],'mode':r['mode'],'roles':r['roles']} for r in v]} for k,v in sorted(groups.items()) if len(v)>1]
summary={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'READ_ONLY_CANDIDATE_CENSUS_NOT_ROOT_SELECTION','limits':{'paths':506,'selected_bytes':67108864,'file_bytes':4194304,'floor_bytes':10737418240,'git_calls':1024},'variants':variants,'all_observed_regular_paths':len(regular),'all_over4MiB':[r for r in regular if r['bytes']>4194304],'exporter_review_final_seal':None,'future_witness_capture':None,'future_actual_witness_review':None,'future_selection_commit':None,'future_remote_receipt':None,'raw_paths_are_not_archival_authority':True,'reuse_needs_explicit_full_path_mode_mapping_and_actual_recovery':True}
for name,data in [('CANDIDATE_ROWS01.json',{'rows':regular}),('ROLE_SUMMARY01.json',role_summaries),('COMPLETE_TYPED_TREES01.json',trees),('DUPLICATE_CONTENT_CANDIDATES01.json',{'groups':duplicates,'not_applied':True}),('CURRENT_CORE_ROWS01.json',{'rows':subset(core_roles),'not_frozen_selection':True}),('SUMMARY01.json',summary)]:
 (H/name).write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
print(json.dumps(summary,indent=2))
