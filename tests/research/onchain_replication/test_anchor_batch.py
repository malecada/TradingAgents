"""Git anchor batch framing and exact-byte parity; synthetic repository only."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication import matching_owner as m
class Tests(unittest.TestCase):
    def parse(self,raw,sizes):
        self.assertTrue(hasattr(m,'_anchor_blobs'),'batch parser missing')
        return list(m._anchor_blobs(raw,sizes))
    def test_framed_binary_and_multiple_objects(self):
        data=[b'line\n\x00binary\n',b'next'];raw=b''.join(b'a'*40+b' blob '+str(len(x)).encode()+b'\n'+x+b'\n' for x in data)
        self.assertEqual([bytes(x) for x in self.parse(raw,list(map(len,data)))],data)
    def test_missing_wrong_type_truncated_trailing_or_wrong_extent_refused(self):
        good=b'a'*40+b' blob 1\nx\n'
        for raw,sizes in [(b'unknown missing\n',[1]),(good.replace(b'blob',b'tree'),[1]),(good[:-1],[1]),(good+b'junk',[1]),(good,[2]),(b'bad header\n',[1]),(good.replace(b' 1\n',b' 1000000000000\n'),[1])]:
            with self.subTest(raw=raw),self.assertRaises(ValueError):self.parse(raw,sizes)
    def test_actual_batch_matches_individual_reads_and_missing_anchor_refuses(self):
        self.assertTrue(hasattr(m,'_anchor_read'),'batch reader missing')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def git(*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL)
            git('init','-q');names=[f'source-{i:03d}.txt' for i in range(87)]
            for i,n in enumerate(names):(root/n).write_bytes(f'item {i}\n'.encode()+b'\x00\nend\n')
            git('add','.');git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','fixture')
            commit=git('rev-parse','HEAD').decode().strip();sizes=[(root/n).stat().st_size for n in names]
            t=time.monotonic();prior=[git('show',commit+':'+n) for n in names];serial=time.monotonic()-t
            t=time.monotonic();actual=list(m._anchor_read(root,commit,names,sizes));batched=time.monotonic()-t
            self.assertEqual([bytes(v) for v in actual],prior)
            print(f'ANCHOR TIMING 87objects serial={serial:.6f}s batch={batched:.6f}s',flush=True)
            with self.assertRaises((ValueError,subprocess.CalledProcessError)):list(m._anchor_read(root,'0'*40,names,sizes))
            with self.assertRaises(ValueError):list(m._anchor_read(root,commit,['missing'],[1]))
            with self.assertRaises(ValueError):list(m._anchor_read(root,commit,['bad\nrequest'],[1]))
    def test_subprocess_failure_propagates(self):
        self.assertTrue(hasattr(m,'_anchor_read'),'batch reader missing')
        with patch.object(subprocess,'check_output',side_effect=subprocess.CalledProcessError(1,['git'])):
            with self.assertRaises(subprocess.CalledProcessError):list(m._anchor_read(Path('.'),'a'*40,['x'],[1]))
if __name__=='__main__':unittest.main(verbosity=2)
