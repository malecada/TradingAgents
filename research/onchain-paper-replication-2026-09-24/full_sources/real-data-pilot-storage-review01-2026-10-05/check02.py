"""Only the corrected mandatory/committed review-table seam; all commands fake."""
from pathlib import Path
import hashlib,importlib.util,json,sys,difflib
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT))
ENTRY=ROOT/'research/onchain-paper-replication-2026-09-24/storage/closed-ledger-pilot-offload-2026-10-05-01'
sha=lambda b:hashlib.sha256(b).hexdigest()
body=(ENTRY/'offload.py').read_bytes()
assert sha(body)=='edf1ade0f56113515316c210dea8b256e11589f9c1eda4c94b077d1bbae08e5d'
assert sha((ENTRY/'bindings.json').read_bytes())=='bad4362b3547f6b5c10202ee35d24a2ed28a4a7600b47a25d51446e8421c4ceb'
old=json.loads((ENTRY/'BINDINGS_BEFORE_REVIEW_CORRECTION01.json').read_bytes())
new=json.loads((ENTRY/'bindings.json').read_bytes())
assert set(old)==set(new)
changed=[k for k in old if old[k]!=new[k]]
assert changed==[str((ENTRY/'offload.py').relative_to(ROOT))]
spec=importlib.util.spec_from_file_location('storage_review_corrected',ENTRY/'offload.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from tradingagents.research.onchain_replication import resources
results=[]
for case in ('exact-committed-table','empty-release-table','uncommitted-release-table','wrong-review-bindings-hash'):
    root=HERE/('correction-fixture-'+case);root.mkdir();entry=root/'entry';entry.mkdir()
    (root/'bound.txt').write_bytes(b'corrected fixture\n')
    (entry/'offload.py').write_bytes(b'worker fixture');(entry/'transport.py').write_bytes(b'transport fixture')
    c={'connection_path':'unused-connection.json','files':[{'bytes':3662934016,'stat_identity':[]} ]}
    (entry/'manifest.json').write_text(json.dumps(c))
    (entry/'bindings.json').write_text(json.dumps({'bound.txt':m.old.sha(root/'bound.txt')}))
    review={'decision':'accepted','manifest_sha256':m.old.sha(entry/'manifest.json'),'worker_sha256':m.old.sha(entry/'offload.py'),'transport_sha256':m.old.sha(entry/'transport.py'),'bindings_sha256':m.old.sha(entry/'bindings.json')}
    if case=='wrong-review-bindings-hash':review['bindings_sha256']='0'*64
    (entry/'RELEASE_REVIEW.json').write_text(json.dumps(review));(entry/'RELEASE_REVIEW.md').write_text('Synthetic review fixture only.\n')
    release={str((entry/n).relative_to(root)):m.old.sha(entry/n) for n in ('RELEASE_REVIEW.json','RELEASE_REVIEW.md','bindings.json')}
    if case=='empty-release-table':release={}
    (entry/'release-bindings01.json').write_text(json.dumps(release))
    git_shows=[]
    def fake(args,**kw):
        if args[:3]==['git','rev-parse','HEAD']:return 'a'*40+'\n'
        if args[:3]==['git','branch','--show-current']:return 'research/onchain-paper-replication-2026-09-24\n'
        if args[:2]==['git','ls-remote']:return 'a'*40+'\trefs/heads/research/onchain-paper-replication-2026-09-24\n'
        if args[:2]==['git','show']:
            path=args[2].split(':',1)[1];git_shows.append(path)
            if case=='uncommitted-release-table' and path=='entry/release-bindings01.json':return b'{}'
            return (root/path).read_bytes()
        if args[0]=='systemctl':return ''
        raise AssertionError(args)
    with patch.object(m,'ROOT',root),patch.object(m,'HERE',entry),patch.object(m,'eligibility',return_value=c['files'][0]),patch.object(m,'verify_saved_graph',return_value=None),patch.object(m.subprocess,'check_output',side_effect=fake),patch.object(m.shutil,'disk_usage',return_value=SimpleNamespace(free=10*1024**3+3662934016+16*1024**2)),patch.object(resources,'mem_available',return_value=4*1024**3):
        try:m.preflight()
        except ValueError as error:
            assert case!='exact-committed-table'
            assert not (entry/'preflight01.json').exists()
            results.append({'case':case,'status':'refused','reason':str(error),'git_shows':git_shows})
        else:
            assert case=='exact-committed-table'
            assert set(git_shows)=={'entry/release-bindings01.json','bound.txt','entry/RELEASE_REVIEW.json','entry/RELEASE_REVIEW.md','entry/bindings.json'}
            results.append({'case':case,'status':'passed','git_shows':git_shows})
(HERE/'source-offload-corrected.py').write_bytes(body)
(HERE/'ENTRY_CORRECTION.diff').write_text(''.join(difflib.unified_diff((HERE/'source-offload.py').read_text().splitlines(True),body.decode().splitlines(True))))
out={'status':'PASS_CORRECTED_ENTRY_ONLY','worker_sha256':sha(body),'bindings_sha256':sha((ENTRY/'bindings.json').read_bytes()),'binding_changes':changed,'checks':results,'actual_native_network_transfer_or_deletion':False}
(HERE/'CHECK02.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2))
