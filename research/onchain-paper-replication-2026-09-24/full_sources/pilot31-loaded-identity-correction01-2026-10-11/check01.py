"""SYNTHETIC pure loaded-identity test; no real authority or native loading."""
import ast
import builtins
import contextlib
import copy
import hashlib
import json
import sys
import types
from pathlib import Path

ROOT = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
PKG = ROOT / 'tradingagents/research/onchain_replication'
PREFIX = 'tradingagents.research.onchain_replication.'
checks = {}

def extract(path, names):
    return [n for n in ast.parse(path.read_bytes()).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]

def require(value, message):
    if not value:
        raise ValueError('import lease: ' + message)

# Real _loaded/_authenticate_loaded, isolated from the process's module table.
table = {}
scope = dict(sys=types.SimpleNamespace(modules=table, flags=sys.flags),
             types=types, Path=Path, hashlib=hashlib, contextlib=contextlib,
             require=require)
tree = ast.parse((PKG/'imported_authority_lease.py').read_bytes())
nodes = [n for n in tree.body if
         isinstance(n, ast.FunctionDef) and n.name in {'_loaded', '_authenticate_loaded'}
         or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
         t.id == 'AUTHORITY_CLASSES' for t in n.targets)]
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(PKG/'imported_authority_lease.py'), 'exec'), scope)
sources = {str((PKG/n).relative_to(ROOT)): hashlib.sha256((PKG/n).read_bytes()).hexdigest()
           for n in ('compiled_normalization_policy.py', 'compiled_small_lse.py')}
loaded = lambda: scope['_loaded'](ROOT, sources)
authenticate = lambda value: scope['_authenticate_loaded'](value, sources, ROOT)

definition_imports = []
def definition_import(name, globals=None, locals=None, fromlist=(), level=0):
    # These actual modules contain only stdlib imports at module scope.
    assert level == 0 and name in {'types', 'hashlib', 'json', 'os', 'stat', 'pathlib'}, name
    definition_imports.append(name)
    return builtins.__import__(name, globals, locals, fromlist, level)

def pure_module(short):
    name = PREFIX + short
    if name not in table:
        path = PKG / (short + '.py')
        module = types.ModuleType(name)
        module.__file__ = str(path)
        module.__builtins__ = dict(vars(builtins), __import__=definition_import)
        exec(compile(path.read_bytes(), str(path), 'exec', dont_inherit=True,
                     optimize=sys.flags.optimize), vars(module))
        table[name] = module
    return table[name]

events = []
def selected_import(name, globals=None, locals=None, fromlist=(), level=0):
    assert name == '' and level == 1
    events.append(tuple(fromlist))
    result = types.SimpleNamespace()
    for short in fromlist:
        # Other imported packages are inert import-event markers, not fake authority.
        value = pure_module(short) if short in {'compiled_normalization_policy', 'compiled_small_lse'} else object()
        setattr(result, short, value)
    return result

def preloader(path):
    ns = {'__builtins__': dict(vars(builtins), __import__=selected_import)}
    exec(compile(ast.Module(body=extract(path, {'_prepare_lease_modules'}), type_ignores=[]),
                 str(path), 'exec'), ns)
    return ns['_prepare_lease_modules']

original = preloader(PKG/'real_pilot_import_caller.py')
candidate = preloader(HERE/'real_pilot_import_caller.py')

# RED: policy is already a normal transitive import; old preloader omits small helper.
pure_module('compiled_normalization_policy')
original(batched=True, grouped=True)
before = loaded()
authenticate(before)
pure_module('compiled_small_lse')  # the actual definition later selected by _modules
after = loaded()
authenticate(after)
checks['RED_new_helper_changes_real_loaded'] = before != after
checks['RED_exact_added_module'] = set(after)-set(before) == {PREFIX+'compiled_small_lse'}

# GREEN: all selected helper definitions exist before the immutable baseline.
table.clear(); events.clear()
pure_module('compiled_normalization_policy')
candidate(batched=True, grouped=True, compiled=True)
baseline = loaded()
authenticate(baseline)
module = pure_module('compiled_small_lse')
checks['GREEN_reimport_keeps_identity'] = loaded() == baseline
checks['GREEN_two_selected_helpers'] = set(baseline) == {PREFIX+'compiled_normalization_policy', PREFIX+'compiled_small_lse'}
checks['stdlib_definition_imports_only'] = set(definition_imports) <= {'types','hashlib','json','os','stat','pathlib'}

# Existing equality checks still detect additions, removals and same-code replacement.
clone = types.ModuleType(PREFIX+'unexpected_alias')
clone.__file__ = str(PKG/'compiled_small_lse.py')
table[clone.__name__] = clone
checks['unexpected_module_detected'] = loaded() != baseline
del table[clone.__name__]
saved = table.pop(PREFIX+'compiled_small_lse')
checks['module_removal_detected'] = loaded() != baseline
table[PREFIX+'compiled_small_lse'] = saved
fn = module.open_backend
module.open_backend = types.FunctionType(fn.__code__, vars(module), fn.__name__, fn.__defaults__, fn.__closure__)
module.open_backend.__module__ = module.__name__
checks['same_code_function_replacement_detected'] = loaded() != baseline
module.open_backend = fn
original_code = fn.__code__
fn.__code__ = original_code.replace(co_consts=original_code.co_consts+('unexpected-code-constant',))
checks['code_mutation_detected'] = loaded() != baseline
try:
    authenticate(loaded())
except ValueError:
    checks['unauthenticated_code_refused'] = True
else:
    checks['unauthenticated_code_refused'] = False
fn.__code__ = original_code
checks['restored_baseline_exact'] = loaded() == baseline

# Unselected import sequence remains byte-for-byte the same list of import events.
for batched, grouped in ((False, False), (True, False), (True, True)):
    events.clear(); original(batched=batched, grouped=grouped); old_events = list(events)
    events.clear(); candidate(batched=batched, grouped=grouped)
    checks[f'unselected_import_sequence_{batched}_{grouped}'] = events == old_events

# Import failure is not swallowed, converted to a receipt, or followed by activation.
primary = ImportError('synthetic selected helper refusal')
def denied(name, globals=None, locals=None, fromlist=(), level=0):
    if 'compiled_small_lse' in fromlist:
        raise primary
    return selected_import(name, globals, locals, fromlist, level)
ns = {'__builtins__': dict(vars(builtins), __import__=denied)}
exec(compile(ast.Module(body=extract(HERE/'real_pilot_import_caller.py', {'_prepare_lease_modules'}), type_ignores=[]), '<preloader>', 'exec'), ns)
try:
    ns['_prepare_lease_modules'](batched=True, grouped=True, compiled=True)
except ImportError as error:
    checks['import_error_identity_preserved'] = error is primary
else:
    checks['import_error_identity_preserved'] = False

# Full AST inverse: only helper option/import and one genuine caller keyword differ.
old_tree = ast.parse((PKG/'real_pilot_import_caller.py').read_bytes())
new_tree = ast.parse((HERE/'real_pilot_import_caller.py').read_bytes())
helper = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_prepare_lease_modules')
assert helper.args.kwonlyargs[-1].arg == 'compiled' and helper.args.kw_defaults[-1].value is False
helper.args.kwonlyargs.pop(); helper.args.kw_defaults.pop()
batched_block = next(n for n in helper.body if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == 'batched')
assert ast.unparse(batched_block.body[-1]) == 'if compiled:\n    from . import compiled_normalization_policy, compiled_small_lse'
batched_block.body.pop()
calls = [n for n in ast.walk(new_tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == '_prepare_lease_modules']
assert len(calls) == 1
choice = calls[0].keywords.pop()
assert choice.arg == 'compiled'
for value, expected in (({'schema_version':1},False), ({'schema_version':6,'batched':{'execution':{}}},False), ({'schema_version':6,'batched':{'execution':{'compiled_normalization_policy':{}}}},True)):
    assert eval(compile(ast.Expression(body=choice.value), '<selected-metadata-only>', 'eval'), {'selected_mcm':value}) is expected
checks['selection_from_registered_metadata'] = True
checks['full_AST_inverse'] = ast.dump(old_tree, include_attributes=False) == ast.dump(new_tree, include_attributes=False)
checks['preload_precedes_activation'] = (HERE/'real_pilot_import_caller.py').read_text().index('            _prepare_lease_modules(') < (HERE/'real_pilot_import_caller.py').read_text().index("            activate(execution,p['imported_authority_lease_input'])")

assert all(checks.values()), checks
result = {'status':'PASS_FOCUSED_SYNTHETIC_IDENTITY','checks':checks,
          'scope':'Actual pure module definitions, _loaded and _authenticate_loaded with an isolated synthetic module registry; no real authority or native backend invoked.',
          'residual':'Real worker module roster delta was not logged. Real-run success, phase durations and capacity remain unmeasured.'}
(HERE/'RESULT01.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks)}))
