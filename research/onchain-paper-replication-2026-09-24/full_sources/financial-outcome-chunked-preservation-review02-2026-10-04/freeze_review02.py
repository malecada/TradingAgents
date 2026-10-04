import hashlib,json,os,stat
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'authenticated-source';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((D/'CHECKS02.json').read_text());a=json.loads((D/'CLEANUP_CHECKS03.json').read_text())
machine={'schema_version':1,'verdict':'ACCEPTED_BOUNDED_SOURCE_CORRECTIONS_ONLY','candidate_source_sha256':sha(S/'chunk_archive01.py'),'candidate_manifest_sha256':sha(S/'MANIFEST02.json'),'prior_withheld_manifest_sha256':sha(D/'prior-MANIFEST01.json'),'source_inverse_sha256':sha(S/'INVERSE03.json'),'principal_checks':c['count'],'cleanup_checks':a['count'],'total_checks':c['count']+a['count'],'candidate_manifest_regular_files':c['author_manifest_files'],'candidate_manifest_regular_bytes':c['author_manifest_bytes'],'CA1':'original actual opaque RED / successor both-readers GREEN; complete shared metadata and flat chunk hash validation','CA2':'original actual redirected creation RED / successor descriptor-bound creation GREEN, retained original owned child on post-anchor namespace replacement','author_large_evidence_is_capacity_measurement':False,'live_outcome_verified':False,'source_installed':False,'authority':None,'future_root_scope':None,'future_caller':None,'future_external_recovery':None,'numerical_execution':None,'paper_financial_credit':0,'report_sha256':sha(D/'REVIEW02.md'),'checks_sha256':sha(D/'CHECKS02.json'),'cleanup_checks_sha256':sha(D/'CLEANUP_CHECKS03.json'),'witnesses_sha256':sha(D/'WITNESSES02.json'),'review_harness_failure_preserved':'HARNESS_FAILURE01.json','limitations':c['not_tested']+['no claim of secondary exception attachment when inherited primary fatal wins','own-process descriptor census only','post-anchor namespace replacement retains original-owned child before refusal']}
(D/'REVIEW02.json').write_text(json.dumps(machine,sort_keys=True,indent=2)+'\n')
entries=[]
for p in sorted(D.rglob('*')):
 if p==D/'MANIFEST02.json':continue
 s=p.lstat();r={'path':p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):r.update(type='file',bytes=s.st_size,sha256=sha(p))
 elif stat.S_ISDIR(s.st_mode):r['type']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(type='symlink',target=os.readlink(p))
 else:raise ValueError(str(p))
 entries.append(r)
o={'schema_version':1,'status':machine['verdict'],'scope':'complete independent owned review tree; includes failed harness, all opaque actual pipelines, correction/partial witnesses, source copies and all nested manifests; excludes only exact root MANIFEST02.json','entries':entries,'members':len(entries),'regular_files':sum(r['type']=='file' for r in entries),'regular_bytes':sum(r.get('bytes',0) for r in entries),'authority':None}
(D/'MANIFEST02.json').write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
print(json.dumps({'manifest_sha256':sha(D/'MANIFEST02.json'),'review_sha256':sha(D/'REVIEW02.json'),'report_sha256':sha(D/'REVIEW02.md'),'members':o['members'],'files':o['regular_files'],'bytes':o['regular_bytes'],'checks':machine['total_checks']}))
