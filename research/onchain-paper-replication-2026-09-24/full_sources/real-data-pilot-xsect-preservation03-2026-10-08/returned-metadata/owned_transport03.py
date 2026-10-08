"""Finite Linux subprocess ownership for the one-use xsect preservation driver."""
import ctypes
import errno
import os
from pathlib import Path
import select
import signal
import subprocess
import time


def _subreaper():
    # This driver must be a dedicated process, never a shared application host.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), 'cannot enable backup child subreaper')
    value = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(value), 0, 0, 0) != 0 or value.value != 1:
        raise RuntimeError('backup child subreaper readback failed')


def _cleanup(proc):
    """Kill only this new session's process group and reap its adopted children."""
    began = time.monotonic()
    prior = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
    result = None
    try:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        # Reap Popen's direct child first, preserving its actual return code.
        proc.wait(timeout=max(.001, 10 - (time.monotonic() - began)))
        adopted = []
        while True:
            while True:
                try:
                    pid, status = os.waitpid(-proc.pid, os.WNOHANG)
                except ChildProcessError:
                    break
                if pid == 0:
                    break
                adopted.append({'pid': pid, 'wait_status': status})
            try:
                os.killpg(proc.pid, 0)
            except ProcessLookupError:
                result = {'direct_child_reaped': True, 'owned_group_absent': True,
                          'adopted_children_reaped': adopted,
                          'cleanup_seconds': time.monotonic() - began}
                return result
            if time.monotonic() - began >= 10:
                raise TimeoutError('owned transport group did not disappear in10seconds')
            time.sleep(.01)
    finally:
        # A pending outer alarm is delivered after owned cleanup, not during it.
        signal.pthread_sigmask(signal.SIG_SETMASK, prior)


def _execute(command, *, destination=None, expected_bytes=None,
             max_seconds=1800, bytes_per_second=None):
    began = time.monotonic()
    received = seen = 0
    tail = b''
    stdout_body = bytearray()
    proc = None
    primary = None
    cleanup = None
    stream = None
    try:
        if destination is not None:
            stream = Path(destination).open('xb')
        proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        streams = {proc.stdout.fileno(): 'stdout', proc.stderr.fileno(): 'stderr'}
        for fd in streams:
            os.set_blocking(fd, False)
        while streams:
            remaining = max_seconds - (time.monotonic() - began)
            if remaining <= 0:
                raise TimeoutError('bounded transport deadline')
            ready, _, _ = select.select(list(streams), [], [], min(.1, remaining))
            for fd in ready:
                chunk = os.read(fd, 65536)
                if not chunk:
                    del streams[fd]
                    continue
                if streams[fd] == 'stderr':
                    seen += len(chunk)
                    tail = (tail + chunk)[-16384:]
                else:
                    received += len(chunk)
                    limit = 65536 if destination is None else expected_bytes
                    if received > limit:
                        raise ValueError('transport stdout exceeds expected bound')
                    if stream is None:
                        stdout_body.extend(chunk)
                    else:
                        stream.write(chunk)
                        delay = received / bytes_per_second - (time.monotonic() - began)
                        if delay > 0:
                            time.sleep(min(delay, remaining))
            # A exited direct child must not leave inherited pipes keeping a
            # descendant alive until the transport timeout. Drain queued data
            # before cleanup; no-writer parent exit is the end of this command.
            if not ready and proc.poll() is not None:
                break
        remaining = max_seconds - (time.monotonic() - began)
        if remaining <= 0:
            raise TimeoutError('bounded transport deadline')
        code = proc.wait(timeout=remaining)
        if code:
            if destination is None:
                raise subprocess.CalledProcessError(code, command,
                    output=bytes(stdout_body), stderr=tail)
            raise RuntimeError('bounded download process failed; see transport receipt')
        if destination is not None and received != expected_bytes:
            raise ValueError('download size shorter than expected bytes')
        if stream is not None:
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException as error:
        primary = error
    finally:
        if proc is not None:
            try:
                cleanup = _cleanup(proc)
            except BaseException as error:
                if primary is None:
                    primary = error
                else:
                    primary.add_note('Owned transport cleanup: ' + repr(error))
            for pipe in (proc.stdout, proc.stderr):
                try:
                    pipe.close()
                except BaseException as error:
                    if primary is None:
                        primary = error
                    else:
                        primary.add_note('Owned transport pipe close: ' + repr(error))
        if stream is not None:
            try:
                stream.close()
            except BaseException as error:
                if primary is None:
                    primary = error
                else:
                    primary.add_note('Owned destination close: ' + repr(error))
    receipt = {'status': 'failed' if primary else 'complete',
               'error_type': type(primary).__name__ if primary else None,
               'pid': proc.pid if proc else None,
               'returncode': proc.returncode if proc else None,
               'received_bytes': received, 'expected_bytes': expected_bytes,
               'elapsed_seconds': time.monotonic() - began,
               'stderr_bytes_seen': seen, 'stderr_truncated': seen > len(tail),
               'stderr_tail': tail.decode('utf-8', errors='replace')}
    if cleanup is not None:
        receipt['owned_cleanup'] = cleanup
    return bytes(stdout_body), receipt, primary, tail


def install(scope):
    """Patch only run/receiver in the exact legacy extraction's shared namespace."""
    _subreaper()
    immutable = scope['_immutable']
    transport = scope['Transport']

    def receive_diagnostic(command, destination, *, expected_bytes,
                           max_seconds, bytes_per_second):
        if expected_bytes < 0 or max_seconds <= 0 or bytes_per_second <= 0:
            raise ValueError('invalid receive bounds')
        receipt_path = Path(str(destination) + '.transport.json')
        if receipt_path.exists():
            raise FileExistsError(receipt_path)
        _, receipt, primary, _ = _execute(command, destination=destination,
            expected_bytes=expected_bytes, max_seconds=max_seconds,
            bytes_per_second=bytes_per_second)
        try:
            immutable(receipt_path, receipt)
        except BaseException as error:
            if primary is None:
                raise
            primary.add_note('Transport receipt publication: ' + repr(error))
        if primary is not None:
            raise primary

    run_number = 0

    def run(self, args):
        nonlocal run_number
        import hashlib
        run_number += 1
        number = run_number
        stdout, receipt, primary, tail = _execute(args)
        receipt = dict(receipt, stdout_bytes=len(stdout),
                       stdout_sha256=hashlib.sha256(stdout).hexdigest())
        try:
            immutable(Path(scope['HERE']) / f'transport-run-{number:04d}.json', receipt)
        except BaseException as error:
            if primary is None:
                raise
            primary.add_note('Transport run receipt publication: ' + repr(error))
        if primary is not None:
            raise primary
        return subprocess.CompletedProcess(args, receipt['returncode'], stdout,
                                           tail)

    scope['receive_diagnostic'] = receive_diagnostic
    transport.run = run
    return transport
