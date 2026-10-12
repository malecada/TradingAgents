"""Deferred stdlib synthetic tests. No Git processes or project/numerical imports.

Adapted cases from tests/research/test_admission_batching.py; wire responses are
invented source evidence for testing only, never admission or usable authority.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

HERE=Path(__file__).resolve().parent

def candidate_namespace():
    tree=ast.parse((HERE/'admission.py').read_text())
    functions={'digest','local_path','_committed','_source_batch_parse','_source_files'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions]
    ns={'Path':Path,'hashlib':hashlib,'re':re,'_SOURCE_BATCH_FILES':128,'_SOURCE_BATCH_BYTES':8*1024**2}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(HERE/'admission.py'),'exec'),ns)
    return ns

class Fixture:
    def __init__(self,root,name='file',body=b'body'):
        self.root=root;self.name=name;self.body=body;self.ns=candidate_namespace()
        self.source='1'*40;self.design='2'*40;self.calls=[];self.hook=None
        self.objects={hashlib.sha1(body).hexdigest().encode():body}
        self.refs={f'{self.source}:{name}':body,f'{self.design}:{name}':body}
        (root/name).write_bytes(body)
        def batch(root,requests,*,bodies=False):
            self.calls.append(('batch-body' if bodies else 'batch-size',tuple(requests)))
            if bodies and self.hook:self.hook()
            result=b''
            for request in requests:
                value=self.objects[request] if bodies else self.refs[request.decode()]
                oid=hashlib.sha1(value).hexdigest().encode();self.objects[oid]=value
                result+=oid+b' blob '+str(len(value)).encode()+b'\n'
                if bodies:result+=value+b'\n'
            return result
        def git(root,*args):
            self.calls.append(('fallback',args));assert args[0]=='show'
            return self.refs[args[1]]
        self.ns['_source_git_batch']=batch;self.ns['_git']=git
    def check(self,expected=None):
        digest=hashlib.sha256(self.body).hexdigest() if expected is None else expected
        return self.ns['_source_files'](self.root,self.source,self.design,{self.name:digest})

class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def fixture(self,**kwargs):return Fixture(self.root,**kwargs)
    def test_literal_patch_and_inverse(self):
        candidate=(HERE/'admission.py').read_bytes();meta=json.loads((HERE/'CANDIDATE01.json').read_text())
        new=b'if local_path(root, name).stat().st_size != current[1]:'
        old=b'if len(local_path(root, name).read_bytes()) != current[1]:'
        self.assertEqual(candidate.count(new),1)
        self.assertEqual(hashlib.sha256(candidate).hexdigest(),meta['candidate_sha256'])
        self.assertEqual(hashlib.sha256(candidate.replace(new,old,1)).hexdigest(),meta['live_source_sha256'])
    def test_intact_binary_input_and_single_content_read(self):
        f=self.fixture(body=b'body\x00\n');real=Path.read_bytes;reads=[]
        from unittest.mock import patch
        def read(path):
            if path==self.root/'file':reads.append(path)
            return real(path)
        with patch.object(Path,'read_bytes',read):self.assertIsNone(f.check())
        self.assertEqual(len(reads),1)
        self.assertEqual([x[0] for x in f.calls],['batch-size','batch-body'])
    def test_size_mismatch_refuses_body_fetch(self):
        f=self.fixture();(self.root/'file').write_bytes(b'longer')
        with self.assertRaisesRegex(ValueError,'committed source differs: file'):f.check()
        self.assertEqual([x[0] for x in f.calls],['batch-size'])
    def test_same_size_content_mutation_refused(self):
        f=self.fixture();(self.root/'file').write_bytes(b'evil')
        with self.assertRaisesRegex(ValueError,'committed source differs: file'):f.check()
    def test_mutation_after_stat_before_final_comparison_refused(self):
        f=self.fixture();f.hook=lambda:(self.root/'file').write_bytes(b'evil')
        with self.assertRaisesRegex(ValueError,'committed source differs: file'):f.check()
        self.assertEqual([x[0] for x in f.calls],['batch-size','batch-body'])
    def test_oversized_pair_uses_original_fallback(self):
        f=self.fixture();f.ns['_SOURCE_BATCH_BYTES']=2
        self.assertIsNone(f.check())
        self.assertEqual([x[0] for x in f.calls],['batch-size','fallback','fallback'])
        (self.root/'file').write_bytes(b'evil')
        with self.assertRaisesRegex(ValueError,'committed source differs'):f.check()
    def test_line_protocol_names_fall_back(self):
        for name in ('line\nbreak','line\rbreak','raw-\udcff'):
            with self.subTest(name=repr(name)):
                f=self.fixture(name=name);self.assertIsNone(f.check())
                self.assertEqual([x[0] for x in f.calls],['fallback','fallback'])
    def test_expected_hash_and_design_still_checked(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'registered source hash differs'):f.check('0'*64)
        f.refs[f'{f.design}:file']=b'evil'
        with self.assertRaisesRegex(ValueError,'source differs from design freeze'):f.check()
    def test_fresh_second_call_not_cached(self):
        f=self.fixture();self.assertIsNone(f.check());(self.root/'file').write_bytes(b'evil')
        with self.assertRaisesRegex(ValueError,'committed source differs'):f.check()
        self.assertEqual(sum(x[0]=='batch-size' for x in f.calls),2)
    def test_forbidden_route_precedes_git(self):
        f=self.fixture();f.name='../outside'
        with self.assertRaisesRegex(ValueError,'registered path must stay'):f.check()
        self.assertEqual(f.calls,[])

if __name__=='__main__':unittest.main()
