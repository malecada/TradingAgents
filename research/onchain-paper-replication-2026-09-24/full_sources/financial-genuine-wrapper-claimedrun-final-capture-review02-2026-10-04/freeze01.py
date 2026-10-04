import hashlib,json,os,stat
from pathlib import Path
O=Path(__file__).resolve().parent;x=json.loads((O/'READBACK01.json').read_text());plan=json.loads((O/'ACTUAL_PARTITION_PLAN01.json').read_text());(O/'REPORT01.md').write_text('''# Independent bounded sharded final-capture successor

Accepted exact source31f8c7df/planner9c38c089 only. Complete declared inverse reproduces original failedcapture01 bytes/AST; unchanged original R4 primitives, proof joins and final original re-enumeration remain. Every frozen author member/type/mode/body/literal target matches. Actual20 original roots retain all1,185 bodies and50 literal targets, unchanged Source0a2/Parent529/95/sourceproof468/binding review0c399. Original failedcapture01/partial fc7d and failure reviews remain immutable.

The actual prepack virtual1,476-member/1,186-body manifest is partitioned into '''+str(len(plan))+''' prospective sorted deterministic shards. Every regular path occurs exactly once; required directory ancestors are included in each shard's typed overhead. Empty directories remain represented in the complete virtual manifest rather than being falsely claimed as restored POSIX directories. Every group satisfies2 MiB logical bodies,256 typed members including parents/PAX header overhead and the conservative gzip bound below the unchanged4 MiB archive cap. No future shard hashes or actual completed capture is asserted.

Independent real opaque multiple-shard tests use three incompressible1.1 MB bodies, original R4 pack/restore and complete byte-for-byte canonical archive reconstruction from recovered tiny flat bodies. Exact disjoint body coverage and observed archive bounds pass. Duplicate paths, missing parents, oversized single bodies and oversized PAX headers refuse. Missing virtual body and wrong literal mode refuse without index; late original additions after shard packing refuse without authentication. Real malformed checksum, forbidden symlink TAR type and truncated gzip footer all refuse. Actual put/new_file MemoryError/SystemExit/KeyboardInterrupt controls preserve first fatal identity through real two-descriptor closes plus close errors; descriptors are absent.

Two reviewer harness failures are retained: initial mode parser assumed strings instead of actual integer modes; malformed-checksum catch list omitted the real tarfile.InvalidHeaderError class. Fresh corrected check02/framing04 succeed without candidate changes or old fixture reuse. All raw scripts/results/partial witnesses remain in this review.

Only owned tiny archives were created/restored. No actual Root capture, Source/Parent mutation, network, numerical import, admission or claim occurred. Root may install exact accepted successor once into its separately named namespace, retain actual failures/partials and seek full independent actual20-tree/shard outcome review. Source predicates are observed time/disk bounds, not continuous watch or universal hard wall-clock guarantees. Final external/fresh-shard recovery, complete caller/review union and numerical eligibility remain separate. Original01 cannot be reopened or accepted as complete.
''');m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();r={'path':p.relative_to(O).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 elif stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 else:raise AssertionError(p)
 m.append(r)
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n');print('checks',x['checks'],'plannedshards',len(plan),'members',len(m))
for n in ['READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
