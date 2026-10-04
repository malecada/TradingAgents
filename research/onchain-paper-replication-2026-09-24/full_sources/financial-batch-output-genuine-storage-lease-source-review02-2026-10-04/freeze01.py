from pathlib import Path
import os,json,stat,hashlib
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();a=json.loads((H/'AUTHENTICATION01.json').read_text());c=json.loads((H/'corrected-controls/CHECKS01.json').read_text())
(H/'REPORT01.md').write_text('''# Independent lease successor02 review

Accepted narrowly as a sampled metadata/resource-accounting utility. Exact SL1 and SL2 original witnesses were reproduced: old first checks accepted, new first checks refused with failure poisoning and descriptor drainage. A permitted reserved callback write returns the final actual sample. Descriptor-free complete fingerprint rejoin follows census cleanup and free-space query; no callback or deferred descriptor close is introduced by that rejoin. The source explicitly qualifies stat signatures rather than immutable bytes.

All699 successor,1105 original and333 original-review members are authenticated, including original hardlinks, literal targets, sparse oversized negative, gzip and failed rapid-rewrite replay. The complete final literal/AST inverse passes; GenuineLease class methods are unchanged, with only the separately declared installed-source PREFIX updated outside the class. Source339 and financial/absent-grant refusals remain. No genuine Target/Owner/Binding/ResearchRun or held transition was constructed or executed.

Fresh old/new controls passed55 assertions. Twelve independent cases add actual post-statvfs extra-member/mode/growth mutations and nine final-rejoin-primary/real-close-secondary pairs. All mutations refuse without refunds; fatal pairs retain exact primary identity and drain both real descriptors. The first inherited correct01 run passed its behavioral controls but failed its stale pre-comment literal inverse. That script, stderr and complete raw trees remain. corrected-controls restores the explicit metadata-only comment when reconstructing the predecessor and passes. This is a harness expectation correction, not source mutation or a retroactive pass.

The original rapid same-size rewrite failure remains failed and was not rerun. The author's separate explicit-mtime155 replay is retained as a qualified metadata test, not proof of byte immutability. Original364 assertions include the155 suite twice. No kernel quota, atomic snapshot, concurrent writer immunity, callback preemption or full population/capacity is inferred. Uninstrumented writes and paths outside the actual admission root, including external Parent/spool/recovery trees, remain unsupported.

Actual coherent source installation, registered genuine grant, guarded caller placement, instrumentation of every writer, cumulative whole-population reservation, external typed recovery, retirement and native capacity remain unresolved. No numerical import, arrays, labels, network, upload, deletion, claim, gate or live source mutation occurred in this review.
''')
m={'schema_version':1,'decision':'ACCEPTED_SOURCE_ONLY_SAMPLED_METADATA_LEASE','source_sha256':sha((H/'storage_lease01.py').read_bytes()),'authentication_checks':a['checks'],'behavioral_assertions':c['checks'],'additional_independent_cases':12,'SL1_SL2_corrected':True,'byte_immutability_claim':False,'genuine_handles':False,'production_authority':False,'capacity_observed':False,'report_sha256':sha((H/'REPORT01.md').read_bytes())};(H/'MACHINE01.json').write_text(json.dumps(m,indent=2)+'\n');rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();r={'path':str(p.relative_to(H)),'mode':oct(stat.S_IMODE(s.st_mode))}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b),nlink=s.st_nlink)
 elif stat.S_ISDIR(s.st_mode):r.update(kind='directory')
 else:r.update(kind='symlink',target=os.readlink(p))
 rows.append(r)
(H/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':rows},sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'auth':a['checks'],'behavioral':c['checks']}))
