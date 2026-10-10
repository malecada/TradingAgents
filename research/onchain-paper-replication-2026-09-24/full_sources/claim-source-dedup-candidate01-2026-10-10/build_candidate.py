from pathlib import Path
import difflib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
original=(ROOT/'tradingagents/research/verify.py').read_text()
(HERE/'baseline_verify.py').write_text(original)
s=original.replace('def _git_transport(root, requests, expression=None):','def _git_transport(root, requests, expression=None, *, _source_check=False, _source_deadline=None):',1)
needle="    command = ['git', 'cat-file', '--batch'] if expression is None else ['git', 'cat-file', 'blob', expression]"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n    if _source_check:\n        if expression is not None:raise ValueError('source extent query cannot use argv expression')\n        command = ['git', 'cat-file', '--batch-check']",1)
needle='    deadline = time.monotonic() + _GIT_SECONDS'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n    if _source_deadline is not None:deadline = min(deadline, _source_deadline)',1)
needle='def _verify_sources(root, pinned, commits):'
helper='''def _verify_source_flush(root, requests, rows):
    """Same-flush duplicate transport only; original logical comparison order.

    Malformed/unavailable/oversize/non-UTF8 domains use the old body route.
    Header and selected body children share the original ten-second budget;
    this adds no per-phase time allowance. No state survives this call.
    """
    import time
    deadline = time.monotonic() + _GIT_SECONDS
    def original():
        return _verify_batch(_git_transport(root, requests, _source_deadline=deadline), rows)
    # Keep old line/argv routing literal. No optimization for unusual encoding.
    try:
        requests.decode('utf-8', 'strict')
    except UnicodeDecodeError:
        return original()
    if len(rows)<2:return original()
    try:
        metadata = _git_transport(root, requests, _source_check=True, _source_deadline=deadline)
    except Exception as error:
        # Ordinary preflight failures cannot mask an earlier original hash
        # failure. Fatal/ambiguous-cleanup exceptions are never retried.
        if isinstance(error, MemoryError):raise
        return original()
    headers = metadata.splitlines(keepends=True)
    if len(headers)!=len(rows):return original()
    extents=[];logical_size=0
    for header in headers:
        match=re.fullmatch(rb'([0-9a-f]{40}) blob (0|[1-9][0-9]*)\\n',header)
        if match is None or len(header)>128:return original()
        extent=(match[1],int(match[2]))
        if extent[1]>_GIT_BODY:return original()
        extents.append(extent)
        logical_size+=len(header)+extent[1]+1
    # Duplicate bodies count against exactly the old aggregate response cap.
    # Old transport errors precede ALL old expected-hash comparisons.
    if logical_size>_GIT_BODY+128*_GIT_PARTS:return original()
    unique=list(dict.fromkeys(extents))
    unique_size=sum(len(oid)+len(str(size))+8+size for oid,size in unique)
    if len(unique)==len(extents) or len(metadata)+unique_size>=logical_size:return original()
    try:
        raw=_git_transport(root,b''.join(oid+b'\\n' for oid,_ in unique),_source_deadline=deadline)
    except Exception as error:
        if isinstance(error, MemoryError):raise
        return original()
    # Any new body framing/identity failure goes back through the old parser.
    # Never report a later extent failure ahead of an earlier original hash.
    bodies={};offset=0
    for oid,size in unique:
        header=oid+b' blob '+str(size).encode('ascii')+b'\\n'
        if raw[offset:offset+len(header)]!=header:return original()
        start=offset+len(header);end=start+size
        if raw[end:end+1]!=b'\\n':return original()
        bodies[(oid,size)]=memoryview(raw)[start:end]
        offset=end+1
    if offset!=len(raw):return original()
    # Recreate the original bounded logical response, including duplicates,
    # and use the unchanged original parser/hash comparisons for EVERY row.
    logical=bytearray()
    for header,extent in zip(headers,extents,strict=True):
        logical.extend(header);logical.extend(bodies[extent]);logical.extend(b'\\n')
    if len(logical)!=logical_size:raise ValueError('source logical response extent differs')
    if time.monotonic()>=deadline:
        raise subprocess.TimeoutExpired(['git','cat-file','--batch'],_GIT_SECONDS)
    return _verify_batch(bytes(logical),rows)


'''
assert s.count(needle)==1
s=s.replace(needle,helper+needle,1)
needle='            _verify_batch(_git_transport(root,bytes(requests)), rows)'
assert s.count(needle)==1
s=s.replace(needle,'            _verify_source_flush(root,bytes(requests),rows)',1)
(HERE/'verify.py').write_text(s)
(HERE/'verify.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='baseline_verify.py',tofile='verify.py')))
(HERE/'verify.inverse.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),original.splitlines(True),fromfile='verify.py',tofile='baseline_verify.py')))
print('candidate built')
