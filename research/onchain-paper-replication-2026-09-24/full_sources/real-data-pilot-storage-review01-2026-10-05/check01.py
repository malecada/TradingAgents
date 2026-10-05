"""Local metadata plus fake-entry checks; no ledger bodies, network or native jobs."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0,str(ROOT))
ENTRY = ROOT/'research/onchain-paper-replication-2026-09-24/storage/closed-ledger-pilot-offload-2026-10-05-01'
sha = lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('storage_review_candidate',ENTRY/'offload.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=json.loads((ENTRY/'manifest.json').read_bytes())
bindings=json.loads((ENTRY/'bindings.json').read_bytes())
# Hash connection bytes only: never parse, print, copy or retain their contents.
for name,h in bindings.items(): assert m.old.sha(ROOT/name)==h,name
row=m.eligibility(ROOT,c)
m.verify_saved_graph(c)
assert row['bytes']==3662934016
assert (ENTRY/'transport.py').read_bytes()==(ROOT/'research/onchain-paper-replication-2026-09-24/storage/closed-ledger-offload-2026-09-30-06/transport.py').read_bytes()
source=ROOT/row['path']
assert source.resolve()==source
assert m.old.identity(source.stat())==row['stat_identity']
unused=['launch-attempt01.json','outer-exit01.json','intent.json','preflight01.json','guard01','complete.json','failed.json','00-verified.json','00-recovered.bin']
assert all(not (ENTRY/n).exists() and not (ENTRY/n).is_symlink() for n in unused)

canonical=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
active=[]
for root in (ROOT,canonical):
    for p in (root/'research_runs').glob('*/claim.json'):
        if not any((p.parent/(n+'.json')).exists() for n in ('complete','failed')):
            v=json.loads(p.read_bytes())
            assert row['path'] not in json.dumps(v)
            for ref in v['experiment']['inputs'].values():
                target=(root/ref['path']).resolve()
                assert target!=source and not (target.is_dir() and source.is_relative_to(target))
            active.append({'root':str(root),'id':p.parent.name,'claim_sha256':m.old.sha(p)})
fs=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
metadata=[fs/'real-data-end-to-end-pilot-preparation01-2026-10-05'/n for n in ('INPUT_SELECTION_DRAFT01.json','GRAPH_STAGE_CASES_DRAFT01.json')]
metadata += [fs/'held-consumer-canonical-root-binding01-2026-10-05'/n for n in ('ROOT_REBOUND_CASE_DRAFTS01.json','METADATA_BINDING01.json','SOURCE_GATE_COMMIT02.json')]
metadata += [fs/'real-data-pilot-execution-path01-2026-10-05/SOURCE_POINTERS01.json']
metadata += sorted((canonical/'fixture_inputs/held/canonical-roles01').glob('*.json'))
metadata += [canonical/'fixture_inputs/original/02-gate-v3.json']
# All selected objects are mappings/configuration metadata, never target arrays.
metadata_pins={}
for p in metadata:
    raw=p.read_bytes()
    assert len(raw)<2*1024**2
    assert row['path'].encode() not in raw and str(source).encode() not in raw
    metadata_pins[str(p)]={'sha256':sha(raw),'bytes':len(raw)}
selection=json.loads(metadata[0].read_bytes())
assert selection['selected']['required_weeks']==[f'2022-{d}T00:00:00Z' for d in ('05-02','05-09','05-16','05-23','05-30','06-06','06-13')]

# Accessible descriptor census is stat/link metadata only, not file contents.
open_consumers=[]; inaccessible=0; vanished=0; checked=0
for process in Path('/proc').iterdir():
    if not process.name.isdigit():continue
    try:
        if process.stat().st_uid!=os.getuid():continue
        descriptors=list((process/'fd').iterdir())
    except PermissionError:inaccessible+=1;continue
    except FileNotFoundError:vanished+=1;continue
    for fd in descriptors:
        try:
            target=os.readlink(fd);checked+=1
            if target==str(source) or target==str(source)+' (deleted)':open_consumers.append({'pid':process.name,'fd':fd.name})
        except PermissionError:inaccessible+=1
        except FileNotFoundError:vanished+=1
assert not open_consumers

from tradingagents.research.onchain_replication import resources
test_results=[]
def fixture(label):
    root=HERE/('fixture-'+label);root.mkdir()
    entry=root/'entry';entry.mkdir()
    (root/'bound.txt').write_bytes(b'bounded entry fixture\n')
    for name in ('offload.py','transport.py'):(entry/name).write_bytes(name.encode())
    manifest={'connection_path':'not-loaded-connection.json','files':[{'bytes':3662934016,'stat_identity':[]} ]}
    (entry/'manifest.json').write_text(json.dumps(manifest))
    bind={'bound.txt':m.old.sha(root/'bound.txt')}
    (entry/'bindings.json').write_text(json.dumps(bind))
    (entry/'release-bindings01.json').write_text('{}')
    review={'decision':'accepted','manifest_sha256':m.old.sha(entry/'manifest.json'),'worker_sha256':m.old.sha(entry/'offload.py'),'transport_sha256':m.old.sha(entry/'transport.py')}
    (entry/'RELEASE_REVIEW.json').write_text(json.dumps(review))
    return root,entry,manifest,review

for fault in ('positive','review-mismatch','bound-body-drift','scratch-one-byte-short','active-unit','unpublished-head'):
    root,entry,manifest,review=fixture(fault)
    if fault=='review-mismatch':
        review['worker_sha256']='0'*64;(entry/'RELEASE_REVIEW.json').write_text(json.dumps(review))
    if fault=='bound-body-drift':(root/'bound.txt').write_bytes(b'changed')
    commands=[]
    def fake_output(args,**kw):
        commands.append(args)
        if args[:3]==['git','rev-parse','HEAD']:return 'a'*40+'\n'
        if args[:3]==['git','branch','--show-current']:return 'research/onchain-paper-replication-2026-09-24\n'
        if args[:2]==['git','ls-remote']:return ('b' if fault=='unpublished-head' else 'a')*40+'\trefs/heads/research/onchain-paper-replication-2026-09-24\n'
        if args[:2]==['git','show']:return b'bounded entry fixture\n'
        if args[0]=='systemctl':return 'onchain-replication-fixture.service' if fault=='active-unit' else ''
        raise AssertionError(('unexpected fake command',args))
    floor=10*1024**3+3662934016+16*1024**2
    free=floor-1 if fault=='scratch-one-byte-short' else floor
    with patch.object(m,'ROOT',root),patch.object(m,'HERE',entry),patch.object(m,'eligibility',return_value=manifest['files'][0]),patch.object(m,'verify_saved_graph',return_value=None),patch.object(m.subprocess,'check_output',side_effect=fake_output),patch.object(m.shutil,'disk_usage',return_value=SimpleNamespace(free=free)),patch.object(resources,'mem_available',return_value=4*1024**3):
        try:m.preflight()
        except ValueError as error:
            assert fault!='positive',str(error)
            assert not (entry/'preflight01.json').exists()
            test_results.append({'case':fault,'status':'refused','reason':str(error)})
        else:
            assert fault=='positive'
            assert json.loads((entry/'preflight01.json').read_bytes())['full_recovery_scratch_required_bytes']==floor
            test_results.append({'case':fault,'status':'passed_at_exact_full_scratch_floor'})

pins={name:m.old.sha(ENTRY/name) for name in ('manifest.json','offload.py','transport.py','bindings.json')}
for name in ('offload.py','transport.py'):(HERE/('source-'+name)).write_bytes((ENTRY/name).read_bytes())
out={'status':'PASS_LOCAL_METADATA_AND_FAKE_ENTRY_ONLY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'entry_pins':pins,'bound_files_checked':len(bindings),'source_stat_identity':row['stat_identity'],
     'ledger_body_read':False,'connection_contents_inspected':False,'connection_sha256':c['connection_sha256'],
     'original_offload_one_and_finish_reused_unchanged':True,'transport_byte_identical':True,
     'closed_producer_and_saved_graph_joins':True,'active_claim_metadata':active,
     'indirect_mapping_metadata_pins':metadata_pins,'matching_current_uid_open_descriptors':open_consumers,
     'descriptor_checks':checked,'descriptor_inaccessible':inaccessible,'descriptor_vanished':vanished,
     'namespace_unused':unused,'fake_entry_checks':test_results,'workspace_free_bytes':shutil.disk_usage(ROOT).free,
     'required_full_scratch_free_bytes':10*1024**3+3662934016+16*1024**2,
     'native_or_network_operations':False,'source_deleted':False,'remote_recovery_proven':False}
(HERE/'CHECK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:out[k] for k in ('status','bound_files_checked','active_claim_metadata','descriptor_checks','descriptor_inaccessible','descriptor_vanished','workspace_free_bytes','required_full_scratch_free_bytes','fake_entry_checks')},indent=2))
