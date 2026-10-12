"""Opt-in durable complete-batch import; admission remains genuine caller-owned.

No directory scan guesses a prefix. Every recovered body is a registered input
and the caller must validate the reviewed parent/allowance/recovery authority.
"""
from dataclasses import dataclass, fields
from weakref import WeakKeyDictionary
import hashlib
import json
import os
import struct
from .batched_journal import HEADER, RECORD, MAGIC, STATUS, body, digest, require
from . import batched_numeric_execution as numeric_format

POLICY = 'completed-prefix-v1'
_VERIFIED = WeakKeyDictionary()
_READERS = WeakKeyDictionary()
_USED = WeakKeyDictionary()
MAX_MANIFEST_BYTES = 32*1024**2
SUFFIXES = ('.pending.json', '.records.bin', '.complete.json')

@dataclass(frozen=True, eq=False)
class CompletedBatch:
    score_bodies: tuple
    origins: bytes
    summary: bytes
    commit: bytes
    records: tuple
    legacy: bool = False

@dataclass(frozen=True, eq=False)
class CompletedPrefix:
    parent_experiment: str
    successor_experiment: str
    workflow_identity: str
    graph_hash: str
    next_ordinal: int
    batches: tuple
    origin_sha256: str
    score_sha256: str
    numerical_contract_sha256: str
    spent_counters: tuple
    manifest_sha256: str
    descriptors: tuple = ()
    verification_counters: tuple = ()


def _json(raw):
    value = json.loads(raw)
    require(body(value) == raw, 'continuation canonical JSON required')
    return value


def commit_batch(journal, numeric, contract_sha256):
    """Last durable publication, after score + numeric closure, before retirement."""
    require(type(contract_sha256) is str and len(contract_sha256)==64 and all(c in '0123456789abcdef' for c in contract_sha256), 'continuation contract digest required')
    index = journal.batch - 1
    require(index >= 0 and numeric.batch == journal.batch and numeric.ordinal == journal.cells and not numeric.buffer, 'score/numeric complete boundary differs')
    require(not numeric.poisoned and not numeric.closed, 'numeric continuation unavailable')
    journal.read_complete(index)
    blobs = tuple(journal._read(f'{index:08d}'+suffix)[0] for suffix in SUFFIXES)
    summary, _ = numeric_format.read_file(numeric.batches_fd, f'{index:012d}.json', numeric_format.SUMMARY_LIMIT)
    s = _json(summary)
    numeric._origin_current()
    origins = os.pread(numeric.origins_fd, 9*(s['stop']-s['start']), 9*s['start'])
    require(digest(origins)==s['origin_sha256'] and s['stop']==journal.cells, 'continuation origin join differs')
    prior=getattr(numeric,'imported_costs',{})
    value = {'policy':POLICY, 'batch':index, 'start':s['start'], 'stop':s['stop'],
             'contract_sha256':contract_sha256, 'cost_epoch_start':getattr(numeric,'continuation',{}).get('imported_cells',0), 'score_sha256':[digest(b) for b in blobs],
             'origin_sha256':digest(origins), 'summary_sha256':digest(summary),
             'counters':s['counters'], 'checkpoint_attempts':numeric.memo.executor.checkpoints+prior.get('checkpoint_attempts',0),
             'checkpoint_reserved_bytes':numeric.memo.executor.reserved_bytes+prior.get('checkpoint_reserved_bytes',0),
             'operation_counters':{k:getattr(numeric.memo.executor,k)+prior.get(k,0) for k in ('completed_operations','advance_calls','abandoned_call_operation_limit')}}
    raw = body(value)
    name = f'{index:08d}.prefix.json'
    journal._write(name, raw, journal.max_body)
    return raw


def _decode_batch(blobs, index, start, batch_cells, cells, contract, *, legacy=False):
    require(type(blobs) is tuple and len(blobs)==6 and all(type(b) is bytes for b in blobs), 'six recovered bodies required')
    pending, payload, complete, origins, summary, commit = blobs
    p, m, s, c = map(_json, (pending,complete,summary,commit))
    stop = min(start+batch_cells,cells)
    require(p == {'schema':3,'kind':'engineering_pending','start':start,'stop':stop,'workload_sha256':contract['descriptor_sha256'],'disposition':'attempted_unknown_without_complete'}, 'prefix pending/order/config differs')
    require(len(payload)==HEADER.size+(stop-start)*RECORD.size, 'prefix score extent differs')
    require(m == {'schema':3,'kind':'engineering_complete','pending_sha256':digest(pending),'payload_sha256':digest(payload),'payload_bytes':len(payload),'record_bytes':RECORD.size,'purposes_sha256':m.get('purposes_sha256')}, 'prefix score commitment differs')
    require(HEADER.unpack_from(payload)==(MAGIC,RECORD.size,start,stop,bytes.fromhex(digest(pending)),bytes.fromhex(m['purposes_sha256'])), 'prefix score header differs')
    records=tuple(RECORD.iter_unpack(payload[HEADER.size:])); aggregate=hashlib.sha256()
    import math
    for ordinal,row in enumerate(records,start):
        require(row[0]==ordinal and math.isfinite(row[2]) and 0<=row[2]<=1 and row[4] in STATUS.values(), 'prefix score record differs')
        aggregate.update(row[1])
    require(aggregate.hexdigest()==m['purposes_sha256'], 'prefix purpose order differs')
    require(len(origins)==9*(stop-start) and s['format']==numeric_format.FORMAT and s['batch']==index and s['start']==start and s['stop']==stop and s['origin_sha256']==digest(origins), 'prefix numeric range/hash differs')
    computed=reused=0
    for ordinal,(mode,origin) in enumerate(numeric_format.RECORD.iter_unpack(origins),start):
        require((mode==0 and origin==ordinal) or (mode==1 and origin<ordinal), 'prefix origin order differs')
        computed+=mode==0;reused+=mode==1
    require(s['computed']==computed and s['reused']==reused and s['old_per_occurrence_execution_credit'] is False, 'prefix numeric counts differ')
    require(type(s['elapsed_seconds']) is float and math.isfinite(s['elapsed_seconds']) and s['elapsed_seconds']>=0
            and s['receipt_framing']=='u64be-length/canonical-json-newline' and type(s['receipt_sha256']) is str
            and len(s['receipt_sha256'])==64 and all(x in '0123456789abcdef' for x in s['receipt_sha256']), 'prefix receipt/timing differs')
    if 'phase_totals' in s:numeric_format.validate_phase_totals(s['phase_totals'])
    require(type(s['counters']) is dict and all(type(k) is str and type(v) is int and 0<=v<2**127 for k,v in s['counters'].items()), 'prefix counters invalid')
    expected={'policy':POLICY,'batch':index,'start':start,'stop':stop,'contract_sha256':contract.get('numerical_contract_sha256',digest(body(contract))), 'cost_epoch_start':c.get('cost_epoch_start'),'score_sha256':[digest(b) for b in blobs[:3]],'origin_sha256':digest(origins),'summary_sha256':digest(summary),'counters':s['counters'], 'checkpoint_attempts':c.get('checkpoint_attempts'),'checkpoint_reserved_bytes':c.get('checkpoint_reserved_bytes'),'operation_counters':c.get('operation_counters')}
    require(type(c.get('cost_epoch_start')) is int and 0<=c['cost_epoch_start']<=start, 'prefix cost epoch differs')
    if legacy:
        expected['policy']='legacy-recovered-prefix-v1'
    require(c==expected and all(type(c[k]) is int and 0<=c[k]<2**127 for k in ('checkpoint_attempts','checkpoint_reserved_bytes')), 'prefix durable commit differs')
    require(type(c['operation_counters']) is dict and set(c['operation_counters'])=={'completed_operations','advance_calls','abandoned_call_operation_limit'} and all(type(v) is int and 0<=v<2**127 for v in c['operation_counters'].values()), 'prefix operation counters unavailable')
    expected_batch=(blobs[:3],origins,summary,commit,records,legacy)
    result=CompletedBatch(*expected_batch)
    require(type(result) is CompletedBatch and tuple(getattr(result,f.name) for f in fields(result))==expected_batch,'batch constructor changed authenticated fields')
    return result


def _original39_contract():
    return {'format': 'original39-post-prefix-failure-v1', 'parent': 'eth-paper-real-data-end-to-end-resource-20261012-39', 'claim_sha256': '54628d15f251bf49187df05619e2261e6da4540065b8b946d517070d9eb60d95', 'failed_sha256': 'cace46a41f93823bc75e267ad367c1833300bc9af297cc9fc543ed8412ec5497', 'evidence': {'traceback': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261012-39/guard/child.log', 'sha256': '4b7f24b61af7f7daa40888a0aa5b17b001aa25cd46d469d3c198be2304f0a5a8'}, 'return_review': {'path': 'research/onchain-paper-replication-2026-09-24/full_sources/pilot39-outcome-increment37-review-2026-10-12/RETURN_REVIEW01.json', 'sha256': 'dddc9b54f42c790323b4f0ae5715d3f78b4234894c3131e6bf9aa1612826d33d'}, 'recovery': {'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full24-preparation-increment01-2026-10-09/full39outcome37/FRESH_GIT_RECOVERY37.json', 'sha256': '73f0d1ab38e6b4158b632f601815c8363ebc7a1d200e708029b7f20e212d5db4'}, 'selection': {'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full24-preparation-increment01-2026-10-09/full39outcome37/SELECTION37.json', 'sha256': '0759247af7cc39a029d6da083911c3abcce2173f55dfc82e205ca954b07d2b2b'}, 'capture': {'path': 'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-full24-preparation-increment01-2026-10-09/full39outcome37/CAPTURE37.json', 'sha256': '61a89d6cd2ef1519f085d4ef0874e83c8de96d09cfd3ad52417576462b849565'}, 'guard_final': {'path': 'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261012-39/guard/final.json', 'sha256': '6536f201e4010036e988c1fd24b034fa42739dad0549e7c51c6d891e14d7e668'}, 'output:archive-receipt.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/archive-receipt.json', 'sha256': '43d680dea93690516cc865ebe3987cea7b7a63e459ea5cfed0569618f209f7d6'}, 'output:archive-terminal.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/archive-terminal.json', 'sha256': '5010f549dce1df5795d99c7d06a785c52e182730eb92edd9d8ac093a89dca965'}, 'output:cell-ledger.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/cell-ledger.json', 'sha256': '5e7e9bd53aeb9dd6442f6333a51675e974d986326f7415b9cb212f312a5cbd54'}, 'output:phase-timing.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/phase-timing.json', 'sha256': '54d5db168066e7c623a5915bff62270479075b799dc15131a0e93ce02382ed39'}, 'output:pilot-summary.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/pilot-summary.json', 'sha256': '0b37e4d463229981a746d7d10670c27d6e85c28f57d2da84a9d9b5cd14b5643f'}, 'output:resource-binding.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/resource-binding.json', 'sha256': 'fa40899a60cd15be57b007fc9c815ff32879fcd3fdd23fecea32b2cd67f24a7f'}, 'output:resource-journal.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/resource-journal.json', 'sha256': 'fa40899a60cd15be57b007fc9c815ff32879fcd3fdd23fecea32b2cd67f24a7f'}, 'output:resource-population-binding.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/resource-population-binding.json', 'sha256': '363b51245af7a38217ccba9b6c8d0cf9283e38cd4fc0b03e1e4498a82555aa5e'}, 'output:resource-population.json': {'path': 'research_runs/eth-paper-real-data-end-to-end-resource-20261012-39/outputs/resource-population.json', 'sha256': '2bba5228869300fe51c40ce62ae482a23afd65d5a49b69d605e1f0e6b99101b0'}}, 'sources': {'tradingagents/research/onchain_replication/batched_continuation.py': '1accf714c9853766f9ffa48c1191fe0706d4b397599c14b7aa8d302cc09d331b', 'tradingagents/research/onchain_replication/batched_driver.py': 'f8fe3e83d4d7d55e477cc054659dd8335034f872ce7ab589573ad6cd3ee53335', 'tradingagents/research/onchain_replication/batched_journal.py': 'a550157d767f0c78dfdfdefa6fe5e46ec037e4cc2c885d9f23d330c1400b5678', 'tradingagents/research/onchain_replication/batched_numeric_execution.py': '6284a216957b50e4b5a9f0ca0640f88ef8d9e719b235d089903429b1b8a76916', 'tradingagents/research/onchain_replication/batched_numeric_reuse.py': '1362725cdf967cd4f324e0c5e410fee1971ff07610c3d2b5efb5978e96469586', 'tradingagents/research/onchain_replication/batched_pair_executor.py': '0d1c7a14866b53e6bde4b9db6e3eff4740190d16bc3db0f6532d60afd3142005', 'tradingagents/research/onchain_replication/compact_mcm_batched.py': 'dc14816d304dde383b7a10dd55558fe72d95e5c1da870a721ab512126943bae6', 'tradingagents/research/onchain_replication/grouped_offload.py': 'e11ca240b89ab611c521f68adda38322ff191d17e11f6c64387b230b3708aed2', 'tradingagents/research/onchain_replication/real_pilot_import_caller.py': '02ca18cd68375a07a6176081309469277f7b74be285a3b29d93af2fd052206ae', 'tradingagents/research/onchain_replication/typed_payload_operations.py': 'a5668d7fe9c261c1908170969b39d675947c19beb1d04fad824f6f6a4e801f56', 'tradingagents/research/onchain_replication/imported_authority_interval.py': 'e61ef97f883ed9d27107f6316b774697b8949d83c313928150a0ae717b283f6f', 'tradingagents/research/onchain_replication/imported_authority_lease.py': 'ea25f774d4165e460824eaee0425bb6d860825fb7e97784360bb914f5fada741', 'tradingagents/research/onchain_replication/imported_mcm_identity.py': '15d45478fc33602763b65acebd20f571e8fcbd1fd7b40e3aba05c9a900da1ccf'}, 'batches': [['f88f11c19e9812f1d0922b6ae787bfc3e6789b225622dd36b3970298b141799f', 'd9ecde40c1a8c84653c50dcbee78bbec85413d23e5e3f2edadeede6116d7f7ca', '1c1088e539d1007012ef7d0b1c3e9e4a447234b7e582b07cf40c5302792df07f', '5afd467f7936579c7aa3bb9023503c57ec0555977f6bf3c7b894f233ba84cc8c', '61c73774c8185c9c0316cf8c3b616b333dac554dfd9494d2801430611421498b', 'b6246538b8fa0b355f793014a29a8c7eb119f8b0dc54add0bcc460dde7b44d9c'], ['268bde7d229b5212263363431b85281298680d9a6e77081307620a32c1fb2d96', '5dd2d7112041c4830ee603f3a1f3ef6f049f81505c3e4c3a27d5925dac115629', '3551d39feb58008011d8ff338f4d2755d3ec886d2974392f893f6340ccf4dcf1', '8d35b262fc4739a91ecbf009e48d4185231fb5767ca30b5db4c016468dad2e0a', '572194f2a1907fa9be36373fab881815904f539acaddad3e15722ca28588c276', 'e32225ed5fbc1f9bf84694c02cb0ca789571fcee9d5aa9f6b43841f95687d3b3'], ['bbe0c64c71b7625d8d72baf69d258e10ca85d8c46dcbab197306a23aff68694f', 'deaad7d3a392bb832e3e9fcf2cfd675177f92ef488d9eaa216ce388fd63cfec1', 'fd708aa0731957ec77f1ed824bab061f1f59e8b72a13dd5a29085012d6a29348', 'ec70457271adc99c2d722a22e022ea0dace95ed0f6c16dce96da347a50723978', '3872ee8d3a5a8949755c320cc833d51897288b587c3509a81bbe4eefd7bf7dbc', '1cab632f7ce57d2a49c0047ff4c8be66f31f92bdc5374c754c3166f4597c743d'], ['9799f0026c4c5802eb85dbf6a90f1d191f5f26f6f809ff3ee7ffb007b907f25a', '51c772fc7be0b891225624d0d8f978a837cf89d0342102caf299e7f013441c47', '617eecd1505abb9e42716d6bc5dbacd0ba6bcfe073a714f0403af84df7a58458', '9da8cb549cf5ce6015998fd2d3946997ee3ac8c0f410306c29eeac487d95aead', '315a7063a8822e0324c52cd306faffa1d04c3e45c2101ba7e3303466bb88a3a0', '0c6da996ec38e66fda42fac05bb2c0b67040ef93402fafb16b65928ff67452fe'], ['f9bde83841d1dfdcf9b98fee5f3703c46887f859687939058c8678af0a2df50b', '22bce77345bbc58608439ab13895838a8beb6666d5542eeaeb6438a28fecc454', 'b28c11c4e3604b77222ced8b0d164f100918e6c7833ad615ad6654898107bee2', '62b70fdec466434fcfa0701158eac03101a60b1c264b10fc5430042b12991658', 'e7e89c5cc39537946390c8c4cbc01c7f8db13d099dde104691624d5541a00662', 'd61a883ba67f06d57580a70f256158c6a179a18bf0c58ebf5e2af27f85e202aa'], ['1e0300bb4a96a0eaec14f06e0323c59459b31640d6a6d17eff6419565df08cb9', '85fc22b7837f6f8004ea7da4578c32dd4d3de19bc71b13500191b19fbed13b1a', '350a599f886cc796ce02519af12bd4759dfc73b72575f196af7228495a1243ed', 'c16a2d0cb4057b9a4be76d5b0127458e4da863288e2f4371b1c80093d58080e7', '61e9e38891abcaaa9fe02b6e267344e93b03f99ad408acac5fee62b89b15eac4', '1246633d710ab02a0b57a0a6fdae4e001f5d62e328f26e77f076e3e5678fc9f9'], ['aefd05cb0c2cce13b7b9d2015677d674537270e1e9acbea97a06c3b634e780a7', 'aa0fd074172998e591b2a2fd9a5943e7ee8e355abba6f6dbb8448880ec6c0991', '6334c8c8c56b99f50761ab035f89a2ef0fa47392e3abae001a5ff7bf61d83063', '132e62238dbab309b58f8936e5d7f3226e4e3e434d66548198e0a65c651972ca', 'f2c0f88dbdc9c451383d6048992c7b73f4a678b88349548bf59cfd606c82986a', '616559423bf8cc12beaf00a9948372c1bde5e80f6ada6d3037ea64fb25a28b9d'], ['f0320825d2dcb6f61feba979ac628c9f72a61e6b3b70c4cdd2699fb2fde2964f', '6cccd973af6e72d7ecc19953eae34c1a6e930ceac6be933ea8d2be367d0a1084', 'ba2aa96d271e5f0c434e3ea52576b5a7c93982b1379834d243b096eb75883ae0', 'aaf9f3cb6ee57f8c6d879cd5816ab2ac5ecd4ea20cdb910dd330edd08a930456', 'edc7faec626d2a51ebc98669236fadefad14a3c4f3d0c0ce0cc83d0f3cece7f5', '6da0db52678ded767a64c7fff0455712adf3cfd3954b728f1a9dbffdec64ecfc'], ['30091b768d0b13afbd8f4dafd7df3bd59895b39dd14c0bd042351e00a36db2f5', 'b674d5448486182b5891d1a3c0bcfa028dcb6c5bcd7be2f7aadf8dac6fb2199c', '0aac033b814db7670463627d649868f8f713aebb341280be9e356fc841949543', 'f043995efb1f97a6959ebaa470d4f99c7e84f4a68553334a9ee7a19a9f08fbf7', '205eb6f1ff0a2aff9145b7351ab9826f2b0cbee739223bb42ea4201e917883d5', '834596f93fedb7785c7b18a696b42ae03bd1a6545bc6df403b6303e30d356692'], ['c476b51ca39584584eef4e325eac712e7190d58835e3f4a916875134ef7306f8', '042607d0642fcbf40169ad3577a306b8aa592e4b6356fe0f0aef644eac79b31d', '0ba78570e5de5a2fa19f4a95fb93ab42b27b5f6f34cf1d783ed19917ee5bb938', 'dfd791a1e5f5cb98542306edbb288a6e25640f50c4af4b7018dda56b2b0a3a14', '3befa3a69c8efea243d63287aca88e347c4d6e3042daffe244e66c9f61f28482', 'd0f50578b32279e3feac1c0e16c63bf1a3d57096bdd345cd78997dee1861bf0f'], ['5b15bfc84a78bfc2047d6fe192124f11159188e8d35dddbc0172614040b059e7', 'a130f58551e4a03118db01a405eceda83cb8e8908a4b3918149dbe2f0ec4716b', 'da7ea78ace21decda22fc30ccbeab5e45a163cdb1b459157e141d32123844211', 'd2602febcdc994c093a494a50c804739b3d6802f41c05d4475de207824109340', '40d48c425926eb428b1fc08598774607767bbe76afa174d57e778f01097e0305', 'efb106e5346a22a8338581a8de6cf01baba013c23da4778e7fb6cf66dda1c71c'], ['acbdfd7193fc39f7c4dde221d6036861e71febf28ca1b56337b1eb21b6320abd', 'd0f16e2d5adc66ab4ca0e8ea8322f21c32a237d924b5238c8fdd0772c61ee03b', 'f2992de0098b6e3d21bc35301fc15492b5a81c2f0b08fa0d6132ecb4f9d4e50c', '570b95aebd66a716048a3ad97e5c9e22f34f7f75c54f443805024905bde93c97', 'ad7386dd9b66516e40f20cd97b8a8626399345297640d24c0d2c9dc31d9378c9', 'fe80a8c989e6b6f94e862dd60604c0497a64002e4b2d858944f2fd4ed201205a'], ['6f66b693e9a90c36d784d6dde3279fb1f9b55704b8881958870052cce8d24469', '21fba081ccaa3fd47a7bc003dfc2d56071b19bdf9ab04d9e373ffe3f135203da', '7d30d1fbab561736fc1a35c635bcffd1a02709d6dfdbb5e154a562415db30fe6', '23795b893232d4f613c99c1a4bfadc173b83c37e1b1d74514344a87c7957906a', 'b240afbcd56c5cbd9c669e4f42783c445ab623e94191cdeb91a4bb76c6c79541', '9ee705ed2d9eb44261c923fe664d1e50b003ff2705df4cd98309d3d6b4f869ee'], ['a188cc4cad247be362bfe23b55184a7773e38a75b045c4b852ea07f649fe8d0a', '7de7c4654b7e91d5e1c4012cf3d2bdc331cf58511897a181c084bc2a06cfa58c', '2896dd62ea008058dbdb366fb2d58aa32af507d61959f6f16d91f215d9786e46', '992e679898fc49afd6081ef78040ad3885adaabbd95c2ed95a5b35703437d504', '7710d0fe7e607c95b8ce729e11b95ce70d67675390ffa6a303f61c87b5d6719e', 'ff4b002d75136fe6ca82d84c8f797534e998e3b4f03993465978a8b6877d44de'], ['3523a90d5ead6d29837df6f7dd62b34dad31be64b3d8a041e697132e09286ce3', 'e79bfa513b5f04afa8f61375b36876a13c989c6cbfc86aefe7f674ad5463cdbd', '4e78d344547e14b018644e4cd8676d9ed6b3a1c4f61d0e4a1b490de7b78daf15', '66f77aaa62aa1fba2b67d5e00d9cc579e79e4d370aff8ddb6db5f1e682911478', 'a0b12fbbaac53d4dff2187c014c620c2508b5ed0e7ea55f5f98fbbbad7753977', '98903139d34a937647af195a0a3dee918d59612b6d2b3f4f033531154b665e8e'], ['d7fc792a994236557d70c290e0f1d58efe5da68c932fdd14fa6e6bc38f673bc6', 'b0a92ca4169eee1737381c05cf481d52859760a33e335f97a26798b250464ddf', '7f2e6bc4489426bcdf307246cc7571f092b2ee07ccb88a723c73d05e683f1d47', 'ef28f563380d0d85d164d6005bb3cf0be70775195a8c5bcc2f613c3ced9423da', 'f0d649207177606341d048938deaf08941a9c6b8a87b6e98d0d358e91c455d40', '2fcb96634b9d558a466d8c15f7f2172decfb22967735ba9d682188be587c0008']], 'costs': {'checkpoint_attempts': 0, 'checkpoint_reserved_bytes': 0, 'abandoned_call_operation_limit': 0, 'advance_calls': 128653, 'completed_operations': 995818907}, 'stop': 65536}

def _original39_accounting(raw, m, review, claim, failed, evidence_raw, source_raw):
    """Finite byte proof only; called after genuine admission and both recoveries."""
    fixed=_original39_contract()
    a=_json(raw)
    require(set(a)=={'format','parent_experiment','parent_claim_sha256','parent_failed_sha256',
        'evidence','source_bodies','spent_counters','retained_partial_work','preserved_unknowns'},
        'derived accounting schema differs')
    require(a['format']==fixed['format']==m['parent_accounting_mode']
        and a['parent_experiment']==m['parent_experiment']==fixed['parent']
        and a['parent_claim_sha256']==fixed['claim_sha256']
        and a['parent_failed_sha256']==fixed['failed_sha256']
        and review['parent_accounting_mode']==fixed['format']
        and review['parent_accounting_sha256']==digest(raw), 'derived accounting identity/review differs')
    require(claim==_json(evidence_raw['claim']),
        'derived original claim differs')
    require(digest(evidence_raw['claim'])==fixed['claim_sha256']
        and digest(evidence_raw['failed'])==fixed['failed_sha256']
        and failed==_json(evidence_raw['failed']), 'derived original terminal differs')
    require(set(a['evidence'])==set(fixed['evidence']) and set(evidence_raw)==set(fixed['evidence'])|{'claim','failed'},
        'derived recovered evidence roster differs')
    for key,pin in fixed['evidence'].items():
        require(a['evidence'][key]['sha256']==pin['sha256'] and digest(evidence_raw[key])==pin['sha256'],
            'derived original evidence bytes differ')
        if key.startswith('output:'):
            require(failed['output_sha256'][key[7:]]==pin['sha256'],'derived original output seal differs')
    selection=_json(evidence_raw['selection']);returned=_json(evidence_raw['return_review'])
    rows={r['path']:r for r in selection['rows'] if r['type']=='regular'}
    for key in ('traceback','guard_final'):
        pin=fixed['evidence'][key]
        require(rows[pin['path']]['sha256']==pin['sha256'],'derived raw original outside recovered selection')
    require(returned['decision']=='accepted' and returned['actual_operations']==13
        and returned['regular_files']==318 and returned['returned_typed_body_checks'] is True,
        'derived full external return absent')
    for key in ('recovery','selection','capture'):
        pin=fixed['evidence'][key]
        require(returned['evidence'][pin['path']]==pin['sha256'],'derived return review join differs')
    require(set(a['source_bodies'])==set(source_raw)==set(fixed['sources']),'derived original source roster differs')
    for path,sha in fixed['sources'].items():
        require(claim['experiment']['source_files'][path]==sha
            and a['source_bodies'][path]['sha256']==sha and digest(source_raw[path])==sha,
            'derived original source differs')
    require(m.get('provenance_mode','durable-commit')=='durable-commit'
        and len(m['batches'])==16 and [[r['sha256'] for r in batch] for batch in m['batches']]==fixed['batches'],
        'derived exact sixteen durable batches required')
    require(all(type(values) is dict and set(values)==set(fixed['costs'])
        and all(type(v) is int and 0<=v<2**127 for v in values.values())
        for values in (a['spent_counters'],m['spent_counters'],a['retained_partial_work'])),
        'derived exact integer cost fields required')
    require(a['spent_counters']==m['spent_counters']==fixed['costs']
        and a['retained_partial_work']=={k:0 for k in fixed['costs']}
        and a['preserved_unknowns']==['telemetry','cache','transport','outer_disposition'],
        'derived five-counter no-tail scope differs')
    return a


def _target_identity(run,target):
    from tradingagents.research.lifecycle import ResearchRun
    from .imported_mcm_identity import Target
    require(type(run) is ResearchRun and type(target) is Target,
        'genuine continuation Run/Target required')
    owner=target.owner;execution=target.execution;bound=owner.bound
    require(bound._run is run and execution._owner is owner and execution._bound is bound,
        'continuation target Run/Owner differs')
    return (target,owner,execution,bound)


def _poll_target(run,target):
    pin=_target_identity(run,target)
    type(target).lease(target)
    require(all(a is b for a,b in zip(pin,_target_identity(run,target),strict=True)),
        'continuation target authority changed during poll')


def _reader_target(run,reader):
    if len(reader)==4:return None
    require(len(reader)==5 and type(reader[4]) is tuple and len(reader[4])==4,
        'continuation reader target pin differs')
    pin=reader[4];target=pin[0]
    require(all(a is b for a,b in zip(pin,_target_identity(run,target),strict=True)),
        'continuation reader target replaced')
    return target


def _bind_contract_template(run,target,m,expected_contract):
    """Bind only operational identities after genuine Target creation."""
    from . import compact_mcm_batched
    require(m['contract_mode']=='genuine-target-contract-template-v1' and target is not None,
        'explicit genuine target contract template required')
    pin=_target_identity(run,target)
    template=m['contract']
    fields={'source_sha256','config_sha256','dictionary_sha256','graph_hash','node_order_hash',
        'descriptor_sha256','workflow_identity','cells','batch_cells','numerical_contract_sha256'}
    require(type(template) is dict and set(template)==fields and set(expected_contract)==fields
        and template['workflow_identity'] is None and template['descriptor_sha256'] is None,
        'exact two-slot contract template required')
    role=m['runtime_policy_input']
    require(type(role) is str and role in run.admission.inputs,'registered runtime MCM policy required')
    raw=_bounded_input(run,role,max_bytes=2*1024**2,target=target)
    policy=_json(raw)
    _poll_target(run,target)
    scope=type(target).derive_scope(target)
    require(scope==target.scope and scope['graph']==target.key
        and scope['dictionary']==target.dictionary.identity, 'genuine target scope differs')
    rows=len(target.graph.node_ids);cells=rows*32
    descriptor={'rows':rows,'cells':cells,'motifs':32,'graph_hash':target.key,
        'node_order_hash':scope['node_order'],'workload_sha256':scope['workflow'],'purpose_schema_version':2}
    start={'rows':rows,'cells':cells,'graph_hash':target.key,'scope':scope}
    compact_mcm_batched.validate(policy,cells)
    current=compact_mcm_batched._continuation_contract(target,start,policy,descriptor)
    frozen={**current,'workflow_identity':None,'descriptor_sha256':None}
    require(body(frozen)==body(template) and body(current)==body(expected_contract),
        'template scientific/source/config or runtime contract differs')
    require(all(a is b for a,b in zip(pin,_target_identity(run,target),strict=True)),
        'template target authority changed')
    return descriptor


def _authority(run, m, *, target=None):
    """Admitted parent, immutable terminal evidence and two recovered inventories."""
    ad=run.admission
    if target is not None:_poll_target(run,target)
    run._active();run._check_source()
    if target is not None:_poll_target(run,target)
    require(ad.experiment['parent']==m['parent_experiment'] and ad.effective_attempt_budget>0,
            'registered continuation parent/allowance differs')
    parent=ad.root/'research_runs'/m['parent_experiment']
    require(not os.path.lexists(parent/'complete.json'), 'COMPLETE parent refused')
    def registered(ref):
        require(type(ref) is dict and set(ref)=={'role','sha256'}, 'authority registered reference required')
        raw=_bounded_input(run,ref['role'],max_bytes=MAX_MANIFEST_BYTES,**({'target':target} if target is not None else {}))
        require(len(raw)<=MAX_MANIFEST_BYTES and digest(raw)==ref['sha256'], 'authority body differs')
        return raw
    claim_raw=registered(m['parent_claim']);failed_raw=registered(m['parent_failed'])
    claim=json.loads(claim_raw);failed=json.loads(failed_raw)
    require(ad.root/ad.inputs[m['parent_claim']['role']]['path']==parent/'claim.json'
            and ad.root/ad.inputs[m['parent_failed']['role']]['path']==parent/'failed.json',
            'registered original parent terminal paths required')
    require(failed['status']=='failed' and failed['experiment_id']==m['parent_experiment']
            and failed['claim_sha256']==digest(claim_raw) and claim['experiment_id']==m['parent_experiment']
            and claim['program_id']==ad.spec['program_id'] and claim['family']['mechanism_id']==ad.family['mechanism_id'],
            'FAILED parent claim/family differs')
    review=json.loads(registered(m['review']))
    require(review['policy']==POLICY and review['decision']=='accepted'
            and review['parent_claim_sha256']==digest(claim_raw) and review['parent_failed_sha256']==digest(failed_raw)
            and review['successor_experiment']==ad.experiment_id
            and review['contract_sha256']==digest(body(m['contract']))
            and review['batches_sha256']==digest(body(m['batches']))
            and review['descriptors_sha256']==digest(body(m.get('descriptors',{})))
            and review['spent_counters_sha256']==digest(body(m['spent_counters'])), 'reviewed continuation joins differ')
    if 'contract_mode' in m:
        require(m['contract_mode']=='genuine-target-contract-template-v1'
            and review['contract_mode']==m['contract_mode']
            and review['contract_template_sha256']==digest(body(m['contract']))
            and review['runtime_policy_input']==m['runtime_policy_input'], 'reviewed contract template differs')
    recovered={}
    for kind in ('score_offload','numeric_origin'):
        receipt_raw=registered(m['recoveries'][kind])
        receipt=json.loads(receipt_raw)
        require(review['recoveries'][kind]==digest(receipt_raw) and receipt['status']=='recovered'
                and receipt['parent_experiment']==m['parent_experiment'] and receipt['scope']==kind,
                'required recovered scope differs')
        originals=receipt['original_evidence']
        require(type(originals) is list and 0<len(originals)<=16, 'bounded original external recovery evidence required')
        for original in originals:registered(original)
        require(review['original_evidence'][kind]==digest(body(originals)), 'original recovery evidence join differs')
        recovered[kind]=set(receipt['body_sha256'])
    for refs in m['batches']:
        require(all(ref['sha256'] in recovered['score_offload'] for ref in refs[:3])
                and all(ref['sha256'] in recovered['numeric_origin'] for ref in refs[3:]), 'missing required recovered scope body')
    accounting_raw=registered(m['parent_accounting'])
    if 'parent_accounting_mode' in m:
        fixed=_original39_contract()
        require(m['parent_accounting_mode']==fixed['format'], 'unknown parent accounting mode')
        a=_json(accounting_raw)
        require(type(a) is dict and type(a.get('evidence')) is dict and type(a.get('source_bodies')) is dict
            and set(a['evidence'])==set(fixed['evidence'])
            and set(a['source_bodies'])==set(fixed['sources']), 'bounded derived proof roster required')
        evidence_raw={'claim':claim_raw,'failed':failed_raw}
        for key,ref in a['evidence'].items():evidence_raw[key]=registered(ref)
        source_raw={path:registered(ref) for path,ref in a['source_bodies'].items()}
        return _original39_accounting(accounting_raw,m,review,claim,failed,evidence_raw,source_raw)
    require(digest(accounting_raw) in failed['output_sha256'].values()
            and review['parent_accounting_sha256']==digest(accounting_raw), 'actual parent spent output required')
    accounting=json.loads(accounting_raw)
    require(accounting['parent_experiment']==m['parent_experiment']
            and accounting['spent_counters']==m['spent_counters']
            and type(accounting['retained_partial_work']) is dict
            and all(type(v) is int and v>=0 for v in accounting['retained_partial_work'].values()), 'parent spent/partial accounting differs')
    return accounting


def verify_prefix(run, registered_input, *, expected_contract, target=None):
    """A parser result is not authority; only a genuine admitted run returns it."""
    from tradingagents.research.lifecycle import ResearchRun
    require(type(run) is ResearchRun, 'genuine continuation admission required')
    target_pin=None if target is None else _target_identity(run,target)
    manifest_raw=_bounded_input(run,registered_input,max_bytes=MAX_MANIFEST_BYTES,**({'target':target} if target is not None else {}))
    require(len(manifest_raw)<=MAX_MANIFEST_BYTES, 'prefix manifest extent exceeded')
    m=_json(manifest_raw)
    runtime_descriptor=None
    if 'contract_mode' in m:
        runtime_descriptor=_bind_contract_template(run,target,m,expected_contract)
        require(m['policy']==POLICY and m.get('provenance_mode','durable-commit') in ('durable-commit','legacy-recovered-prefix-v1'), 'prefix exact contract differs')
    else:
        require(m['policy']==POLICY and m.get('provenance_mode','durable-commit') in ('durable-commit','legacy-recovered-prefix-v1') and m['contract']==expected_contract, 'prefix exact contract differs')
    required={'source_sha256','config_sha256','dictionary_sha256','graph_hash','node_order_hash','descriptor_sha256','workflow_identity','cells','batch_cells'}
    require(required<=set(expected_contract), 'prefix numerical contract incomplete')
    require(type(expected_contract['batch_cells']) is int and 0<expected_contract['batch_cells']<=4096
            and type(expected_contract['cells']) is int and 0<expected_contract['cells']<2**63, 'prefix finite bounds required')
    require(m['successor_experiment']==run.admission.experiment_id and m['parent_experiment']!=m['successor_experiment'] and m['parent_status']=='FAILED', 'fresh successor/FAILED parent required')
    require(m['successor_experiment'] not in m['ancestor_experiments'] and m['parent_experiment'] in m['ancestor_experiments'], 'continuation identity reused')
    if runtime_descriptor is None:
        require((m['contract']['workflow_identity'],m['contract']['graph_hash']) not in _USED.get(run,set()),'continuation already consumed by successor')
    else:
        require((expected_contract['workflow_identity'],expected_contract['graph_hash']) not in _USED.get(run,set()),'continuation already consumed by successor')
    descriptors=_descriptors(m.get('descriptors',{}),expected_contract)
    if runtime_descriptor is not None:
        runtime_key=digest(body(runtime_descriptor))
        require(runtime_key==expected_contract['descriptor_sha256'],'runtime descriptor digest differs')
        require(runtime_key not in descriptors or descriptors[runtime_key]==body(runtime_descriptor),'runtime descriptor conflicts with parent')
        descriptors[runtime_key]=body(runtime_descriptor)
    accounting=_authority(run,m,**({'target':target} if target is not None else {}))
    batches=[];start=0;last_costs={};origin_cache=None;origin_reads=0;last_summary=None;last_epoch=None;oh=hashlib.sha256();sh=hashlib.sha256()
    require(type(m['batches']) is list and 0<len(m['batches'])<=65536, 'bounded nonempty prefix required')
    for index,refs in enumerate(m['batches']):
        require(type(refs) is list and len(refs)==6, 'prefix registered body roster differs')
        refs=_references(refs)
        batch=_registered_batch(run,refs,index,expected_contract,m.get('provenance_mode')=='legacy-recovered-prefix-v1',descriptors,**({'target':target} if target is not None else {}))
        commit_value=_json(batch.commit);summary_value=_json(batch.summary)
        epoch=commit_value['cost_epoch_start']
        require((index==0 and epoch==0) or epoch==last_epoch or epoch==start, 'prefix memo reset boundary differs')
        if last_summary is not None and epoch==last_epoch:
            require(set(summary_value['counters'])==set(last_summary)
                    and all(v>=last_summary[k] for k,v in summary_value['counters'].items() if k!='accounted_cache_bytes'),
                    'prefix cumulative numeric counters decreased')
        last_summary=summary_value['counters'];last_epoch=epoch
        costs=_costs(batch.commit)
        require(all(costs[k]>=last_costs.get(k,0) for k in costs), 'prefix spent counters decreased')
        last_costs=costs
        for record,(mode,origin) in zip(batch.records,numeric_format.RECORD.iter_unpack(batch.origins),strict=True):
            if mode:
                origin_batch,offset=divmod(origin,expected_contract['batch_cells'])
                if origin_batch==index:source=batch
                else:
                    if origin_cache is None or origin_cache[0]!=origin_batch:
                        origin_reads+=1
                        origin_cache=(origin_batch,_registered_batch(run,batches[origin_batch],origin_batch,expected_contract,m.get('provenance_mode')=='legacy-recovered-prefix-v1',descriptors,**({'target':target} if target is not None else {})))
                    source=origin_cache[1]
                require(record[2:]==source.records[offset][2:]
                        and numeric_format.RECORD.unpack_from(source.origins,offset*9)==(0,origin),
                        'reused origin score/status differs')
        batches.append(refs);start+=len(batch.records);oh.update(batch.origins);sh.update(batch.score_bodies[1])
    require(start==m['next_ordinal'] and start<=expected_contract['cells'] and (start==expected_contract['cells'] or start%expected_contract['batch_cells']==0), 'partial/finished prefix refused')
    require(type(m['spent_counters']) is dict and all(type(k) is str and type(v) is int and 0<=v<2**127 for k,v in m['spent_counters'].items()), 'spent accounting required')
    _check_spent(m['spent_counters'],accounting['retained_partial_work'],last_costs)
    require(_bounded_input(run,registered_input,max_bytes=MAX_MANIFEST_BYTES,**({'target':target} if target is not None else {}))==manifest_raw, 'prefix changed during verification')
    _authority(run,m,**({'target':target} if target is not None else {}))
    if runtime_descriptor is not None:
        require(_bind_contract_template(run,target,m,expected_contract)==runtime_descriptor,'runtime template binding changed during verification')
    expected=(m['parent_experiment'],m['successor_experiment'],expected_contract['workflow_identity'],expected_contract['graph_hash'],start,tuple(batches),oh.hexdigest(),sh.hexdigest(),expected_contract.get('numerical_contract_sha256',digest(body(expected_contract))),tuple(sorted(m['spent_counters'].items())),digest(manifest_raw),tuple(sorted(descriptors.items())),(('verified_batches',len(batches)),('prior_origin_batch_reads',origin_reads),('max_decoded_batches_retained',2)))
    result=CompletedPrefix(*expected)
    require(type(result) is CompletedPrefix and tuple(getattr(result,f.name) for f in fields(result))==expected, 'prefix constructor changed authenticated fields')
    _VERIFIED[result]=expected
    _READERS[result]=(run,body(expected_contract),m.get('provenance_mode')=='legacy-recovered-prefix-v1',registered_input)
    if target is not None:
        require(all(a is b for a,b in zip(target_pin,_target_identity(run,target),strict=True)), 'continuation target changed during verification')
        _READERS[result]=(*_READERS[result],target_pin)
    return result


def restore_prefix(prefix, journal, numeric, consumer):
    """Copy only authenticated complete batches into a fresh successor namespace."""
    require(type(prefix) is CompletedPrefix and _VERIFIED.pop(prefix,None)==tuple(getattr(prefix,f.name) for f in fields(prefix)), 'verified unused prefix required')
    require(journal.cells==journal.batch==numeric.ordinal==numeric.batch==0, 'fresh prefix destination required')
    require(not journal.closed and not journal.poisoned and callable(consumer), 'prefix destination unavailable')
    try:
        reader=_READERS.get(prefix)
        if reader is not None:
            run,_,_,role=reader[:4]
            target=_reader_target(run,reader)
            key=(prefix.workflow_identity,prefix.graph_hash)
            used=_USED.setdefault(run,set())
            require(key not in used,'continuation already consumed by successor')
            used.add(key)
            manifest=_bounded_input(run,role,max_bytes=MAX_MANIFEST_BYTES,**({'target':target} if target is not None else {}))
            require(digest(manifest)==prefix.manifest_sha256,'prefix admission changed before restoration')
            _authority(run,_json(manifest),**({'target':target} if target is not None else {}))
            if 'contract_mode' in _json(manifest):
                runtime_descriptor=_bind_contract_template(run,target,_json(manifest),_json(reader[1]))
                require(dict(prefix.descriptors).get(digest(body(runtime_descriptor)))==body(runtime_descriptor)
                    and runtime_descriptor['workload_sha256']==prefix.workflow_identity,'restored runtime template binding differs')
        for index in range(len(prefix.batches)):
            batch=_load_batch(prefix,index)
            for suffix,raw in zip(SUFFIXES,batch.score_bodies,strict=True):
                journal._write(f'{index:08d}'+suffix,raw,max(journal.max_body,HEADER.size+journal.batch_cells*RECORD.size))
            require(tuple(journal.read_complete(index))==batch.records, 'restored score differs')
            numeric.import_completed_batch(batch.origins,batch.summary)
            suffix='.legacy-prefix-counter.json' if batch.legacy else '.prefix.json'
            journal._write(f'{index:08d}'+suffix,batch.commit,journal.max_body)
            journal.cells+=len(batch.records);journal.batch+=1
            for row in batch.records:
                ordinal=row[0];center,motif=divmod(ordinal,32)
                consumer(ordinal,center,motif,struct.pack('<f',row[2]))
        require(journal.cells==numeric.ordinal==prefix.next_ordinal, 'restored prefix cursor differs')
        numeric.imported_costs={k:dict(prefix.spent_counters).get(k,v) for k,v in _costs(batch.commit).items()}
        numeric.memo.restore_ordinal(prefix.next_ordinal)
        numeric.continuation={'policy':POLICY,'manifest_sha256':prefix.manifest_sha256,'parent_experiment':prefix.parent_experiment,'imported_cells':prefix.next_ordinal,'imported_computed':numeric.computed,'imported_reused':numeric.reused,'spent_counters':dict(prefix.spent_counters),'memo_reset_count':1}
    except BaseException:
        journal.poisoned=True;numeric._poison();raise


def _costs(commit):
    value=_json(commit)
    return dict(checkpoint_attempts=value['checkpoint_attempts'],checkpoint_reserved_bytes=value['checkpoint_reserved_bytes'],**value['operation_counters'])


def verify_purposes(prefix,tasks):
    """Compare authentic reconstructed graph/motif purposes before sink import."""
    require(type(prefix) is CompletedPrefix and prefix in _VERIFIED,'verified prefix required')
    # The driver supplies a factory for authentic parent operational descriptors.
    # A plain iterator remains the bounded parser-fixture interface.
    for index in range(len(prefix.batches)):
        batch=_load_batch(prefix,index)
        owned=callable(tasks)
        iterator=tasks(batch,_descriptor_for(prefix,batch)) if owned else tasks
        try:
            for record in batch.records:
                purpose,a,b=next(iterator)
                require(purpose['ordinal']==record[0] and hashlib.sha256(body(purpose)).digest()==record[1],
                        'restored graph/motif purpose differs')
                del a,b,purpose
        finally:
            if owned:iterator.close()


def _references(refs):
    require(type(refs) is list and len(refs)==6,'six registered references required')
    result=[]
    for ref in refs:
        require(type(ref) is dict and set(ref)=={'role','sha256'}
                and type(ref['role']) is str and 0<len(ref['role'])<=128
                and ref['role'].isascii() and all(x.isalnum() or x in '_-.' for x in ref['role'])
                and type(ref['sha256']) is str and len(ref['sha256'])==64
                and all(c in '0123456789abcdef' for c in ref['sha256']), 'prefix recovered reference differs')
        result.append((ref['role'],ref['sha256']))
    require(len({role for role,_ in result})==6,'distinct registered prefix roles required')
    return tuple(result)


def _polled_batch_inputs(run,names,target):
    from tradingagents.research.lifecycle import _lock
    from .original_dictionary import _read_registered
    _poll_target(run,target)
    values=run.read_inputs(names,max_each_bytes=1024**2,max_total_bytes=4*1024**2)
    pins=tuple((name,run.admission.inputs[name]['path'],run.admission.inputs[name]['sha256']) for name in names)
    _poll_target(run,target)
    # Read-only post-callback rejoin; no Target callback under this lock.
    with _lock(run.admission.root):
        run._active()
        require(pins==tuple((name,run.admission.inputs[name]['path'],run.admission.inputs[name]['sha256']) for name in names),
            'continuation batch contract changed after target poll')
        for name in names:
            require(_read_registered(run,name,max_bytes=1024**2)==values[name],
                'continuation batch body changed after target poll')
        run._active()
    return values


def _registered_batch(run,refs,index,contract,legacy,descriptors=None,*,target=None):
    names=tuple(role for role,_ in refs)
    if target is None:values=run.read_inputs(names,max_each_bytes=1024**2,max_total_bytes=4*1024**2)
    else:values=_polled_batch_inputs(run,names,target)
    blobs=tuple(values[role] for role,_ in refs)
    require(all(digest(raw)==sha for raw,(_,sha) in zip(blobs,refs,strict=True)), 'recovered prefix body changed')
    if descriptors:
        pending=_json(blobs[0]);key=pending['workload_sha256']
        require(key in descriptors,'unreviewed parent descriptor')
        contract={**contract,'descriptor_sha256':key}
    return _decode_batch(blobs,index,index*contract['batch_cells'],contract['batch_cells'],contract['cells'],contract,legacy=legacy)


def _load_batch(prefix,index):
    reader=_READERS.get(prefix)
    if reader is None:
        # Only internal parser tests install such a grant. verify_prefix always
        # retains immutable role/hash references and a genuine ResearchRun.
        batch=prefix.batches[index]
        require(type(batch) is CompletedBatch,'registered prefix reader missing')
        return batch
    run,contract,legacy,_=reader[:4]
    target=_reader_target(run,reader)
    return _registered_batch(run,prefix.batches[index],index,_json(contract),legacy,dict(prefix.descriptors),**({'target':target} if target is not None else {}))


def _bounded_input(run,name,*,max_bytes,target=None):
    """Source-checked registered metadata transaction, capped before allocation.

    This explicit continuation route permits a 32MiB manifest/inventory; the
    shared general-purpose 2MiB/4MiB role reader remains unchanged.
    """
    from tradingagents.research.lifecycle import _lock
    if target is not None:
        _poll_target(run,target)
        value=_bounded_input(run,name,max_bytes=max_bytes)
        pin=(run.admission.inputs[name]['path'],run.admission.inputs[name]['sha256'])
        _poll_target(run,target)
        # No callback while the non-reentrant lifecycle lock is held.
        with _lock(run.admission.root):
            run._active()
            require(pin==(run.admission.inputs[name]['path'],run.admission.inputs[name]['sha256']),
                'continuation contract changed after target poll')
            require(_registered_body(run,name,max_bytes)==value,
                'continuation body changed after target poll')
            run._active()
        return value
    require(type(max_bytes) is int and 0<max_bytes<=MAX_MANIFEST_BYTES,'continuation metadata bound differs')
    with _lock(run.admission.root):
        run._active();run._check_source()
        require(type(name) is str and name in run.admission.inputs,'unregistered continuation input')
        info=run.admission.inputs[name];pin=(info['path'],info['sha256'])
        value=_registered_body(run,name,max_bytes)
        run._active();run._check_source()
        require(pin==(run.admission.inputs[name]['path'],run.admission.inputs[name]['sha256']), 'continuation input contract changed')
        require(_registered_body(run,name,max_bytes)==value,'continuation input changed during admission')
        run._active()
        return value


def _registered_body(run,name,limit):
    import stat
    from . import score_batches as io
    from .original_dictionary import _close_owned
    root=run.admission.root.resolve();info=run.admission.inputs[name];path=root/info['path']
    require(path.is_relative_to(root) and path.resolve()==path,'continuation input path redirected')
    parent,fd=io._open(path.parent);child=None
    try:
        io._root(parent,fd)
        child=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=fd)
        before=os.fstat(child)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==root.stat().st_dev
                and 0<=before.st_size<=limit,'continuation metadata type/size/device differs')
        parts=[];size=0
        while True:
            block=os.read(child,min(65536,limit+1-size))
            if not block:break
            size+=len(block);require(size<=limit,'continuation metadata capacity exceeded');parts.append(block)
        value=b''.join(parts)
        require(len(value)==before.st_size and io._signature(before)==io._signature(os.fstat(child))
                ==io._signature(os.stat(path.name,dir_fd=fd,follow_symlinks=False)),'continuation input changed during read')
        io._root(parent,fd)
        require(path.resolve()==path and digest(value)==info['sha256'],'continuation registered body differs')
        return value
    finally:_close_owned((() if child is None else (child,))+(fd,),io)


def _descriptors(values,contract):
    require(type(values) is dict and len(values)<=1024,'bounded parent descriptor epochs required')
    result={}
    for key,value in values.items():
        require(type(value) is dict and set(value)=={'rows','cells','motifs','graph_hash','node_order_hash','workload_sha256','purpose_schema_version'}, 'parent descriptor schema differs')
        require(all(type(value[k]) is int and value[k]>0 for k in ('rows','cells','motifs','purpose_schema_version'))
                and all(type(value[k]) is str and len(value[k])==64 and all(c in '0123456789abcdef' for c in value[k])
                        for k in ('graph_hash','node_order_hash','workload_sha256')), 'parent descriptor types differ')
        encoded=body(value)
        require(digest(encoded)==key and value['graph_hash']==contract['graph_hash']
                and value['node_order_hash']==contract['node_order_hash'] and value['cells']==contract['cells']
                and value['rows']*32==value['cells'] and value['motifs']==32 and value['purpose_schema_version']==2,
                'parent descriptor scientific population differs')
        result[key]=encoded
    if values:require('numerical_contract_sha256' in contract,'stable scientific continuation contract required')
    return result


def _descriptor_for(prefix,batch):
    if not prefix.descriptors:return None
    key=_json(batch.score_bodies[0])['workload_sha256']
    values=dict(prefix.descriptors)
    require(key in values,'parent descriptor unavailable')
    return _json(values[key])


def _check_spent(spent,partial,completed):
    require(all(spent.get(k,-1)>=v+partial.get(k,0) for k,v in completed.items()),
            'parent spent counters refund completed or partial work')
