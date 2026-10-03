from pathlib import Path
import hashlib
p=Path(__file__).resolve().parent
b=(p/'verify.baseline01.py').read_text()
assert hashlib.sha256(b.encode()).hexdigest()=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
h='''def _registration_pair(root, claim):
    """Two fresh ordered logical reads; no retained/caller-supplied authority.

    The existing transport bounds the whole pair, including duplicate requests.
    Transport failures can precede first-body comparisons. Second ordinary
    reference/framing errors remain deferred until the original design check.
    """
    source, path = claim['source'], claim['registration']
    if type(source) is not str or type(path) is not str:
        raise ValueError('registration references require plain strings')
    first, request = _source_request(source, path)
    delayed = None
    try:
        design = claim['design_source']
        if type(design) is not str:
            raise ValueError('registration references require plain strings')
        second, other = _source_request(design, path)
    except Exception as error:
        if isinstance(error, MemoryError):
            raise
        delayed = error
        second = other = None
    if delayed is not None or request is None or other is None or len(request)+len(other)>_GIT_REQUEST:
        value = _git_transport(root, b'', first)
        if len(value)>_GIT_BODY:
            raise ValueError('Git blob body ceiling exceeded')
        yield value
        if delayed is not None:
            raise delayed
        value = _git_transport(root, b'', second)
        if len(value)>_GIT_BODY:
            raise ValueError('Git blob body ceiling exceeded')
        yield value
        return
    raw = _git_transport(root, request+other)
    offset = 0
    for index in range(2):
        end = raw.find(b'\\n', offset, offset+128)
        if end<0:
            raise ValueError('Git batch header missing or oversized')
        fields = raw[offset:end].split(b' ')
        if (len(fields)!=3 or re.fullmatch(rb'[0-9a-f]{40}',fields[0]) is None
                or fields[1]!=b'blob' or re.fullmatch(rb'0|[1-9][0-9]*',fields[2]) is None):
            raise ValueError('Git batch object missing, malformed or non-blob')
        size = int(fields[2])
        if size>_GIT_BODY:
            raise ValueError('Git blob body ceiling exceeded')
        offset=end+1
        if offset+size>=len(raw) or raw[offset+size:offset+size+1]!=b'\\n':
            raise ValueError('Git batch short body or terminator')
        value=raw[offset:offset+size];offset+=size+1
        if index==1 and offset!=len(raw):
            raise ValueError('Git batch trailing response')
        yield value


'''
c=b.replace('def verify_claim(',h+'def verify_claim(',1)
c=c.replace('    registration = _blob(root, claim["source"], claim["registration"])','    registration_pair = _registration_pair(root, claim)\n    registration = next(registration_pair)',1)
c=c.replace('if _blob(root, claim["design_source"], claim["registration"]) != registration:', 'if next(registration_pair) != registration:',1)
(p/'verify.candidate01.py').write_text(c)
