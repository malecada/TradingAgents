import atexit,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;D=B/'financial-wrapper-complete100-failed-root-remote03-2026-10-04';C=B/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';checks=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 assert v,n
def save(n,x):(H/n).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
atexit.register(lambda:save('CHECK03_PROGRESS.json',checks))
c=json.loads((C/'CAPTURE01.json').read_text())
def compare(root,m,label,exclude_git=False):
 ck(label+' root mode',stat.S_IMODE(root.lstat().st_mode)==m['root_mode']);seen=[]
 for base,dirs,files in os.walk(root,followlinks=False):
  if Path(base)==root and exclude_git:dirs[:]=[x for x in dirs if x!='.git']
  for n in dirs+files:seen.append(str((Path(base)/n).relative_to(root)))
 ck(label+' full namespace excludes only declaredGit',sorted(seen)==[x['path'] for x in m['members']])
 for row in m['members']:
  p=root/row['path'];s=p.lstat();ck(label+' original mode '+row['path'],stat.S_IMODE(s.st_mode)==row['mode'])
  if row['kind']=='file':
   ck(label+' original body '+row['path'],stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and s.st_size<=4194304 and sha(p.read_bytes())==row['sha256'])
  else:ck(label+' original directory '+row['path'],stat.S_ISDIR(s.st_mode))
compare(Path(c['scopes']['capsule01']['original']),json.loads((C/'CAPSULE_MASTER_MANIFEST01.json').read_text()),'CAP',True)
compare(Path(c['scopes']['parent']['original']),json.loads((C/'PARENT_MANIFEST01.json').read_text()),'Parent')
support=json.loads((C/'SUPPORT_MANIFEST01.json').read_text());roots=json.loads((C/'SUPPORT_ROOTS01.json').read_text());mapping=json.loads((C/'ROOT_EVIDENCE_PATHS01.json').read_text());supportby={x['path']:x for x in support['members']}
for row in mapping:
 p=Path(row['original']);b=p.read_bytes();m=supportby[row['support_path']];ck('actual mapped original Root evidence '+row['support_path'],len(b)==row['bytes']==m['bytes'] and sha(b)==row['sha256']==m['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['mode']==m['mode'])
for key,prefix in [('review_original',Path(roots['review_original']).name),('contract_original','original-final-contract')]:
 root=Path(roots[key]);members=[]
 for row in support['members']:
  if row['path'].startswith(prefix+'/'):members.append(dict(row,path=row['path'][len(prefix)+1:]))
 compare(root,{'root_mode':roots[key.replace('_original','_root_mode')],'members':members},prefix)
# Concrete release is only useful while all destinations remain absent.
absent=[f'flat-{x}01' for x in ['capsule01','capsule02','capsule03','capsule04','capsule05','capsule06','capsule07','capsule08','parent','support']]+['FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json']
ck('all exact future flat entry paths still absent',all(not os.path.lexists(D/x) for x in absent))
save('ORIGINAL_REJOIN01.json',{'status':'PASS_ORIGINAL_FULL_SCOPES','checks':len(checks),'capsule_full_names_excluding_baseline_git':588,'capsule_bodies':475,'parent_typed':28,'parent_bodies':24,'support_typed':26,'support_bodies':23,'actual_flat_still_unperformed':True})
print(json.dumps({'status':'PASS_ORIGINAL_FULL_SCOPES','checks':len(checks)}))
