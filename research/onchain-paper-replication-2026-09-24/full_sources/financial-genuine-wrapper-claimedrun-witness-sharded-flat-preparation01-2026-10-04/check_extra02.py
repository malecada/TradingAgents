import copy,json,sys,ast
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import restore_witness01 as M
R=M.R;expected=json.loads(R.read(H,'EXPECTED_ORIGINALS01.json'));checks=[]
for i in range(5):
 for kind in ('late','root','mode','hash','link'):
  t=copy.deepcopy(expected['scope_trees']);rows=t[i]['members']
  if kind=='late':rows.append(copy.deepcopy(rows[-1]))
  elif kind=='root':t[i]['original_root']+='/redirect'
  elif kind=='mode':rows[0]['mode']^=1
  elif kind=='hash':next(r for r in rows if r['kind']=='file')['sha256']='0'*64
  else:
   link=next((r for r in rows if r['kind']=='lexical-symlink'),None)
   if link is None:rows.append({'kind':'lexical-symlink','path':'extra','mode':511,'target':'literal'})
   else:link['target']+='altered'
  try:M.validate_expected_trees(t)
  except ValueError:checks.append(str(i)+' '+kind)
  else:raise AssertionError(kind)
old=(H/'original-restore_sharded01.py').read_text();new=(H/'restore_witness01.py').read_text();functions=lambda s:{n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)};a=functions(old);b=functions(new)
for n in ('reserve','restore_ordinary','restore_shards','reference','selected_reference','manifest_join','contract','hashed'):
 assert a[n]==b[n];checks.append('unchanged '+n)
source=R.read(H,'recovery_pax01.py');assert R.digest(source)=='a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2';checks.append('acceptedPAX exact complete source')
review=H.parent/'financial-genuine-wrapper-claimedrun-witness-pax-framer-correction-review01-2026-10-04';raw=R.read(review,'MACHINE01.json');assert R.digest(raw)=='64bc091e50fda054306df6ef7d966582b8a4580d5591049fe6cf409105503588';assert json.loads(raw)['decision']=='accepted-source-only-witness-pax-framer-correction';checks.append('actual independentPAX review pin')
R.put(H/'EXTRA_CHECKS01.json',{'count':len(checks),'checks':checks,'actual_root_restore':False});print(len(checks))
