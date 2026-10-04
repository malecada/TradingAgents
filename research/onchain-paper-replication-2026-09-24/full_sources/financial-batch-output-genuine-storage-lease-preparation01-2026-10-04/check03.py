import ast,hashlib,json,os,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import storage_lease01 as L
rows=[]
def ok(v,n):
    if not v:raise AssertionError(n)
    rows.append(n)
def refuse(fn,n):
    try:fn()
    except BaseException as e:rows.append(n+':'+type(e).__name__);return e
    raise AssertionError(n)
root=HERE/'opaque03';root.mkdir(mode=0o700)
def make(name,cb=lambda:None):
    r=root/name;r.mkdir(mode=0o700);roles={k:k for k in L.ROLES}
    for p in roles.values():(r/p).mkdir(mode=0o700)
    return r,L.OwnedLease(r,'lease',roles,64*L.MIB,64*L.MIB,cb)
# Post callback mutations in the genuine state machinery are detected; descriptors
# below are utility metadata, not simulated Target/Owner/Run handles.
r,x=make('callback_mutation');object.__setattr__(x,'_callback',x._callback_identity)
# Change through original callback itself rather than replace its identity.
slot={}
def cb():
    if 'lease' in slot:slot['lease'].tickets['foreign']={'kind':'file','size':1,'allocated':65536,'final':None}
r,x=make('callback_original',cb);slot['lease']=x
refuse(x.check,'original callback descriptor mutation refused');ok(x.failed and x.fd is None,'callback mutation closes owned resources')
# Real fd metadata writer failure; reserved path and spent counter remain.
r,x=make('journal_fail');before=x.logical_reserved;original=L.os.write;calls=[]
def failwrite(fd,data):
    calls.append(fd);raise KeyboardInterrupt('journal interrupted')
try:
    L.os.write=failwrite
    e=refuse(lambda:x.reserve('codec',[('codec/future','file',17)]),'reservation journal failure')
finally:L.os.write=original
ok(type(e) is KeyboardInterrupt and x.failed and x.logical_reserved>before,'failed journal retains spend and original fatal')
ok(x.fd is None and x.ledger_fd is None and x.failure_journal_attempted,'failed journal all descriptors closed after independent diagnostic')
ok(len(list((r/'lease').glob('event-*.json')))>=3,'partial reservation and diagnostic files retained')
ok(len(x.failures)>=2,'secondary publication failure object retained')
# A genuine unmodified callback is sampled before/after a writer. Missing writes
# remain reservations, never success evidence or refunds.
r,x=make('no_write');a=x.allocated_reserved;x.reserve('spool',[('spool/missing','file',3)]);x.check();x.close()
ok(not (r/'spool/missing').exists() and x.allocated_reserved>a,'unused reserved copy receives no refund or completion claim')
# Existing append journal ticket freezes once declared final extent reached.
r,x=make('append');(r/'journal/original').write_bytes(b'a')
refuse(x.check,'outside baseline unreserved journal refused')
r=root/'existing';r.mkdir(mode=0o700);roles={k:k for k in L.ROLES}
for p in roles.values():(r/p).mkdir(mode=0o700)
(r/'journal/original').write_bytes(b'a');x=L.OwnedLease(r,'lease',roles,64*L.MIB,64*L.MIB,lambda:None)
x.reserve('journal',[('journal/original','file',3)])
with (r/'journal/original').open('ab') as f:f.write(b'b')
x.check()
with (r/'journal/original').open('ab') as f:f.write(b'c')
x.check();x.close();ok((r/'journal/original').read_bytes()==b'abc','actual existing bounded append retained')
# Directory timestamps and bodies can change only under sampling; logical and
# physical actual values are independently reconstructed from lstat.
r,x=make('independent');x.reserve('codec',[('codec/a','file',3)]);(r/'codec/a').write_bytes(b'abc');sample=x.check()
entries=[r]+list(r.rglob('*'));ok(sample['logical_bytes']==sum(p.lstat().st_size for p in entries),'independent total logical includes directory extents')
ok(sample['allocated_bytes']==sum(p.lstat().st_blocks*512 for p in entries),'independent allocated includes directory blocks')
x.close()
# Each new event slot remains finite and never reset. Direct exact same predicate
# under scaled limit; original production constants unchanged on disk.
r,x=make('finite');original=L.EVENTS
try:
    L.EVENTS=x.serial
    refuse(lambda:x.reserve('codec',[('codec/a','file',3)]),'finite journal exhaustion')
finally:L.EVENTS=original
ok(x.failed and x.fd is None,'journal exhaustion closes and never retries')
# Repeated failures are immutable terminal contexts, no close retry on recycledfd.
for _ in range(10):refuse(x.check,'repeated terminal refusal')
# Exact source API joins and default preservation, WITHOUT importing project code.
base=HERE.parent;capture=json.loads((base/'financial-batch-output-genuine-production-handoff-investigation01-2026-10-04/SOURCE_BODIES01.json').read_text());source_rows=[]
needed=('compact_owner.py','matching_owner.py','imported_mcm_identity.py','compact_mcm.py','compact_mcm_publication.py','workflow_storage.py','lifecycle.py','held_score_consumer.py','completed_f32.py')
for path,body in capture.items():
    if Path(path).name not in needed:continue
    raw=Path(path).read_bytes();ok(raw==body.encode(),'unchanged genuine source '+path)
    tree=ast.parse(body);source_rows.append({'path':path,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'definitions':[{'name':n.name,'line':n.lineno,'ast_sha256':hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()} for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))]})
source=(HERE/'storage_lease01.py').read_text();tree=ast.parse(source)
for token in ('held.check(self.owner)','self.owner.bound.check()','target.check()','verify_current(self.owner)',"run.read_input('storage_lease')","run.read_input('execution_job')",'type(bound) is', 'type(run) is','run.admission.source!=DENIED_SOURCE',"policy['sample_count']==512", "policy['motif_count']==32", "graphs[target.key]",'run.admission.experiment[\'source_files\']','_cleanup is module(\'owned_io\')._cleanup'):
    ok(token in source,'actual source boundary retained '+token)
ok(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('start','admit','remove','unlink','rmtree','reset','retire') for n in ast.walk(tree)),'no start/admit/removal/reset/retirement source calls')
# Fully declared draft-to-final source edits; no original implementation touched.
a=(HERE/'storage_lease01.draft01.py').read_text();b=source
old={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(a).body if isinstance(n,(ast.ClassDef,ast.FunctionDef))};new={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
changed=[n for n in old if old[n]!=new[n]];ok(changed==['OwnedLease','GenuineLease'],'only declared two new candidate class refinements')
(HERE/'SOURCE_JOINS01.json').write_text(json.dumps({'bodies':source_rows,'literal_source_snapshot':str(base/'financial-batch-output-genuine-production-handoff-investigation01-2026-10-04/SOURCE_BODIES01.json'),'new_candidate_changed_classes':changed,'original_source_bodies_modified':0},indent=2,sort_keys=True)+'\n')
(HERE/'CHECKS03.json').write_text(json.dumps({'checks':len(rows),'names':rows,'genuine_handles_executed':False,'source_sha256':hashlib.sha256(source.encode()).hexdigest()},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(rows),'status':'PASS'}))
