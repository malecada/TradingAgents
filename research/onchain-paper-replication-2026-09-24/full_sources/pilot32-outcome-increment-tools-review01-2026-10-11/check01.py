"""Focused source-only outcome23 review; no selector/capture/recovery/Git execution."""
import ast,difflib,hashlib,json,os,stat
from pathlib import Path
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'outcome23';O=H/'outcome21';checks={};refs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def rb(p):
 assert not ({'.git','.venv','keys','apis'}&set(p.parts));assert p.name not in {'connection.json','archive_transport01.json'};b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'sha256':sha(b),'bytes':len(b)};return b
def j(p):return json.loads(rb(p))
def ck(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(name,v):
 with (P/name).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
try:
 manifest=j(D/'HELPERS_MANIFEST01.json');ck(sha((D/'HELPERS_MANIFEST01.json').read_bytes())=='3636bf9acfe83b423b6bcfc8460fcd294ca5304445472ac9f393ff8d22ff330b','exact requested helper manifest')
 for name,row in manifest['files'].items():b=rb(D/name);ck(len(b)==row['bytes'] and sha(b)==row['sha256'],'manifest '+name)
 prior=j(F/'pilot31-outcome-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json');ck(prior['decision']=='ACCEPT_SOURCE_ONLY_OUTCOME21_TOOLS' and sha((F/'pilot31-outcome-increment-tools-review01-2026-10-11/TOOLS_REVIEW01.json').read_bytes())=='e7a325ca2a182acd614cb1cb2b72de39a81fd5c75c72c1b20741a3a8afca4e4a','accepted original21 source review')
 replacements=[('full31increment20/FRESH_GIT_RECOVERY20.json','full32increment22/FRESH_GIT_RECOVERY22.json'),('real-data-pilot-full31-entry-preparation02-2026-10-11','real-data-pilot-full32-entry-preparation01-2026-10-11'),('pilot31-terminal-outcome-review01','pilot32-terminal-outcome-review01'),('pilot31-outcome-increment-tools-review01','pilot32-outcome-increment-tools-review01'),('20261011-31','20261011-32'),('0a7e3521b3b4de6c7b23d46f64360329539a28786507d752439bf0f5194045a7','5e17d749cbc55255fbe6008b02e01bf6b85930bb5b418020af751f77f3ee5805'),('capture21.py','capture23.py'),('recover21.py','recover23.py'),('select21.py','select23.py'),('SELECTION20.json','SELECTION22.json'),('SELECTION21.json','SELECTION23.json'),('CAPTURE21.json','CAPTURE23.json'),('GIT_OPERATIONS21.json','GIT_OPERATIONS23.json'),('FRESH_GIT_RECOVERY21.json','FRESH_GIT_RECOVERY23.json'),('increment21.tar','increment23.tar'),('outcome21.tar','outcome23.tar'),('real-pilot-full31-outcome-20261011-21.git','real-pilot-full32-outcome-20261011-23.git'),('failed31','failed32'),('recovered20','recovered22')]
 patch=[];sources={}
 for role in ('select','capture','recover'):
  oldpath=O/(role+'21.py');newpath=D/(role+'23.py');before=rb(oldpath).decode();after=rb(newpath).decode();p=str(oldpath.relative_to(R));ck(refs[p]==manifest['original_helpers'][p]==prior['references'][p],'accepted predecessor helper '+role)
  expected=before
  for a,b in replacements:expected=expected.replace(a,b)
  ck(expected==after,'exact literal inverse '+role);ast.parse(after);sources[role]=after
  patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(oldpath.relative_to(R)),tofile=str(newpath.relative_to(R))))
 ck(''.join(patch).encode()==rb(D/'LITERAL_PATCH01.diff'),'independently regenerated exact literal patch')
 recovery=j(H/'full32increment22/FRESH_GIT_RECOVERY22.json');ck(refs[str((H/'full32increment22/FRESH_GIT_RECOVERY22.json').relative_to(R))]['sha256']==manifest['baseline_recovery']['sha256']=='352c225838c47a4b0a393da751b56fbf33bc5fe82e8a55fb2ec9f2838173566d','actual22 exact recovery baseline')
 returnedreview=j(F/'pilot32-preparation-increment-return-review01-2026-10-11/REVIEW01.json');ck(sha((F/'pilot32-preparation-increment-return-review01-2026-10-11/REVIEW01.json').read_bytes())=='0c6453bf79e0f7e78f2f2169bd7f8c388e69313a961c36cdfc17dbd518a2df92','accepted actual22 returned-body review reused')
 capture=j(R/recovery['capture']['path']);ck(refs[recovery['capture']['path']]['sha256']==recovery['capture']['sha256'],'prior22 capture pin');selection=j(H/'full32increment22/SELECTION22.json');ck(refs[str((H/'full32increment22/SELECTION22.json').relative_to(R))]['sha256']==capture['selection']['sha256'],'prior22 selection pin')
 excluded=[capture['archive']['path'],recovery['returned_archive']['path'],str((H/'full32increment22/actual_external_archive_blob_return.stdout').relative_to(R))];ck(len(set(excluded))==3 and capture['archive']['sha256']==recovery['returned_archive']['sha256'],'exact three prior22 duplicate archive refs no archive replay')
 terminal=j(F/'pilot32-terminal-outcome-review01-2026-10-11/REVIEW01.json');ck(sha((F/'pilot32-terminal-outcome-review01-2026-10-11/REVIEW01.json').read_bytes())=='bbcd9d0e7474890fecc034e6ea7969c13a885f15ac593cf81e2d1d732bd196e9' and terminal['source']==manifest['actual_attempt_source']=='f958c3dba16b3da7b33c548971ca427d3257880c','actual accepted32 terminal source prerequisite')
 scopes=[R/p for p in manifest['explicit_scopes']];ck(len(scopes)==5 and all(str(p.relative_to(R)) in sources['select'] or p.name=='eth-paper-real-data-end-to-end-resource-20261011-32' for p in scopes),'five exact changed current scopes')
 # Authenticate actual source expressions without executing selector top level.
 tree=ast.parse(sources['select']);ns={'ROOT':R,'N':'eth-paper-real-data-end-to-end-resource-20261011-32'}
 scoped=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scopes' for t in n.targets));ck(eval(compile(ast.Expression(scoped),'scope-paths-only','eval'),ns)==scopes,'actual five literal scope expressions match manifest')
 owned=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='owned' for t in n.targets)));ck(owned==['real-data-pilot-full32-entry-preparation01-2026-10-11','pilot32-terminal-outcome-review01-2026-10-11','pilot32-outcome-increment-tools-review01-2026-10-11'],'exact three owned public directories')
 rawcurrent=[p for p in terminal['inventory'] if p.startswith(('research_runs/','research_artifacts/'))];ck(all(any((R/p).is_relative_to(s) for s in scopes) for p in rawcurrent),'all authenticated current32 raw originals inside explicit scopes')
 ck('ROOT_TERMINAL_OPERATION01.json' in '\n'.join(terminal['inventory']) and any((F/owned[0]/'ROOT_TERMINAL_OPERATION01.json').is_relative_to(F/name) for name in owned),'actual Root terminal receipt inside owned entry')
 ck(all(not (R/'research_artifacts/real_pilot_runtime').is_relative_to(s) and not s.is_relative_to(R/'research_artifacts/real_pilot_runtime') for s in scopes),'private runtime entirely outside explicit raw scopes')
 # Current declared roster plausibility only, no body selection/capture or historical scans.
 entries=[]
 for root in [F/name for name in owned]+scopes:
  assert root.is_dir() and not root.is_symlink()
  for p in sorted(root.rglob('*')):
   rel=str(p.relative_to(R));assert not ({'.git','.venv','node_modules','keys','apis'}&set(p.parts));assert p.name not in {'.env','hf_token.txt','connection.json','id_ed25519_storagebox_u676273','archive_transport01.json'} and not p.name.startswith('.env.')
   s=p.lstat();kind='regular' if stat.S_ISREG(s.st_mode) else 'directory' if stat.S_ISDIR(s.st_mode) else 'symlink' if stat.S_ISLNK(s.st_mode) else 'unsupported';assert kind!='unsupported'
   if kind=='regular':assert s.st_nlink==1 and s.st_size<=64*1024**2
   entries.append({'path':rel,'type':kind,'mode':format(stat.S_IMODE(s.st_mode),'04o'),'bytes':s.st_size if kind=='regular' else 0})
 ck(True,'current explicit eight-root metadata roster regular unique bounded no credential path')
 ck(all(not os.path.lexists(D/n) for n in ('SELECTION23.json','CAPTURE23.json','FRESH_GIT_RECOVERY23.json','GIT_OPERATIONS23.json','failed-outcome-increment23.tar','fresh-git-recovered-outcome23.tar')),'fresh selected helper outputs absent')
 bare=R.parent/'onchain-pilot-recovery/real-pilot-full32-outcome-20261011-23.git';ck(not os.path.lexists(bare),'fresh recovery23 bare destination absent; no internals inspected')
 save('ROSTER_METADATA01.json',{'scope':'Current fixed scopes metadata only. Future Git-derived paths remain Root selector responsibility. No file bodies read.','entries':entries})
 argv={role:['.venv/bin/python','-B',str((D/(role+'23.py')).relative_to(R))] for role in ('select','capture','recover')}
 result={'schema_version':1,'decision':'ACCEPT_SOURCE_ONLY_OUTCOME23_TOOLS','reviewer':'independent outcome16_release_review','checks':checks,'helper_manifest':{'path':str((D/'HELPERS_MANIFEST01.json').relative_to(R)),**refs[str((D/'HELPERS_MANIFEST01.json').relative_to(R))]},'references':refs,'root_commands':argv,'explicit_scopes':manifest['explicit_scopes'],'owned_roots':owned,'prior_archive_exclusions':excluded,'baseline_source':recovery['source'],'metadata_entries':len(entries),'conditions':['Root alone: commit/freeze current public outcome/review/helper files and verify intended finite Git delta, then run select23 and capture23 exactly once.','Commit/push captured archive and exact selection/capture; only then run recover23 once. Retain every original output and failure.','Independent actual23 returned-body review must authenticate selection/capture/archive/typed denominator/reencoding/original operation outputs before any preservation-complete claim.'],'limitations':['Literal-only successor to accepted21; unchanged body/type/mode/stability/nlink1/64MiB/secret/symlink/PAX/no-alternates guards reused without matrix replay.','No selector/capture/recovery/Git/network/private runtime or empirical execution; actual Git-diff path roster is not simulated or approved generically.','Three prior22 archive aliases are excluded by exact reference, with equality rechecked by Root selector. No broad store/runtime/scientific-input/POSIX/deletion authority.','Current public metadata roster check is an instant observation; Root original guards must still pass at actual selection/capture.']}
 save('TOOLS_REVIEW01.json',result);print(json.dumps({'decision':result['decision'],'checks':len(checks),'metadata_entries':len(entries),'sha256':sha((P/'TOOLS_REVIEW01.json').read_bytes())},sort_keys=True))
except BaseException as e:save('FAILED_CHECK01.json',{'error':repr(e),'checks':checks,'references':refs});raise
