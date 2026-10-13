"""Exchange-address labels: union of Dune Spellbook `cex_evms_addresses` (BSL 1.1,
research use) and dawsbot/eth-labels `mainnet/exchange` (MIT), pinned to commits.
The list itself stays in gitignored artifacts; commits record sources and hashes."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pyarrow as pa

from . import config

_ROW = re.compile(r"\(\s*(0x[0-9a-fA-F]{40})\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*date\s*'(\d{4}-\d{2}-\d{2})'\s*\)")


def parse_spellbook(text):
    rows = {}
    for m in _ROW.finditer(text):
        rows[m.group(1).lower()] = {'name': m.group(2), 'added': m.group(5)}
    candidates = len(re.findall(r'\(\s*0x', text))
    return rows, candidates - len(_ROW.findall(text))


def parse_ethlabels(text):
    out = {}
    for r in json.loads(text):
        a = r['address'].lower()
        if re.fullmatch(r'0x[0-9a-f]{40}', a):
            out[a] = {'name': r.get('nameTag') or ''}
    return out


def union(spell, eth):
    out = {}
    for src, rows in (('ethlabels', eth), ('spellbook', spell)):
        for a, v in rows.items():
            e = out.setdefault(a, {'name': '', 'added': None, 'sources': []})
            e['sources'].append(src)
            e['name'] = e['name'] or v.get('name', '')
            e['added'] = e['added'] or v.get('added')
    for e in out.values():
        e['sources'] = sorted(e['sources'])
    return out


def _commit(get, repo, branch):
    return json.loads(get(f'https://api.github.com/repos/{repo}/commits/{branch}'))['sha']


def fetch_and_store(get, out_dir, cfg=None):
    c = (cfg or config.load())['labels']
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta, raw = {'sources': {}}, {}
    for name in ('spellbook', 'ethlabels'):
        s = c[name]
        sha = _commit(get, s['repo'], s['branch'])
        url = f"https://raw.githubusercontent.com/{s['repo']}/{sha}/{s['path']}"
        body = get(url)
        raw[name] = body.decode()
        (out_dir / f'{name}.raw').write_bytes(body)
        meta['sources'][name] = {'repo': s['repo'], 'commit': sha, 'path': s['path'], 'url': url,
                                 'sha256': hashlib.sha256(body).hexdigest()}
    spell, unparsed = parse_spellbook(raw['spellbook'])
    eth = parse_ethlabels(raw['ethlabels'])
    meta['sources']['spellbook'].update(count=len(spell), unparsed=unparsed)
    meta['sources']['ethlabels'].update(count=len(eth))
    u = union(spell, eth)
    body = json.dumps(u, sort_keys=True, indent=0).encode()
    (out_dir / 'labels.json').write_bytes(body)
    meta.update(count=len(u), sha256=hashlib.sha256(body).hexdigest())
    (out_dir / 'meta.json').write_text(json.dumps(meta, indent=1, sort_keys=True))
    return meta


def load(path):
    return json.loads(Path(path).read_text())


def exchange_array(path):
    return pa.array(sorted(load(path)), pa.string())