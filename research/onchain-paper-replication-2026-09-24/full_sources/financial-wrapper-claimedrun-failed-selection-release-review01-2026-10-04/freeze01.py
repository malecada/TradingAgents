import json,hashlib,stat
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,sort_keys=True,indent=2)+'\n').encode();r=json.loads((D/'READBACK01.json').read_bytes())
for name in ('SELECTED_BODIES01.json','SOURCE_INVERSE01.json','recover01.py','restore01.py'):(D/name).write_bytes((T/name).read_bytes())
m={'schema_version':1,'decision':'ACCEPTED_EXACT_EIGHT_BODY_FAILED_CAPTURE_SELECTION','commit':r['commit'],'selection_sha256':r['selection_sha256'],'required_body_count':8,'selected_logical_bytes':2594804,'expected_git_operations':27,'transport_source_sha256':sha((D/'recover01.py').read_bytes()),'flat_source_sha256':sha((D/'restore01.py').read_bytes()),'capture_sha256':'08f69b601770c81572e5223f1f5cdec21e2c48072ba86394255b0c5bcddc9ae1','source_review_manifest_sha256':r['source_review_manifest_sha256'],'actual_confirmation_sha256':r['root_operational_confirmation_sha256'],'unresolved_draft_completion_evidence_used':False,'checks':r['checks'],'actual_remote_receipt':None,'actual_flat_receipt':None,'native_or_replay_authority':False,'scope':'ONE original fresh external transfer of this exact8 selection, subject to actual receipt and independent outcome review before flat restore.'};(D/'MACHINE01.json').write_bytes(enc(m))
(D/'REPORT01.md').write_text('''# Exact failed-capture selection release

Accepted the exact eight canonical selected bodies at committed `fab9462e111fcf12a0be0e37e50b72a80cabe4bf`, selection SHA716a22930e6671dea25e16224c98ec352dcbd5674c961d75b5f612e54f10a928. The set equals the helper's eight REQUIRED rows, with no supplemental or duplicate members. Total2,594,804 bytes, largest2,278,895 bytes, expected27 bounded Git operations. Original transportb1b661 and flat1cdfe7 source bodies and prior source-review0c858a94 are unchanged.

352 checks authenticate every current selected body against actual immutable committed Git objects, mode and OID, and all61 committed source/review support bodies. The prior complete63-node review seal and each body/mode remain unchanged. The previous full canonical483-member capture acceptance applies to byte-identical archives; it was not rerun or relabeled as external recovery.

Nine bounded local read-only Git calls were performed. No network request was issued. The separate Root-retained confirmation101afe29 joins actual readback761d46/session18660/completionc8b62b exit0 to this commit. Earlier REMOTE_CONFIRMATION37's unresolved completion-label placeholder is explicitly excluded as completion evidence and preserved unchanged.

Both original remote and flat namespaces remain absent. This release permits Root's one original external byte fetch for the exact selection. Its actual receipt is unknown; all fetched objects, real tool/cleanup outcomes and full saved-byte joins require subsequent independent review before actual flat restoration. No numerical/replay/claim/capacity/runtime-body/POSIX authority is granted. The original failed identity, spent2/highest19 and Parent null remain unchanged.
''')
rows=[]
for p in [D]+sorted(D.rglob('*')):
 if p.name=='MANIFEST01.json':continue
 s=p.lstat();v={'path':'.'if p==D else p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode),'kind':'directory'if p.is_dir()else'file'}
 if v['kind']=='file':v.update(bytes=s.st_size,sha256=sha(p.read_bytes()))
 rows.append(v)
(D/'MANIFEST01.json').write_bytes(enc({'schema_version':1,'self_excluded':True,'members':rows}));print(json.dumps({'machine_sha256':sha((D/'MACHINE01.json').read_bytes()),'manifest_sha256':sha((D/'MANIFEST01.json').read_bytes()),'members':len(rows)}))
