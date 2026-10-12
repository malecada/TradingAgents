"""Authenticate exact six changed bodies and literal inverse patches only."""
import ast,hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parent; F=P.parent; R=F.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
old=json.loads((R/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-36/claim.json').read_text())['experiment']['source_files']
def inverse(candidate,patch):
    lines=candidate.decode().splitlines(keepends=True); diff=patch.read_text().splitlines(keepends=True)
    out=[];cursor=0;i=0
    while i<len(diff):
        line=diff[i]
        if not line.startswith('@@'):
            i+=1;continue
        h=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',line);assert h
        start=int(h[1])-1;assert start>=cursor
        out.extend(lines[cursor:start]);cursor=start;i+=1
        while i<len(diff) and not diff[i].startswith('@@'):
            line=diff[i]
            if line.startswith(('--- ','+++ ')):break
            if line.startswith((' ','-')):
                assert lines[cursor]==line[1:];cursor+=1
            if line.startswith((' ','+')):out.append(line[1:])
            assert line[:1] in ' +-'
            i+=1
    out.extend(lines[cursor:]);return ''.join(out).encode()
entries=[
('tradingagents/research/admission.py','pilot37-admission-size-read-candidate-2026-10-11/admission.py','pilot37-admission-size-read-candidate-2026-10-11/INVERSE01.diff'),
('tradingagents/research/onchain_replication/streamed_gat.py','pilot37-gat-lifetime-candidate-2026-10-11/streamed_gat_candidate.py','pilot37-gat-lifetime-candidate-2026-10-11/INVERSE_PATCH01.diff'),
('tradingagents/research/onchain_replication/compact_mcm.py','pilot38-entry-policy-correction-2026-10-12/compact_mcm.py','pilot38-entry-policy-correction-2026-10-12/INVERSE01.diff'),
('tradingagents/research/onchain_replication/job.py','pilot38-observer-ledger-correction-2026-10-12/job.py','pilot38-observer-ledger-correction-2026-10-12/INVERSE01.diff'),
('tradingagents/research/onchain_replication/imported_authority_lease.py','pilot38-target-boundary-coalescing-2026-10-12/imported_authority_lease.py','pilot38-target-boundary-coalescing-2026-10-12/imported_authority_lease.py.inverse'),
('tradingagents/research/onchain_replication/imported_mcm_identity.py','pilot38-target-boundary-coalescing-2026-10-12/imported_mcm_identity.py','pilot38-target-boundary-coalescing-2026-10-12/imported_mcm_identity.py.inverse')]
result=[]
for name,source,patch in entries:
    candidate=(F/source).read_bytes(); restored=inverse(candidate,F/patch)
    assert sha(restored)==old[name]
    ast.parse(candidate);ast.parse(restored)
    current=(R/name).read_bytes()
    assert sha(current) in (old[name],sha(candidate))
    result.append({'path':name,'candidate_path':str((F/source).relative_to(R)),'candidate_sha256':sha(candidate),'candidate_bytes':len(candidate),'original36_sha256':sha(restored),'inverse_exact':True,'current_sha256':sha(current),'currently_installed':current==candidate})
(P/'SOURCE_CHECK01.json').write_text(json.dumps({'status':'PASS_SIX_EXACT_LITERAL_INVERSES','source_anchor':'998d353d86d683e8a095ebffb4e539a5c849ca68','entries':result,'final_integration_join_pending':True},indent=2)+'\n')
print(json.dumps({'status':'PASS_SIX_EXACT_LITERAL_INVERSES','installed':sum(x['currently_installed'] for x in result)}))
