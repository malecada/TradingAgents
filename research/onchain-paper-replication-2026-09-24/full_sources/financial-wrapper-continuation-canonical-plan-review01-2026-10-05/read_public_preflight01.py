"""Read actual Root public preflight once; never invoke Parent/preclaim/lifecycle."""
from pathlib import Path
import os,sys,json
H=Path(__file__).resolve().parent;F=H.parent;C=F/'heartbeat-root-checkpoint10-2026-10-04'
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01')
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();refs={};contents={}
for n in ('CANONICAL_CONTINUATION_PUBLIC_PREFLIGHT01_RECEIPT.json','CANONICAL_CONTINUATION_PUBLIC_PREFLIGHT01.stdout','CANONICAL_CONTINUATION_PUBLIC_PREFLIGHT01.stderr'):
 raw=rd.read(C/n,'3169426abb32851a2f16fc263c34f69078e031f5c5d1b3452953e77107ced50b' if n.endswith('RECEIPT.json') else None);contents[n]=raw;refs[n]={'path':str(C/n),'sha256':R.digest(raw)}
 with R.new_file(H/('ACTUAL_'+n)) as fd:
  offset=0
  while offset<len(raw):
   nbytes=os.write(fd,raw[offset:]);rd.need(nbytes>0,'complete literal evidence write');offset+=nbytes
  os.fsync(fd)
a=json.loads(contents['CANONICAL_CONTINUATION_PUBLIC_PREFLIGHT01_RECEIPT.json']);out=contents['CANONICAL_CONTINUATION_PUBLIC_PREFLIGHT01.stdout'];err=contents['CANONICAL_CONTINUATION_PUBLIC_PREFLIGHT01.stderr'];v=json.loads(out)
rd.need(a['actual_tool_exit_code']==0 and a['tool_session']==59493 and a['final_chunk']=='4ac336' and not a['claim_started'] and not a['checkpoint_decoded'],'actual Root recorded public metadata exit0/no claim')
rd.need(err==b'' and R.digest(err)==a['stderr_sha256'] and R.digest(out)==a['stdout_sha256'],'actual raw stdout/stderr receipt joins')
qr=rd.read(P/'REQUEST_FINAL01.json','a9a04d60abced0ae01f192a7fc3897bf3972891d374a98f33f15522b8dc20e18');q=json.loads(qr)
draft=json.loads(rd.read(P/'REQUEST_FINAL_REVIEW_DRAFT01.json','410f544ceca7083937faf49449d291a569dc2246d012f1827bd54989a8517768'))
release={'path':str(H/'FINAL_PARENT_RELEASE01.json'),'sha256':'6cbd5316929afe7eceee03dfa894eafd2c0ddadd3f48ea68407428c67c8f9d50'}
rd.need(q==dict(draft,final_review=release) and R.digest(qr)==a['final_request_sha256'],'canonical final request adds only exact genuine release')
rd.read(Path(release['path']),release['sha256']);rd.read(P/'parent01.py',q['caller_sha256']);rd.read(P/'preclaim01.py',q['helper_hashes']['preclaim01.py'])
rd.need(v['status']=='PRECLAIM_METADATA_VALIDATED_NO_CLAIM' and v['source']==a['source']==q['source'] and v['experiment']==q['identity'] and v['phase']==q['expected_phase']=='continue100' and v['input_hashes']==q['input_hashes'] and len(v['input_hashes'])==29 and not v['checkpoint_decoded'],'actual exact source/29-role/phase output')
rd.need(v['metadata_bytes_read']==a['metadata_bytes_read']==7997640 and v['metadata_bytes_read']<8*1024**2,'actual complete metadata total under frozen8MiB')
rd.need(v['policy_sha256']==q['input_hashes']['operational_source_compatibility']=='ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887','unchanged actual policy')
cap=Path(q['capsule_root']);paths=[P/'attempt',cap/'research_runs'/q['identity'],cap/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/q['identity']]
rd.need(all(not os.path.lexists(p) for p in paths),'actual fresh numerical namespaces absent at review')
head=rd.read(cap/'.git/HEAD').decode().strip();source=rd.read(cap/'.git'/head[5:]).decode().strip() if head.startswith('ref: ') else head;rd.need(source==q['source'],'actual CAP source unchanged')
rd.finish();result={'schema_version':1,'status':'PASSED_ACTUAL_PUBLIC_METADATA_PREFLIGHT_NO_CLAIM','public_preflight_passed':True,'actual_refs':refs,'actual_Root_exit':0,'actual_tool_session':59493,'actual_final_chunk':'4ac336','canonical_request_sha256':R.digest(qr),'final_review':release,'source':source,'identity':q['identity'],'reader_bytes':v['metadata_bytes_read'],'reader_cap_bytes':8*1024**2,'reader_remaining_bytes':8*1024**2-v['metadata_bytes_read'],'checkpoint_decoded':False,'actual_namespace_absence':[str(p) for p in paths],'preflight_rerun_by_reviewer':False,'numerical_entry_executed':False,'new_numerical_outcome':None,'fresh_Root_resource_check_still_required':True,'checks':rd.checks,'read_bytes':rd.total}
R.put(H/'PUBLIC_PREFLIGHT_READBACK01.json',result);print(json.dumps(result))
