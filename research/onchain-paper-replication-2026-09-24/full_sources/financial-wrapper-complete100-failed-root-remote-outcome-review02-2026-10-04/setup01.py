from pathlib import Path
import hashlib,json,stat,ast,subprocess,os
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';A=F/'financial-wrapper-complete100-failed-preservation-tooling03-2026-10-04';T=F/'financial-wrapper-complete100-failed-root-remote02-2026-10-04';O=F/'financial-wrapper-complete100-failed-root-remote-outcome-review02-2026-10-04';O.mkdir(mode=0o700)
h=lambda b:hashlib.sha256(b).hexdigest()
mp=A/'MANIFEST01.json';assert h(mp.read_bytes())=='dc698101a432dff3ac745c457558d654850355f150a1d4ab328e04f586356828';m=json.loads(mp.read_bytes());rows=m['members'];paths=[]
for x in rows:
 p=A/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
 if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
 elif x['kind'] in ('dir','directory'):assert stat.S_ISDIR(s.st_mode)
 elif x['kind']=='symlink':assert os.readlink(p)==x.get('target',x.get('link_target'))
 else:raise AssertionError(x)
 paths.append(x['path'])
assert sorted(paths)==sorted(str(p.relative_to(A)) for p in A.rglob('*') if p!=mp)
for name in ['watch01.py','recover01.py','restore01.py','ORIGINAL_watch01.py','ORIGINAL_recover01.py','SOURCE_INVERSE01.json','REMOTE_SOURCE_INVERSE01.json','REPORT01.md']:(O/name).write_bytes((A/name).read_bytes())
(O/'utilities').mkdir()
for p in (A/'utilities').iterdir():
 if p.is_file():(O/'utilities'/p.name).write_bytes(p.read_bytes())
x=json.loads((A/'SOURCE_INVERSE01.json').read_bytes());s=(A/'watch01.py').read_text();assert s.count(x['new_literal'])==1;back=s.replace(x['new_literal'],x['old_literal']);assert back==(A/'ORIGINAL_watch01.py').read_text()
r=json.loads((A/'REMOTE_SOURCE_INVERSE01.json').read_bytes());back=(A/'recover01.py').read_text()
for e in reversed(r['edits']):assert back.count(e['new'])==1;back=back.replace(e['new'],e['old'])
assert back==(A/'ORIGINAL_recover01.py').read_text()
old=A.parent/'financial-wrapper-complete100-failed-preservation-tooling02-2026-10-04'
for n in ['restore01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py']:assert (A/n).read_bytes()==(old/n).read_bytes()
# Authenticate original operational bodies, preserve original nulls, and check current absence only.
raw=O/'actual-failed';raw.mkdir();pins={}
for n in ['FAILED01.json','ROOT_REMOTE02_INTENT01.json','ROOT_REMOTE02_SPAWN01.json','ROOT_REMOTE02_EXIT01.json','ROOT_REMOTE02.stdout','ROOT_REMOTE02.stderr']:
 b=(T/n).read_bytes();(raw/n).write_bytes(b);pins[n]=h(b)
f=json.loads((raw/'FAILED01.json').read_bytes());ex=json.loads((raw/'ROOT_REMOTE02_EXIT01.json').read_bytes());assert ex['actual_root_exit']==1
for n in ['stdout','stderr']:b=(raw/('ROOT_REMOTE02.'+n)).read_bytes();assert len(b)==ex[n+'_bytes'] and h(b)==ex[n+'_sha256']
assert len(f['operations'])==7 and f['operations'][-1]['exit'] is None
absences=[]
for c in f['operations']:
 assert c['actual_child_limits']=={'pid':c['pid'],'fsize':[4194304,4194304]} and not c['cleanup_failures']
 assert not Path('/proc',str(c['pid'])).exists()
 try:os.killpg(c['pid'],0)
 except ProcessLookupError:pass
 else:raise AssertionError('group exists')
 absences.append(c['pid'])
assert 'initial_owned_allocation' not in f and 'whole_tree_observations' not in f
assert not (T/'REMOTE_RECOVERY01.json').exists() and not (T/'selected').exists()
(O/'AUTHENTICATION01.json').write_text(json.dumps({'author_manifest':h(mp.read_bytes()),'members':len(rows),'literal_and_ast_inverse':True,'unchanged_flat_and_primitives':True,'failed_original_pins':pins,'current_child_pid_and_group_absent':absences,'original_fetch_exit':None,'original_baseline_and_watch_history':None,'no_complete_remote_receipt':True},indent=2)+'\n')
# Replay genuine tiny controls on copied source under owned directories, never entry/main.
for name in ['controls01.py','local03.py','adversarial05.py']:
 d=O/('replay-'+name[:-3]);d.mkdir();(d/'utilities').mkdir()
 for p in O.glob('*.py'):(d/p.name).write_bytes(p.read_bytes())
 for p in (O/'utilities').iterdir():(d/'utilities'/p.name).write_bytes(p.read_bytes())
 s=(A/name).read_text()
 if name=='controls01.py':s=s.replace("HERE.parent/'financial-wrapper-complete100-failed-preservation-tooling02-2026-10-04/watch01.py'","HERE/'ORIGINAL_watch01.py'")
 (d/name).write_text(s)
 with (d/'stdout.txt').open('xb') as out,(d/'stderr.txt').open('xb') as err:q=subprocess.run([str(R/'.venv/bin/python'),'-B',str(d/name)],cwd=R,stdout=out,stderr=err,timeout=40)
 (d/'EXIT.json').write_text(json.dumps({'returncode':q.returncode})+'\n');print(name,q.returncode)
