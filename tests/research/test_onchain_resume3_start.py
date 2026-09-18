"""TLS-only preflight fails before any empirical claim or launch artifact."""
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock
import pytest

BASE = Path(__file__).resolve().parents[2]/'research/onchain-graph-2026-09-16/comparison'


def starter(monkeypatch):
    monkeypatch.syspath_prepend(str(BASE))
    spec = importlib.util.spec_from_file_location('resume3_start_test', BASE/'resume3_start.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.sys, 'argv', ['starter', '--source', 'a'*40])
    monkeypatch.setattr(module.socket, 'getaddrinfo', lambda *a, **k: [])
    return module


def test_failed_tls_does_not_claim_or_publish(monkeypatch):
    module = starter(monkeypatch)
    admission = MagicMock()
    publish = MagicMock()
    monkeypatch.setattr(module, 'admit_resume3', admission)
    monkeypatch.setattr(module, 'publish', publish)
    def fail(*a, **k):
        assert k['timeout'] == 15
        raise TimeoutError('invented TLS timeout')
    monkeypatch.setattr(module.socket, 'create_connection', fail)
    with pytest.raises(TimeoutError): module.main()
    admission.assert_not_called()
    publish.assert_not_called()


def test_tls_success_precedes_admission(monkeypatch):
    module = starter(monkeypatch)
    tls = MagicMock()
    tls.__enter__.return_value.version.return_value = 'TLSv1.3'
    context = MagicMock()
    context.wrap_socket.return_value = tls
    monkeypatch.setattr(module.ssl, 'create_default_context', lambda: context)
    connection = MagicMock()
    monkeypatch.setattr(module.socket, 'create_connection', lambda *a, **k: connection)
    def admitted(*a, **k):
        context.wrap_socket.assert_called_once()
        raise ValueError('synthetic admission stop')
    monkeypatch.setattr(module, 'admit_resume3', admitted)
    with pytest.raises(ValueError, match='synthetic admission stop'): module.main()
