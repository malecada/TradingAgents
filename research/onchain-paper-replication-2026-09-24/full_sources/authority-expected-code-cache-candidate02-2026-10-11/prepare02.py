"""Write prospective two-file candidate only, no authority/science imports."""
from pathlib import Path
import ast,difflib,hashlib,json
H=Path(__file__).resolve().parent;R=H.parents[3];D=R/'tradingagents/research/onchain_replication'
assumption='Expected source code is compiled once per loaded module per activation. Repeated compile/audit/profiling and compiler-warning side effects are intentionally not equivalent; no absence of hooks is asserted. Every authentication still freshly reads and hashes source and checks current loaded capabilities. No validation success, stat or resolved-path cache.'
policy={'schema_version':1,'kind':'activation-owned-expected-code-v1','max_loaded_modules':2048,'max_code_objects':262144,'assumption':assumption}
old=(D/'imported_authority_lease.py').read_text();s=old.replace('import contextlib,hashlib,json,sys,types','import contextlib,hashlib,json,sys,types\nimport builtins')
insert='''
_EXPECTED_COMPILE = builtins.compile
EXPECTED_POLICY = POLICY_LITERAL

def expected_code_policy(value):
    if value is None:return None
    require(type(value) is dict and set(value)==set(EXPECTED_POLICY), 'exact expected-code policy required')
    require(all(type(value[k]) is type(v) and value[k]==v for k,v in EXPECTED_POLICY.items()), 'unsupported expected-code contract')
    return tuple(sorted(value.items()))

def _expected_context(lease,selected):
    compiler=builtins.compile
    require(compiler is _EXPECTED_COMPILE and type(compiler) is types.BuiltinFunctionType
            and compiler.__module__=='builtins' and compiler.__name__=='compile'
            and globals().get('compile',compiler) is compiler, 'captured builtin compiler required')
    require(len(lease.loaded)<=dict(selected)['max_loaded_modules'], 'expected module allowance exceeded')
    scope=tuple((name,module,path,functions) for name,(module,path,functions) in lease.loaded.items())
    return (compiler,sys.flags.optimize,lease.loaded,tuple(lease.sources.items()),lease.run.admission.root,scope)

def _expected_current(lease,*,check_scope=False):
    require(lease._expected_policy is lease._expected_policy_pin, 'expected-code policy replaced')
    if lease._expected_policy is None:return
    require(expected_code_policy(dict(lease._expected_policy))==lease._expected_policy, 'expected-code policy changed')
    context=lease._expected_context
    require(context is lease._expected_context_pin and lease._expected_tables is lease._expected_tables_pin, 'expected-code table/context replaced')
    compiler,optimize,loaded,sources,root,scope=context
    require(builtins.compile is compiler and _EXPECTED_COMPILE is compiler
            and globals().get('compile',compiler) is compiler and sys.flags.optimize==optimize, 'expected-code compiler/optimization changed')
    if not check_scope:return
    require(lease.loaded is loaded and tuple(lease.sources.items())==sources
            and lease.run.admission.root==root, 'expected-code source scope changed')
    require(len(loaded)==len(scope), 'expected-code loaded roster changed')
    for name,module,path,functions in scope:
        require(name in loaded and loaded[name][0] is module and loaded[name][1]==path
                and loaded[name][2] is functions and sys.modules.get(name) is module, 'expected-code module scope changed')
        for label,fn,code in functions:
            require(fn.__code__ is code, 'expected-code loaded function code changed: '+label)

'''.replace('POLICY_LITERAL',repr(policy))
pos=s.index('def _checked_value(');s=s[:pos]+insert+s[pos:]
# Preserve the complete original authenticator, including default compiler calls.
a=old.index('def _authenticate_loaded(');b=old.index('def _checked_value(',a);cached=old[a:b]
cached=cached.replace('def _authenticate_loaded(loaded,sources,root):','def _authenticate_expected(lease):\n    _expected_current(lease,check_scope=True)\n    compiler,optimize,loaded,source_items,root,scope=lease._expected_context\n    sources=lease.sources;expected=lease._expected_tables;tables=[];total_codes=0\n    require(_loaded(root,sources)==loaded, "expected-code current loaded scope differs")')
cached=cached.replace('    for module,p,functions in loaded.values():','    for index,(module,p,functions) in enumerate(loaded.values()):')
a=cached.index('        compiled=compile(');b=cached.index('        for label,fn,code in functions:',a)
compileblock=cached[a:b].replace("compiled=compile(raw,str(p),'exec',dont_inherit=True,optimize=sys.flags.optimize)","compiled=compiler(raw,str(p),'exec',dont_inherit=True,optimize=optimize)")
replacement="        if expected is None:\n"+''.join('    '+l for l in compileblock.splitlines(True))+'''            total_codes+=sum(len(v) for v in codes.values())
            require(total_codes<=dict(lease._expected_policy)['max_code_objects'], 'expected code allowance exceeded')
            frozen=types.MappingProxyType({name:tuple(values) for name,values in codes.items()})
            tables.append((p,sources[str(p.relative_to(root))],frozen))
        else:
            require(len(expected)==len(loaded), 'expected table extent changed')
            path,digest,codes=expected[index]
            require(path==p and digest==sources[str(p.relative_to(root))], 'expected table path/hash differs')
'''
cached=cached[:a]+replacement+cached[b:]
cached=cached.rstrip()+"\n    _expected_current(lease,check_scope=True)\n    return tuple(tables) if expected is None else expected\n\n"
pos=s.index('def _checked_value(');s=s[:pos]+cached+s[pos:]
s=s.replace('def __init__(self,token,execution,selected):','def __init__(self,token,execution,selected,expected_policy=None):')
a="        self.loaded=_loaded(root,self.sources);_authenticate_loaded(self.loaded,self.sources,root)"
b="""        self.loaded=_loaded(root,self.sources)
        self._expected_policy=expected_code_policy(expected_policy);self._expected_policy_pin=self._expected_policy
        self._expected_context=self._expected_context_pin=None
        self._expected_tables=self._expected_tables_pin=None
        if self._expected_policy is None:
            _authenticate_loaded(self.loaded,self.sources,root)
        else:
            self._expected_context=self._expected_context_pin=_expected_context(self,self._expected_policy)
            self._expected_tables=self._expected_tables_pin=_authenticate_expected(self)
            _expected_current(self,check_scope=True)"""
assert a in s;s=s.replace(a,b)
s=s.replace('        e=self.execution\n        require(self.scheduler', '        e=self.execution\n        _expected_current(self)\n        require(self.scheduler')
s=s.replace("        require(current==self.loaded,'loaded module/function identity changed')", "        require(current==self.loaded,'loaded module/function identity changed')\n        _expected_current(self,check_scope=True)")
s=s.replace('        _authenticate_loaded(self.loaded,self.sources,self.run.admission.root)', "        if self._expected_policy is None:\n            _authenticate_loaded(self.loaded,self.sources,self.run.admission.root)\n        else:\n            require(_authenticate_expected(self) is self._expected_tables,'expected table replaced by authentication')")
s=s.replace('    contract=Lease(_TOKEN,execution,selected);execution._sampled_authority_lease=contract', "    expected=None\n    if 'expected_code_cache_input' in plan:\n        role=plan['expected_code_cache_input']\n        require(role in run.admission.inputs and role!=input_name,'distinct admitted expected-code input required')\n        expected=expected_code_policy(json.loads(run.read_input(role)))\n        require(expected is not None,'explicit expected-code selection required')\n    contract=Lease(_TOKEN,execution,selected,**({'expected_policy':dict(expected)} if expected is not None else {}));execution._sampled_authority_lease=contract")
caller=(D/'real_pilot_import_caller.py').read_text();c=caller
anchor="    partial = 'partial_progress' in p"
new="""    code_cache='expected_code_cache_input' in p
    require(not code_cache or (interval and full and type(p['expected_code_cache_input']) is str
            and 0<len(p['expected_code_cache_input'])<=128 and p['expected_code_cache_input'].isascii()
            and all(c.isalnum() or c in '_-' for c in p['expected_code_cache_input'])
            and p['expected_code_cache_input']!=p['imported_authority_lease_input']), 'explicit distinct expected-code input required')
"""
assert anchor in c;c=c.replace(anchor,new+anchor)
a="| ({'imported_authority_lease_input'} if interval else set())";assert a in c;c=c.replace(a,a+" | ({'expected_code_cache_input'} if code_cache else set())")
a="    if 'archive_inputs' in p:roles.update(p['archive_inputs'].values())"
b="""    if 'expected_code_cache_input' in p:
        from .imported_authority_lease import expected_code_policy
        require(expected_code_policy(_read(ad,p['expected_code_cache_input'])) is not None,'explicit expected-code selection required')
        roles.add(p['expected_code_cache_input'])
"""
assert a in c;c=c.replace(a,b+a)
texts={'imported_authority_lease.py':s,'real_pilot_import_caller.py':c};patch=[];inverse=[];refs={}
for n,text in texts.items():
 ast.parse(text);before=(D/n).read_text()
 with (H/n).open('x') as f:f.write(text)
 path=str((D/n).relative_to(R));patch.extend(difflib.unified_diff(before.splitlines(True),text.splitlines(True),fromfile=path,tofile=n));inverse.extend(difflib.unified_diff(text.splitlines(True),before.splitlines(True),fromfile=n,tofile=path))
 refs[path]={'baseline_sha256':hashlib.sha256(before.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(text.encode()).hexdigest()}
for n,body in [('LITERAL_PATCH02.diff',''.join(patch)),('LITERAL_INVERSE02.diff',''.join(inverse))]:
 with (H/n).open('x') as f:f.write(body)
for n,value in [('POLICY02.json',policy),('SOURCE_REQUIREMENTS02.json',refs)]:
 with (H/n).open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
print('two prospective sources generated, no imports')
