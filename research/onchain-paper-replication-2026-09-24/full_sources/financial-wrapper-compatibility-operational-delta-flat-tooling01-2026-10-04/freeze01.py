from pathlib import Path
import ast,difflib,hashlib,json,os,stat
P=Path(__file__).absolute().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(o):return (json.dumps(o,sort_keys=True,indent=2)+'\n').encode()
def put(n,o):(P/n).write_bytes(enc(o))
old=(P/'ORIGINAL_restore01.py').read_bytes();new=(P/'restore01.py').read_bytes()
# Exact reversible byte-span representation. It declares a new orchestration,
# not an invented four-edit or all-AST-unchanged relationship.
edits=[]
for kind,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
 if kind!='equal':edits.append({'old_start':a,'old_end':b,'new_start':c,'new_end':d,'old':old[a:b].decode(),'new':new[c:d].decode()})
rebuilt=new
for e in reversed(edits):
 assert rebuilt[e['new_start']:e['new_end']]==e['new'].encode()
 rebuilt=rebuilt[:e['new_start']]+e['old'].encode()+rebuilt[e['new_end']:]
assert rebuilt==old
put('SOURCE_INVERSE01.json',{'schema_version':1,'original_sha256':sha(old),'candidate_sha256':sha(new),'scope':'New one-delta receipt-bound orchestration; unchanged four dependencies. Full reversible byte inverse to historical ten-scope caller; no narrow same-AST claim.','edits':edits,'byte_inverse':True,'ast_inverse':ast.dump(ast.parse(rebuilt))==ast.dump(ast.parse(old))})
(P/'SOURCE_DIFF01.patch').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='ORIGINAL_restore01.py',tofile='restore01.py')))
source=P.parent/'financial-wrapper-compatibility-operational-delta-tooling01-2026-10-04'
pins={}
for n in ['watch01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py']:
 a=(P/n).read_bytes();b=(source/n).read_bytes();assert a==b;assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b));pins[n]=sha(a)
counts=[json.loads((P/n).read_bytes())['checks'] for n in ['CONTROLS01.json','CONTROLS02.json']]
put('MACHINE01.json',{'schema_version':1,'status':'SOURCE_PREPARATION_REQUIRES_INDEPENDENT_REVIEW','source_sha256':sha(new),'primitive_pins':pins,'checks_by_script':counts,'checks_total':sum(counts),'inverse_sha256':sha((P/'SOURCE_INVERSE01.json').read_bytes()),'capture_sha256':'61f3560c6fc64b7122f12a690ab728407803c7bb3c3406fd1a754456e207f939','selected_count':10,'selected_logical_bytes':451691,'captured_typed_members':41,'captured_regular_bodies':33,'captured_logical_bytes':943578,'actual_external_entry':False,'actual_remote_receipt':None,'actual_root_tool_exit':None,'source_only_local_frozen_archive_roundtrips':2,'original_capture01_withheld':True,'no_scientific_or_runtime_authority':True,'raw_harness_failure':'INITIAL_CHECK01.err: dynamic import omitted local watch path; no entry and no writes outside owned scope; corrected source local path and later controls passed','source_drafts_preserved':['SOURCE_DRAFT01.py','SOURCE_DRAFT02.py','restore.template01.py','restore.template02.py'],'limits':{'whole_logical':67108864,'whole_allocated':100663296,'per_file':4194304,'free_floor':10737418240,'overall_seconds':180,'sample_limit':64,'sample_seconds':5},'future_requirements':['independent source review','exact installation in the actual new remote receiver root','genuine pinned SELECTED_BODIES01 and successful REMOTE_RECOVERY01 from fixed remote helper','Root sole flat entry, actual terminal and complete independent actual recovery review','No acceptance from presence of a success JSON if later failed marker/tool failure exists']})
(P/'REPORT01.md').write_text('''# Operational delta flat source preparation

The new restore01.py implements one actual-receipt-bound ordinary flat restoration into flat-operational-delta01. It binds the exact ten selected bodies (451,691 bytes), genuine commit/selection, ordered dynamic Git-operation denominator (10 + unique objects + 20), regular Git modes/OIDs, child exit and reaped exit both zero, empty cleanup failures, actual4MiB limit readbacks and the unchanged sampled whole-tree policy. No future receipt is supplied or fabricated by this preparation. CLI requires explicit actual remote and selection SHA256 values. Actual Root tool exit remains separate from receiver child exits.

The exact capture61f3560c contains41 typed members/33 files/943,578 logical bytes, four current source bodies, policy/adoption metadata and nine new Git object bodies. load_capture preserves original null external/flat fields and complete origin/mode mapping; full manifest and archive hashes are pinned. Both local tests restored every real frozen opaque archive body, rejoined all modes and bytes, and used unchanged R4 canonical framing and full recompression. This is source-control evidence, not actual external recovery. The old385 Git basis is separate; this helper retains nine objects as opaque bytes and performs no Git reconstruction/fsck. Original capture01 remains withheld and unchanged.

All four copied dependencies are byte/AST-identical: PAX framer a054, owned IO09d1, bounded Gitdb4a and sampled watchcd2200. The orchestration is NEW; SOURCE_INVERSE01 records its complete reversible byte/AST inverse to the older ten-scope restore. It does not falsely claim four substitutions or unchanged orchestration. Two initial draft sources/templates and the initial import harness traceback remain retained. The actual file prefix is new-git-objects; it is validated against actual metadata.

Whole owned-tree64MiB logical/96MiB allocated, per-file4MiB,10GiB floor and180-second limits are sampled before/after the bounded restore and verification. The initial baseline is included; no subset of the current remote root is treated as the whole root. The receipt has post-write sampled evidence, with a separate sidecar and final stdout observation. No continuous quota, atomic coverage, kernel aggregate limit, storage saving, POSIX reconstruction, runtime-body completeness or scientific capacity is claimed. A success JSON followed by a failure is retained forensic evidence, never sufficient for acceptance without Root terminal and independent review.

Controls include all33 actual bodies, complete metadata/modes, selection missing/duplicate/order/hash/extent/path/type refusal, old genuine remote wrong-scope refusal, exact source operation predicates replayed against all109 genuine old operation records, real FD closure under injected KeyboardInterrupt, retained partial bytes, fatal/journal pair controls, actual lexical link and hardlink refusal, wrong private mode/nonempty directory, corrupt/truncated/trailing archive and changed manifest-mode/hash refusal. No synthetic new remote receipt or research authority is produced. Full future actual receipt admission is unperformed. No entry, network, scientific package, array/checkpoint decode, Run, Owner, claim, registration or live source mutation occurred.

Root must preserve/install the reviewed complete helper closure in the actual receiver directory, then supply genuine actual remote and selection pins for its sole entry. Independent actual recovery review must verify every restored body, terminal outcome and final whole-tree observations before a recovery claim. This source preparation grants neither release nor numerical permission.
''')
# Literal typed complete census includes all owned controls, hardlinks and lexical link.
rows=[]
def visit(path,rel=''):
 for p in sorted(path.iterdir(),key=lambda p:p.name):
  n=p.name if not rel else rel+'/'+p.name
  if n=='MANIFEST01.json':continue
  s=p.lstat();r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p));rows.append(r)
  elif stat.S_ISDIR(s.st_mode):r.update(kind='directory');rows.append(r);visit(p,n)
  elif stat.S_ISREG(s.st_mode):b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b),nlink=s.st_nlink);rows.append(r)
  else:raise ValueError(n)
visit(P);rows.sort(key=lambda r:r['path'])
put('MANIFEST01.json',{'schema_version':1,'scope':'complete source preparation excluding this self seal; lexical witnesses are not followed','members':rows,'typed_members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows)})
print(json.dumps({n:sha((P/n).read_bytes()) for n in ['restore01.py','MANIFEST01.json','MACHINE01.json','REPORT01.md','SOURCE_INVERSE01.json']}));print('checks',sum(counts),'members',len(rows))
