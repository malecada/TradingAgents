"""Select actual public increments since the last verified external return."""
import datetime
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
F = HERE.parent.parent
assert HERE == ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full24-preparation-increment01-2026-10-09/full38increment33', 'deploy reviewed copies to exact H/full38increment33 before Root execution'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior = HERE.parent/'full36increment32/FRESH_GIT_RECOVERY32.json'
assert sha(prior)=='8db63835ace586bc84bb93f7ab4a87debab2e2c89ddd34cda61d353b314b3b50', 'actual32 baseline receipt changed'
review=F/'pilot36-increment32-return-release-review-2026-10-11/RETURN_REVIEW01.json'
assert sha(review)=='230a939c4ed35ed09d0fc3dda5ad9328f7920c4686769d6f3e6a852a557ec1f8', 'accepted32 return review changed'
base = json.loads(prior.read_bytes())['source']
names = set(subprocess.check_output(
    ['git', 'diff', '--name-only', base, 'HEAD'], cwd=ROOT, text=True).splitlines())
owned=['pilot38-target-boundary-coalescing-2026-10-12', 'pilot38-integration-cumulative-review-2026-10-12', 'real-data-pilot-full38-cumulative-preparation01-2026-10-12', 'real-data-pilot-full38-binding-preparation01-2026-10-12', 'pilot-efficiency-integration-2026-10-12', 'pilot38-entry-capacity-investigation-2026-10-12', 'pilot38-observer-ledger-correction-2026-10-12', 'pilot37-optimization-checks-2026-10-12', 'pilot38-admission-coalescing-2026-10-12', 'pilot36-outcome-review-2026-10-12', 'pilot38-public-binding-review-2026-10-12', 'pilot38-entry-policy-correction-2026-10-12', 'real-data-pilot-full38-entry-preparation01-2026-10-12', 'real-data-pilot-full36-entry-preparation01-2026-10-11', 'pilot36-increment32-return-release-review-2026-10-11', 'pilot36-increment32-tools-review-2026-10-11', 'pilot38-increment33-tools-candidate-2026-10-12', 'pilot38-increment33-tools-review-2026-10-12', 'pilot38-entry-registration-review-2026-10-12']
scope_directories=set()
for name in owned:
    root=F/name
    assert root.is_dir() and not root.is_symlink(), 'required final public scope absent: '+name
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():
            names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
closed_scopes=[ROOT/path for path in ['research_runs/eth-paper-real-data-end-to-end-resource-20261011-36', 'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261011-36', 'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent/eth-paper-real-data-end-to-end-resource-20261011-36', 'research_artifacts/onchain_representations/4c1d07a983d266df70164d623a20d61a71499c9fec9e9d6a64a1f7ba6b1583e6/eth-paper-real-data-end-to-end-resource-20261011-36']]
for root in closed_scopes:
    assert root.is_dir() and not root.is_symlink(), 'required closed36 owned root absent: '+str(root)
    scope_directories.add(root)
    for path in root.rglob('*'):
        if path.is_file() or path.is_symlink():names.add(str(path.relative_to(ROOT)))
        elif path.is_dir():scope_directories.add(path)
# Exact generated32 receipts/raw operations only. Never traverse historical H.
prior_generated_names=['CAPTURE32.json', 'FINAL_REMOTE_CONFIRMATION32.json', 'FRESH_GIT_RECOVERY32.json', 'GIT_OPERATIONS32.json', 'ROOT_ACTUAL_OPERATIONS32.json', 'ROOT_CAPTURE_OPERATIONS32.json', 'SELECTION32.json', 'actual_external_archive_blob_return.stderr', 'actual_external_archive_blob_return.stdout', 'actual_external_commit_body.stderr', 'actual_external_commit_body.stdout', 'actual_external_commit_only_fetch.stderr', 'actual_external_commit_only_fetch.stdout', 'actual_external_selected_blob_fetch.stderr', 'actual_external_selected_blob_fetch.stdout', 'fetched_head_readback.stderr', 'fetched_head_readback.stdout', 'final_commit32.stderr', 'final_commit32.stdout', 'final_diffcheck32.stderr', 'final_diffcheck32.stdout', 'final_push32.stderr', 'final_push32.stdout', 'final_remote_readback32.stderr', 'final_remote_readback32.stdout', 'fresh_bare_init.stderr', 'fresh_bare_init.stdout', 'fresh_remote_add.stderr', 'fresh_remote_add.stdout', 'local_archive_git_tree_join.stderr', 'local_archive_git_tree_join.stdout', 'local_head.stderr', 'local_head.stdout', 'remote_actual_branch_readback.stderr', 'remote_actual_branch_readback.stdout', 'remote_get_url.stderr', 'remote_get_url.stdout', 'root_commit32.stderr', 'root_commit32.stdout', 'root_diffcheck32.stderr', 'root_diffcheck32.stdout', 'root_push32.stderr', 'root_push32.stdout', 'set_promisor.stderr', 'set_promisor.stdout', 'set_tree_zero_filter.stderr', 'set_tree_zero_filter.stdout']
for name in prior_generated_names:
    path=prior.parent/name
    assert path.is_file() and not path.is_symlink(), 'required actual32 receipt absent: '+name
    names.add(str(path.relative_to(ROOT)))
helper_names=('select33.py', 'capture33.py', 'recover33.py', 'TOOL_SCOPE01.json', 'HELPERS_MANIFEST01.json', 'LITERAL_PATCH01.diff', 'LITERAL_INVERSE01.diff', 'select33_02.py', 'TOOL_SCOPE02.json', 'SELECTOR02_MANIFEST01.json', 'SELECTOR02_PATCH01.diff', 'SELECTOR02_INVERSE01.diff', 'ROOT_CAPTURE_FAILURE33.json', 'root_select33.stdout', 'root_select33.stderr')
for name in helper_names:names.add(str((HERE/name).relative_to(ROOT)))
fixed_public_names=['research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md', 'docs/superpowers/plans/2026-10-11-onchain-pilot-efficiency.md', 'research/onchain-paper-replication-2026-09-24/CURRENT_IMPLEMENTATION.md', 'research/onchain-paper-replication-2026-09-24/STATE.md']
for relative in fixed_public_names:
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink(), relative
    names.add(relative)
main_source_names=['tradingagents/research/admission.py', 'tradingagents/research/onchain_replication/compact_mcm.py', 'tradingagents/research/onchain_replication/imported_authority_lease.py', 'tradingagents/research/onchain_replication/imported_mcm_identity.py', 'tradingagents/research/onchain_replication/job.py', 'tradingagents/research/onchain_replication/streamed_gat.py', 'tests/research/onchain_replication/test_compact_mcm.py', 'tests/research/test_streamed_gat_lifetime_candidate.py']
extra_git_delta_pins={'research/onchain-paper-replication-2026-09-24/full_sources/pilot36-entry-overhead-investigation-2026-10-11/OBSERVATION01.json': '592fec7f539684c4b145082a02447557324c39de919473df94d7a7567a9abea0', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot36-entry-overhead-investigation-2026-10-11/REPORT.md': '7103d375bb9f5ac5d0e02e7ad4563078c360c0be0e95bc4375ace15acf575cf3', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot36-entry-overhead-investigation-2026-10-11/RESULT01.log': 'c2d53426f6b98df6f3da412214221e6db46daf326f4531905b3238070dd4dedf', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot36-entry-overhead-investigation-2026-10-11/observe01.py': 'ae25de5446e25384a93094e2f5447ca89f2eabe0b2571037d8164860bce7b9cb', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot36-live-observations-2026-10-11/GUARD_SAMPLE01.json': '1b2c71f34aa348af53f1ecea130d1839e30e73f9f23db5b7cd0ac869f968a47a', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot36-live-observations-2026-10-11/ROOT_OBSERVATION01.json': 'ac7e3e888edcbd6f6dd14909b10308773cf94c0497024a2d7d7fe8f2589b2a9a', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-admission-size-read-candidate-2026-10-11/CANDIDATE01.json': 'c93d32c050cad94454761e634fd9ec90017370d09fa90a2158a19803a02aa80c', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-admission-size-read-candidate-2026-10-11/INVERSE01.diff': '49ee82de22e8587d3a4fb599f5c8cb14867a557eb240b30f07b2af9ab24f6ebb', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-admission-size-read-candidate-2026-10-11/PATCH01.diff': '12d6be4fd99a6cc20d2d761e127a3021b891482630bb69820e5a01328dc7c287', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-admission-size-read-candidate-2026-10-11/REPORT.md': '805365bc2c6d4dec273013f5a25733fcec5b4da640cbcd45c1ef0fe3baf0a49d', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-admission-size-read-candidate-2026-10-11/admission.py': '793c4034d23ff4e486e2a888004b1dc69a11383c4d4460f01d1489fd5794f7a7', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-admission-size-read-candidate-2026-10-11/test_candidate01.py': 'acce011744a6dcccc11d64d92c402d01c4f78849082b258121e2e93a9e3f0f97', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-2026-10-11/CAPACITY01.json': '5d777f88cbaa2cdf35c6bf703d0d746d9d02be4cae11a344531d4483a2b5bf40', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-2026-10-11/REPORT.md': 'f3140171fd7621fd0ac1d43f3c3cc635638b27ec9255e44d1768b7b890187e56', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-2026-10-11/RESOURCE01.txt': 'e2a103b176dd6343246da19d57a851285985d6383970f2d04b11fa7e49374a07', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-2026-10-11/RESULT01.log': 'b5639674d0c7897ddfa9dc210ff253aa8203790be6d45fcdff8644e2a8d2f91f', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-2026-10-11/calculate01.py': 'c953916493b7ecb13c298a79187d084c710daec696c49b9260026b6aefa558da', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-review-2026-10-11/CHECK01.json': '3b20808d682d403423f1255800843ffa9db92ba5460099c93bc0f40fba45fb7e', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-review-2026-10-11/CHECK01.log': 'c9f4fde0393a5f45a79ec702a76197c58b4137969c8b6880e75e0239dcda95cb', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-review-2026-10-11/REPORT.md': 'a2c3a3abba6e5b15b6370fa90cae1af482cef32843b1b44cfb11b11684f9deb4', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-continuation-capacity-review-2026-10-11/check01.py': 'f8082403f918e8944cd75e7ac9c32c59dc74f3467dde25f6d0bb80fa407f0c1f', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/INVERSE_PATCH01.diff': '1263d102c0d5f0be6d5043dca7efc1ac35e4d2f6caebf572cae4fb16e5c5096b', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/LITERAL_PATCH01.diff': 'fc8057656c74884588accd84b88eca38bf55c69f30832d4185a5e41a13b55be7', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/MANIFEST01.json': '0786398d0bdaa6abba4c9949571f43fdf261069677a7801ab8916c3a0406ed70', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/PREPARATION01.json': '7dc7513a5db0eec41e0c8d08c1e00ad4720cb6133711274aba943c5c54f875c6', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/REPORT.md': '536ab939d45d2ad922a0d951fa2fa23a9ed7c234b7ebefbe50f4034d994eb2e5', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/STATIC_CHECK01.json': 'f6a775de799b1a4e29c7064515413304d432c4dc51dbdc06c4543123819c2b2a', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/streamed_gat_candidate.py': '7eb9c982b80d3a1e1801c4df8bc862fb02025016feae3e805e184506a08eacf1', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-gat-lifetime-candidate-2026-10-11/test_candidate.py': 'bff2a61fb50debf361011191e87c7f4013ed695a36899ac8f66a26fd9395dfc8', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-training-memory-investigation-2026-10-11/REPORT.md': '2a6a1d091f18b302fbabf703770defe925eb74e171b7ae21fc3bab788caace89', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-training-memory-investigation-2026-10-11/SIZES01.json': '09e25beabc14681f8b26e28eca4ad6c9a85faed483f3922c83d664324a0b0332', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-training-memory-investigation-2026-10-11/SOURCE_SNAPSHOT01.json': '081bff6d7772774f098c788aa1f3d97f38de69a15adef973e9ce99fa8e4007cc', 'research/onchain-paper-replication-2026-09-24/full_sources/pilot37-training-memory-investigation-2026-10-11/calculate01.py': '3bb72ffbf770832538126ae25cb14a88d03a78d0154dee25a319be63e1c3d0fb', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/BUILDER_LITERAL_PATCH01.diff': 'c384c5165062ef18f3e328e2de14ec5b088f279e41535a117f4d9b3d5d6e6494', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/CURRENT_NUMERICAL_GIT_JOIN01.json': '2f44dfd12c2053cd0609961b9b2e2a10690952044da8a6920a611356eb981b06', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/EXPECTED_CODE_POLICY01.json': 'a53290d42b8ebce2519efb15857f1a0a5f9243256713a233ec04ba0f3d19a0db', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/LITERAL_PATCH01.diff': 'ed6226b72c645d8fb1c8982125047e6aed6873b7635bd4fd42a6db6c513718a1', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/MANIFEST01.json': 'f006177c763d7abc2fabb10e8c4ded134caac418d0b739333ef613f343a03530', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/PREPARED01.json': '50ebdf8429e7ae6e0cdc4baf70825179d345c9a3896094d9a5a8ca0d50ede94f', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/PUBLIC_INPUT_REFS_DRAFT01.json': '4bbe4c62370f8a918ae9f2659669ad8049134aa3dcb84d929fa9bb15ef90e773', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/REQUEST01.json': '76fbec48ca50ac739a39a17246415b1d62966c46f299d156aa5a7cd4911f659e', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/ROOT_PREPARATION01.json': '3d8682847c4dd479610d1cea8ea0b82746cadb20391cc4637eb4c6623e696e77', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/bind_actual01.py': '2853b0680c92963298951c96e3a0a0b9816b830861671dc63a230534b49970f6', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/build_public01.py': '12a6ab5d508ccafaf5a7e746f7b459ca347792f14b3f355af490e242b813e910', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/archive_policy.json': 'c434f386e2616e101cb83bc188f7f34e37d656681beddb139c1a5a52e737c0fc', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/archive_transport.json': '6f0adf5b13fa5e563d793881858616c67d643b6017c3ab21a834b27066c0e345', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/compact_policy.json': 'e0c0ae4150c6ddc97662209df7ae60ed08adf7dc00518e94237c9ee94d376ada', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/execution_job.json': '0c113d5c653a7341d935ff1b51073bd9e995e6dc25f7e04aa20ab75656240f44', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/mcm_output_policy.json': '4c45712816a0f59bbb18477c7f78cd05f16a62b338348750ed9743a594f6d447', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/mcm_policy.json': '15d889f972da381ffe24c7147befdc806e7836dc7a1e7f4d382e672af6c1db7d', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/original_import.json': '635dc513c4b1fb9d85c68a393cdc2576dbf1e38320f8c03326ceef26ffdb9fee', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/pair_policy.json': 'dba5b5251be6287536b45f5971d40a201894b02643ce08455d8cccb5bf9cd3fd', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/pilot.json': 'f9cec85bb9b6cd132ef1ffa7f97d9b7d1b01dac2ad695d3dffa492157d487a06', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/producer_plan.json': '8b4781247f9fad85b99983b728274f748eef4bb9aff585ca8e6b45ba4091ebae', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/resource_population_plan.json': '3265929788979c1b1a6bfa628798d68daff4b33847aeb76fca85d0040874d5b4', 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full37-binding-preparation01-2026-10-11/public01/typed_payload.json': 'ee00ceab9b532d97829a1ca0fbb010c211055681212a579c730c5a39bb66b596'}
# Exact post32 committed metadata bodies only; no additional tree traversal.
for relative,expected in extra_git_delta_pins.items():
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink() and sha(ROOT/relative)==expected, relative
    names.add(relative)

# Exact closed36 owned roots above; only the new bound opaque envelope below.
scopes=[ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261012-38-01']
private=ROOT/'research_artifacts/real_pilot_runtime/pilot-transport-20261012-38-01/archive_transport01.json'
assert private.is_file() and not private.is_symlink()
assert private.stat().st_size==930 and sha(private)=='267cc1d38f13245afdf27fc40fb4333ebbf775857ade36ec6fa3007f95929983', 'exact bound38 opaque bytes changed'
private_relative=str(private.relative_to(ROOT))
names.add(private_relative);scope_directories.add(private.parent)
# Already returned preparation36 archive/blob stdout stay immutable at original
# paths and the verified remote object; new receipt bodies are included.
prior_receipt=json.loads(prior.read_bytes())
assert prior_receipt['capture']['path']==str((prior.parent/'CAPTURE32.json').relative_to(ROOT))
assert sha(ROOT/prior_receipt['capture']['path'])==prior_receipt['capture']['sha256'], 'actual32 capture receipt changed'
prior_capture=json.loads((ROOT/prior_receipt['capture']['path']).read_bytes())
excluded={prior_capture['archive']['path'],prior_receipt['returned_archive']['path'],str((prior.parent/'actual_external_archive_blob_return.stdout').relative_to(ROOT))}
assert excluded=={str((prior.parent/name).relative_to(ROOT)) for name in ('pilot36-preparation-increment32.tar','fresh-git-recovered-full36increment32.tar','actual_external_archive_blob_return.stdout')}
for relative in excluded:
    path=ROOT/relative
    assert path.is_file() and not path.is_symlink() and path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256'], relative

# Only actual new or changed bodies; immutable prior recovered entry bodies are reused.
prior_selection=json.loads((prior.parent/'SELECTION32.json').read_bytes())
assert sha(prior.parent/'SELECTION32.json')==prior_capture['selection']['sha256']
previous_rows={row['path']:row for row in prior_selection['rows']}
names.update(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines())
assert not (HERE/'SELECTION33.json').exists(), 'selection33 already spent'
assert all(not (ROOT/relative).is_relative_to(HERE) or (ROOT/relative).name in helper_names for relative in names), 'generated full38increment33 products are outside selection'
# Bound actual committed/working Git deltas to this declared finite increment.
allowed_files={private_relative}|set(extra_git_delta_pins)|set(fixed_public_names+main_source_names)|{str((prior.parent/name).relative_to(ROOT)) for name in prior_generated_names}|{str((HERE/name).relative_to(ROOT)) for name in helper_names}
allowed_roots=[F/name for name in owned]+closed_scopes
assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names), 'Git delta outside declared full38increment33 scope'
main_source_pins={'tradingagents/research/admission.py': '793c4034d23ff4e486e2a888004b1dc69a11383c4d4460f01d1489fd5794f7a7', 'tradingagents/research/onchain_replication/compact_mcm.py': '806f1ebeb4e262f1cc0a7945e2717d538e68b3b1f45452c449cf0c42b7d49942', 'tradingagents/research/onchain_replication/imported_authority_lease.py': 'ea25f774d4165e460824eaee0425bb6d860825fb7e97784360bb914f5fada741', 'tradingagents/research/onchain_replication/imported_mcm_identity.py': '15d45478fc33602763b65acebd20f571e8fcbd1fd7b40e3aba05c9a900da1ccf', 'tradingagents/research/onchain_replication/job.py': '2f842fd6d0bcc8599a92bc89e088406df90f6c0cad171b7e2d0383d0832cab34', 'tradingagents/research/onchain_replication/streamed_gat.py': '7eb9c982b80d3a1e1801c4df8bc862fb02025016feae3e805e184506a08eacf1', 'tests/research/onchain_replication/test_compact_mcm.py': 'd3073795c7b1bbf04a111b6356ca1168eb15abe3daa0cae0b77145545547c6c6', 'tests/research/test_streamed_gat_lifetime_candidate.py': '11e758ea9f1f1e3b3b550f5e718d4142abdb5bb9b86894103e53c9df2e4469a5'}
for relative,expected in main_source_pins.items():
    assert (ROOT/relative).is_file() and not (ROOT/relative).is_symlink() and sha(ROOT/relative)==expected, relative
    names.add(relative)

reused=[]
for relative in sorted(names-excluded):
    old=previous_rows.get(relative);path=ROOT/relative
    if old and old['type']=='regular' and not path.is_symlink() and path.is_file() and format(stat.S_IMODE(path.stat().st_mode),'04o')==old['mode'] and path.stat().st_size==old['bytes'] and sha(path)==old['sha256']:
        reused.append(relative)
names = sorted(names-excluded-set(reused))
rows = []
directories = set(scope_directories)
for relative in names:
    path = ROOT/relative
    assert path.parent.resolve(strict=True) == path.parent, relative
    assert not ({'.git', '.venv', 'node_modules', 'keys', 'apis'} & set(path.parts)), relative
    assert path.name not in ('.env', 'hf_token.txt', 'connection.json', 'id_ed25519_storagebox_u676273'), relative
    assert not relative.startswith(('research_artifacts/', 'research_runs/')) or relative==private_relative or any(path.is_relative_to(root) for root in closed_scopes), relative
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode):
        target = os.readlink(path)
        row = {'path': relative, 'type': 'symlink',
               'mode': format(stat.S_IMODE(before.st_mode), '04o'),
               'linkname': target, 'bytes': 0}
    else:
        assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= 64*1024**2, relative
        body = path.read_bytes()
        row = {'path': relative, 'type': 'regular',
               'mode': format(stat.S_IMODE(before.st_mode), '04o'),
               'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    after = path.lstat()
    assert all(getattr(before, k) == getattr(after, k) for k in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), relative
    rows.append(row)
    parent = path.parent
    while parent != ROOT:
        directories.add(parent)
        parent = parent.parent
dirs = []
for path in sorted(directories):
    assert path.resolve(strict=True) == path and not path.is_symlink()
    dirs.append({'path': str(path.relative_to(ROOT)), 'type': 'directory',
                 'mode': format(stat.S_IMODE(path.stat().st_mode), '04o')})
selection = {
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'baseline_actual_recovery': {'path': str(prior.relative_to(ROOT)), 'sha256': sha(prior)},
    'baseline_source': base,
    'baseline_accepted_review': {'path':str(review.relative_to(ROOT)), 'sha256':sha(review)},
    'prior_inherited_reuse_preserved_by_receipt':prior_selection['exact_unchanged_prior_rows_reused'],
    'earlier_inherited_reuse_preserved_by_receipt':prior_selection['prior_inherited_reuse_preserved_by_receipt'],
    'mandatory_public_roots':owned,
    'exact_additional_committed_metadata_pins':extra_git_delta_pins,
    'prior_generated_files':prior_generated_names,
    'actual_scope_states': [{'path':str(path.relative_to(ROOT)), 'exists':True,'qualification':'Exact closed36 owned root or sole new38 opaque envelope parent; no sibling historical store or referenced connection target.'} for path in closed_scopes+scopes],
    'exact_already_recovered_duplicate_exclusions':sorted(excluded),
    'exact_unchanged_prior_rows_reused':reused,
    'selection_rule': 'Finite new12Oct efficiency, closed36 outcome and38 preparation bodies, exact changed source/tests, public/binding/entry/amendment reviews and actual32 postcapture receipts. Only the newly bound opaque dispatch envelope is selected from private runtime; its referenced connection path is never read. Prior typed bodies reused through actual32 recovery. No historical raw-store traversal, credential-body access or deletion authority.',
    'files': len(rows), 'body_bytes': sum(r['bytes'] for r in rows),
    'rows': rows, 'directories': dirs,
    'symlinks': sum(r['type'] == 'symlink' for r in rows),
    'qualification': 'Public incremental byte/name/type/mode selection only. Symlink targets are recorded without dereferencing; regular bodies have a 64MiB preservation bound independent of unchanged empirical native limits. No originals are copied or retired; no source/runtime/empirical store completeness beyond these selected new bodies is asserted.'}
with (HERE/'SELECTION33.json').open('x') as stream:
    json.dump(selection, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps({'selected_files': len(rows), 'selected_bytes': selection['body_bytes'],
                  'directories': len(dirs)}))
