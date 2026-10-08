"""Metadata-only regression; never constructs a run, Owner, claim or graph."""
import ast
import copy
import importlib.abc
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
class NoNeural(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'torch','tensorflow','jax'}:
            raise AssertionError('neural import forbidden: '+fullname)
sys.meta_path.insert(0,NoNeural())
from tradingagents.research.onchain_replication import matching_pair, compact_policy

def owner_globals(path):
    tree=ast.parse(path.read_text())
    require=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='require')
    namespace={'matching_pair':matching_pair,'__package__':'tradingagents.research.onchain_replication'}
    exec(compile(ast.Module(body=[require],type_ignores=[]),str(path),'exec'),namespace)
    return tree,namespace

FINAL = HERE.parent / 'real-data-pilot-final20-2026-10-08'
PAIR = FINAL / 'templates02/pair_policy01.json'
COMPACT = HERE.parent / 'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json'


def original_validator():
    # Execute the exact two original validation statements from bind, with the
    # real module globals; isolate policy validation from run/graph authority.
    tree,namespace = owner_globals(HERE / 'baseline_matching_owner.py')
    bind = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'bind')
    start = next(i for i,n in enumerate(bind.body) if isinstance(n,ast.Assign)
                 and isinstance(n.targets[0],ast.Name) and n.targets[0].id == 'limits')
    statements = bind.body[start+1:start+3]
    assert 'pair limits differ' in ast.unparse(statements[0])
    code = compile(ast.Module(body=statements,type_ignores=[]), '<original bind policy statements>', 'exec')
    def validate(limits, *, resource=False):
        exec(code, namespace, {'limits':limits})
    return validate


def selected_validator():
    if '--baseline' in sys.argv:
        sys.argv.remove('--baseline')
        return original_validator()
    # Check the production bind path actually calls this exact validator with
    # the resource selector, before descriptor/graph/Owner work.
    tree,namespace=owner_globals(HERE / 'matching_owner.py')
    bind=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bind')
    calls=[n for n in ast.walk(bind) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_pair_limits']
    assert len(calls)==1 and ast.unparse(calls[0])=='_pair_limits(limits, resource=_resource)'
    validator=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_pair_limits')
    exec(compile(ast.Module(body=[validator],type_ignores=[]),str(HERE / 'matching_owner.py'),'exec'),namespace)
    return namespace['_pair_limits']

VALIDATE = selected_validator()

class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.pair=json.loads(PAIR.read_text())['limits']
        self.compact=json.loads(COMPACT.read_text())['stage_policy']['pair']
        self.default={k:v for k,v in self.pair.items() if k in matching_pair.POLICY_FIELDS}

    def test_frozen_pair_and_compact_both_fields(self):
        self.assertEqual(self.pair,self.compact)
        self.assertEqual(self.pair['max_pair_entries_override'],8402640)
        self.assertEqual(self.pair['checkpoint_layout'],{'format':'sharded-npy-v1','chunk_entries':262144})
        for p in (self.pair,self.compact):
            before=copy.deepcopy(p)
            VALIDATE(p,resource=True)
            self.assertEqual(before,p)

    def test_defaults_and_each_optional(self):
        for resource in (False,True):VALIDATE(copy.deepcopy(self.default),resource=resource)
        for field in ('checkpoint_layout','max_pair_entries_override'):
            p=copy.deepcopy(self.default);p[field]=self.pair[field]
            VALIDATE(p,resource=True)
            with self.assertRaises(ValueError):VALIDATE(p,resource=False)
        with self.assertRaises(ValueError):VALIDATE(self.pair,resource=False)
        # Legacy's historical positive-integer range is deliberately unchanged.
        p=copy.deepcopy(self.default);p['max_state_bytes']=2**63
        VALIDATE(p,resource=False)
        with self.assertRaises(ValueError):VALIDATE(p,resource=True)

    def test_malformed(self):
        bad=[]
        for v in (None,[],0,True):bad.append(v)
        for field in matching_pair.POLICY_FIELDS | {'max_pair_entries_override'}:
            for v in (0,-1,True,1.5,'1',None,2**63):
                p=copy.deepcopy(self.pair);p[field]=v;bad.append(p)
        for v in (None,[],{},'sharded-npy-v1',{'format':'other','chunk_entries':1},
                  {'format':'sharded-npy-v1','chunk_entries':True},
                  {'format':'sharded-npy-v1','chunk_entries':0},
                  {'format':'sharded-npy-v1','chunk_entries':-1},
                  {'format':'sharded-npy-v1','chunk_entries':262145},
                  {'format':'sharded-npy-v1','chunk_entries':1.0},
                  {'format':'sharded-npy-v1','chunk_entries':'1'},
                  {'format':'sharded-npy-v1','chunk_entries':1,'extra':1}):
            p=copy.deepcopy(self.pair);p['checkpoint_layout']=v;bad.append(p)
        p=copy.deepcopy(self.pair);p['unknown']=1;bad.append(p)
        p=copy.deepcopy(self.pair);p['chunk_edges']=65537;bad.append(p)
        for field in matching_pair.POLICY_FIELDS:
            p=copy.deepcopy(self.pair);del p[field];bad.append(p)
        for p in bad:
            with self.subTest(policy=p):
                with self.assertRaises(ValueError):VALIDATE(p,resource=True)

    def test_legacy_invalid_unchanged(self):
        bad=[]
        for field in matching_pair.POLICY_FIELDS:
            for v in (0,-1,True,1.5,'1',None):
                p=copy.deepcopy(self.default);p[field]=v;bad.append(p)
        p=copy.deepcopy(self.default);p['unknown']=1;bad.append(p)
        p=copy.deepcopy(self.default);p['chunk_edges']=65537;bad.append(p)
        original=original_validator()
        for p in bad:
            with self.subTest(policy=p):
                with self.assertRaises(ValueError):original(p)
                with self.assertRaises(ValueError):VALIDATE(p)

    def test_capacity_handoff_and_legacy_refusal(self):
        config={'max_pair_entries':4000000,'max_iterations':7}
        self.assertEqual(compact_policy.effective_matching(config,self.pair),
                         {'max_pair_entries':8402640,'max_iterations':7})
        self.assertEqual(config,{'max_pair_entries':4000000,'max_iterations':7})
        self.assertEqual(compact_policy.effective_matching(config,self.default),config)
        p=copy.deepcopy(self.pair);p['max_pair_entries_override']=3999999
        with self.assertRaises(ValueError):compact_policy.effective_matching(config,p)
        stripped=compact_policy.pair_policy(self.pair)
        self.assertNotIn('max_pair_entries_override',stripped)
        self.assertEqual(stripped['checkpoint_layout'],self.pair['checkpoint_layout'])
        # PairSession rejects compact-only schema before reading any graph.
        with self.assertRaisesRegex(ValueError,'pair policy schema'):
            tree=ast.parse(Path(matching_pair.__file__).read_text())
            fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='policy_check')
            # Exact initial schema check, excluding engine import and graph access.
            exec(compile(ast.Module(body=[fn.body[1]],type_ignores=[]),matching_pair.__file__,'exec'),
                 matching_pair.__dict__,{'policy':self.pair,'allow_checkpoint_layout':False})

    def test_no_neural_import(self):
        self.assertFalse('torch' in sys.modules)

if __name__=='__main__':unittest.main(verbosity=2)
