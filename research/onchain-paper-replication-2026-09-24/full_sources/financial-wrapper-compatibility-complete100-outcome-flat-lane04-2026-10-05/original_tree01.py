from pathlib import Path
import os,stat
import recovery_pax01 as R
MEMBERS=32768
def inventory(root,exclude_git=False):
 """Reuse complete typed scan on each original top-level subtree; exclude only CAP/.git."""
 R.require(root.is_absolute() and root.resolve()==root,'canonical original root');pin=R.sig(root.lstat());members=[];names=sorted(p.name for p in root.iterdir())
 for name in names:
  R.path_name(name);p=root/name;s=p.lstat()
  if exclude_git and name=='.git':
   R.require(stat.S_ISDIR(s.st_mode) and p.resolve()==p,'original Git directory required');continue
  if stat.S_ISDIR(s.st_mode):
   m=R.scan(p);members.append({'path':name,'kind':'directory','mode':m['root_mode']});members.extend({**r,'path':name+'/'+r['path']} for r in m['members'])
  else:
   raw=R.read(root,name);R.require(R.sig(p.lstat())==R.sig(s),'original leaf changed');members.append({'path':name,'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(raw),'sha256':R.digest(raw)})
  R.require(len(members)<=MEMBERS,'whole original count')
 R.require(R.sig(root.lstat())==pin and sorted(p.name for p in root.iterdir())==names,'original root membership changed')
 m={'schema_version':1,'root_mode':stat.S_IMODE(root.lstat().st_mode),'members':sorted(members,key=lambda r:r['path'])};R.validate(m);return m

def signatures(root,m):
 paths=[root]+[root/r['path'] for r in m['members']];pins={}
 for p in paths:
  R.require(p.resolve()==p,'original path redirected');s=p.lstat();R.require(stat.S_ISDIR(s.st_mode) or (stat.S_ISREG(s.st_mode) and s.st_nlink==1),'ordinary original');pins[str(p)]=R.sig(s)
 return pins

def unchanged(pins):
 for n,pin in pins.items():
  p=Path(n);R.require(p.resolve()==p and R.sig(p.lstat())==pin,'retained original/evidence signature changed')

