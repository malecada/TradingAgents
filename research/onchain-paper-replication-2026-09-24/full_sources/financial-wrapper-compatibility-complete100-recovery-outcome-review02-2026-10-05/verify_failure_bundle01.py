"""Bounded inline failure-bundle verification; reusable on actual externally recovered bytes."""
from pathlib import Path
import sys,json,base64,stat
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05';sys.path.insert(0,str(OLD));from verify_capture01 import Reader,R,F,C
D=F/'financial-wrapper-compatibility-complete100-failed-remote-capture01-2026-10-05'
def inline(b):return {'bytes':len(b),'sha256':R.digest(b),'base64':base64.b64encode(b).decode('ascii')}
def decode(v):
 R.require(set(v)=={'bytes','sha256','base64'} and type(v['bytes'])is int and 0<=v['bytes']<=R.FILE and type(v['base64'])is str and len(v['base64'])<=4*((R.FILE+2)//3),'bounded exact inline body')
 b=base64.b64decode(v['base64'],validate=True);R.require(len(b)==v['bytes'] and R.digest(b)==v['sha256'],'literal inline body pin');return b
def verify_inline(raw):
 """No restoration. Returns all original failure body bytes for real origin/recovery joins."""
 R.require(len(raw)<=R.FILE,'finite selected composite');q=json.loads(raw);original=decode(q['original_capture_review']);R.require(R.digest(original)=='5db589619e8df5cec1755ebc3a36bffa2d3a8cd3e4c66e41e8d68bc9befc7b18','literal genuine original capture proof');c=q['failed_metadata_capture'];capture=json.loads(decode(c['capture_provenance']));mr=decode(c['manifest']);m=json.loads(mr);R.validate(m);ar=decode(c['archive'])
 R.require(m==capture['payload_manifest'] and mr==R.encode(m) and R.digest(mr)==capture['archive']['manifest_sha256'] and len(ar)==capture['archive']['bytes'] and R.digest(ar)==capture['archive']['sha256']=='45a14ae4af25aa836b357a98232957318142708fc309e7c51519e1d9b21fc50c','exact actual failure archive/provenance joins')
 expected={r['path']:r for r in m['members']};R.require(len(expected)==len(m['members'])==119 and sum(r['kind']=='file' for r in expected.values())==110,'complete typed failure denominator');seen=set();files={};it=R.framed_members(ar);primary=None
 try:
  for n,t,b in it:
   R.require(n in expected and n not in seen,'exact inline archive membership');r=expected[n];seen.add(n);R.require(t.mode==r['mode'] and t.uid==t.gid==0 and t.uname==t.gname=='' and t.mtime==0,'original mode/canonical archive metadata')
   if r['kind']=='directory':R.require(t.isdir() and t.size==0 and b==b'','ordinary typed directory')
   else:R.require(t.isfile() and t.size==len(b)==r['bytes'] and R.digest(b)==r['sha256'],'full opaque archive body');files[n]=b
 except BaseException as e:primary=e
 R._cleanup((it.close,),primary=primary)
 if primary is not None:raise primary
 R.require(seen==set(expected),'complete archive member set');decode(q['independent_failed_readback']);decode(q['independent_report']);R.require(q['external_recovery_accepted'] is False and q['numerical_authority'] is False and q['requires_complete_inline_failure_byte_verification_after_external_recovery'] is True,'no premature external authority');return q,files
def main():
 rd=Reader();cr=rd.read(D/'CAPTURE01.json');capture=json.loads(cr);mr=rd.read(D/'FAILED_ATTEMPTS_MANIFEST01.json','417a0516b8f03896f13a53a10d94e09e382a789b4c5a51ef9f4dc1a250d23c9d');m=json.loads(mr);ar=rd.read(D/'FAILED_ATTEMPTS01.tar.gz','45a14ae4af25aa836b357a98232957318142708fc309e7c51519e1d9b21fc50c');rd.need(len(ar)==132204 and mr==R.encode(m) and capture['payload_manifest']==m,'actual canonical capture bytes')
 priorraw=rd.read(HERE/'FAILED_READBACK01.json');prior=json.loads(priorraw);originals={};expected_rows=[]
 rd.need(len(capture['scopes'])==4 and capture['external_recovery'] is False and capture['genuine_claim_or_numerical_job_started'] is False,'complete four failed scopes')
 for i,scope in enumerate(capture['scopes']):
  before=prior['lanes'][i];root=Path(scope['root']);prefix='lane%02d'%(i+1);rd.need(scope['role']=='failed_remote_'+prefix and scope['payload_prefix']==prefix and str(root)==before['root'] and scope['manifest']==before['manifest'],'original complete failed-root inventory')
  rd.tree(root,scope['manifest']);expected_rows.append({'kind':'directory','path':prefix,'mode':scope['manifest']['root_mode']})
  for row in scope['manifest']['members']:
   expected_rows.append(dict(row,path=prefix+'/'+row['path']))
   if row['kind']=='file':originals[prefix+'/'+row['path']]=root/row['path']
 logs=['FOUR_LANE_REMOTE_ACTUAL_ROOT_EXITS01.json','FOUR_LANE_REMOTE_ENTRY_INTENT01.json']+['LANE%02d_REMOTE_ROOT01.%s'%(i,suffix) for i in range(1,5) for suffix in ('stdout','stderr')]
 expected_rows.append({'path':'root_actual_outputs','kind':'directory','mode':448})
 for n in logs:
  p=C/n;b=rd.read(p);expected_rows.append({'path':'root_actual_outputs/'+n,'kind':'file','mode':stat.S_IMODE(p.lstat().st_mode),'bytes':len(b),'sha256':R.digest(b)});originals['root_actual_outputs/'+n]=p
 rd.need(m['members']==sorted(expected_rows,key=lambda r:r['path']) and len(originals)==110 and len(m['members'])==119,'exact complete four roots plus all10 actual Root artifacts')
 actual=rd.read(C/'FOUR_LANE_REMOTE_ACTUAL_ROOT_EXITS01.json',capture['actual_root_receipt']['sha256']);exits=json.loads(actual);rd.need([(x['lane'],x['actual_root_exit'],x['tool_chunk']) for x in exits['attempts']]==[(1,1,'66456b'),(2,1,'e33df5'),(3,1,'9ee1ee'),(4,1,'38e745')] and all(x['inner_parent_exit_stays_null'] is True and x['genuine_numerical_claim_started'] is False for x in exits['attempts']),'actual separate four tool exits retained')
 report='''All four original receiver attempts permanently FAILED before any Git operation or receiver store creation. The exact receiver encode predicate refuses compact selection bytes; the earlier review omitted this byte-equality check. The old review, source, selections, releases, failures and null inner Parent exits remain unchanged. Actual Root tool exits are separately1; recorded8caller/childPIDs and4childgroups were observed absent. No universal PID history is asserted.\n\nThe complete failure bundle contains all110regular bodies and119typed members: four complete failed Root namespaces plus8actual Root output streams, the original Root intent and separate four-tool exit receipt. Every archive body, retained payload copy and original file was independently compared, with original mode/type/membership retained. Strict PAX framing and literal canonical gzip recompression passed. Original modes remain archival metadata; no POSIX reconstruction or writer exclusion is claimed.\n\nThe original genuine capture review5db589 is embedded literally, preserving its acceptance of26pieces/845regular/1074typed original CAP/Parent members and accepted separate407Git basis. The successful complete100 outcome remains unchanged. The composite adds the complete failed metadata scope, with no financial trial, refund, native release or new scientific claim. All inline failure bytes must be independently verified after actual external transfer/recovery before dependent continuation. This local composite is not an external-recovery proof.\n'''
 reportbytes=report.encode();original=rd.read(OLD/'ACTUAL_CAPTURE_REVIEW01.json','5db589619e8df5cec1755ebc3a36bffa2d3a8cd3e4c66e41e8d68bc9befc7b18')
 q={'schema_version':1,'decision':'ACCEPTED_ORIGINAL_LOCAL_CAPTURE_AND_COMPLETE_FOUR_FAILED_METADATA_CAPTURES_ONLY','reviewer':'independent storage_watch_review','original_capture_review':inline(original),'failed_metadata_capture':{'capture_provenance':inline(cr),'manifest':inline(mr),'archive':inline(ar),'regular_bodies':110,'typed_members':119,'archive_format':'canonical-gzip-PAX','original_modes_preserved_as_metadata':True},'independent_failed_readback':inline(priorraw),'independent_report':inline(reportbytes),'complete100_disposition_unchanged':True,'new_financial_claims':0,'external_recovery_accepted':False,'requires_complete_inline_failure_byte_verification_after_external_recovery':True,'POSIX_instantiation':False,'universal_process_history':None,'numerical_authority':False}
 raw=R.encode(q);parsed,files=verify_inline(raw);rd.tree(D/'payload',m)
 for n,b in files.items():rd.need(rd.read(D/'payload'/n,R.digest(b))==b==rd.read(originals[n],R.digest(b)),'all actual failure original/payload/archive bytes equal')
 sink=R.Sink();R.tar_stream(D/'payload',m,sink);rd.need(sink.count==len(ar) and sink.hash.hexdigest()==R.digest(ar),'literal canonical failure archive recompression');rd.finish()
 (HERE/'FAILED_CAPTURE_REPORT01.md').write_bytes(reportbytes);R.put(HERE/'ACTUAL_CAPTURE_REVIEW02.json',q)
 result={'schema_version':1,'decision':'ACCEPTED_COMPLETE_LOCAL_FAILURE_BUNDLE_AND_LITERAL_COMPOSITE_ONLY','composite_sha256':R.digest(raw),'composite_bytes':len(raw),'archive_sha256':R.digest(ar),'archive_bytes':len(ar),'manifest_sha256':R.digest(mr),'capture_provenance_sha256':R.digest(cr),'actual_Root_exit_receipt_sha256':R.digest(actual),'files':110,'typed_members':119,'originals_raw_bytes':sum(len(b) for b in files.values()),'all_actual_originals_and_payload_equal':True,'literal_PAX_recompression':True,'checks':rd.checks,'read_bytes':rd.total,'external_recovery_accepted':False,'numerical_authority':False}
 (HERE/'FAILED_BUNDLE_READBACK01.json').write_bytes(R.encode(result));print(json.dumps(result))
if __name__=='__main__':main()
