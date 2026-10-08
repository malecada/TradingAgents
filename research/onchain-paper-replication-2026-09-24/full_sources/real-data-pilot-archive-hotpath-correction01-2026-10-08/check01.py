"""AST-executed source seams, real tiny metadata files, fake Owner/guard/transport.
No scientific package imports, ResearchRun, native authority or network.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3] / 'tradingagents/research/onchain_replication'
# Resolve checkout from the retained research/full_sources nesting.
assert SOURCE.is_dir(), SOURCE


def require(ok, message):
    if not ok:
        raise ValueError(message)


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def key(value):
    return hashlib.sha256(raw(value)).hexdigest()


def sig(s):
    return s.st_dev, s.st_ino


def open_root(path):
    path = Path(path)
    require(path.resolve() == path, 'redirected root')
    return path, os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def same_root(path, fd):
    require(path.resolve() == path and sig(path.stat()) == sig(os.fstat(fd)), 'root changed')


def read(fd, name, limit):
    child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
    try:
        data = os.read(child, limit + 1)
        require(len(data) <= limit, 'metadata size')
        return data
    finally:
        os.close(child)


def inventory(fd, expected):
    require(set(os.listdir(fd)) == expected, 'inventory differs')


def exact(root, name, expected):
    require((root / name).read_bytes() == expected, 'exact metadata differs')


def entries(path, expected, *, required, _imported=False):
    require(set(p.name for p in path.iterdir()) == expected == required, 'entries differ')


def load_nodes(path, names, env, class_name=None):
    tree = ast.parse(path.read_text())
    body = tree.body if class_name is None else next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == class_name).body
    nodes = [n for n in body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    assert len(nodes) == len(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    return {name: env[name] for name in names}


history_env = {}
# Import this stdlib-only module directly, without importing the package.
exec(compile((SOURCE/'archive_control_history.py').read_text(), str(SOURCE/'archive_control_history.py'), 'exec'), history_env)
P = dict(schema_version=1, format=history_env['FORMAT'], assumption=history_env['ASSUMPTION'],
         success_control_bytes=1024, success_diagnostic_bytes=1024, shard_bytes=4096,
         full_interval_ms=1000, max_callbacks_between_full=4096, max_stale_ms=60000)


class Fixture:
    def __init__(self, path, candidate=True, history=True, typed=False):
        self.now = 0.0
        self.full = self.guards = self.transports = self.claims = 0
        self.bad_guard = self.bad_transport = self.bad_claim = self.bad_typed = False
        self.advance_after_first = None
        package = types.ModuleType('synthetic_archive_' + path.name)
        package.__path__ = []
        sys.modules[package.__name__] = package
        owner_module = types.ModuleType(package.__name__ + '.compact_owner')
        ledger_module = types.ModuleType(package.__name__ + '.archive_owner_operations')
        typed_module = types.ModuleType(package.__name__ + '.typed_payload_operations')
        def typed_evidence(ledger):
            require(not self.bad_typed, 'typed pin changed')
        typed_module.ledger_evidence = typed_evidence
        for mod in (owner_module, ledger_module, typed_module):
            sys.modules[mod.__name__] = mod
            setattr(package, mod.__name__.rsplit('.',1)[1], mod)
        class Owner: pass
        class Ledger: pass
        class Stage: pass
        self.owner = owner = Owner()
        self.ledger = ledger = Ledger()
        owner_module.Owner = Owner
        owner_module.Stage = Stage
        owner_module.cache_key = key
        owner_module.exact = exact
        io = types.SimpleNamespace(_open=open_root, _root=same_root, _read=read, _json=raw,
                                   _signature=sig, META_LIMIT=65536)
        owner_module.io = io
        ledger_module.Ledger = Ledger
        ledger_module._close_descriptor = os.close
        def transport(view):
            self.transports += 1
            require(not self.bad_transport, 'transport refused')
            return 'transport'
        policy = types.SimpleNamespace(writer=types.SimpleNamespace(archive=types.SimpleNamespace(_transport=transport, _inventory=inventory)))
        env = dict(__package__=package.__name__, require=require, owners=owner_module, policy=policy,
                   io=io, os=os, thaw=lambda x:x, _close_descriptor=os.close)
        chosen = HERE if candidate else SOURCE
        names = ['_configuration','_evidence','_full_evidence','_current','_stage','_live']
        funcs = load_nodes(chosen/'archive_owner_operations.py', names, env, 'Ledger')
        for name, fn in funcs.items(): setattr(Ledger, name, fn)
        def count_full(this):
            self.full += 1
            funcs['_full_evidence'](this)
        Ledger._full_evidence = count_full
        owner_env = dict(__package__=package.__name__, require=require, Owner=Owner,
                         cache_key=key, Path=Path, present=lambda p:p.exists(), entries=entries,
                         matching_owner=types.SimpleNamespace(metadata=lambda p,r:(None,p.read_bytes())),
                         io=io, os=os, exact=exact, OWNER_BYTES=2)
        owner_module.verify_current = load_nodes(chosen/'compact_owner.py', ['verify_current'], owner_env)['verify_current']
        path.mkdir()
        journal = path/'journal'; journal.mkdir()
        compact = journal/'compact'; compact.mkdir()
        ledger.root = journal/'archive-operations'; ledger.root.mkdir()
        ledger._inode = sig(ledger.root.stat())
        stage = Stage(); stage.root = compact/'mcm'; stage.root.mkdir()
        stage.name = stage.kind = 'mcm'; stage.owner = owner; stage.closed = False
        stage.intent = b'intent'; (stage.root/'intent.json').write_bytes(stage.intent)
        stage.inode = sig(stage.root.stat()); stage.reservation = 1
        stage.integrity = lambda:require(not stage.closed, 'stage closed')
        operation = types.SimpleNamespace(root=ledger.root/'op', record={'kind':'writer'}, _terminal=False, _stage=stage)
        operation.root.mkdir(); (operation.root/'intent.json').write_bytes(raw(operation.record))
        closed = types.SimpleNamespace(root=ledger.root/'closed', record={'kind':'reader'}, _terminal={'complete.json':b'complete'})
        closed.root.mkdir(); (closed.root/'intent.json').write_bytes(raw(closed.record)); (closed.root/'complete.json').write_bytes(b'complete')
        self.operation = operation
        ledger._active = operation; ledger._operations = {'op':operation,'closed':closed}
        ledger._pins = {n:sig(op.root.stat()) for n,op in ledger._operations.items()}
        ledger._expected = {'start.json':b'ledger'}; (ledger.root/'start.json').write_bytes(b'ledger')
        ledger._closed = ledger._poisoned = False
        ledger.owner = owner; owner._archive_operations = ledger
        owner._transition = ledger._transition = object()
        context = types.SimpleNamespace(_history_policy=P)
        ledger._history_context = context
        ledger._history = history_env['Interval'](P, clock=lambda:self.now) if history else None
        ledger._history_pin = ledger._history
        ledger.record = {'selected':'synthetic'}
        ledger.selection = types.SimpleNamespace(_owner=owner, _transport=types.SimpleNamespace(_context=context),
                                                  record={'policy':{'transport_identity':'transport'}})
        def lease():
            self.guards += 1
            require(not self.bad_guard, 'native guard refused')
        owner.lease = lease; ledger.selection.check = lease
        owner.identity = 'owner'; ledger._spent = {'units':1}; ledger._spent_sha = key(ledger._spent)
        ledger._identity = key(ledger._configuration())
        owner.poisoned = owner.closed = owner.closing = False
        owner.check_binding = lambda:None
        owner.configuration = lambda:{'fixed':True}; owner.configuration_sha256 = key(owner.configuration())
        owner.reserved = owner._reserved = owner.maximum = 3
        def active():
            self.claims += 1
            require(not self.bad_claim, 'claim refused')
        run_dir = path/'run'; run_dir.mkdir()
        owner.bound = types.SimpleNamespace(_run=types.SimpleNamespace(_active=active, directory=run_dir,
                                            admission=types.SimpleNamespace(root=path)),
                                           record={'journal_directory':str(journal)}, _ancestry_arguments=None, _snapshots={})
        # The genuine journal-parent inventory is exact; separate fixture run root.
        owner_env['entries'] = lambda p,e,**kw: entries(p,e,**kw) if p != journal.parent else require(journal.is_dir(), 'journal absent')
        owner.root = compact; owner.inode = sig(compact.stat()); owner.start = b'owner'
        (compact/'owner.json').write_bytes(owner.start)
        owner.required = ['mcm']; owner.stages = {'mcm':stage}; owner.active = stage
        if typed: ledger._typed_expected = {}
        self.verify = owner_module.verify_current
    def hot(self): self.ledger._live(self.operation)


def refuses(call, text):
    try: call()
    except ValueError as error:
        assert text in str(error), (text,str(error))
    else: raise AssertionError('expected refusal: '+text)



# Whole-file compile plus AST equality outside the three permitted methods.
for filename, permitted in (('archive_owner_operations.py', {'_current','_live'}),
                            ('compact_owner.py', {'verify_current'})):
    trees=[]
    for directory in (SOURCE,HERE):
        text=(directory/filename).read_text()
        compile(text,str(directory/filename),'exec')
        tree=ast.parse(text)
        class RemoveChanged(ast.NodeTransformer):
            def visit_FunctionDef(self,node):
                return None if node.name in permitted else self.generic_visit(node)
        trees.append(ast.dump(RemoveChanged().visit(tree),include_attributes=False))
    assert trees[0]==trees[1], filename

with tempfile.TemporaryDirectory(dir=HERE) as temp:
    root = Path(temp)
    number = 0
    def make(**kw):
        global number
        number += 1
        return Fixture(root/str(number), **kw)
    baseline = make(candidate=False)
    candidate = make()
    for _ in range(100): baseline.hot(); candidate.hot()
    assert baseline.full == 100 and candidate.full == 1
    initial_candidate_full = candidate.full
    assert (candidate.guards,candidate.transports,candidate.claims) == (100,100,100)
    assert candidate.ledger._history.calls == 199 # Both sampled callbacks retained.
    candidate.now = 1.0; candidate.hot(); assert candidate.full == 2
    count = make(); count.hot()
    for _ in range(2047): count.hot()
    assert count.full == 1 and count.ledger._history.calls == 4095
    count.hot(); assert count.full == 2 and count.ledger._history.calls == 1
    for kind in ('default','full','verify','legacy','typed'):
        f = make(history=kind!='legacy', typed=kind=='typed')
        for _ in range(3):
            if kind=='default': f.ledger._current(full=False)
            elif kind=='full': f.ledger._current(full=True, sampled_evidence=True)
            elif kind=='verify': f.verify(f.owner)
            else:f.hot()
        assert f.full == (6 if kind in ('legacy','full') else 3), (kind,f.full)
    for mutation, message in (
        (lambda f:setattr(f,'bad_guard',True),'native guard'),
        (lambda f:setattr(f,'bad_transport',True),'transport'),
        (lambda f:setattr(f,'bad_claim',True),'claim'),
        (lambda f:setattr(f.owner,'poisoned',True),'poisoned'),
        (lambda f:setattr(f.ledger,'_spent',{'units':2}),'accounting'),
        (lambda f:(f.operation.root/'intent.json').write_bytes(b'changed'),'intent'),
        (lambda f:setattr(f.owner,'active',None),'no longer active'),
        (lambda f:setattr(f.ledger._history_context,'_history_policy',dict(P, full_interval_ms=2)),'context'),
    ):
        f=make(); f.hot(); mutation(f); refuses(f.hot,message)
    f=make(); f.hot(); f.ledger.root.rename(f.ledger.root.with_name('old')); f.ledger.root.mkdir()
    refuses(f.hot,'directory changed')
    f=make(); f.hot(); metadata=f.owner.bound._run.directory/'binding.json'
    metadata.write_bytes(b'bound'); f.owner.bound._snapshots={metadata:b'bound'}
    metadata.write_bytes(b'changed'); refuses(f.hot,'binding metadata')
    f=make(); f.hot(); f.operation._terminal={'complete.json':b'terminal'}
    refuses(f.hot,'terminal or replaced')
    f=make(typed=True); f.hot(); f.bad_typed=True; refuses(f.hot,'typed pin')
    for force in (False,True):
        f=make(); f.hot(); (f.ledger.root/'closed'/'complete.json').write_bytes(b'changed')
        f.hot(); assert f.full==1 # Documented closed-history detection is sampled.
        if force: refuses(lambda:f.ledger._current(full=False),'metadata changed')
        else: f.now=1.0; refuses(f.hot,'metadata changed')
        refuses(f.hot,'poisoned')
    for time_value,message in ((60.0,'stale'),(-0.1,'backward')):
        f=make(); f.hot(); f.now=time_value; refuses(f.hot,message); refuses(f.hot,'poisoned')
    f=make(); f.hot(); original=f.ledger._full_evidence
    def slow(): original(); f.now+=60
    f.ledger._full_evidence=slow; f.now=1
    refuses(f.hot,'expired'); refuses(f.hot,'poisoned')
    # Time crossing between callbacks must still be caught by the second check.
    f=make(); f.hot(); original=f.ledger._configuration
    def crossing(): f.now=1; return original()
    f.ledger._configuration=crossing; f.hot(); assert f.full==2
    print(json.dumps({'status':'PASS','baseline_full_evidence_calls_per_100_hot_leases':baseline.full,
                      'candidate_full_evidence_calls_per_100_initial_hot_leases':initial_candidate_full,
                      'retained_guard_transport_claim_calls_each':100,
                      'post_first_100_hot_leases_sampled_callback_counter':199,
                      'fixtures':number,'scope':'extracted actual source methods; synthetic authority callbacks and metadata only'},indent=2))
