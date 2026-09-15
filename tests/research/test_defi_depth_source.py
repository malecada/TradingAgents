"""Invented protocol states only; no network or historical performance test."""
import importlib.util
import json
from pathlib import Path

import pytest
from eth_utils import keccak

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'research/defi-depth-2026-09-15'
loader = importlib.util.spec_from_file_location('defi_depth_q1_test', HERE/'q1_source.py')
q1 = importlib.util.module_from_spec(loader)
loader.loader.exec_module(q1)


def word(value):
    if isinstance(value, str):
        value = int(value, 16)
    return format(int(value) % 2**256, '064x')


def fixture():
    spec = json.loads((HERE/'q1-spec.json').read_text())
    for c in spec['chains']:
        c['historical_block'] = 100
        c['history_header'] = {'number': 100, 'timestamp': 1000, 'hash': '0x'+'11'*32}
    return spec


def fake_transport(spec, denied=False, broken_index=False):
    chains = {c['url']: c for c in spec['chains']}
    calls = []

    def fetch(url, payload):
        calls.append((url, payload))
        if denied and url == spec['chains'][0]['url']:
            return {'body': b'denied', 'http_status': 403, 'headers': {}, 'error': 'HTTP 403', 'body_complete': True}
        c = chains[url]
        if payload['method'] == 'eth_chainId':
            result = hex(c['chain_id'])
        elif payload['method'] == 'eth_getBlockByNumber':
            old = payload['params'][0] == hex(c['historical_block'])
            result = {'number': hex(100 if old else 200), 'timestamp': hex(1000 if old else 2000),
                      'hash': '0x'+('11' if old else '22')*32}
        else:
            action = next(a for a in c['actions'] if a['to'] == payload['params'][0]['to'] and a['data'] == payload['params'][0]['data'])
            key = action['key']
            if 'expected' in action:
                values = action['expected']
            elif key == 'aave-income':
                values = [0 if broken_index else 10**27]
            elif key in ('aave-scaled-supply', 'aave-total-supply'):
                values = [1000]
            elif key == 'lp-slot0':
                values = [2**96, 0, 0, 1, 1, 0, True]
            elif key in ('lp-lower', 'lp-upper'):
                values = [0]*8
            else:
                values = [100]
            result = '0x'+''.join(word(v) for v in values)
        body = json.dumps({'jsonrpc': '2.0', 'id': payload['id'], 'result': result}).encode()
        return {'body': body, 'http_status': 200, 'headers': {}, 'error': None, 'body_complete': True}
    return fetch, calls


def test_full_inventory_and_immutable_publication_order(capsys):
    spec = fixture()
    fake, calls = fake_transport(spec)
    outputs = {}

    def publish(name, value):
        assert name not in outputs
        if name.endswith('-receipt.json'):
            assert name.replace('-receipt.json', '-attempt.json') in outputs
        outputs[name] = value
    result = q1.capture(spec, publish, fake)
    assert len(calls) == result['requests'] == 129
    assert len(result['cells']) == 141
    assert all(r['status'] == 'complete' for r in result['cells'])
    assert len(outputs) == 399  # main() adds the400th summary output
    assert result['financial_outcomes_computed'] is False
    assert result['elapsed_time_kill'] is False
    for _, payload in calls:
        if payload['method'] == 'eth_call':
            assert payload['params'][1]['requireCanonical'] is True
            assert payload['params'][1]['blockHash'] in ('0x'+'11'*32, '0x'+'22'*32)


def test_denial_preserves_all_cells_and_continues_other_chains(capsys):
    spec = fixture()
    fake, calls = fake_transport(spec, denied=True)
    result = q1.capture(spec, lambda *_: None, fake)
    assert len(calls) == 87
    assert len(result['cells']) == 141
    assert sum(r['status'] == 'unavailable' for r in result['cells']) == 47


def test_zero_index_is_not_admitted_as_accrual_identity(capsys):
    spec = fixture()
    fake, _ = fake_transport(spec, broken_index=True)
    result = q1.capture(spec, lambda *_: None, fake)
    assert sum(r['status'] == 'unavailable' for r in result['cells']) == 6
    assert all(r['id'].endswith('aave-supply-identity') for r in result['cells'] if r['status'] == 'unavailable')


@pytest.mark.parametrize('value,kind', [(2, 'bool'), (256, 'uint8'), (2**160, 'address'), (2**24-1, 'int24')])
def test_noncanonical_abi_rejected(value, kind):
    with pytest.raises(ValueError):
        q1.decode_words('0x'+word(value), [kind])


def test_negative_tick_requires_valid_sign_extension():
    assert q1.decode_words('0x'+word(-887220), ['int24']) == [-887220]


@pytest.mark.parametrize('field,value', [('hash', '0x'+'33'*32), ('number', '0x65'), ('timestamp', '0x3e9')])
def test_old_block_mismatch_is_not_substituted(field, value):
    chain = fixture()['chains'][0]
    h = {'hash': chain['history_header']['hash'], 'number': '0x64', 'timestamp': '0x3e8'}
    h[field] = value
    with pytest.raises(ValueError):
        q1.header(h, chain, 'history', 10000, {})


def test_finalized_must_follow_frozen_history_even_if_reread_failed():
    chain = fixture()['chains'][0]
    h = {'number': hex(99), 'timestamp': hex(999), 'hash': '0x'+'33'*32}
    with pytest.raises(ValueError, match='does not follow history'):
        q1.header(h, chain, 'finalized', 10000, {})


@pytest.mark.parametrize('index,value', [(1, 900000), (2, 1), (3, 0), (4, 0)])
def test_impossible_initialized_slot_state_rejected(index, value):
    words = [2**96, 0, 0, 1, 1, 0, True]
    words[index] = value
    with pytest.raises(ValueError):
        q1.validate_slot(words)


def test_frozen_selectors_and_only_public_protocol_addresses():
    spec = fixture()
    for chain in spec['chains']:
        for action in chain['actions']:
            assert action['data'][:10] == '0x'+keccak(text=action['signature'])[:4].hex()
            assert action['to'] in {chain[k] for k in ('pool', 'factory', 'atoken', 'aave_pool', 'usdc', 'weth')}
        cash = next(a for a in chain['actions'] if a['key'] == 'aave-contract-cash')
        assert cash['data'][10:] == word(chain['atoken'])


def test_error_and_wrong_response_id_are_not_states():
    payload = {'id': 'expected'}
    for data in ({'jsonrpc': '2.0', 'id': 'other', 'result': '0x01'},
                 {'jsonrpc': '2.0', 'id': 'expected', 'error': {'message': 'missing trie node'}}):
        with pytest.raises(ValueError):
            q1.envelope(json.dumps(data).encode(), payload)
