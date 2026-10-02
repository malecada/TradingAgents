"""Tiny offline candidate checks. No package/model/Torch/NumPy import."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import MagicMock, patch
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PHASES=('graph_validation','graph_load','model','tensor_adapter','forward','loss','backward','optimizer','checkpoint','reload')
EVENTS=tuple(x+'_'+y for x in PHASES for y in ('before','after'))
IDENTITY={k:'a'*64 for k in ('plan_sha256','claim_sha256','model_config_sha256','graph_manifest_sha256')}
IDENTITY.update(source_commit='b'*40,cell_id='neural_checkpoint-2022-01-03')
SCOPE=None

def module():
    package=types.ModuleType('phase_candidate');package.__path__=[str(HERE/'candidate')];sys.modules['phase_candidate']=package
    parent=types.ModuleType('phase_parent');parent.__path__=[];sys.modules['phase_parent']=parent
    # Candidate uses real reviewed JSON bounding only; never actual physical authority/job.
    spec=importlib.util.spec_from_file_location('phase_candidate.neural_physical',ROOT/'tradingagents/research/onchain_replication/neural_physical.py')
    physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical);sys.modules[spec.name]=physical
    lifecycle=types.ModuleType('phase_candidate.lifecycle');lifecycle.current_metadata_scope=lambda:SCOPE
    sys.modules['phase_parent.lifecycle']=lifecycle
    package.__name__='phase_parent.phase_candidate';sys.modules[package.__name__]=package
    sys.modules['phase_parent.phase_candidate.neural_physical']=physical
    spec=importlib.util.spec_from_file_location('phase_parent.phase_candidate.neural_phases',HERE/'candidate/neural_phases.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class FakeScope:
    def __init__(self,root):
        self.root=root;self.roots={'producer':root/'producer'};self.roots['producer'].mkdir()
        self.anchor={'source':IDENTITY['source_commit'],'experiment':'invented'}
        self.anchor_hash='c'*64;self.policy={'max_json_bytes':262144};self.live=True;self.writes=0
    def check(self):
        if not self.live:raise RuntimeError('original authority lost')
        return {'claim_sha256':IDENTITY['claim_sha256']}
    def atomic(self,path,value):
        self.check();self.writes+=1;path.write_text(json.dumps(value))
    def read_metadata(self,path):self.check();return json.loads(path.read_text())

class Checks(unittest.TestCase):
    def setUp(self):
        global SCOPE
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);SCOPE=self.scope=FakeScope(self.root)
        self.directory=self.scope.roots['producer']/'cell-00';self.directory.mkdir()
        self.mod=module();self.raw_sample=self.mod._sample;self.mod._sample=lambda path:{'memory_current_bytes':None,'qualification':'unavailable'}
        self.mod.time=types.SimpleNamespace(monotonic=lambda:1.0)
    def journal(self):return self.mod.PhaseJournal(self.scope,self.directory,IDENTITY,Path('/sys/fs/cgroup/invented'))
    def test_order_full_bounded_and_no_reopen(self):
        journal=self.journal()
        for event in EVENTS:journal.record(event)
        value=json.loads((self.directory/'phase-journal.json').read_text())
        self.assertEqual([v['event'] for v in value['events']],list(EVENTS))
        self.assertLessEqual(len(json.dumps(value).encode()),65536)
        self.assertEqual(len(list(self.directory.iterdir())),1)
        with self.assertRaises(ValueError):journal.record(EVENTS[-1])
        with self.assertRaises((ValueError,FileExistsError)):self.journal()
    def test_out_of_order_refuses_before_write(self):
        journal=self.journal()
        with self.assertRaises(ValueError):journal.record('forward_before')
        self.assertEqual(self.scope.writes,0)
    def test_lost_authority_and_changed_journal_refuse(self):
        journal=self.journal();journal.record(EVENTS[0]);original=(self.directory/'phase-journal.json').read_bytes()
        self.scope.live=False
        with self.assertRaises(RuntimeError):journal.record(EVENTS[1])
        self.assertEqual((self.directory/'phase-journal.json').read_bytes(),original)
        self.scope.live=True
        with self.assertRaises(ValueError):journal.record(EVENTS[1])
    def test_tampered_prior_receipt_and_parent_refuse(self):
        journal=self.journal();journal.record(EVENTS[0]);p=self.directory/'phase-journal.json';p.write_text('{}')
        with self.assertRaises(ValueError):journal.record(EVENTS[1])
    def test_oversize_readback_refused_no_truncation(self):
        journal=self.journal();self.mod._sample=lambda p:{'pressure':'x'*70000}
        with self.assertRaises(ValueError):journal.record(EVENTS[0])
        self.assertEqual(self.scope.writes,0)
    def test_postwrite_failure_cannot_retry(self):
        journal=self.journal();atomic=self.scope.atomic
        def fail(p,v):atomic(p,v);raise SystemExit('postwrite fake fatal')
        self.scope.atomic=fail
        with self.assertRaises(SystemExit):journal.record(EVENTS[0])
        self.assertEqual(json.loads((self.directory/'phase-journal.json').read_text())['events'][0]['event'],EVENTS[0])
        self.scope.atomic=atomic
        with self.assertRaises(ValueError):journal.record(EVENTS[0])
    def test_run_cell_original_scientific_ast_unchanged(self):
        def cleaned(path,candidate):
            node=next(x for x in ast.parse(path.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='run_cell')
            if candidate:
                i=[a.arg for a in node.args.kwonlyargs].index('phases');node.args.kwonlyargs.pop(i);node.args.kw_defaults.pop(i)
                class Strip(ast.NodeTransformer):
                    def visit_Expr(self,x):
                        if isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='_phase':return None
                        return self.generic_visit(x)
                node=Strip().visit(node)
            return ast.dump(node,include_attributes=False)
        self.assertEqual(cleaned(HERE/'baseline/neural_resource.py',False),cleaned(HERE/'candidate/neural_resource.py',True))
    def test_metadata_read_preserves_first_fatal_when_close_uncertain(self):
        fatal=MemoryError('first fatal read')
        class Stream:
            def __enter__(self):return self
            def __exit__(self,*a):raise OSError('uncertain close')
            def read(self,n):raise fatal
        class FakePath:
            def open(self,*a):return Stream()
            def __fspath__(self):return '/invented-kernel-metadata'
        with patch.object(os,'open',return_value=99),patch.object(os,'read',side_effect=fatal),patch.object(os,'close',side_effect=OSError('uncertain close')):
            with self.assertRaises(MemoryError) as caught:self.mod._read(FakePath(),64)
        self.assertIs(caught.exception,fatal)
    def test_changed_parent_inode_refused(self):
        journal=self.journal();journal.record(EVENTS[0])
        self.directory.rename(self.directory.with_name('preserved-original'));self.directory.mkdir()
        with self.assertRaises(ValueError):journal.record(EVENTS[1])
        self.assertFalse((self.directory/'phase-journal.json').exists())
    def test_telemetry_bounds_and_unknown_not_zero(self):
        folder=self.root/'fake-cgroup';folder.mkdir()
        (folder/'memory.current').write_text('123')
        (folder/'memory.stat').write_text('anon 100\nfile 23\n')
        (folder/'memory.pressure').write_text('some avg10=1.00 total=2\nfull avg10=0.00 total=0\n')
        value=self.raw_sample(folder);self.assertEqual(value['memory_current_bytes'],123);self.assertEqual(value['anon_bytes'],100)
        (folder/'memory.current').write_text('9'*65);(folder/'memory.pressure').write_text('x'*513)
        value=self.raw_sample(folder);self.assertIsNone(value['memory_current_bytes']);self.assertIsNone(value['pressure'])
        self.assertIn('memory_current',value['unavailable']);self.assertIn('pressure',value['unavailable'])
    def test_fatal_telemetry_not_suppressed(self):
        journal=self.journal()
        def die(p):raise MemoryError('invented allocation failure')
        self.mod._sample=die
        with self.assertRaises(MemoryError):journal.record(EVENTS[0])
        self.assertEqual(self.scope.writes,0)
        with self.assertRaises(ValueError):journal.record(EVENTS[0])
    def test_physical_producer_fatal_one_cell_full_denominator_no_retry(self):
        from contextlib import contextmanager
        tree=ast.parse((HERE/'candidate/neural_resource.py').read_text())
        node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='produce_registered_neural_resource')
        class NoImports(ast.NodeTransformer):
            def visit_Import(self,x):return None
            def visit_ImportFrom(self,x):return None
        node=NoImports().visit(node)
        producer=self.root/'sources'/'invented';producer.mkdir(parents=True);self.scope.roots['producer']=producer
        self.scope.birth=lambda role:producer
        class Run:
            def __init__(self):
                self._claim_sha256=IDENTITY['claim_sha256'];self.admission=types.SimpleNamespace(root=self_root,experiment_id='invented',source=IDENTITY['source_commit'],inputs={'g':{'path':'not-read','sha256':'a'*64}})
            def _active(self):pass
            def _check_source(self):pass
            def read_input(self,name):return b'not-read'
        self_root=self.root;run=Run();loads=[]
        cells=[{'cell_id':'neural_checkpoint-'+w,'graph_input':'g','expected_nodes':2,'expected_edges':1} for w in self.mod.WEEKS]
        plan={'cells':cells,'limits':{'max_graph_bytes':1024,'cooperative_cell_seconds':60,'max_checkpoint_bytes':1024,'max_output_bytes':2**20}}
        graph=types.SimpleNamespace(node_ids=('a','b'),edge_index=types.SimpleNamespace(shape=(2,1)))
        @contextmanager
        def mapped(*a,**kw):yield graph
        def load(*a):loads.append(1);return graph
        fatal=SystemExit('invented forward interruption')
        def cell(*a,phases,**kw):
            for event in EVENTS[4:9]:phases.record(event)
            raise fatal
        g={'ResearchRun':Run,'_bound_worker':lambda *a:{'cgroup':'/sys/fs/cgroup/invented'},'registered_plan':lambda *a:(plan,{},'a'*64),'PREFIX':'sources','_namespace':lambda *a:None,'current_metadata_scope':lambda:self.scope,'_immutable':lambda path,value:path.write_text(json.dumps(value)),'file_hash':lambda p:'x','digest':lambda b:'a'*64,'canonical_bytes':lambda v:b'{}','time':types.SimpleNamespace(monotonic=lambda:1.0),'torch':types.SimpleNamespace(set_num_threads=lambda n:None),'sync_directory':lambda p:None,'Path':Path,'PhaseJournal':self.mod.PhaseJournal,'_phase':lambda p,e:p.record(e) if p else None,'open_mapped_graph':mapped,'load_graph':load,'run_cell':cell,'gc':types.SimpleNamespace(collect=lambda:None),'_fatal':lambda e:isinstance(e,SystemExit),'_allocated':lambda p:0}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'fake-producer','exec'),g)
        with self.assertRaises(SystemExit) as caught:g['produce_registered_neural_resource'](run,'plan')
        self.assertIs(caught.exception,fatal);self.assertEqual(loads,[1])
        ledger=json.loads((producer/'failure-ledger.json').read_text())
        self.assertEqual([x['status'] for x in ledger],['failed']+['unavailable']*8)
        self.assertFalse((producer/'cell-01').exists())
        receipt=json.loads((producer/'cell-00'/'phase-journal.json').read_text())
        self.assertEqual(receipt['events'][-1]['event'],'forward_before')
        with self.assertRaises(FileExistsError):g['produce_registered_neural_resource'](run,'plan')
        self.assertEqual(loads,[1])
    def test_fake_operator_full_order_and_fatal_stage_receipt(self):
        def run(path,phases=None,fatal=False):
            tree=ast.parse(path.read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run_cell')
            node.body=[x for x in node.body if not isinstance(x,(ast.Import,ast.ImportFrom))]
            calls=[];world=MagicMock(name='ops');rng=world.rng;model=world.model;optimizer=world.optimizer;state={}
            def seed(n):calls.append(('seed',n));return rng
            def build(*a):
                calls.append(('model',a))
                if fatal:raise SystemExit('fake model fatal')
                return model
            def save(s,writer):state.update(s);writer.write(b'invented checkpoint')
            torch=world.torch;torch.optim.Adam.return_value=optimizer;torch.save.side_effect=save;torch.load.side_effect=lambda *a,**kw:state
            torch.isfinite.return_value=True
            class Writer:
                def __init__(self,s,m):self.stream=s
                def write(self,b):return self.stream.write(b)
            g={'time':types.SimpleNamespace(monotonic=lambda:1.0),'np':types.SimpleNamespace(float32='float32'),'torch':torch,'seed_all':seed,'ReplicationModel':build,'capture_rng':lambda r:{'invented':1},'restore_rng':lambda *a:calls.append(('restore',)), '_state_hash':lambda s:'x','Path':Path,'_BoundedWriter':Writer,'os':os,'_close_checkpoint':lambda s,p:s.close(),'_fatal':lambda e:isinstance(e,BaseException),'sync_directory':lambda p:None,'file_hash':lambda p:'hash','resource':types.SimpleNamespace(RUSAGE_SELF=0,getrusage=lambda x:types.SimpleNamespace(ru_maxrss=1)),'_phase':lambda p,e:p.record(e) if p is not None else None}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'fake-run-cell','exec'),g)
            directory=self.root/('with-receipts' if phases else 'baseline-run');directory.mkdir()
            kwargs={'max_checkpoint_bytes':1024,'cooperative_seconds':60}
            if phases is not None:kwargs['phases']=phases
            graph=types.SimpleNamespace(node_ids=('a','b'),edge_index=world.edge)
            g['run_cell'](graph,{},directory,IDENTITY,**kwargs)
            # File paths differ, scientific operator arguments and RNG order do not.
            ops=[x[0] for x in world.mock_calls]
            return calls,ops
        baseline=run(HERE/'baseline/neural_resource.py')
        journal=self.journal()
        for event in EVENTS[:4]:journal.record(event)
        candidate=run(HERE/'candidate/neural_resource.py',journal)
        self.assertEqual(baseline,candidate)
        self.assertEqual(len(json.loads((self.directory/'phase-journal.json').read_text())['events']),20)
        # New fake cell identity, not a retry of either preceding cell.
        global SCOPE
        self.directory=self.scope.roots['producer']/'cell-01';self.directory.mkdir()
        identity=dict(IDENTITY,cell_id='neural_checkpoint-2022-06-13')
        journal=self.mod.PhaseJournal(self.scope,self.directory,identity,Path('/sys/fs/cgroup/invented'))
        for event in EVENTS[:4]:journal.record(event)
        (self.root/'with-receipts').rename(self.root/'prior-fake-run')
        with self.assertRaises(SystemExit):run(HERE/'candidate/neural_resource.py',journal,True)
        events=json.loads((self.directory/'phase-journal.json').read_text())['events']
        self.assertEqual(events[-1]['event'],'model_before')
        self.assertNotIn('model_after',[x['event'] for x in events])

if __name__=='__main__':
    unittest.main(verbosity=2)
