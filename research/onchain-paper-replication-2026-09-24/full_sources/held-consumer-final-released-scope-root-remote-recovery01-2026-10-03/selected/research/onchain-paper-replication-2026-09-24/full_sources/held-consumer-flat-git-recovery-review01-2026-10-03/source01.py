import ast,hashlib,json,os,stat
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-flat-git-recovery-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(ok,label):
 assert ok,label
 checks.append(label)
raw=(P/'MANIFEST01.json').read_bytes();ck(H(raw)=='ef17aaee27e1589b6d477e203d5155034abce0e1bbe0f2b08d7d51db899046ad','frozen manifest');man=json.loads(raw);kinds={}
for r in man['members']:
 p=P/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==r['mode'],'mode '+r['path']);kind=r['kind'];kinds[kind]=kinds.get(kind,0)+1
 if kind=='file':
  ck(stat.S_ISREG(s.st_mode) and s.st_nlink==r['nlink'],'file '+r['path']);raw=p.read_bytes();ck(len(raw)==r['bytes'] and H(raw)==r['sha256'],'body '+r['path'])
 elif kind=='directory':ck(stat.S_ISDIR(s.st_mode),'directory '+r['path'])
 elif kind=='symlink':ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'symlink '+r['path'])
 elif kind=='fifo':ck(stat.S_ISFIFO(s.st_mode),'fifo '+r['path'])
 else:raise AssertionError(kind)
ck(len(man['members'])==8041,'8041members');ck({r['path'] for r in man['members']}=={str(p.relative_to(P)) for p in P.rglob('*') if p.name!='MANIFEST01.json'},'no extras')
for name,h in [('git_recovery01.py','f0c7bab42387eb75d3f37b45f785de591090e12b49f0fed1e2c67d0c742dbc59'),('bounded_git_fd01.py','4f997af0a6bdbe64e588241759ce596d751ee556357793af2f1c63cd0fdef87a')]:ck(H((P/name).read_bytes())==h,name+' exact')
a=(P/'bounded_git01.py').read_text();b=(P/'bounded_git_fd01.py').read_text();undo=b.replace("cwd='/proc/self/fd/'+str(root),pass_fds=(root,),env=env,stdin=","cwd=root,env=env,stdin=");ck(a==undo and ast.dump(ast.parse(a))==ast.dump(ast.parse(undo)),'complete one-line FD inverse')
prior=O.parent/'held-consumer-final-recovery-preparation03-2026-10-03'
for name,original in [('archive03.py','recovery03.py'),('bounded_git01.py','bounded_git01.py'),('owned_io.py','owned_io.py')]:ck((P/name).read_bytes()==(prior/original).read_bytes(),'prior accepted bytes '+name)
pins=json.loads((P/'SOURCE_PINS01.json').read_bytes())
for name,r in pins.items():
 if '/' in name:
  raw=(O.parent/name).read_bytes();ck(H(raw)==r['sha256'] and len(raw)==r['bytes'],'known source evidence '+name)
e=json.loads((P/'EXPECTED_ORIGINAL_TEMPLATE01.json').read_bytes());h=json.loads((O.parent/'held-consumer-historical-admission-closure-investigation01-2026-10-03/COPY_PLAN01.json').read_bytes());c=json.loads((O.parent/'held-consumer-original-git-runtime-root-binding01-2026-10-03/ORIGINAL_GIT_RUNTIME_BINDING01.json').read_bytes());ck(e['current'] is None,'current null');ck(e['historical']['claims']==h['claims'],'exact four original claim rows');ck(len(e['historical']['lookups'])==638,'638historical rows');ck(e['selected_c6']['commit']==c['actual_original_source'] and len(e['selected_c6']['rows'])==26,'actual C6/26');ck(all(x is None for k,x in json.loads((P/'ROOT_SPEC_TEMPLATE01.json').read_bytes()).items() if k!='schema_version'),'all unavailable roots/pins null')
(O/'SOURCE01.json').write_text(json.dumps({'check_count':len(checks),'typed_members':len(man['members']),'types':kinds,'scope':'source-only; no actual source capture or recovery','checks_tail':checks[-18:]},indent=2)+'\n');print('PASS',len(checks),'source/member checks',kinds)
