from pathlib import Path
import hashlib,json,os,stat
B=Path(__file__).resolve().parent;P=B.parent/'paper-treatment-fit-admission-preparation02-2026-10-04';R=B.parent/'paper-treatment-fit-admission-review02-2026-10-04';REL='overlay/tradingagents/research/onchain_replication/treatment_admission.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,obj):(B/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
c=json.loads((B/'DA4_CHECKS01.json').read_text())
put('DA4_PROTOCOL01.json',{'schema_version':1,'status':'uninstalled-source-only-successor-awaiting-different-author-review','candidate_sha256':sha(B/REL),'prior_candidate_manifest':sha(P/'MANIFEST02.json'),'prior_withheld_review_manifest':sha(R/'MANIFEST01.json'),'prior_review_machine':sha(R/'REVIEW02.json'),'correction':'One exact absence-predicate substitution: reject symlink leaf, reject existing leaf, require lexical path equal resolved path to reject ancestor redirection. No import/default/API change.','source_change':json.loads((B/'DA4_INVERSE01.json').read_text()),'checks':c['checks'],'path_case_count':len(c['path_cases']),'unchanged':['All source outside the one predicate','Original01/02 and independent review02 bytes preserved','DA1 exact failed fallback/retained-row distinction and no fabricated fields','DA2 ownership transfer/closure and DA3 first-fatal/secondary-error behavior','Source/input/claim/terminal/parent/component/coverage/per-week config/common-mask/causal rules','PRODUCER_SOURCE_PINS=None; complete fund consumption remains refused'],'authority':{'SourceInstalled':False,'source_commit':None,'producer_source_pins':None,'registration':None,'gate':None,'claim':None,'native_execution':None,'financial_credit':0},'limits':['No actual Run/Owner/claim/native/numerical execution','Predicate controls use actual owned filesystem entries; no concurrent path mutation or atomic whole-tree absence guarantee','Four owned symlink witnesses are typed in the manifest; this is no external recovery/POSIX reconstruction claim','Root must independently review, bind genuine source maps, integrate/register/preserve/recover and admit resources before numerical release']})
(B/'DA4_IMPLEMENTATION01.md').write_text(f'''# DA4 exact absence-predicate correction

An uninstalled source successor changes one predicate in treatment_admission.py. An absent postmortem row now requires a non-symlink leaf, no existing leaf and equality of the lexical and resolved path. This rejects dangling leaf symlinks and ancestor redirection even when the final target is missing. No module import, API/default, producer pin, row field or downstream scientific check changes.

The full byte/AST inverse restores downstream02 exactly. Every other inherited body and the prior WITHHELD review are retained. Producer pins remain None and fund membership/vintage/known_at policy remains unadmitted; no genuine claim or source map is guessed.

DA4_CHECKS01 records {c['checks']} checks, including 16 old/new actual-path cases: missing paths under real canonical directories accept; regular files, directories, live and dangling links, and live/dangling ancestor redirects refuse in the successor. The old predicate accepts the dangling leaf and both ancestor-to-missing cases, reproducing RED witnesses. The original unavailable id/status/reason object is returned unchanged; complete/active/coerced cases refuse. All unrelated source AST and exact prior manifests/bytes/modes were checked. No tests reran a financial experiment or imported numerical modules.

Four actual owned symlink witnesses remain under owned-path-cases01 and are explicitly typed with targets in MANIFEST03. They are not installed runtime paths and no recovered POSIX claim follows. Concurrent mutation and atomic whole-tree absence are not claimed. Different-author review and Root's separate exact source binding/integration/registration/preservation/resource admission remain required.
''')
entries=[]
for p in sorted(B.rglob('*')):
 rel=p.relative_to(B).as_posix()
 if rel=='MANIFEST03.json':continue
 s=p.lstat();entry={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):entry['type']='directory'
 elif stat.S_ISREG(s.st_mode):entry.update(type='file',bytes=s.st_size,sha256=sha(p))
 elif stat.S_ISLNK(s.st_mode):
  target=os.readlink(p);raw=os.fsencode(target);entry.update(type='symlink',target=target,target_bytes=len(raw),target_sha256=hashlib.sha256(raw).hexdigest())
 else:raise ValueError('unsupported candidate entry')
 entries.append(entry)
put('MANIFEST03.json',{'schema_version':1,'scope':'complete typed uninstalled DA4 candidate including owned symlink targets; exact manifest self-excluded','entries':entries,'members':len(entries),'regular_files':sum(e['type']=='file' for e in entries),'symlinks':sum(e['type']=='symlink' for e in entries)})
print(json.dumps({'source':sha(B/REL),'protocol':sha(B/'DA4_PROTOCOL01.json'),'report':sha(B/'DA4_IMPLEMENTATION01.md'),'manifest':sha(B/'MANIFEST03.json'),'checks':c['checks'],'members':len(entries),'files':sum(e['type']=='file' for e in entries),'symlinks':sum(e['type']=='symlink' for e in entries)},indent=2))
