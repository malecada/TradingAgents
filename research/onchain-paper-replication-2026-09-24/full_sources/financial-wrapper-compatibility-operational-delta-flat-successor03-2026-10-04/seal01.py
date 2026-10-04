from pathlib import Path
import json,hashlib,stat,os,ast,difflib
O=Path(__file__).resolve().parent;F=O.parent;h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());V=F/'financial-wrapper-compatibility-operational-delta-flat-review02-2026-10-04';m=J(V/'MANIFEST01.json');assert h((V/'MANIFEST01.json').read_bytes())=='b6d61e7ec3691ac44cd9c6a205b1af5574536433c4d5c57c6342e3a9ebd19018'
for x in m['members']:
 p=V/x['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==x['mode']
 if x['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'] and h(p.read_bytes())==x['sha256']
 elif x['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
 elif x['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target']
 elif x['kind']=='fifo':assert stat.S_ISFIFO(s.st_mode)
 else:raise AssertionError(x['kind'])
assert {p.relative_to(V).as_posix() for p in V.rglob('*')}=={x['path'] for x in m['members']}|set(m.get('excluded',['MANIFEST01.json']))
for n in ['MANIFEST01.json','MACHINE01.json','REPORT01.md','WITNESS01.json','WITNESS02.json']:(O/('PEER_'+n)).write_bytes((V/n).read_bytes())
old=(O/'ORIGINAL_restore01.py').read_text();new=(O/'restore01.py').read_text();edits=[]
for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
 if tag!='equal':edits.append({'old_start':a,'old_end':b,'new_start':c,'new_end':d,'old':old[a:b],'new':new[c:d]})
x=new
for e in reversed(edits):assert x[e['new_start']:e['new_end']]==e['new'];x=x[:e['new_start']]+e['old']+x[e['new_end']:]
assert x==old and ast.dump(ast.parse(x))==ast.dump(ast.parse(old));a={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(old).body if isinstance(x,ast.FunctionDef)};b={x.name:ast.dump(x,include_attributes=False) for x in ast.parse(new).body if isinstance(x,ast.FunctionDef)};changed=sorted(n for n in a if a[n]!=b[n]);assert changed==['authenticate_selected','load_capture','load_failed_capture','run','verify_flat']
inv={'schema_version':1,'original_sha256':h(old.encode()),'source_sha256':h(new.encode()),'full_byte_AST_inverse':True,'changed_functions':changed,'added_class':'VerifiedCohort','unchanged_functions':sorted(set(a)-set(changed)),'edits':edits};(O/'SOURCE_INVERSE01.json').write_text(json.dumps(inv,indent=2)+'\n');(O/'SOURCE_DIFF01.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original4832',tofile='terminalcohort03')))
A=F/'financial-wrapper-compatibility-operational-delta-flat-successor02-2026-10-04'
for n in ['watch01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py','REQUIRED_BODIES01.json']:assert (O/n).read_bytes()==(A/n).read_bytes()
status={'schema_version':1,'decision':'PREPARED_TERMINAL_COHORT_SOURCE_CORRECTION_FOR_INDEPENDENT_REVIEW','source_sha256':h(new.encode()),'original_source_sha256':h(old.encode()),'original_withheld_review_manifest_sha256':h((V/'MANIFEST01.json').read_bytes()),'original_withheld_review_members_verified':len(m['members']),'inverse_sha256':h((O/'SOURCE_INVERSE01.json').read_bytes()),'original_controls_replayed':J(O/'REPLAY_CONTROLS01.json')['checks'],'new_oldRED_newREFUSAL_pairs':5,'new_cohort_controls':len(J(O/'COHORT04.json')),'actual_remote_receipt':None,'actual_root_restore':None,'source_integration':None,'independent_review':None,'release':None,'native_or_numerical_authority':False};(O/'MACHINE01.json').write_text(json.dumps(status,indent=2)+'\n')
(O/'REPORT01.md').write_text('''# Terminal cohort correction03

Prepared source only. Frozen source02 4832 and its complete independently withheld review remain unchanged. The complete peer review manifest and all original witnesses were authenticated; selected original machine/report/witness/seal copies are retained here as navigation, not replacements for the full original tree.

VerifiedCohort brackets each actual read with a before-read full signature and a post-read/descriptor-cleanup equality check, retaining byte length/hash proofs. It authenticates complete expected directory populations with canonical private directories and0600 single-link regular files. Every enumeration iterator is independently closed before final namespace/signature passes. The terminal descriptor-free pass rejoins device/inode/type/mode/nlink/extent/mtime/ctime/allocation signatures for every authenticated path, including metadata, both flat scopes and all selected prerequisites. The receiver root is anchored by canonical private owner/mode/device/inode while deliberate intent/output/receipt publications may change its directory times; exact selected and flat namespaces retain complete directory signatures and membership.

The shared run cohort spans actual remote receipt, canonical selection, all15 selected bodies, both archive/capture/manifest/origin prerequisites and both restored populations. It is rejoined after the last scope's original boundary and all own reads/iterator cleanup, before recovery publication and again after receipt/sidecar reads and final boundary. Original first-fatal and secondary cleanup semantics remain unchanged. No before/after metadata sample promises atomicity, writer exclusion, immunity to same-signature ABA or post-return mutation.

Five real owned oldRED→newREFUSAL pairs cover earlier bytes, private mode, foreign member, metadata and cross-scope earlier output changes during the last actual read close. Six further controls cover selected prerequisite bytes/modes, private receiver root mode, mutation during real iterator cleanup, namespace extras and same-read cleanup mutations before a new baseline could be trusted. All105 original source02 controls replayed, including both actual local canonical archives,64 bodies+2metadata, completed first/partial failed second output, nine fatal close pairs and original refused metadata/frame/reuse cases. Final-source witnesses were rerun in distinct fresh namespaces.

Two initial witness harnesses forgot to assign the close callback into their proxy. They did not demonstrate corruption or a source failure; raw assertions/progress and all their intact outputs remain. The third harness installed the real hook and passed; final fifth run confirms the frozen source including root anchors. The intermediate first source draft is retained. No historical result was rewritten.

Exact15pins507946B, two fixed output roots, unchanged4 MiB files/64 MiB logical/96 MiB allocated/10 GiB floor/member/depth bounds,180 seconds/64 run samples and all R4/watch primitives remain unchanged. The full literal/AST inverse records five changed original functions and one added class. Public successful run/main/entry was not executed, no accepted remote receipt was fabricated, and no original Root restoration, network, numerical import, Admission/Owner/Run, source adoption or claim occurred. Actual remote, installed release and fresh recovery remain mandatory. Old385 and failed-byte171 composition and final caller/gate/runtime/capacity authority remain separate.
''')
rows=[]
for p in sorted(O.rglob('*')):
 if p.name in ['MANIFEST01.json','SEAL01.out','SEAL01.err'] and p.parent==O:continue
 s=p.lstat();r={'path':p.relative_to(O).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 else:r.update(kind='file',bytes=s.st_size,sha256=h(p.read_bytes()))
 rows.append(r)
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'root_mode':stat.S_IMODE(O.stat().st_mode),'members':rows,'excluded':['MANIFEST01.json','SEAL01.out','SEAL01.err']},indent=2)+'\n')
for n in ['restore01.py','MACHINE01.json','MANIFEST01.json']:print(n,h((O/n).read_bytes()))
print('members',len(rows))
