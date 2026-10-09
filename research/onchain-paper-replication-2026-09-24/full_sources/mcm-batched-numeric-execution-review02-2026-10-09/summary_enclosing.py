from pathlib import Path
H=Path(__file__).resolve().parent
# Reuse only metadata module setup, without the preceding fixture/test execution.
setup=(H/'enclosing_exception.py').read_text().split("root=H/'enclosing-fixture'")[0]
exec(compile(setup,str(H/'enclosing_exception.py'),'exec'))
root=H/'summary-enclosing-fixture';root.mkdir();(root/'numeric-batches').mkdir();x=object.__new__(ns['NumericExecution'])
x.root=root;x.fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);x.root_pin=ns['sig'](os.fstat(x.fd))[:2];x.batches_fd=os.open(root/'numeric-batches',os.O_RDONLY|os.O_DIRECTORY);x.batches_pin=ns['sig'](os.fstat(x.batches_fd))[:2]
x.origins_fd=os.open(root/'numeric-origins.bin',os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);x.origin_sig=ns['sig'](os.fstat(x.origins_fd))
x.memo=types.SimpleNamespace(end_batch=lambda:None,counters={});x.ordinal=1;x.buffer=bytearray(ns['RECORD'].pack(0,0));x.batch=0;x.batch_computed=1;x.batch_reused=0;x.batch_elapsed=0.;x.elapsed_seconds=0.;x.receipts=hashlib.sha256();x.summary_inventory=hashlib.sha256();x.origin_hash=hashlib.sha256();x.summary_hash=hashlib.sha256();x.summary_bytes=0;x.max_summary_bytes=8192;x.max_origin_bytes=9
outer=ValueError('unrelated handled caller error');closed=[]
def close(d):os.close(d);closed.append(d);raise OSError('actual close then synthetic cleanup-only failure')
proxy=types.SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});proxy.close=close;ns['os']=proxy
try:
 try:raise outer
 except ValueError:x._complete_batch()
finally:
 for d in (x.origins_fd,x.batches_fd,x.fd):os.close(d)
assert x.batch==1 and len(closed)==2 and not x.buffer
out={'summary_credit_after_cleanup_failure':x.batch,'cleanup_errors_suppressed':len(closed),'outer_notes':outer.__notes__,'synthetic_metadata_only':True,'arrays_or_authority_objects':False}
(H/'SUMMARY_ENCLOSING_RESULT01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
