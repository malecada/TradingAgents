"""Real candidate reader + extracted actual storage helpers; tiny local files only.

AST extraction skips the numerical import, not helper implementation. No current
Binding, empirical artifact, NumPy, Torch, scope or claim is constructed.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch
from test_candidate02 import Candidate

class Reader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):Candidate.setUpClass();cls.m=Candidate.m
    def io_module(self):
        root=Path(__file__).resolve().parents[4]
        path=root/'tradingagents/research/onchain_replication/score_batches.py'
        selected={'CleanupFailure','_require','_hash','_json','_signature','_stamp','_read','_open','_root','_cleanup','_release','_close_after_failure'}
        nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in selected]
        io=ModuleType('tradingagents.research.onchain_replication.score_batches')
        io.__dict__.update(os=os,sys=sys,Path=Path,stat=stat,json=json,hashlib=hashlib,META_LIMIT=8192)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),io.__dict__)
        return io
    def invoke(self,body_error=None,close_error=None,close_number=1):
        io=self.io_module();pkg=ModuleType('tradingagents.research.onchain_replication');pkg.score_batches=io
        with tempfile.TemporaryDirectory(prefix='original-dictionary-reader-') as temp:
            root=Path(temp);(root/'tiny.json').write_bytes(b'{}')
            run=SimpleNamespace(admission=SimpleNamespace(root=root,inputs={'tiny':{'path':'tiny.json','sha256':hashlib.sha256(b'{}').hexdigest()}}))
            real_close=os.close;real_read=os.read;closed=[]
            def close(fd):
                closed.append(fd);real_close(fd)
                if close_error is not None and len(closed)==close_number:raise close_error
            def read(fd,n):
                if body_error is not None:raise body_error
                return real_read(fd,n)
            class Stream:
                def __init__(self,fd):self.fd=fd
                def fileno(self):return self.fd
                def read(self,n):return read(self.fd,n)
                def close(self):pass
            with patch.dict(sys.modules,{pkg.__name__:pkg,io.__name__:io}),patch.object(os,'close',close),patch.object(os,'read',read),patch.object(os,'fdopen',lambda fd,*a,**k:Stream(fd)):
                error=None
                try:value=self.m._read_registered(run,'tiny')
                except BaseException as caught:error=caught;value=None
            self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
            return value,error
    def test_body_first_fatal_identity_survives_child_close_error(self):
        for fatal in (MemoryError('body'),SystemExit('body')):
            _,error=self.invoke(fatal,OSError('uncertain child close'))
            self.assertIs(error,fatal)
    def test_parent_close_first_fatal_identity(self):
        fatal=MemoryError('parent close');_,error=self.invoke(close_error=fatal,close_number=2)
        self.assertIs(error,fatal)
    def test_ordinary_primary_promotes_first_later_fatal(self):
        primary=ValueError('body');fatal=MemoryError('child close');_,error=self.invoke(primary,fatal)
        self.assertIs(error,fatal);self.assertIs(error.__cause__,primary)
    def test_success_exact_bytes(self):
        value,error=self.invoke();self.assertIsNone(error);self.assertEqual(value,b'{}')

    def test_independent_descriptor_closes_after_first_failure(self):
        io=self.io_module();calls=[];fatal=SystemExit('first close')
        def close(fd):
            calls.append(fd)
            if fd==101:raise fatal
            raise OSError('second close')
        with patch.object(os,'close',close):
            with self.assertRaises(SystemExit) as caught:self.m._close_owned((101,102),io)
        self.assertIs(caught.exception,fatal);self.assertEqual(calls,[101,102])

if __name__=='__main__':unittest.main()
