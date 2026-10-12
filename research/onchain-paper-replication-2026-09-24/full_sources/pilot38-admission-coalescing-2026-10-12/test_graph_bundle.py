"""Stdlib source-fixture tests only; fixtures never represent Run authority."""
import ast,contextlib,hashlib,json,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
ORIGINAL=ROOT/'tradingagents/research/onchain_replication/real_pilot_population.py'
CANDIDATE=D/'real_pilot_population_candidate.py'
POLICY='source-checked-resource-graph-manifests-v1'


def statements(path):
    tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='produce')
    start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='graphs' for t in n.targets))
    end=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='observed' for t in n.targets))
    return ast.Module(body=fn.body[start:end],type_ignores=[])


class FixtureRun:
    """Deterministic test double for documented call counts; no actual admission."""
    def __init__(self,bodies):self.bodies=bodies;self.singles=[];self.bundles=[];self.source_checks=0;self.fail_bundle=None
    def read_input(self,name):
        self.singles.append(name);self.source_checks+=1
        value=self.bodies[name]
        if isinstance(value,BaseException):raise value
        return value
    def read_inputs(self,names,*,max_each_bytes,max_total_bytes):
        self.bundles.append((names,max_each_bytes,max_total_bytes));self.source_checks+=2
        if self.fail_bundle is not None:raise self.fail_bundle
        values={}
        for k in names:
            value=self.bodies[k]
            if isinstance(value,BaseException):raise value
            if len(value)>max_each_bytes:raise ValueError('each bound')
            values[k]=value
        if sum(map(len,values.values()))>max_total_bytes:raise ValueError('total bound')
        return values


def fixture():
    keys=[f'{i:064x}' for i in range(7)]
    plan={'graphs':{f'week{i}':f'g{i}' for i in range(7)}}
    pilot={'graph_inputs':{h:f'g{i}' for i,h in enumerate(keys)}}
    bodies={f'g{i}':json.dumps({'graph_hash':h,'metadata':dict(asset='ETH',start_utc=f'week{i}',end_utc=f'end{i}',available_at=f'avail{i}',source_hashes=['s'],graph_config_hash='config')}).encode() for i,h in enumerate(keys)}
    return plan,pilot,bodies


def apply(path,run,selected):
    plan,pilot,_=fixture()
    def require(ok,message):
        if not ok:raise ValueError(message)
    env=dict(run=run,plan=plan,pilot=pilot,graph_input_policy=selected,json=json,require=require,GRAPH_CONFIG_SHA='config',
        CalendarGraph=lambda *args:args,digest=lambda x:hashlib.sha256(x).hexdigest())
    exec(compile(statements(path),str(path),'exec'),env)
    return env['graphs'],env['manifest_pins']


class GraphBundleTests(unittest.TestCase):
    def test_original_bytes_pinned(self):
        pin=json.loads((D/'BASE01.json').read_text())
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),pin['sha256'])
    def test_selected_one_bounded_sorted_transaction(self):
        _,_,bodies=fixture();run=FixtureRun(bodies)
        expected=apply(ORIGINAL,FixtureRun(bodies),None)
        self.assertEqual(apply(CANDIDATE,run,POLICY),expected)
        self.assertEqual(run.singles,[])
        self.assertEqual(run.bundles,[(tuple(f'g{i}' for i in range(7)),2*1024**2,4*1024**2)])
        self.assertEqual(run.source_checks,2)
    def test_absent_policy_preserves_legacy_role_order(self):
        _,_,bodies=fixture();run=FixtureRun(bodies)
        apply(CANDIDATE,run,None)
        self.assertEqual(run.singles,[f'g{i}' for i in range(7)])
        self.assertEqual(run.bundles,[]);self.assertEqual(run.source_checks,7)
    def test_invalid_selection_refuses_before_read(self):
        _,_,bodies=fixture();run=FixtureRun(bodies)
        with self.assertRaisesRegex(ValueError,'graph input policy'):apply(CANDIDATE,run,'unknown')
        self.assertEqual(run.singles,[]);self.assertEqual(run.bundles,[])
    def test_bundle_error_escapes_unchanged_without_semantic_work(self):
        _,_,bodies=fixture();run=FixtureRun(bodies);primary=RuntimeError('source changed');run.fail_bundle=primary
        with self.assertRaises(RuntimeError) as got:apply(CANDIDATE,run,POLICY)
        self.assertIs(got.exception,primary);self.assertEqual(run.singles,[])
    def test_semantic_refusal_preserved_after_valid_bundle(self):
        _,_,bodies=fixture();value=json.loads(bodies['g2']);value['metadata']['asset']='OTHER';bodies['g2']=json.dumps(value).encode()
        for path,selected in ((ORIGINAL,None),(CANDIDATE,POLICY)):
            with self.assertRaisesRegex(ValueError,'complete graph identity differs'):apply(path,FixtureRun(bodies),selected)
    def test_mixed_failure_order_is_explicit_selection_deviation(self):
        _,_,bodies=fixture();value=json.loads(bodies['g0']);value['metadata']['asset']='OTHER';bodies['g0']=json.dumps(value).encode()
        bodies['g6']=RuntimeError('later role integrity failure')
        with self.assertRaisesRegex(ValueError,'complete graph identity differs'):apply(ORIGINAL,FixtureRun(bodies),None)
        with self.assertRaisesRegex(RuntimeError,'later role integrity failure'):apply(CANDIDATE,FixtureRun(bodies),POLICY)
    def test_retains_grouped_api_fresh_check_count(self):
        tree=ast.parse((ROOT/'tradingagents/research/lifecycle.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ResearchRun')
        fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='read_inputs')
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_check_source']
        self.assertEqual(len(calls),2)

if __name__=='__main__':unittest.main()
