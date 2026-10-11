"""One independent timing-fix followup: source inverse plus synthetic core."""
import ast,json,subprocess,hashlib
from pathlib import Path
from tradingagents.research.onchain_replication import phase_timing as pt
from tests.research.onchain_replication.test_pilot_efficiency_selection import test_complete_compute_retains_commits_and_joins_numeric_score_bodies
root=Path.cwd();dest=Path(__file__).parent
source=Path('tradingagents/research/onchain_replication/real_pilot_import_caller.py')
new=ast.parse(source.read_text());old=ast.parse(subprocess.check_output(['git','show','HEAD:'+str(source)],text=True))
def operation(tree):return next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=='operation')
def entry(node):
    return isinstance(node,ast.With) and len(node.items)==1 and isinstance(node.items[0].context_expr,ast.Call) and ast.unparse(node.items[0].context_expr)=="phase_timing.measure('entry')"
scopes=[x for x in ast.walk(operation(new)) if entry(x)]
assert len(scopes)==2
for scope in scopes:
    assert not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('produce_imported','run_one_update') for x in ast.walk(scope))
class Inverse(ast.NodeTransformer):
    def visit_With(self,node):
        node=self.generic_visit(node)
        return node.body if entry(node) else node
    def visit_Call(self,node):
        node=self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='_prepare_lease_modules':
            node.keywords=[k for k in node.keywords if k.arg not in ('numeric','continuation')]
        return node
assert ast.dump(Inverse().visit(operation(new)),include_attributes=False)==ast.dump(Inverse().visit(operation(old)),include_attributes=False)
fixture=dest/'fixed-caller-shape';fixture.mkdir();totals=pt.PhaseTotals()
with pt.activate(totals):
    with pt.measure('entry'):pass
    with pt.measure('entry'):pass
    test_complete_compute_retains_commits_and_joins_numeric_score_bodies(fixture,False,True)
for i in range(3):
    summary=json.loads((fixture/f'stream/numeric-batches/{i:012d}.json').read_bytes())
    assert summary['phase_totals']['phases']['entry']['calls']==2
    assert summary['phase_totals']['phases']['publication']['calls']>0
report=dict(status='PASS',checks=['exact operation AST inverse except reviewed timing scopes and selected module kwargs','two finite caller preparation scopes','96 synthetic cells with selected NumPy policy and active collector','three completed batch telemetry bodies'],caller_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),empirical_authority=False)
(dest/'FIX_FOLLOWUP01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
