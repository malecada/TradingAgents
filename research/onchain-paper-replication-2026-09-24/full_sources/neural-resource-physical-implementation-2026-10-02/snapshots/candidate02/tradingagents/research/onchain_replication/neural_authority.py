"""Bounded live-parent authority for the explicit neural physical route.

Trusted admitted local processes only; no hostile memory/kernel guarantee. No
secret or disk authority fallback. The original parent performs owned births.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import socket
import struct
import threading
import time
import uuid


def process_start(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]


def _receive(sock,maximum):
    deadline=time.monotonic()+2
    def exact(count):
        pieces=[]
        while count:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('physical authority bounded read timeout')
            sock.settimeout(remaining);value=sock.recv(count)
            if not value:raise RuntimeError('physical parent authority response truncated')
            pieces.append(value);count-=len(value)
        return b''.join(pieces)
    size=struct.unpack('!I',exact(4))[0]
    if size>maximum:raise ValueError('physical authority message exceeds bounded extent')
    return json.loads(exact(size))


def _send(sock,value,maximum):
    from .neural_physical import _bounded_encode
    data=_bounded_encode(value,maximum)
    sock.sendall(struct.pack('!I',len(data))+data)


def _close_socket(sock,primary=None):
    from .neural_physical import PhysicalCleanupFailure
    try:sock.close()
    except BaseException as error:
        if primary is not None:
            primary.add_note('physical socket close uncertainty: '+repr(error))
            if not isinstance(primary,Exception) or isinstance(primary,MemoryError):raise primary
        if not isinstance(error,Exception) or isinstance(error,MemoryError):raise error from primary
        failure=PhysicalCleanupFailure('physical owned socket close uncertain; no close retry')
        failure.add_note(repr(error));raise failure from primary


@contextmanager
def _owned_socket(sock):
    primary=None
    try:yield sock
    except BaseException as error:primary=error;raise
    finally:_close_socket(sock,primary)


class ParentAuthority:
    def __init__(self,maximum,handler):
        self.maximum=maximum;self.handler=handler;self.failure=None;self.stopping=threading.Event()
        self.identity={'pid':os.getpid(),'start_ticks':process_start(os.getpid()),'uid':os.getuid(),'address':'neural-physical-'+uuid.uuid4().hex}
        self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.closed=False;self.thread=None
        try:
            self.socket.bind('\0'+self.identity['address']);self.socket.listen(4);self.socket.settimeout(.2)
            self.thread=threading.Thread(target=self._serve,name='neural-physical-authority',daemon=True)
            self.thread.start()
        except BaseException as primary:
            self.stopping.set();self.closed=True
            _close_socket(self.socket,primary)
            raise

    def _serve(self):
        while not self.stopping.is_set():
            try:client,_=self.socket.accept()
            except socket.timeout:continue
            except OSError:
                if not self.stopping.is_set():self.failure=RuntimeError('authority accept failed')
                return
            try:
                with _owned_socket(client):
                    client.settimeout(2)
                    _,uid,_=struct.unpack('3i',client.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
                    if uid!=self.identity['uid']:raise ValueError('physical authority peer UID differs')
                    request=_receive(client,self.maximum)
                    if self.failure is not None:raise RuntimeError('physical original parent authority failed: '+str(self.failure)[:512])
                    try:result=self.handler(request)
                    except BaseException as error:
                        # A partially completed owned transition is never rebaselined/retried.
                        self.failure=error
                        _send(client,{'error':type(error).__name__+': '+str(error)[:512]},self.maximum)
                    else:_send(client,{'result':result},self.maximum)
            except BaseException as error:
                if self.failure is None:self.failure=error
                else:self.failure.add_note('authority transport cleanup: '+repr(error)[:512])

    def close(self):
        if not self.closed:
            primary=self.failure;self.stopping.set();self.closed=True
            try:self.thread.join(timeout=3)
            except BaseException as error:
                if primary is None:primary=error
                else:primary.add_note('physical authority thread join failed: '+repr(error))
            # The handler may have failed after shutdown began but before join returned.
            joined=self.failure
            if joined is not None and joined is not primary:
                if primary is None:primary=joined
                elif isinstance(primary,Exception) and (not isinstance(joined,Exception) or isinstance(joined,MemoryError)):
                    joined.add_note('earlier authority shutdown failure: '+repr(primary));joined.__cause__=primary;primary=joined
                else:primary.add_note('in-flight authority failure: '+repr(joined))
            if self.thread.is_alive():
                error=RuntimeError('physical parent authority thread did not stop')
                if primary is None:primary=error
                else:primary.add_note(str(error))
            try:_close_socket(self.socket,primary)
            except BaseException as error:primary=error
            self.failure=primary
        if self.failure is not None:
            if not isinstance(self.failure,Exception) or isinstance(self.failure,MemoryError):raise self.failure
            raise RuntimeError('physical parent authority failed: '+str(self.failure)[:512]) from self.failure


def request(identity,anchor_hash,value,maximum):
    try:
        if process_start(identity['pid'])!=identity['start_ticks']:raise ValueError('physical original parent process replaced')
        with _owned_socket(socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)) as client:
            client.settimeout(2);client.connect('\0'+identity['address'])
            pid,uid,_=struct.unpack('3i',client.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
            if pid!=identity['pid'] or uid!=identity['uid'] or process_start(pid)!=identity['start_ticks']:
                raise ValueError('physical original parent authority peer differs')
            _send(client,{'anchor_sha256':anchor_hash,**value},maximum)
            response=_receive(client,maximum)
        if 'error' in response:raise RuntimeError('physical parent authority refused: '+response['error'])
        return response['result']
    except (OSError,KeyError,json.JSONDecodeError) as error:
        raise RuntimeError('physical original parent authority unavailable; no disk fallback') from error
