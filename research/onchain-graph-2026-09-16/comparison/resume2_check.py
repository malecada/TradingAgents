"""Independent raw continuation audit; no runner imports or numerical decoding."""
import copy
import json
import os
from pathlib import Path

from check_bulk import check_day as check_raw
from check_capture import digest, load, receipts, require

PREFIX = 'research/onchain-graph-2026-09-16/comparison'


def transport(record):
    if record.get('status') not in (None, 200, 206):
        return False
    error = record.get('error', '')
    lowered = error.lower()
    forbidden = ('certificate', 'hostname', 'wrong_version_number', 'unsupported protocol',
                 'protocol_version', 'handshake_failure', 'no shared cipher')
    if any(word in lowered for word in forbidden):
        return False
    kind = error.partition(':')[0]
    if kind == 'URLError':
        symptoms = ('connection reset', 'connection aborted', 'connection refused', 'broken pipe',
                    'timed out', 'timeout', 'temporary failure in name resolution',
                    'name or service not known', 'nodename nor servname provided',
                    'getaddrinfo failed', 'unexpected_eof', 'eof occurred')
        return any(word in lowered for word in symptoms)
    if kind == 'SSLError':
        return any(word in lowered for word in ('unexpected_eof', 'eof occurred'))
    return error == 'ValueError: response body length mismatch' or kind in {
        'ConnectionResetError', 'ConnectionAbortedError', 'ConnectionRefusedError', 'BrokenPipeError',
        'TimeoutError', 'SSLEOFError', 'IncompleteRead', 'RemoteDisconnected', 'gaierror'}


def check_day(root, date, cell):
    report = check_raw(root, date, cell)
    own = Path(root)/PREFIX
    cohort = load(own/'resume2-cohort.json')
    require(date in cohort['dates'], 'date outside continuation cohort')
    directory = own/'bulk-artifacts'/date
    attempts = directory.with_name(date+'-attempts')
    require(not attempts.is_symlink(), 'symlink attempt directory')
    manifest_path = attempts/'manifest.json'
    require(digest(manifest_path.read_bytes()) == cell['attempts_manifest_sha256'], 'attempt manifest hash')
    manifest = load(manifest_path)
    require(manifest['date'] == date and manifest['max_attempts'] == 4 and
            manifest['delays_seconds'] == [5, 15, 45], 'attempt policy binding')
    entries = manifest['files']
    names = [entry['path'] for entry in entries]
    require(len(names) == len(set(names)) and set(names)|{'manifest.json'} ==
            {p.name for p in attempts.iterdir()}, 'attempt member denominator')
    for entry in entries:
        name = entry['path']
        require(Path(name).name == name and name not in {'.', '..'}, 'unsafe attempt path')
        path = attempts/name
        require(path.is_file() and not path.is_symlink(), 'nonregular attempt member')
        require(path.stat().st_size == entry['bytes'] and digest(path.read_bytes()) == entry['sha256'],
                'attempt member hash/size')
    actual = receipts(attempts)
    selected = receipts(directory)
    require(len(actual) == manifest['requests'] == cell['actual_network_requests'] <= 1164,
            'physical request denominator')
    require(sum(r['bytes'] for r, _ in actual) == manifest['received_bytes'] ==
            cell['actual_network_received_bytes'] <= 1088*1024**2, 'physical byte denominator')
    require(all(r['bytes'] <= 32*1024**2+1 and r['blob']['stored_bytes'] <= 33*1024**2
                for r, _ in actual), 'physical individual bound')
    require(manifest['denied'] == any(r['status'] in (401, 403, 429) for r, _ in actual), 'denial binding')
    prefix = cohort['prefixes'].get(date)
    reused = cell['reused_requests']
    require(type(reused) is int and 0 <= reused <= len(selected), 'prefix count')
    reused_bytes = 0
    if reused:
        require(prefix is not None and reused == prefix['receipt_count'], 'frozen prefix denominator')
        for entry in prefix['files']:
            require(Path(entry['path']).name == entry['path'], 'unsafe prefix path')
            raw = (directory/entry['path']).read_bytes()
            require(len(raw) == entry['bytes'] and digest(raw) == entry['sha256'], 'frozen prefix changed')
        for record, _ in selected[:reused]:
            require(record['status'] in (200, 206) and not record.get('error'), 'failed prefix reused')
            reused_bytes += record['bytes']
    elif cell['status'] == 'complete':
        require(prefix is None, 'successful prefix omitted')
    require(reused_bytes == cell['reused_received_bytes'], 'reused bytes')
    require(cell['logical_requests'] == cell['requests'] and
            cell['logical_received_bytes'] == cell['received_bytes'], 'logical counters')
    mappings = sorted(attempts.glob('mapping-*.json'))
    require(len(mappings) == len(actual), 'attempt mapping denominator')
    groups = {}
    last_logical = reused
    for index, ((record, _), mapping_path) in enumerate(zip(actual, mappings), 1):
        require(mapping_path.name == f'mapping-{index:04d}.json', 'mapping sequence')
        mapping = load(mapping_path)
        require(mapping['physical_request'] == index, 'physical mapping identity')
        number, attempt = mapping['logical_request'], mapping['attempt']
        require(type(number) is int and type(attempt) is int and 1 <= attempt <= 4, 'attempt index')
        if number != last_logical:
            require(number == last_logical+1 and attempt == 1, 'logical mapping order')
            if last_logical in groups:
                previous = groups[last_logical][-1][1]
                require(not previous.get('error') and previous['status'] in (200, 206), 'continued after failed logical request')
            last_logical = number
        group = groups.setdefault(number, [])
        require(attempt == len(group)+1, 'retry sequence')
        require(mapping['delay_seconds'] == [0, 5, 15, 45][attempt-1], 'retry delay')
        if group:
            previous = group[-1][1]
            require(transport(previous), 'retry after deterministic failure')
            require(record['url'] == previous['url'] and record['request_headers'] == previous['request_headers'],
                    'retry identity changed')
        group.append((index, record))
    require(set(groups) == set(range(reused+1, len(selected)+1)), 'selected/physical logical denominator')
    for number, group in groups.items():
        index, record = group[-1]
        projected = copy.deepcopy(record)
        projected['request_number'] = number
        projected['blob']['path'] = f'request-{number:04d}.body.zst'
        require(projected == selected[number-1][0], 'selected receipt differs from final attempt')
        physical_body = attempts/record['blob']['path']
        selected_body = directory/projected['blob']['path']
        require(os.path.samefile(physical_body, selected_body), 'selected body is not bound hardlink')
        if transport(record):
            require(len(group) == 4 and cell['status'] == 'unavailable' and
                    'transport retries exhausted' in (cell['stopped'] or ''), 'transport exhaustion stop missing')
    inodes = {}
    metadata = 0
    for parent in (directory, attempts):
        for path in parent.iterdir():
            info = path.stat()
            if path.suffix == '.zst':
                inodes[(info.st_dev, info.st_ino)] = info.st_size
            else:
                fragment = max(4096, os.statvfs(path).f_frsize)
                metadata += max(info.st_blocks*512, ((info.st_size+fragment-1)//fragment)*fragment)
    require(sum(inodes.values()) == cell['retained_raw_bytes'], 'unique inode raw accounting')
    require(metadata == cell['retained_metadata_allocated_bytes'], 'physical metadata accounting')
    report.update(actual_network_requests=len(actual), actual_network_received_bytes=cell['actual_network_received_bytes'],
                  reused_requests=reused, attempts_verified=True)
    return report
