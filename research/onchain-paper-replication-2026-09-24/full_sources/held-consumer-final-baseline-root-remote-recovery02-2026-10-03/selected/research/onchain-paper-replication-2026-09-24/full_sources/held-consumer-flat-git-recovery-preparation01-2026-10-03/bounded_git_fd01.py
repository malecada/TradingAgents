"""Exact accepted stdlib Git cleanup/framing helper subset; no authority."""
import os,selectors,subprocess,time
class CleanupFailure(BaseException):pass

def require(v,m):
    if not v:raise ValueError(m)

def fatal(e):return isinstance(e,MemoryError) or (not isinstance(e,Exception) and not isinstance(e,CleanupFailure))

def cleanup(actions,primary=None):
    failures=[]
    for action in actions:
        try:action()
        except BaseException as error:failures.append(error)
    errors=([primary] if primary is not None else [])+failures
    chosen=next((e for e in errors if fatal(e)),None)
    if chosen is not None:raise chosen
    if failures:raise CleanupFailure('owned read/process cleanup uncertain') from (primary or failures[0])
    if primary is not None:raise primary

def git(root,args,request=b'',cap=8*1024**2):
    """Fresh offline Git process; bounded pipes/cleanup, no fetch or mutation."""
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'}
    require(len(request)<=65536,'Git request bound');child=None;poll=None;primary=None;out=bytearray();err=bytearray();offset=0;stdin_close_attempted=False
    try:
        child=subprocess.Popen(['git','-c','protocol.allow=never',*args],cwd='/proc/self/fd/'+str(root),pass_fds=(root,),env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        poll=selectors.DefaultSelector()
        for stream,event in ((child.stdin,selectors.EVENT_WRITE),(child.stdout,selectors.EVENT_READ),(child.stderr,selectors.EVENT_READ)):os.set_blocking(stream.fileno(),False);poll.register(stream,event)
        deadline=time.monotonic()+10
        while poll.get_map():
            require(time.monotonic()<deadline,'Git bounded deadline')
            for key,event in poll.select(.1):
                if key.fileobj is child.stdin:
                    if offset<len(request):offset+=os.write(child.stdin.fileno(),request[offset:offset+16384])
                    else:
                        poll.unregister(child.stdin);stdin_close_attempted=True;child.stdin.close()
                else:
                    data=os.read(key.fileobj.fileno(),65536)
                    if not data:poll.unregister(key.fileobj)
                    else:
                        buf=out if key.fileobj is child.stdout else err;buf.extend(data);require(len(buf)<=(cap if buf is out else 65536),'Git response bound')
        require(child.wait(timeout=1)==0,'Git source lookup failed')
    except BaseException as error:primary=error
    actions=[]
    if child is not None:
        # Never poll or inspect pipe.closed outside independently protected actions.
        # Popen.kill is harmless after an already reaped child; its own failures
        # cannot suppress the independent wait/pipe cleanup or prior fatal.
        actions.extend([child.kill,lambda:child.wait(timeout=5)])
        actions.extend(stream.close for stream in ((() if stdin_close_attempted else (child.stdin,))+(child.stdout,child.stderr)))
    if poll is not None:actions.append(poll.close)
    cleanup(actions,primary);return bytes(out)
