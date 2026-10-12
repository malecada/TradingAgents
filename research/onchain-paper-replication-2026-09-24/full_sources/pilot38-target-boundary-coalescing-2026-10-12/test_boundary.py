"""Stdlib source fixtures only. No constructed empirical authority or numerical import."""
import ast,builtins,copy,json,runpy,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
BASELINE='--baseline' in sys.argv
if BASELINE:sys.argv.remove('--baseline')
def canonical_bytes(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def require(ok,why):
    if not ok:raise ValueError(why)
def source(name):return HERE/(('baseline_' if BASELINE else '')+name+'.py')
def extract(path,name,ns,cls=None):
    tree=ast.parse(path.read_text());body=tree.body
    if cls:body=next(n for n in body if isinstance(n,ast.ClassDef) and n.name==cls).body
    node=next(n for n in body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
    return ns[name]
INTERVAL=runpy.run_path(str(ROOT/'tradingagents/research/onchain_replication/imported_authority_interval.py'))
class Fixture:
    def __init__(self,leased=True):
        self.events=[];self.original={'ordered_motifs':['a','b']};self.current={'execution':'fixed'}
        self.raw=canonical_bytes({'current':self.current,'original':self.original});self.mutate=lambda:None
        self.active=True;self.content=True;self.graph='fixed';self.full_failure=None
        fixture=self
        class Target:pass
        class Lease:pass
        self.target=Target();t=self.target;self.contract=Lease();c=self.contract
        def verify(owner):self.events.append('verify');require(self.active,'revoked')
        def content(stage):self.events.append('content');require(self.content,'content changed')
        def read(run,role):self.events.append('read');self.mutate();return b'manifest'
        modules={'compact_owner':NS(verify_current=verify),'imported_mcm_identity':NS(Target=Target),
                 'provenance':NS(canonical_bytes=canonical_bytes)}
        def imp(name,globals=None,locals=None,fromlist=(),level=0):
            if level:
                if not name:return NS(**{key:modules[key] for key in fromlist})
                return modules[name]
            return builtins.__import__(name,globals,locals,fromlist,level)
        ns={'__builtins__':dict(vars(builtins),__import__=imp),'require':require,'json':json,
            'canonical_bytes':canonical_bytes,'Lease':Lease,'compact_owner':modules['compact_owner'],
            'original_import_stage':NS(content=content),'original_dictionary':NS(_read_registered=read),
            'graph_hash':lambda g:self.graph,'node_order_hash':lambda n:'order'}
        ns['_checked_value']=extract(source('imported_authority_lease'),'_checked_value',ns)
        Lease.check=extract(source('imported_authority_lease'),'check',ns,'Lease')
        wrapper=extract(source('imported_authority_lease'),'target_lease',ns)
        modules['imported_authority_lease']=NS(target_lease=wrapper);self.wrapper=wrapper
        for name in ('check','lease','final'):setattr(Target,name,extract(source('imported_mcm_identity'),name,ns,'Target'))
        policy={'schema_version':1,'kind':INTERVAL['KIND'],'live_interval_ms':1,'fingerprint_interval_ms':2,
                'full_interval_ms':10,'max_stale_ms':100,'max_calls_between_full':100,'assumption':INTERVAL['ASSUMPTION']}
        c.scheduler=INTERVAL['Interval'](policy,clock=lambda:0.0);c.closed=False;c.targets={};c.target=None
        c.value=self.raw;c.owner=object();c.stage=NS(integrity=lambda:self.events.append('integrity'))
        c._identity=lambda:require(not c.closed,'closed');c._finger=lambda: self.events.append('finger');c._live=lambda:verify(c.owner)
        def full():
            self.events.append('full')
            if self.full_failure:raise self.full_failure
            result=self.execution_check()
            require(canonical_bytes(result)==c.value,'full imported baseline differs')
            if c.target is not None:c.target.final(full_graph=False)
            return canonical_bytes(result)
        c._full=full
        execution=NS(_execution=self.current,_execution_pin=canonical_bytes(self.current),
                     _materialized=NS(_integrity=lambda:copy.deepcopy(self.original)),_stage=c.stage,check=self.execution_check)
        if leased:execution._sampled_authority_lease=c
        c.execution=execution;t.execution=execution
        run=NS(admission=NS(inputs={'graph':{'sha256':'manifest-pin'}}))
        t.owner=NS(bound=NS(_run=run));t._input='graph';t._manifest_sha='manifest-pin';t._manifest=b'manifest'
        t._execution_pin=self.raw;t._motifs=['a','b'];t.scope='scope';t.derive_scope=lambda:'scope'
        t._pins=lambda:self.events.append('pins');t.graph=NS(node_ids=());t.key='fixed';t._node_order='order'
    def execution_check(self):
        self.events.append('execution');require(self.active,'revoked')
        return copy.deepcopy({'current':self.current,'original':self.original})

class BoundaryTests(unittest.TestCase):
    def test_selected_eliminates_middle_execution(self):
        f=Fixture();self.assertIsNone(f.target.check());self.assertEqual(f.events.count('execution'),2)
        self.assertEqual(f.events.count('read'),1);self.assertFalse(f.contract.closed)
    def test_legacy_exact_execution_order(self):
        f=Fixture(False);f.target.check()
        self.assertEqual([e for e in f.events if e in ('execution','read')],['execution','read','execution'])
    def test_each_check_gets_fresh_entry_and_exit(self):
        f=Fixture();f.target.check();f.target.check();self.assertEqual(f.events.count('execution'),4)
    def test_interval_never_returns_value(self):
        f=Fixture();f.wrapper(f.target,boundary=True)
        before=f.events.count('execution');self.assertIsNone(f.wrapper(f.target));self.assertEqual(f.events.count('execution'),before)
        self.assertIsNone(f.wrapper(f.target,boundary=True));self.assertEqual(f.events.count('execution'),before+1)
    def test_interval_value_request_refuses_and_poisons(self):
        for boundary,value in [(False,True),(1,True),(True,1)]:
            f=Fixture()
            with self.subTest(boundary=boundary,value=value):
                with self.assertRaises(ValueError):f.wrapper(f.target,boundary=boundary,_return_value=value)
                self.assertTrue(f.contract.closed);self.assertTrue(f.contract.scheduler.closed)
                self.assertEqual(f.events,[])
    def test_fresh_value_independent_metadata(self):
        f=Fixture();value=f.wrapper(f.target,boundary=True,_return_value=True)
        value['current']['execution']='caller changed';self.assertEqual(f.current['execution'],'fixed')
        self.assertEqual(f.wrapper(f.target,boundary=True,_return_value=True)['current']['execution'],'fixed')
    def test_postread_mutations_refuse_at_final_and_poison(self):
        for mode in ('current','original','revocation','content'):
            f=Fixture()
            def mutate():
                if mode=='current':f.current['execution']='late'
                elif mode=='original':f.original['ordered_motifs'].reverse()
                elif mode=='revocation':f.active=False
                else:f.content=False
            f.mutate=mutate
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):f.target.check()
                self.assertTrue(f.contract.closed);self.assertTrue(f.contract.scheduler.closed)
                self.assertEqual(f.events.count('read'),1)
    def test_postread_graph_mutation_refuses_original_final_graph_guard(self):
        f=Fixture();f.mutate=lambda:setattr(f,'graph','late')
        with self.assertRaisesRegex(ValueError,'registered target contents changed'):f.target.check()
        # This check is outside target_lease in both versions; no new poison claim.
        self.assertFalse(f.contract.closed)
    def test_late_fatal_closes_contract(self):
        f=Fixture();f.mutate=lambda:setattr(f,'full_failure',MemoryError('late fatal'))
        with self.assertRaisesRegex(MemoryError,'late fatal'):f.target.check()
        self.assertTrue(f.contract.closed);self.assertTrue(f.contract.scheduler.closed)
    def test_manifest_refusal_priority_and_poison_unchanged(self):
        f=Fixture();f.target._manifest=b'wrong'
        with self.assertRaisesRegex(ValueError,'target manifest changed'):f.target.check()
        self.assertFalse(f.contract.closed);self.assertEqual(f.events.count('execution'),1)
    def test_postcallback_metadata_and_baseline_mutations_poison(self):
        for mode in ('current','original','baseline','fingerprint'):
            f=Fixture()
            def late():
                if mode=='current':f.current['execution']='late callback'
                elif mode=='original':f.original['ordered_motifs'].reverse()
                elif mode=='baseline':f.contract.value=b'{}'
                else:f.contract._finger=lambda:require(False,'late fingerprint mutation')
            f.contract.stage.integrity=late
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):f.wrapper(f.target,boundary=True,_return_value=True)
                self.assertTrue(f.contract.closed);self.assertTrue(f.contract.scheduler.closed)
    def test_mixed_late_failure_priority_explicit(self):
        f=Fixture()
        def mutate():
            f.current['execution']='late';f.full_failure=MemoryError('final boundary fatal')
        f.mutate=mutate
        # Candidate reaches retained final boundary. Baseline raises the earlier
        # middle execution-identity mismatch; exact priority intentionally changes.
        with self.assertRaisesRegex(MemoryError,'final boundary fatal'):f.target.check()
        self.assertTrue(f.contract.closed)
    def test_existing_checked_value_mutation_refusals(self):
        ns={'require':require,'json':json,'__builtins__':dict(vars(builtins),__import__=lambda *a,**k:NS(canonical_bytes=canonical_bytes))}
        fn=extract(source('imported_authority_lease'),'_checked_value',ns)
        current={'x':1};original={'y':2};raw=canonical_bytes({'current':current,'original':original})
        valid=[raw,raw,current,canonical_bytes(current),original]
        for index,replacement in [(0,b'{}'),(1,b'{}'),(2,{}),(3,b'{}'),(4,{})]:
            args=copy.deepcopy(valid);args[index]=replacement
            with self.subTest(index=index):
                with self.assertRaises(ValueError):fn(*args)
    def test_unchanged_guard_functions(self):
        for file,cls,names in [('imported_authority_lease','Lease',['check','_full']),('imported_mcm_identity','Target',['lease','final','_pins','derive_scope'])]:
            def bodies(prefix):
                tree=ast.parse((HERE/(prefix+file+'.py')).read_text());c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
                return {n.name:ast.dump(n) for n in c.body if isinstance(n,ast.FunctionDef) and n.name in names}
            self.assertEqual(bodies('baseline_'),bodies(''))
    def test_no_numerical_imports(self):self.assertFalse({'numpy','torch','tensorflow','jax'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
