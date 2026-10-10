import resource
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
from pathlib import Path
import hashlib,json,os,struct,datetime
P=Path(__file__).resolve().parent; F=P.parent; R=P.parents[3]
E=P/'evidence02';E.mkdir(exist_ok=False)
cap=16*1024**2; total=0; inventory={};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,prefix=None):
 global total
 p=Path(p);p=p if p.is_absolute() else R/p
 with p.open('rb') as f:
  before=os.fstat(f.fileno());b=f.read(min(cap-total+1,prefix if prefix is not None else cap-total+1));after=os.fstat(f.fileno())
 total+=len(b);ck(total<=cap,'bounded read '+p.name)
 ck((before.st_dev,before.st_ino)==(after.st_dev,after.st_ino),'same inode '+p.name)
 if prefix is None:ck(before.st_size==after.st_size==len(b),'stable body '+p.name)
 else:ck(len(b)==prefix and after.st_size>=prefix,'complete prefix '+p.name)
 rel=str(p.relative_to(R));name=f'{len(inventory):03d}-'+p.name
 (E/name).write_bytes(b);inventory[rel]={'bytes':len(b),'sha256':sha(b),'copy':'evidence02/'+name,'prefix_only':prefix is not None,'before_size':before.st_size,'after_size':after.st_size}
 return b
def js(p):return json.loads(read(p))
W=R/'research_artifacts/onchain_batched_offload/c64f82cdaebfcadd2c0227b40ac26bfdf7c53705c0d8f56903f3183c0ea49cc2/mcm-0114d61904938208c75497abe82c5dae32b7d2110a4e460d1942f84dc473ba/preserve/00000000'
# Exact task path (separate from any semantic inference).
W=R/'research_artifacts/onchain_batched_offload/c64f82cdaebfcadd2c0227b40ac26bfdf7c53705c0d8f56903f3183c0ea49cc2/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba/preserve/00000000'
o=js(W/'offload.json');m=js(W/'manifest.json');h=o['history'];B=o['binding'];receipt=o['receipt'];S=Path(B['root']).parent;L=Path(h['directory']);op=h['intent_sha256']
ck(o['format']=='registered-grouped-offload-v1' and o['resume_supported'] is False,'group explicit historical nonresume format')
ck((o['first_batch'],o['batches'],o['start'],o['stop'],o['cells'],o['retired_files'])==(0,16,0,65536,65536,48),'exact first group denominator')
ck(m==o['manifest'] and sha(raw(m))==B['manifest_sha256'],'manifest embedded and external hash')
ck(m['files']==len(m['members'])==48 and m['archive_bytes']==3532800 and m['raw_bytes']==3483544,'archive declared extent')
tokens=bytes.fromhex(B['source_tokens']);ck(len(tokens)==2688,'48 token extent')
ck(read(S/'stream/closure-tokens.bin',2688)==tokens,'original stream closure prefix exact group tokens')
missing=[];sizes=[]
for i,member in enumerate(m['members']):
 dev,ino,size,digest=struct.unpack_from('>QQQ32s',tokens,56*i);sizes.append(size)
 expected=Path(B['root'])/f'{i//3:08d}{(".pending.json",".records.bin",".complete.json")[i%3]}'
 ck(member['source_path']==member['resolved_path']==str(expected) and member['member']==f'files/{i:08d}','member order/path '+str(i))
 ck(member['bytes']==size and member['expected_sha256']==digest.hex(),'member token hash/extent '+str(i))
 if not expected.exists():missing.append(str(expected.relative_to(R)))
ck(sum(sizes)==m['raw_bytes'],'member raw byte sum')
ck(((sum(512+((x+511)//512)*512 for x in sizes)+1024+10239)//10240)*10240==m['archive_bytes'],'independent tar extent arithmetic')
ck(all(sizes[i]==92+53*4096 for i in range(1,48,3)),'declared journal extents fit original framing only')
pi=js(W/'preserve/intent.json');pc=js(W/'preserve/complete.json');pd=js(W/'preserve/disposed.json');ri=js(W/'recover/intent.json');rv=js(W/'recover/verified.json');rc=js(W/'recover/complete.json');sv=js(W/'semantic/verified.json')
ck(pi==pc==receipt,'preservation actual receipt bodies')
rsha=sha(raw(receipt));ck(pd['receipt_sha256']==ri['receipt_sha256']==rsha and pd['owned_transfer_payloads_disposed'] is True,'receipt disposition joins')
ck(ri['receipt']==receipt and rv['intent_sha256']==sha(raw(ri)) and rc['verified_sha256']==sha(raw(rv)) and rc['owned_cache_disposed'] is True,'recovery hash chain and disposal')
ck(rv['payload_sha256']==receipt['source_sha256']==m['archive_sha256']==sv['archive_sha256'] and rv['bytes']==receipt['bytes']==m['archive_bytes'],'declared recovered archive identity')
ck(sv['binding']==B and (sv['start'],sv['stop'],sv['files'])==(0,65536,48),'semantic historical original roster join')
ti=js(L/h['intent']);tc=js(L/h['complete']);part=js(L/f'typed-part-{op}-000000000000.json');tr=js(L/f'typed-grouped-retirement-{op}.json');td=js(L/f'typed-grouped-retired-{op}.json');rd=js(L/f'typed-read-{op}-0000000000000000.json');ls=js(L/'start.json');si=js(S/'intent.json');owner=js(L.parent/'owner.json');start=js(L.parent/'start.json')
ck(sha(raw(ti))==op and sha(raw(tc))==h['complete_sha256'],'typed intent and completion external anchors')
ck(ti['binding']==tr['binding']==td['binding']==B and ti['owner']==si['owner']==ls['owner']==W.parents[2].name,'actual owner binding')
ck(ti['stage']==si['stage']==S.name and ti['stage_intent_sha256']==sha(raw(si)),'original stage intent anchor')
ck(type(ti['ledger_identity']) is str and len(ti['ledger_identity'])==64 and ti['kind']=='mcm-batched-bundle-v3' and ti['batched_parent']=='actual-active-mcm-stage-v1','selected typed active stage and ledger')
ck(part['operation_sha256']==tc['operation_sha256']==tr['operation_sha256']==td['operation_sha256']==op and part['receipt']==receipt and part['receipt_sha256']==tr['receipt_sha256']==td['receipt_sha256']==rd['receipt_sha256']==rsha,'typed part retirement read operation chain')
ck(part['fresh_full_recovery'] is True and part['index']==0 and tc['parts']==1 and tc['parts_sha256']==sha(bytes.fromhex(sha(raw(part)))),'typed recovered part aggregate')
ck(receipt['scope']==sha(raw({'operation':op,'index':0,'bytes':3532800,'sha256':m['archive_sha256']})),'receipt scope independently reconstructed')
ck(tc['preserved_bytes']==tc['recovered_bytes']==3532800 and td['files']==48 and tr['recovery_attempt']==str(W/'recover') and tr['semantic_root']==str(W/'semantic'),'recorded full recovery and retirement')
origin=read(S/'stream/numeric-origins.bin',65536*9);computed=reused=0
for batch in range(16):
 n=js(S/f'stream/numeric-batches/{batch:012d}.json');chunk=origin[batch*4096*9:(batch+1)*4096*9]
 ck(n['batch']==batch and n['start']==batch*4096 and n['stop']==(batch+1)*4096 and sha(chunk)==n['origin_sha256'],'numeric summary exact prefix '+str(batch))
 c=r=0
 for k,(mode,source) in enumerate(struct.iter_unpack('>BQ',chunk)):
  ordinal=batch*4096+k
  if mode==0 and source==ordinal:c+=1
  elif mode==1 and source<ordinal and origin[source*9]==0:r+=1
  else:raise AssertionError('origin metadata '+str(ordinal))
 ck((c,r)==(n['computed'],n['reused']),'origin computed/backward computed-source counts '+str(batch));computed+=c;reused+=r
ck((computed,reused)==(63904,1632),'independent group origin aggregate')
nextpending=js(S/'matching/00000016.pending.json');ck((nextpending['start'],nextpending['stop'])==(65536,69632),'subsequent pending proves serial callback returned under pinned source')
prior=js(F/'pilot29-first-batch-metadata-review01-2026-10-10/REVIEW01.json');prior_m=js(F/'pilot29-first-batch-metadata-review01-2026-10-10/MANIFEST01.json')
for i in range(3):
 e=prior['evidence'][str(Path(m['members'][i]['source_path']).relative_to(R))]
 ck(e['sha256']==m['members'][i]['expected_sha256'],'accepted first batch member hash reuse '+str(i))
gate=js(F/'real-data-pilot-full29-entry01-2026-10-09/gate04.json');pins=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261009-29']['source_files']
for name in ('grouped_offload.py','grouped_offload_semantics.py','typed_payload_operations.py','typed_payload_policy.py','batched_journal.py','batched_driver.py','batched_numeric_execution.py','compact_mcm_batched.py','archive_consume.py','archive_chunks.py','preservation.py','archive_owner_operations.py'):
 path='tradingagents/research/onchain_replication/'+name;ck(sha(read(path))==pins[path],'actual admitted source pin '+name)
absent=[str(x.relative_to(R)) for x in (W/'bundle.tar',W/'semantic/recovered.tar',W/'semantic/tree',W/'recover/payload.bin',W.parent.parent/'final/accepted-coverage.json',S/'stage-complete.json') if not x.exists()]
result={'disposition':'ACCEPT_BOUNDED_GROUP_TYPED_HISTORY_METADATA_ONLY','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'read_bytes':total,'read_cap_bytes':cap,'limits':{'cpu_seconds':30,'address_space_bytes':384*1024**2,'output_file_bytes':4*1024**2,'cpu_affinity':[3],'nice':10},'inventory':inventory,'owner':ti['owner'],'stage':ti['stage'],'offload_sha256':sha(raw(o)),'manifest_sha256':sha(raw(m)),'archive_sha256_declared_only':m['archive_sha256'],'cells':65536,'computed':computed,'reused':reused,'missing_original_members':missing,'absent_paths':absent,'next_pending':nextpending,'no_separate_durable_post_sink_marker':True,'source_order_inference':'Next batch pending is downstream of successful previous post_batch and delivered increment. No final whole-MCM completion inferred.','fixture_failure':'review01 incorrectly assumed ledger identity was the start-file hash; source archive_owner_operations.py:93 binds root/inode/record/selection/owner. Failed raw logs and first evidence set retained. Ledger identity reconstruction excluded from acceptance.', 'not_tested':['ledger complete configuration identity independently reconstructed','actual full-group archive bytes or 48 member-body hashes/framing/purpose replay; disposed bodies unavailable locally','current remote availability or fresh external recovery','provisional per-cell receipt stream hashes','numeric values, f32 conversion, graph-purpose/key equivalence, cache numerical equality','whole MCM completion, neural updates, financial outcomes, admission or runtime performance']}
(P/'REVIEW01.json').write_bytes(raw(result));print(json.dumps({'disposition':result['disposition'],'checks':len(checks),'read_bytes':total,'sha256':sha(raw(result)),'owner_record':owner,'root_start':start}))
