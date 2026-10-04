from pathlib import Path
import json,hashlib,stat,os
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
(H/'REPORT01.md').write_text('''# Independent shared storage lease review

WITHHELD_SL1_SL2. Complete author1105-member scope, raw failures, four literal links, hardlink multiplicities, source/body/AST references and unchanged owned_io are authenticated. No genuine handles or numerical modules were constructed or imported. The original364 assertion count comprises a155-assertion suite repeated twice plus49 and5; it is not364 distinct cases.

## SL1: trailing boundary callback can invalidate a returned sample

OwnedLease.check executes _sample inside _operation. After yielding, _operation invokes _boundary, including the externally supplied callback, without a final tree rejoin. witness01 uses an actual owned utility root. On this trailing callback, it creates an unreserved diagnostic file. check returns successfully with failed=False and stale counters despite the file being present. The next check refuses unreserved new member. This is an exact scheduled callback operation, not a naturally observed race or fake genuine boundary. The final sampled postcondition must be joined after callbacks that can affect it.

## SL2: census descriptor cleanup can invalidate an earlier file signature

census verifies each member immediately before its descriptor cleanup. A later member's actual close can mutate an already scanned member; final directory/root signatures do not detect same-extent file writes. witness02 identifies the actual later z inode, closes its descriptor, changes earlier a bytes and explicitly changes a's mtime. check accepts the obsolete earlier signature. Next check refuses unreserved existing file mutation. All bytes are owned opaque controls. A bounded complete population/currentness rejoin after cleanup is required; repeating only the unchanged per-member census shifts the same cleanup gap. No continuous atomicity is expected.

## Additional observed limitation and passing scope

Unmodified author check02 replay stopped at accepted partial: the rapid same-size rewrite of a sealed file was not rejected on this filesystem. The complete failed script/output/tree is preserved; no155-pass claim is made for this replay. The source stores metadata signatures, not file content hashes; a timestamp-based utility cannot promise byte immutability when observed fingerprints coincide. This is separate from the two deterministic scheduled witnesses above. The author claim must remain explicitly metadata-only or receive separately reviewed byte verification if immutable content is required.

Author check03's49 controls and check04's5 source controls passed independently. They cover strict state/grant/refusal, final guards, first-fatal cleanup and actual unavailable source behavior. Source inspection confirms entire-admission-root census with no excluded subtree, full monotone path reservations, finite journal slots, no refunds/reopen/retirement, and original held Owner/Binding/ResearchRun checks without acquiring a new scientific identity. Source339 and financial routing remain refused. Actual placement inside the genuine held transition and complete writer instrumentation are unexecuted prerequisites, not established by utility callbacks.

The sparse4MiB+1 author fixture and its lossless gzip remain original, including zero allocated blocks at the recorded observation. It is an offline negative, not native-admissible output, measured physical reservation or full capacity. Spool/recovery/Parent paths outside the actual admission root receive no credit. No lease grant, gate, live source, empirical accounting, network, publication or deletion authority was created. The inherited replay includes its original controlled empty-directory disappearance fixture; no original or live directory was changed or cleaned up.
''')
a=json.loads((H/'AUTHENTICATION01.json').read_text());m={'schema_version':1,'decision':'WITHHELD_SL1_SL2','source_sha256':sha((H/'storage_lease01.py').read_bytes()),'authentication_checks':a['checks'],'passed_replay_assertions':54,'failed_replay':'check02 accepted partial','witnesses':{n:sha((H/n).read_bytes()) for n in ['WITNESS01.json','WITNESS02.json']},'genuine_authority_executed':False,'capacity_observed':False,'report_sha256':sha((H/'REPORT01.md').read_bytes())};(H/'MACHINE01.json').write_text(json.dumps(m,indent=2)+'\n')
rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':oct(stat.S_IMODE(s.st_mode))}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b),nlink=s.st_nlink)
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:r.update(kind='symlink',target=os.readlink(p))
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':rows},sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'checks':a['checks']}))
