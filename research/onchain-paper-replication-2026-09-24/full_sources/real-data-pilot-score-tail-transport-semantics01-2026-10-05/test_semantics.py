"""Offline synthetic format checks; no research run, NumPy or authority modules."""
import ast
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import struct
import tempfile
import types
import unittest
import score_tail_semantics as v

HERE = Path(__file__).resolve().parent
MAIN = HERE.parents[3]
TAIL = MAIN/'tradingagents/research/onchain_replication/score_tail.py'
BATCH = MAIN/'tradingagents/research/onchain_replication/score_batches.py'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
SCOPE = {key: sha(key.encode()) for key in v.SCOPE_FIELDS}
OWNER = sha(b'synthetic non-authoritative fixture owner')

# Execute only unchanged original stdlib encoding functions and append method.
# The local harness is a synthetic file writer, NOT ScoreTail/Owner/Run authority.
batch_tree = ast.parse(BATCH.read_text())
functions = [x for x in batch_tree.body if isinstance(x, ast.FunctionDef)
             and x.name in ('_require', '_identity', '_hash', '_json')]
assert len(functions) == 4
bg = {'hashlib': hashlib, 'json': json, 're': re, 'META_LIMIT': 8192}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(BATCH), 'exec'), bg)
batch = types.SimpleNamespace(**{x.name: bg[x.name] for x in functions})
tail_tree = ast.parse(TAIL.read_text())
cls = next(x for x in tail_tree.body if isinstance(x, ast.ClassDef) and x.name == 'ScoreTail')
append = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == 'append')
g = {'batch': batch, 'require': batch._require, 'FRAME': struct.Struct('<Qd32s'),
     'RECORD_BYTES': 80, 'os': os, 'math': math}
exec(compile(ast.Module(body=[append], type_ignores=[]), str(TAIL), 'exec'), g)


class FixtureWriter:
    append = g['append']

    def _check(self, expected_size=None):
        assert os.fstat(self.record_fd).st_size == (self.acknowledged * 80
               if expected_size is None else expected_size)


def fixture(scores=(0., .25, 1.), first=0):
    start = {'schema_version': 1, 'kind': 'mcm-score-tail', 'scope': SCOPE, 'owner': OWNER,
             'start_cell': first, 'cells': len(scores), 'destination': sha(b'synthetic destination'),
             'record_format': '<Qd32s32s', 'record_bytes': 80}
    start_raw = batch._json(start)
    w = FixtureWriter();w.start = start;w.acknowledged = 0;w.head = sha(start_raw)
    with tempfile.TemporaryFile(dir=HERE) as f:
        w.record_fd = f.fileno()
        for i, value in enumerate(scores):
            w.append(first+i, sha(('purpose-'+str(i)).encode()), value)
        f.seek(0);body = f.read()
    terminal = {'schema_version': 1, 'start_sha256': sha(start_raw), 'status': 'complete',
                'reason': '', 'acknowledged_cells': len(scores), 'head': w.head,
                'records_bytes': len(body), 'records_sha256': sha(body)}
    return start_raw, batch._json(terminal), body


def call(start, terminal, body=None, read=None, **overrides):
    options = dict(start_raw=start, terminal_raw=terminal, start_sha256=sha(start),
                   terminal_sha256=sha(terminal), scope=SCOPE, owner=OWNER)
    options.update(overrides)
    return v.verify_complete(io.BytesIO(body).read if read is None else read, **options)


def metadata(raw, **updates):
    value = json.loads(raw);value.update(updates);return batch._json(value)


class Checks(unittest.TestCase):
    def test_original_complete_short_reads_and_fd(self):
        s,t,b = fixture();r = io.BytesIO(b);requests = []
        def short(n):
            requests.append(n);return r.read(min(n,7))
        result = call(s,t,read=short)
        self.assertEqual(result['cells_verified'],3)
        self.assertEqual(result['records_sha256'],sha(b))
        self.assertLessEqual(max(requests),80)
        self.assertFalse(result['purpose_ancestry_verified'])
        self.assertFalse(result['scientific_completion'])
        with tempfile.TemporaryFile(dir=HERE) as f:
            f.write(b);f.seek(0)
            self.assertEqual(call(s,t,read=lambda n:os.read(f.fileno(),n)),result)
        s,t,b = fixture((0.,),first=2**63-2)
        self.assertEqual(call(s,t,b)['cells_verified'],1)

    def test_partial_failed_empty_denominator(self):
        s,t,b = fixture()
        for payload in (b'', b[:-1], b[:80]):
            with self.subTest(size=len(payload)), self.assertRaises(ValueError):call(s,t,payload)
        for update in ({'status':'failed'}, {'acknowledged_cells':2}, {'records_bytes':239},
                       {'acknowledged_cells':True}, {'schema_version':True}):
            with self.subTest(update=update), self.assertRaises(ValueError):call(s,metadata(t,**update),b)
        empty_s=metadata(s,cells=0)
        empty_t=metadata(t,start_sha256=sha(empty_s),acknowledged_cells=0,records_bytes=0,
                         records_sha256=sha(b''),head=sha(empty_s))
        with self.assertRaises(ValueError):call(empty_s,empty_t,b'')

    def test_reordered_corrupt_trailing_and_rehashed_invalid_values(self):
        s,t,b=fixture()
        damaged=bytearray(b);damaged[17]^=1
        for payload in (b[80:160]+b[:80]+b[160:],bytes(damaged),b+b'!',b+b[:80]):
            with self.subTest(hash=sha(payload)), self.assertRaises(ValueError):call(s,t,payload)
        # Authentic byte hashes/chains cannot make nonfinite/out-of-range values
        # or wrong ordinal semantically acceptable.
        s,t,b=fixture((0.,))
        for ordinal,value in ((0,float('nan')),(0,float('inf')),(0,-.1),(0,1.1),(1,.5)):
            frame=struct.pack('<Qd32s',ordinal,value,bytes(32))
            head=hashlib.sha256(bytes.fromhex(sha(s))+frame).digest();body=frame+head
            terminal=metadata(t,head=head.hex(),records_sha256=sha(body))
            with self.subTest(value=value,ordinal=ordinal), self.assertRaises(ValueError):call(s,terminal,body)

    def test_metadata_pins_scope_and_reader_contract(self):
        s,t,b=fixture()
        for update in ({'owner':'0'*64},{'scope':{**SCOPE,'graph':'0'*64}},
                       {'terminal_sha256':'0'*64},{'start_sha256':'0'*64}):
            with self.subTest(update=update), self.assertRaises(ValueError):call(s,t,b,**update)
        for bad_s in (metadata(s,extra=True),metadata(s,record_bytes=True),metadata(s,cells=104858)):
            with self.assertRaises(ValueError):call(bad_s,metadata(t,start_sha256=sha(bad_s)),b)
        with self.assertRaises(ValueError):call(s,t,read=lambda n:b'x'*(n+1))
        with self.assertRaises(ValueError):call(s,t,read=lambda n:None)
        with self.assertRaisesRegex(OSError,'original reader failure'):
            def failed(n):raise OSError('original reader failure')
            call(s,t,read=failed)


if __name__=='__main__':
    unittest.main(verbosity=2)
