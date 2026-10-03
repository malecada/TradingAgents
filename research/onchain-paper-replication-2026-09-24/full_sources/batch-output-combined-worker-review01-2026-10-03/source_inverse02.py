"""Independent byte patch reconstruction, source origins and lifecycle order."""
import ast, hashlib, json, re
from pathlib import Path
H=Path(__file__).resolve().parent
P=H.parent/'batch-output-combined-worker-preparation01-2026-10-03'
D=H.parent/'batch-output-produced-f32-adapter-preparation02-2026-10-03'
L=H.parent/'held-consumer-selected-transfer-worker-preparation02-2026-10-03'
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source/tradingagents/research/onchain_replication')
rows=[]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def check(label,value):assert value,label;rows.append(label)
def reverse_patch(actual,patch):
    lines=actual.splitlines(keepends=True);out=[];cursor=0;ps=patch.splitlines(keepends=True);i=2
    while i<len(ps):
        header=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',ps[i]);assert header
        old_start,old_count,new_start,new_count=(int(x) if x is not None else 1 for x in header.groups())
        start=new_start-1;out.extend(lines[cursor:start]);cursor=start;i+=1;old=[];new=[]
        while i<len(ps) and not ps[i].startswith('@@'):
            line=ps[i];assert line[0] in ' +-'
            if line[0] in ' -':old.append(line[1:])
            if line[0] in ' +':new.append(line[1:])
            i+=1
        assert len(old)==old_count and len(new)==new_count and lines[cursor:cursor+new_count]==new
        out.extend(old);cursor+=new_count
    out.extend(lines[cursor:]);return ''.join(out)
source_records=[]
for name in ('held_score_consumer.py','resource_fixture.py'):
    raw=(P/name).read_bytes();baseline=(P/(name+'.baseline')).read_bytes();prior=(L/name).read_bytes();current=(C/name).read_bytes()
    check('full byte inverse '+name,reverse_patch(raw.decode(),(P/(name+'.patch')).read_text()).encode()==baseline)
    check('actual accepted201 origin '+name,baseline==prior)
    check('actual current199 origin remains original '+name,current==(L/(name+'.baseline04.txt')).read_bytes())
    source_records.append({'name':name,'candidate_sha256':sha(raw),'baseline201_sha256':sha(baseline),'current199_sha256':sha(current),'current199_path':str(C/name)})
current_ast={n.name:n for n in ast.parse((C/'resource_fixture.py').read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
candidate_ast={n.name:n for n in ast.parse((P/'resource_fixture.py').read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
old_execute=current_ast['execute'];new_execute=candidate_ast['_execute_original'];new_execute.name='execute'
check('current199 original numerical execute AST',ast.dump(old_execute)==ast.dump(new_execute))
source=(D/'compact_mcm.py').read_text()
needles=["stream.finish()", "stage_ref = owner._finish_stage(stage,", "ticket = publication._publish(", "reference = io._write(fd,'complete.json'", "result = Produced(", "result._check()", "consume_if_selected(result,held)"]
positions=[source.index(x) for x in needles]
check('original stream/stage/publication/completion/hook order',positions==sorted(positions))
adapter=(P/'completed_f32.py').read_text()
checks={
 'real completed worker context':'context=durable.Context(run,policy_input=selection[0],job_input=job_input)',
 'real Produced type':'type(produced) is compact_mcm.Produced',
 'imported Target exclusion of NPY':'type(target) is imported_mcm_identity.Target',
 'original Owner type':'type(owner) is compact_owner.Owner',
 'original held type':'type(held) is compact_owner._HeldTransition',
 'closed original stage and active owner':'stage.closed and owner.active is None and not owner.closed and not owner.poisoned',
 'completion object sealed body':'canonical_bytes(thaw(produced.record))==self._producer_pin',
 'actual immutable companions':"{'manifest.json','matrix.f32'}",
 'real scope not dictionary authority':'type(context) is durable.Context and context.run is run and context.input==selected[0] and context.policy==selected[1]',
 'genuine bind claim dispatch':'operation=context.bind(source).claim();operation.dispatch();context.check()',
 'thread owned serialized raw scope':'with _LOCK:',
 'whole complete raw members':'sizes=(8192,4*32*nodes[slot[\'graph\']])',
 'full command cleanup deadline':"commands*(tx['command_seconds']+tx['cleanup_seconds'])<=policy['deadline_seconds']<=job['resources']['wall_seconds']"
}
for label,needle in checks.items():check('source obligation '+label,needle in adapter)
context=(D/'archive_non_tail.py').read_text()
for label,needle in {
 'genuine ResearchRun':"type(run) is ResearchRun",
 'no cross thread Context':"get_ident()==self.thread",
 'no reservation refund':"self.spent==expected",
 'genuine CompletedF32 only':"type(source) is CompletedF32",
 'live Operation slot':"self.ledger.context.active is self and self.ledger.context.operations.get(self.ledger.identity) is self",
 'pinned complete ledger':"encode(self.ledger.record)==self._record_pin",
 'failure revokes original owner':"self.ledger.owner.poisoned=True"
}.items():check('source obligation '+label,needle in context)
record={'status':'PASS','check_count':len(rows),'checks':rows,'body_origins':source_records,'lifecycle_order':dict(zip(needles,positions)),'qualification':'Static source obligations and exact byte origin/inverse checks; no genuine Context/Owner/Produced or transport executed.'}
(H/'SOURCE_INVERSE_RESULTS02.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(rows)}))
