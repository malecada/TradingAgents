import copy,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;MAIN=H.parents[3];checks=[]
def ok(v,n):assert v,n;checks.append(n)
rows=json.loads((H/'CANDIDATE_ROWS02.json').read_bytes())['rows'];batches=json.loads((H/'TRANSPORT_BATCHES02.json').read_bytes())['batches'];typed=json.loads((H/'COMPLETE_TYPED_ROOTS02.json').read_bytes());expected={r['path']:r for r in rows}
def validate(groups):
 assert len(groups)==2
 sets=[]
 for g in groups:
  rs=g['rows'];names=[r['path'] for r in rs];assert names==sorted(set(names));assert len(rs)<=506 and sum(r['bytes'] for r in rs)<=67108864 and all(r['bytes']<=4194304 for r in rs)
  assert all(r==expected[r['path']] for r in rs);assert 11+2*len(rs)<=1024;sets.append(set(names))
 shared=set(groups[0]['mandatory_shared_anchors']);assert shared==set(groups[1]['mandatory_shared_anchors']) and len(shared)==6
 assert sets[0]&sets[1]==shared and sets[0]|sets[1]==set(expected)
 assert len(sets[1]-shared)==330
validate(batches);ok(True,'exact2 bounded packets full cover/shared6/disjointpayloads')
for r in rows:
 p=MAIN/r['path'];st=p.lstat();body=p.read_bytes();ok(stat.S_ISREG(st.st_mode) and not p.is_symlink() and len(body)==r['bytes'] and hashlib.sha256(body).hexdigest()==r['sha256'] and stat.S_IMODE(st.st_mode)==r['mode'],'actual selected body '+r['path'])
links=0
for role,t in typed.items():
 root=Path(t['root']);actual={'.'}
 for parent,ds,fs in os.walk(root,followlinks=False):
  for name in ds+fs:actual.add((Path(parent)/name).relative_to(root).as_posix())
 ok(actual=={r['path'] for r in t['members']},'whole typed root '+role)
 for r in t['members']:
  p=root/r['path'];st=p.lstat();ok(stat.S_IMODE(st.st_mode)==r['mode'],'typed actual mode')
  if r['kind']=='file':key=p.relative_to(MAIN).as_posix();ok(key in expected and all(expected[key][k]==r[k] for k in ('bytes','sha256','mode')),'typed file selected')
  elif r['kind']=='lexical-symlink':ok(stat.S_ISLNK(st.st_mode) and os.readlink(p)==r['target'],'literal link retained');links+=1
  else:ok(stat.S_ISDIR(st.st_mode),'directory/root metadata retained')
ok(links==45,'exact45 literal links')
for kind in ('omit','duplicate','hash','mode','path','foreign','anchor','cap'):
 bad=copy.deepcopy(batches)
 if kind=='omit':bad[1]['rows'].pop()
 elif kind=='duplicate':bad[1]['rows'].append(copy.deepcopy(bad[1]['rows'][-1]))
 elif kind=='hash':bad[1]['rows'][0]['sha256']='0'*64
 elif kind=='mode':bad[1]['rows'][0]['mode']^=1
 elif kind=='path':bad[1]['rows'][0]['path']+='/redirect'
 elif kind=='foreign':bad[1]['rows'].append(copy.deepcopy(bad[0]['rows'][-1]))
 elif kind=='anchor':bad[1]['mandatory_shared_anchors'].pop()
 else:bad[1]['rows'][0]['bytes']=4194305
 try:validate(bad)
 except (AssertionError,KeyError):ok(True,'mutation refuses '+kind)
 else:raise AssertionError(kind)
(H/'CHECKS01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'actual_external_operation':False},indent=2)+'\n');print('PASS',len(checks))
