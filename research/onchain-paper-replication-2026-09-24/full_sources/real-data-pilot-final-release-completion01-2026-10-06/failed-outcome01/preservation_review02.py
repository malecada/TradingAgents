"""Exact source literal inverse and failed-pilot archive member integrity only."""
from pathlib import Path
import hashlib,io,json,stat,tarfile

R=Path.cwd()
BASE=Path('research/onchain-paper-replication-2026-09-24')
F=BASE/'full_sources'
H=F/'real-data-pilot-final-release-completion01-2026-10-06/failed-outcome01'
I='real-pilot-first-resource-failed-preservation-20261006-01'
OLDI='real-pilot-may30-continuation-preservation-20261006-01'
S=BASE/'storage'/I
OLD=BASE/'storage'/OLDI
CAP=F/'real-data-pilot-first-resource-failed-increment01-2026-10-06'
cache={}
def raw(p):
    p=Path(p)
    if p not in cache:
        q=R/p;s=q.lstat()
        assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
        b=q.read_bytes();assert len(b)==s.st_size
        z=q.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
        cache[p]=b
    return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(name,obj):
    p=H/name
    with p.open('x') as f:f.write(json.dumps(obj,sort_keys=True,indent=2)+'\n')
    return p

envelope=read(S/'envelope01.json');selection=read(S/'selection01.json');inverse=read(S/'INVERSE01.json')
assert sha(S/'envelope01.json')=='652290a8786f0b801ea06528d35ccfb7e4b779a1ee128246522f622c72185c45'
assert envelope['identity']==selection['identity']==I
assert inverse['only_replacement']=={'new_identity':I,'old_identity':OLDI}
prior=read(OLD/'RELEASE_REVIEW01.json');prior_env=read(OLD/'envelope01.json')
current_prior=BASE/'storage/real-pilot-july25-ledger-preservation-20261006-02'
current_release=read(current_prior/'RELEASE_REVIEW01.json');current_env=read(current_prior/'envelope01.json')
assert current_release['decision']=='accepted' and current_release['envelope_sha256']==sha(current_prior/'envelope01.json')
changed={'tradingagents/research/onchain_replication/resources.py','tradingagents/research/onchain_replication/workflow_storage.py'}
old_draft=read(S/'envelope.before-current-source-binding01.json')
assert sha(S/'envelope.before-current-source-binding01.json')=='dba25d95a265c5eccaa9ed32e0a8de5c0d2a3aa89083ac78922cdbd7dc0296c0'
inverse_envelope=dict(envelope);inverse_envelope['source_files']=dict(envelope['source_files'])
for p in changed:inverse_envelope['source_files'][p]=old_draft['source_files'][p]
inverse_envelope['scanner_sha256']=old_draft['scanner_sha256']
inverse_envelope['evidence']=envelope['evidence'][:3]
assert inverse_envelope==old_draft
assert prior['decision']=='accepted' and prior['identity']==OLDI and prior['envelope_sha256']==sha(OLD/'envelope01.json')
for current,previous in (('actual_entry','entry_predecessor'),('actual_keep','keep_predecessor')):
    a,b=inverse[current],inverse[previous]
    assert sha(a['path'])==a['sha256'] and sha(b['path'])==b['sha256']
    assert prior['evidence'][b['path']]==b['sha256']
    assert raw(a['path']).count(I.encode())==raw(b['path']).count(OLDI.encode())==1
    assert raw(a['path']).replace(I.encode(),OLDI.encode())==raw(b['path'])
assert len(envelope['source_files'])==12
for p,pin in envelope['source_files'].items():
    assert sha(p)==pin
    if p in changed:
        assert current_env['source_files'][p]==pin and current_release['evidence'][p]==pin
    elif p not in (inverse['actual_entry']['path'],inverse['actual_keep']['path']):
        assert prior_env['source_files'][p]==pin and prior['evidence'][p]==pin
for key in ('connection','environment','transport','local_only_evidence'):
    assert envelope[key]==prior_env[key]
assert envelope['scanner_sha256']==current_env['scanner_sha256']==envelope['source_files']['tradingagents/research/onchain_replication/workflow_storage.py']
private=envelope['connection']['path']
assert envelope['local_only_evidence']==[private] and private not in envelope['source_files']
assert private not in cache
assert sha(envelope['selection']['path'])==envelope['selection']['sha256']
assert sha(envelope['environment']['path'])==envelope['environment']['sha256']
assert envelope['helper']==inverse['actual_keep']
required={str(H/'OUTCOME_REVIEW01.json'):'9941387f26b7e3fe79f60848eac3a967b740700142d290ecbc83679d571466a4',
          str(H/'BODY_REVIEW01.json'):'03e91fe321fafa7c66d50a155a3157be5105709e1870ae6a32a64229ec1b5d53',
          str(CAP/'CAPTURE02.json'):'d9ba120e744432423d8cad321d059a9e2689c79b394c5daf5a55b1b8cce93fbf'}
required.update({str(current_prior/'envelope01.json'):'d0d8877bef6ae530157e0dd28ff50cc570aa46176efd63d00830156adb3c4b93',
                 str(current_prior/'RELEASE_REVIEW01.json'):'b7ed4c0000dab114201e433e5e9aa18100b0a25081340912bf64eae0c6262121',
                 str(F/'real-data-pilot-residual-enforcement-review01-2026-10-06/candidate-review03/REVIEW01.json'):'58475dfbb52798c98751dbbfa502828f08c98c366b7e7a9ef2e299f212f83fb2'})
assert {r['path']:r['sha256'] for r in envelope['evidence']}==required
for p,pin in required.items():assert sha(p)==pin
body=read(H/'BODY_REVIEW01.json');capture=read(CAP/'CAPTURE02.json')
assert body['decision']=='accepted' and capture['fresh_external_recovery'] is None
assert capture['regular_count']==body['regular_files']==38
assert capture['directory_count']==body['directory_count']==10
assert capture['original_regular_bytes']==body['logical_bytes']==399493
files={v['path']:v for v in body['files']};dirs={v['path']:v for v in body['directories']}
members={v['path']:v for v in capture['members']}
assert len(members)==len(capture['members'])==48 and set(members)==set(files)|set(dirs)
for p,v in files.items():
    assert members[p]['kind']=='regular' and all(members[p][k]==v[k] for k in ('bytes','sha256','mode'))
    s=Path(p).lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
    assert members[p]['stat_identity']==[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for p,v in dirs.items():assert members[p]['kind']=='directory' and members[p]['mode']==v['mode']
assert selection['count']==len(selection['files'])==1 and selection['directories']==[]
row=selection['files'][0];archive=Path(row['path'])
assert selection['total_bytes']==selection['max_body_bytes']==row['bytes']==491520
assert capture['archive']=={k:row[k] for k in ('path','sha256','bytes')}
archive_review=read(H/'ARCHIVE_REVIEW01.json')
assert sha(H/'ARCHIVE_REVIEW01.json')=='cadfc44c78f0bb1d74f14e32abc37e29138109476e7c83a7829730f78eb21bb0'
assert archive_review['decision']=='accepted' and archive_review['archive']==capture['archive']
assert archive_review['capture_sha256']==sha(CAP/'CAPTURE02.json') and archive_review['body_review_sha256']==sha(H/'BODY_REVIEW01.json')
assert row['sha256']=='b958a847dd6a1ad83b1e24694338c76d034cab104004580bcbe49c13860ebf08'
s=archive.lstat();assert row['mode']==stat.S_IMODE(s.st_mode) and row['nlink']==s.st_nlink==1
assert row['stat_identity']==[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
assert selection['disk_floor_bytes']==10*1024**3 and selection['transport_payload_budget_bytes']==8*1024**3 and selection['owned_tree_limit_bytes']==5*1024**3
assert selection['remote']=='research-backups/onchain-paper-replication-2026-09-24/'+I
# Exact archive/member bytes were checked once in actual e67b20. Reuse that
# immutable accepted proof with the unchanged archive stat identity above.
unused=('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json')
assert all(not (S/n).exists() and not (S/n).is_symlink() for n in unused)
check={'schema_version':1,'decision':'passed','identity':I,
    'envelope_sha256':sha(S/'envelope01.json'),'selection_sha256':sha(S/'selection01.json'),
    'archive':capture['archive'],'archive_review_reused':ref(H/'ARCHIVE_REVIEW01.json'),'regular_members':38,'typed_directory_members':10,'unpacked_regular_bytes':399493,
    'archive_members_body_hashes_and_modes_joined':True,'no_unlisted_members':True,
    'actual_source_literal_inverse_verified':True,'entry_identity_occurrences':1,'helper_identity_occurrences':1,
    'unchanged_public_transitive_source_pins':8,'current_accepted_source_rebindings':sorted(changed),'total_source_pins':12,
    'prior_accepted_release':ref(OLD/'RELEASE_REVIEW01.json'),
    'sole_transport_selection':'One closed failed-pilot increment archive; originals and fresh recovered archive retained.',
    'one_use_namespace_observed_unused':True,'private_connection_body_opened':False,
    'native_or_transport_invoked':False,'scientific_claim_or_budget_created':False,
    'external_byte_recovery_verified':False,'notes':['Capture01 stays preserved as a narrower capture; Capture02 contains the separately authenticated resource journal.',
       'Archive mode/name/body integrity is accepted; POSIX reconstruction and external recovery are not established.',
       'Fixed native caps and fresh entry Git/remote/process/namespace/RAM/disk controls are reused unchanged and must pass at actual launch.']}
cp=write('PRESERVATION_SOURCE_CHECK01.json',check)
evidence=dict(envelope['source_files'])
for p in (S/'envelope01.json',S/'selection01.json',S/'INVERSE01.json',CAP/'CAPTURE02.json',
          H/'OUTCOME_REVIEW01.json',H/'BODY_REVIEW01.json',H/'MANIFEST01.json',cp,H/'preservation_review02.py',
          H/'ARCHIVE_REVIEW01.json',H/'PRESERVATION_CHECK_FAILURE01.json',H/'preservation_review01.py',
          S/'envelope.before-current-source-binding01.json',
          OLD/'RELEASE_REVIEW01.json',OLD/'envelope01.json',
          Path(inverse['entry_predecessor']['path']),Path(inverse['keep_predecessor']['path']),
          Path(envelope['environment']['path']),*[Path(p) for p in required]):evidence[str(p)]=sha(p)
assert private not in evidence and str(archive) not in evidence
release={'schema_version':1,'decision':'accepted','identity':I,'envelope_sha256':sha(S/'envelope01.json'),
    'evidence':dict(sorted(evidence.items())),'scope':'ONE ordinary native preservation of exactly one491520-byte archive covering38 retained regular metadata/log bodies399493bytes and10typed directory names/modes from the permanently failed pilot. Separate real resource journal included; no other original stores or private/runtime bodies.',
    'review_check':ref(cp),'archive_reference':capture['archive'],
    'qualification':'Conditional source/entry release only. Exact current committed envelope/release/public evidence and actual remote HEAD, unchanged installed runtime, unused ordinary identity, no competing native/program claim, fresh3.5GiB RAM and full retained-recovery disk plus10GiB floor must pass in genuine entry. Existing256MiBmax/192MiBhigh/zeroSwap/3GiBreserve/twoCPU/14400second/5GiBowned/8GiBpayload controls unchanged. No empirical claim/budget, future recovery, POSIX reconstruction, deletion, capacity or successful transport outcome is granted. Prior failed pilot remains spent; never relaunch it.',
    'private_connection':'Unchanged inherited local-only reference; body not opened by reviewer.',
    'not_tested':['No transport/network/native entry or fresh physical/process/runtime/remote-Git preflight invoked.',
       'No external archive recovery yet; it requires actual fresh round trip and independent byte/member/mode acceptance.',
       'No scientific/numerical input inspection, fitting or experiment rerun.']}
rp=write('PRESERVATION_RELEASE_REVIEW01.json',release)
mp=write('PRESERVATION_MANIFEST01.json',{'schema_version':1,'decision':'accepted','identity':I,'files':[ref(H/'preservation_review02.py'),ref(cp),ref(rp)]})
print(json.dumps({'release':ref(rp),'manifest':ref(mp),'check':ref(cp),'evidence_count':len(evidence),'decision':'accepted'},sort_keys=True))
