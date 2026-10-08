"""Isolated real-source metadata/Interval checks; no authority objects created."""
import ast,copy,importlib.abc,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT))
class NoNeural(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'torch','tensorflow','jax'}:raise AssertionError('neural import prohibited')
sys.meta_path.insert(0,NoNeural())
from tradingagents.research.onchain_replication.provenance import canonical_bytes
from tradingagents.research.onchain_replication.imported_authority_interval import Interval,require,fingerprint,ASSUMPTION,KIND
BASELINE='--baseline' in sys.argv
if BASELINE:sys.argv.remove('--baseline')
PATH=HERE/('baseline_imported_authority_lease.py' if BASELINE else 'imported_authority_lease.py')
def actual_value_validator():
    tree=ast.parse(PATH.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_checked_value']
    assert len(nodes)==1,'same-boundary returned value validator absent'
    ns={'require':require,'json':json,'__package__':'tradingagents.research.onchain_replication'}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(PATH),'exec'),ns);return ns['_checked_value']

class BoundaryTests(unittest.TestCase):
    def test_actual_value_accepts_and_is_independent(self):
        fn=actual_value_validator();current={'identity':'current'};original={'motifs':['a','b']}
        raw=canonical_bytes({'current':current,'original':original})
        result=fn(raw,raw,current,canonical_bytes(current),original)
        result['original']['motifs'].append('changed')
        self.assertEqual(original,{'motifs':['a','b']})
        self.assertNotEqual(canonical_bytes(result),raw)
    def test_late_value_execution_and_original_mutations(self):
        fn=actual_value_validator();current={'identity':'current'};original={'motifs':['a','b']}
        raw=canonical_bytes({'current':current,'original':original})
        valid=[raw,raw,current,canonical_bytes(current),original]
        for index,replacement in [(0,b'{}'),(1,b'{}'),(2,{'identity':'late'}),(3,b'{}'),(4,{'motifs':['late']})]:
            args=copy.deepcopy(valid);args[index]=replacement
            with self.subTest(index=index):
                with self.assertRaises(ValueError):fn(*args)
    def test_actual_interval_late_source_revocation_and_fatal(self):
        # Real existing scheduler; callbacks are metadata actions, not Owner mocks.
        policy={'schema_version':1,'kind':KIND,'live_interval_ms':1,'fingerprint_interval_ms':2,
                'full_interval_ms':10,'max_stale_ms':100,'max_calls_between_full':100,'assumption':ASSUMPTION}
        with tempfile.TemporaryDirectory(dir=HERE) as d:
            p=Path(d)/'source.py';p.write_text('before');pin=fingerprint(p)
            for mode in ('source','revocation','fatal'):
                p.write_text('before');pin=fingerprint(p);ticks=[0.0];active=[True];calls=[]
                interval=Interval(policy,clock=lambda:ticks[0])
                def full():
                    calls.append('full')
                    if mode=='source':p.write_text('after')
                    if mode=='revocation':active[0]=False;ticks[0]=0.003
                    if mode=='fatal':raise MemoryError('late fatal')
                def finger():require(fingerprint(p)==pin,'late source mutation')
                def live():require(active[0],'late revocation')
                with self.subTest(mode=mode):
                    with self.assertRaises(MemoryError if mode=='fatal' else ValueError):
                        interval.validate(full,finger,live,boundary=True)
                    self.assertTrue(interval.closed)
                    self.assertEqual(calls,['full'])
    def test_call_sites_and_unchanged_guards(self):
        tree=ast.parse(PATH.read_text());lease=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Lease')
        method=next(n for n in lease.body if isinstance(n,ast.FunctionDef) and n.name=='check')
        self.assertIn('_return_value',[a.arg for a in method.args.kwonlyargs])
        rendered=ast.unparse(method)
        for text in ['self._finger()', 'compact_owner.verify_current(self.owner)', 'self.stage.integrity()',
                     'self.execution._materialized._integrity()', 'self.closed = True', 'self.scheduler.closed = True',
                     '_checked_value(', 'boundary=boundary']:
            self.assertIn(text,rendered)
        self.assertLess(rendered.index('self.scheduler.now()'),rendered.index('compact_owner.verify_current(self.owner)'))
        self.assertLess(rendered.index('self._finger()'),rendered.index('return _checked_value('))
        old=ast.parse((HERE/'baseline_imported_mcm_identity.py').read_text());new=ast.parse((HERE/'imported_mcm_identity.py').read_text())
        oldcls=next(n for n in old.body if isinstance(n,ast.ClassDef));newcls=next(n for n in new.body if isinstance(n,ast.ClassDef))
        for name in ['check','final','lease','sources','_pins','derive_scope']:
            get=lambda cls:ast.dump(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
            self.assertEqual(get(oldcls),get(newcls),name)
        init=next(n for n in newcls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
        checkpoints=[n for n in ast.walk(init) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_checkpoint']
        self.assertEqual(len(checkpoints),4)
        self.assertEqual(sum(any(k.arg=='value' and k.value.value is True for k in n.keywords) for n in checkpoints),2)
    def test_no_neural(self):self.assertFalse('torch' in sys.modules)

if __name__=='__main__':unittest.main(verbosity=2)
