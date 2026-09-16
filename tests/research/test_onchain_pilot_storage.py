"""Synthetic capture/storage checks; never contact the archive."""
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

PATH = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/pilot/storage.py'
SPEC = importlib.util.spec_from_file_location('onchain_pilot_storage', PATH)
storage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(storage)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def capture(self, **limits):
        return storage.BinaryCapture(dict(base_url='https://example.test/archive/', **limits), self.directory)

    def response(self, chunks, status=206):
        class Response:
            headers = {'ETag': '"opaque"', 'Content-Range': 'bytes 0-2/9'}
            def __init__(self):
                self.status = status
                self.chunks = iter(chunks)
            def read(self, amount):
                result = next(self.chunks, b'')
                if isinstance(result, Exception):
                    raise result
                return result[:amount]
            def close(self):
                pass
        return Response()

    def test_blob_roundtrip_no_overwrite_and_durable_publication(self):
        path = self.directory / 'blob.zst'
        with patch.object(storage.os, 'fsync', wraps=storage.os.fsync) as fsync:
            meta = storage.write_blob(path, b'abc' * 100)
            self.assertGreaterEqual(fsync.call_count, 2)
        self.assertEqual(storage.read_blob(path, meta), b'abc' * 100)
        self.assertEqual(meta['base64_theoretical_bytes'], 400)
        with self.assertRaises(FileExistsError):
            storage.write_blob(path, b'different')
        for field, value in [('raw_bytes', 299), ('raw_sha256', 'bad'), ('stored_bytes', 0),
                             ('stored_sha256', 'bad'), ('raw_bytes', storage.MAX_RAW + 1)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                storage.read_blob(path, dict(meta, **{field: value}))
        path.write_bytes(path.read_bytes() + b'junk')
        with self.assertRaises(ValueError):
            storage.read_blob(path, meta)

    def test_empty_and_json_immutable(self):
        path = self.directory / 'empty.zst'
        meta = storage.write_blob(path, b'')
        self.assertEqual(storage.read_blob(path, meta), b'')
        output = self.directory / 'immutable.json'
        storage.atomic_json(output, {'x': 1})
        with self.assertRaises(FileExistsError):
            storage.atomic_json(output, {'x': 2})
        self.assertEqual(json.loads(output.read_text()), {'x': 1})

    def test_range_success_intent_precedes_io_and_no_retries(self):
        capture = self.capture()
        def open_response(request, timeout):
            self.assertTrue((self.directory / 'request-0001-intent.json').exists())
            self.assertEqual(request.get_header('If-match'), '"opaque"')
            self.assertEqual(timeout, 30)
            return self.response([b'abc', b''])
        capture.opener = Mock(open=Mock(side_effect=open_response))
        body, receipt = capture.get('https://example.test/archive/object', {'Range': 'bytes=0-2', 'If-Match': '"opaque"'})
        self.assertEqual(body, b'abc')
        self.assertEqual(receipt['status'], 206)
        self.assertEqual(receipt['response_headers']['etag'], '"opaque"')
        self.assertTrue((self.directory / 'request-0001.json').exists())
        self.assertEqual(storage.read_blob(self.directory / receipt['blob']['path'], receipt['blob']), body)
        capture.opener.open.assert_called_once()

    def test_denial_stops_future_acquisition_with_receipt(self):
        for status in (401, 403, 429):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                capture = storage.BinaryCapture({'base_url': 'https://example.test/'}, tmp)
                capture.opener = Mock(open=Mock(return_value=self.response([b'no'], status)))
                self.assertIsNone(capture.get('https://example.test/a')[0])
                _, receipt = capture.get('https://example.test/b')
                self.assertIn('source denied', receipt['error'])
                self.assertTrue((Path(tmp) / 'request-0002.json').exists())
                capture.opener.open.assert_called_once()

    def test_prefix_retained_timeout_and_incomplete_read(self):
        for error, prefix in [(TimeoutError('timeout'), b'abc'),
                              (http.client.IncompleteRead(b'def', 6), b'abcdef')]:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as tmp:
                capture = storage.BinaryCapture({'base_url': 'https://example.test/'}, tmp)
                capture.opener = Mock(open=Mock(return_value=self.response([b'abc', error])))
                body, receipt = capture.get('https://example.test/a')
                self.assertIsNone(body)
                self.assertEqual(storage.read_blob(Path(tmp) / receipt['blob']['path'], receipt['blob']), prefix)
                capture.opener.open.assert_called_once()

    def test_overflow_and_budget_exhaustion(self):
        capture = self.capture(max_response_bytes=3, max_requests=1)
        capture.opener = Mock(open=Mock(return_value=self.response([b'abcd'])))
        body, receipt = capture.get('https://example.test/archive/a')
        self.assertIsNone(body)
        self.assertEqual(receipt['bytes'], 4)
        self.assertIn('limit exceeded', receipt['error'])
        _, stopped = capture.get('https://example.test/archive/b')
        self.assertIn('request budget exhausted', stopped['error'])
        self.assertTrue((self.directory / 'request-0002.json').exists())
        capture.opener.open.assert_called_once()

    def test_url_header_boundaries(self):
        capture = self.capture()
        capture.opener = Mock()
        for url in ['http://example.test/archive/a', 'https://example.test.evil/archive/a',
                    'https://user@example.test/archive/a', 'https://example.test/archive/../a',
                    'https://example.test/archive/%2e%2e/a', 'https://example.test/archive/a?X-Amz-Signature=abc']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                capture.get(url)
        with self.assertRaises(ValueError):
            capture.get('https://example.test/archive/a', {'Authorization': 'secret'})
        capture.opener.open.assert_not_called()
        self.assertIsNone(storage.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.test'))


if __name__ == '__main__':
    unittest.main()
