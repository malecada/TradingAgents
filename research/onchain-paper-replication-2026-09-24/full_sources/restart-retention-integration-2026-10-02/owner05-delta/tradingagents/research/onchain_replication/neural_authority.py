"""Bounded live-parent authority for the explicit neural physical route.

Trusted admitted local processes only; no hostile memory/kernel guarantee. No
secret or disk authority fallback. The original parent performs owned births.
"""
import json
import os
from pathlib import Path
import socket
import struct
import threading
import uuid


def process_start(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]


def _receive(sock,maximum):
    def exact(count):
        pieces=[]
        while count:
            value=sock.recv(count)
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


class ParentAuthority:
    def __init__(self,maximum,handler):
        self.maximum=maximum;self.handler=handler;self.failure=None;self.stopping=threading.Event()
        self.identity={'pid':os.getpid(),'start_ticks':process_start(os.getpid()),'uid':os.getuid(),'address':'neural-physical-'+uuid.uuid4().hex}
        self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.socket.bind('\0'+self.identity['address']);self.socket.listen(4);self.socket.settimeout(.2)
        self.thread=threading.Thread(target=self._serve,name='neural-physical-authority',daemon=True)
        self.thread.start()

    def _serve(self):
        while not self.stopping.is_set():
            try:client,_=self.socket.accept()
            except socket.timeout:continue
            except OSError:
                if not self.stopping.is_set():self.failure='authority accept failed'
                return
            try:
                with client:
                    client.settimeout(2)
                    _,uid,_=struct.unpack('3i',client.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
                    if uid!=self.identity['uid']:raise ValueError('physical authority peer UID differs')
                    request=_receive(client,self.maximum)
                    if self.failure is not None:raise RuntimeError('physical original parent authority failed: '+self.failure)
                    try:result=self.handler(request)
                    except BaseException as error:
                        # A partially completed owned transition is never rebaselined/retried.
                        self.failure=type(error).__name__+': '+str(error)[:512]
                        _send(client,{'error':self.failure},self.maximum)
                    else:_send(client,{'result':result},self.maximum)
            except BaseException as error:
                self.failure=type(error).__name__+': '+str(error)[:512]

    def close(self):
        self.stopping.set();self.thread.join(timeout=3)
        self.socket.close()
        if self.thread.is_alive():raise RuntimeError('physical parent authority thread did not stop')
        if self.failure is not None:raise RuntimeError('physical parent authority failed: '+self.failure)


def request(identity,anchor_hash,value,maximum):
    try:
        if process_start(identity['pid'])!=identity['start_ticks']:raise ValueError('physical original parent process replaced')
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
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
