from pathlib import Path
import ast,json,hashlib,difflib,datetime
H=Path('research/onchain-paper-replication-2026-09-24/full_sources'); D=H/'real-data-pilot-full24-preparation-increment01-2026-10-09'; N=D/'outcome27'; O=H/'pilot34-outcome-increment-tools-review01-2026-10-11'; refs={};checks=[]
def ref(p):
 b=p.read_bytes();r={'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};refs[str(p)]=r;return r
def read(p):ref(p);return json.loads(p.read_text())
def ck(x,s):
 checks.append(s);assert x,s
def dump(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
m=read(N/'HELPERS_MANIFEST01.json');ck(refs[str(N/'HELPERS_MANIFEST01.json')]['sha256']=='662f7414a2085944a8fd3acf7334219ef000160d4f49764fbc58c59e2b5d074c','frozen manifest')
for name,r in m['files'].items():
 a=ref(N/name);ck(all(a[k]==v for k,v in r.items() if k in a),'frozen member '+name)
old={};new={};patch='';inverse=''
for role,base,num in [('select','outcome25',25),('capture','outcome25',25),('recover','full34increment26',26)]:
 old[role]=(D/base/f'{role}{num}.py').read_text();ref(D/base/f'{role}{num}.py');new[role]=(N/f'{role}27.py').read_text()
 patch+=''.join(difflib.unified_diff(old[role].splitlines(True),new[role].splitlines(True),fromfile=f'{role}{num}.py',tofile=f'{role}27.py'))
 inverse+=''.join(difflib.unified_diff(new[role].splitlines(True),old[role].splitlines(True),fromfile=f'{role}27.py',tofile=f'{role}{num}.py'))
ck(patch==(N/'LITERAL_PATCH01.diff').read_text(),'exact three-helper literal patch');ck(inverse==(N/'LITERAL_INVERSE01.diff').read_text(),'exact three-helper inverse diff')
cap=new['capture']
for a,b in [('SELECTION27','SELECTION25'),('CAPTURE27','CAPTURE25'),('increment27','increment25'),('failed34','failed33')]:cap=cap.replace(a,b)
ck(cap==old['capture'],'capture exact literal inverse');ck(ast.dump(ast.parse(cap))==ast.dump(ast.parse(old['capture'])),'capture exact AST inverse');ck('sha276' not in new['capture'],'capture digest typo absent')
rec=new['recover']
for a,b in [('failed34 outcome','fresh34 preparation'),('failed34-outcome-20261011-27','full34-preparation-20261011-26'),('FRESH_GIT_RECOVERY27','FRESH_GIT_RECOVERY26'),('GIT_OPERATIONS27','GIT_OPERATIONS26'),('CAPTURE27','CAPTURE26'),('fresh-git-recovered-outcome27','fresh-git-recovered-preparation26')]:rec=rec.replace(a,b)
ck(rec==old['recover'],'recovery exact literal inverse');ck(ast.dump(ast.parse(rec))==ast.dump(ast.parse(old['recover'])),'recovery exact AST inverse')
s=new['select'];tree=ast.parse(s)
def assignment(name,text=s):
 t=ast.parse(text);return next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id==name for z in n.targets))
def segment(text,node):return ast.get_source_segment(text,node)
owned=ast.literal_eval(assignment('owned').value);ck(len(owned)==34 and len(set(owned))==34,'34 distinct explicit public directories');ck(O.name in owned and 'graph-hash-current-serialization-candidate01-2026-10-11' in owned,'review and graph source explicitly selected')
for name in owned:ck((H/name).is_dir() and not (H/name).is_symlink(),'owned scope exists '+name)
metadata=ast.literal_eval(assignment('public_metadata_dependencies').value)
ck(len(metadata)==5,'five fixed small public runtime references')
for name,r in metadata.items():
 ck('real_pilot_runtime' not in name and name.endswith('.json'),'public metadata path only');a=ref(Path(name));ck(a['sha256']==r['sha256'] and a['bytes']==r['bytes'],'exact fixed public metadata')
# Invert only enumerated selector changes, then compare whole literal and AST.
z=s
start=z.index('owned = ');stop=z.index('for name in (',start)
a=old['select'];a_start=a.index('owned = ');a_stop=a.index('for name in (',a_start)
z=z[:start]+a[a_start:a_stop]+z[stop:]
for diagnostic in [", 'CAPTURE_GENERATION_FAILURE01.txt'",", 'AUTHOR_CHECK_INITIAL01.json'"]:z=z.replace(diagnostic,'')
z='\n'.join(line for line in z.split('\n') if not line.startswith("assert not (HERE/'SELECTION27") and not line.startswith('assert all(not (ROOT/relative).is_relative_to(HERE)'))
ns=segment(z,assignment('scopes',z));os=segment(a,assignment('scopes',a));z=z.replace(ns,os+'\nscope_directories=set()')
for x,y in [('full34increment26/FRESH_GIT_RECOVERY26','full33increment24/FRESH_GIT_RECOVERY24'),('SELECTION26','SELECTION24'),('select27.py','select25.py'),('capture27.py','capture25.py'),('recover27.py','recover25.py'),('SELECTION27','SELECTION25'),('resource-20261011-34','resource-20261011-33'),('failed34','failed33'),('recovered26','recovered24')]:z=z.replace(x,y)
ck(z==a,'selector exact enumerated literal inverse');ck(ast.dump(ast.parse(z))==ast.dump(ast.parse(a)),'selector exact enumerated AST inverse')
ck("assert root.is_dir() and not root.is_symlink()" in s and 'elif path.is_dir():scope_directories.add(path)' in s,'owned absence fails closed and empty dirs retained')
scopes=segment(s,assignment('scopes'));ck(scopes.count("ROOT/")==6 and 'onchain_compact_mcm/eab8' in scopes and 'real_pilot_runtime' not in scopes,'six exact current outcome scopes excludes private runtime')
ck("before.st_size <= 64*1024**2" in s and "os.readlink(path)" in s and "before.st_nlink == 1" in s,'original type/mode/opaque bounded handling retained')
P=D/'full34increment26';r=read(P/'FRESH_GIT_RECOVERY26.json');c=read(P/'CAPTURE26.json');sel=read(P/'SELECTION26.json');accepted=read(H/'pilot34-preparation-increment-return-review01-2026-10-11/REVIEW01.json')
ck(refs[str(H/'pilot34-preparation-increment-return-review01-2026-10-11/REVIEW01.json')]['sha256']=='0fdeb0c250c50fd677cb787d24192bc961d965541bfcd9013b6a3fcfd4430707','accepted actual26 review reused')
ck(r['source']==accepted['source']=='67335f5e1987f28219e75e8cb679ff339739d853','actual26 baseline source');ck(refs[str(P/'CAPTURE26.json')]['sha256']==r['capture']['sha256'] and refs[str(P/'SELECTION26.json')]['sha256']==c['selection']['sha256'],'baseline selection capture joins')
ex=[Path(c['archive']['path']),Path(r['returned_archive']['path']),P/'actual_external_archive_blob_return.stdout']
for p in ex:ck(ref(p)['sha256']==r['returned_archive']['sha256'],'actual duplicate alias hash '+p.name)
ck(not (N/'SELECTION27.json').exists() and not (N/'failed-outcome-increment27.tar').exists() and not (N/'FRESH_GIT_RECOVERY27.json').exists(),'no current products yet')
ck(not (Path.cwd().parent/'onchain-pilot-recovery/real-pilot-failed34-outcome-20261011-27.git').exists(),'fresh recovery destination absent')
result={'decision':'accepted','scope':'Exact frozen outcome27 helper source and bounded command entry only; no helper execution or actual selection/capture/recovery acceptance.','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'references':refs,'owned_public_directories':owned,'raw_scopes_source':scopes,'baseline_source':r['source'],'commands':{role:f'taskset -c 3 nice -n 10 .venv/bin/python -B {N}/{role}27.py' for role in ('select','capture','recover')},'ordering':['Root confirms all34 public directories, this review and current STATE/coordination/Git delta frozen before one-use selection.','Root executes select27 then capture27 once; failure bytes retained.','Root commits exact selected archive and required bodies, pushes and verifies actual source remotely, then executes recover27 once.','Independent actual returned-byte review remains required before claiming external recovery.'],'changed_behavior':['Owned roots now mandatory and non-symlink; absent root refuses instead of silently skipping.','Owned directory trees preserve empty directories and symlink entries; final type/path guards remain.','Five fixed public runtime metadata bodies checked against exact hashes before selection.','Sixth exact current compact_mcm scope added; private runtime dispatch remains excluded.','Generated outcome27 product admission refused; exclusive selection creation unchanged.'],'diagnostic':'Original pre-freeze sha276 capture generation typo and initial author check retained as explicit selected diagnostics; corrected capture has exact accepted25 inverse.','limitations':['No directory-body census, scientific validation, private-body reads, network, Git mutation or helpers executed in this review.','Declared final roster must remain frozen through capture; metadata stat checks are not global writer exclusion.','Regular bodies at most64MiB; symlinks recorded not dereferenced. Unknown wider filesystem/runtime completeness is not asserted.','Source approval does not prove actual remote return, POSIX reconstruction or deletion authority.']}
dump(O/'TOOLS_REVIEW01.json',result)
(O/'REPORT.md').write_text('Accepted frozen outcome27 source and command entry only. Capture and recovery invert exactly to accepted25/26 literals and AST. Selector changes are enumerated and invert exactly:34 mandatory public roots, typed/empty directory preservation, five authenticated public runtime refs, six exact failed34 scopes, and generated-product refusal. Own review directory and graph-source dependency are explicit. All three prior26 archive aliases hash-identical; actual26 source/selection/capture joins authenticated against accepted returned review. Original pre-freeze sha276 diagnostic retained, corrected capture unchanged mechanically. Root must freeze final roster/current public Git delta, select and capture once, commit/push actual archive, then use fresh recovery once. Actual returned-byte review is separate; no helpers executed here.\n')
dump(O/'MANIFEST01.json',{'status':'FROZEN_TOOLS_SOURCE_REVIEW','files':{p.name:ref(p) for p in sorted(O.iterdir()) if p.name!='MANIFEST01.json'}})
print(json.dumps({'review':ref(O/'TOOLS_REVIEW01.json'),'manifest':ref(O/'MANIFEST01.json'),'checks':len(checks)}))
