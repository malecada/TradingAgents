from pathlib import Path
p=Path('tradingagents/research/onchain_replication/neural_physical.py');s=p.read_text().replace('from itertools import chain','import time')
s=s.replace('def _hash(path):return hashlib.sha256(path.read_bytes()).hexdigest()', '''def _read(path,maximum):
    """Nonblocking bounded regular metadata; refuse changed path/extent after read."""
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC);primary=None
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1:raise ValueError('physical control type must be single-link regular file')
        if before.st_size>maximum:raise ValueError('physical control extent exceeds limit')
        parts=[];remaining=before.st_size
        while remaining:
            piece=os.read(fd,min(remaining,65536))
            if not piece:raise ValueError('physical control extent shortened')
            parts.append(piece);remaining-=len(piece)
        if os.read(fd,1):raise ValueError('physical control extent grew')
        after=os.fstat(fd);current=path.lstat()
        key=lambda info:(info.st_dev,info.st_ino,info.st_mode,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_nlink)
        if key(before)!=key(after) or key(after)!=key(current):raise ValueError('physical control changed during read')
        return b''.join(parts)
    except BaseException as error:primary=error;raise
    finally:_close(fd,primary)


def _hash(path,maximum):return hashlib.sha256(_read(path,maximum)).hexdigest()''')
s=s.replace("raw=(base/'physical-anchor.json').read_bytes();anchor=json.loads(raw)","raw=_read(base/'physical-anchor.json',validate(policy)['max_json_bytes']);anchor=json.loads(raw)")
s=s.replace("_hash(self.base/'physical-anchor.json')", "_hash(self.base/'physical-anchor.json',self.policy['max_json_bytes'])")
s=s.replace("def _state(self):return json.loads((self.base/'physical-state.json').read_bytes())", "def _state(self):return json.loads(_read(self.base/'physical-state.json',self.policy['max_json_bytes']))")
s=s.replace("if not path.exists():", "if not os.path.lexists(path):")
a=s.index("            paths=chain((path,),path.rglob('*'))");b=s.index("        claim=self.roots['lifecycle']/'claim.json'",a)
s=s[:a]+'''            begin=time.monotonic()
            flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC
            def account(info):
                nonlocal allocated,logical,files,entries
                entries+=1
                if time.monotonic()-begin>5:raise ValueError('physical scan time limit exceeded')
                if info.st_dev!=self.root.stat().st_dev or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):raise ValueError('physical special entry/device refused')
                allocated+=info.st_blocks*512
                if stat.S_ISREG(info.st_mode):
                    if info.st_nlink!=1:raise ValueError('physical unexpected hardlink')
                    logical+=info.st_size;files+=1
                    if info.st_size>self.policy['max_file_bytes']:raise ValueError('physical file write limit exceeded')
                if entries>self.policy['max_entries']:raise ValueError('physical entry budget exceeded')
            identity=lambda info:[info.st_dev,info.st_ino]
            def visit(fd,depth):
                account(os.fstat(fd))
                with os.scandir(fd) as children:
                    for entry in children:
                        before=os.stat(entry.name,dir_fd=fd,follow_symlinks=False)
                        if stat.S_ISDIR(before.st_mode):
                            if depth>=16:raise ValueError('physical depth envelope exceeded')
                            child=os.open(entry.name,flags,dir_fd=fd);primary=None
                            try:
                                opened=os.fstat(child)
                                if identity(before)!=identity(opened):raise ValueError('physical directory changed during open')
                                visit(child,depth+1)
                                if identity(os.stat(entry.name,dir_fd=fd,follow_symlinks=False))!=identity(opened):raise ValueError('physical directory changed during scan')
                            except BaseException as error:primary=error;raise
                            finally:_close(child,primary)
                        else:account(before)
            fd=os.open(path,flags);primary=None
            try:
                if identity(os.fstat(fd))!=actual:raise ValueError('physical original root replaced while opening')
                visit(fd,0)
                if _identity(path)!=actual or path.resolve()!=path:raise ValueError('physical original root changed during scan')
            except BaseException as error:primary=error;raise
            finally:_close(fd,primary)
''' + s[b:]
s=s.replace("value=json.loads(claim.read_bytes())", "value=json.loads(_read(claim,self.policy['max_json_bytes']))").replace("identity=_hash(claim)","identity=_hash(claim,self.policy['max_json_bytes'])")
s=s.replace("        if 'producer' in state", "        elif state['claim_sha256'] is not None:raise ValueError('physical original claim disappeared')\n        if 'producer' in state")
p.write_text(s)
