from pathlib import Path
import json,hashlib,ast
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'financial-wrapper-compatibility-preclaim-correction02-2026-10-04';D.mkdir(mode=0o700);A=F/'financial-wrapper-compatibility-preclaim-source01-2026-10-04';V=F/'financial-wrapper-compatibility-preclaim-source-review01-2026-10-04';old=(A/'preclaim01.py').read_text()
a="        self.cache={}\n";b="        self.cache={}\n        self.verified_signatures={}\n";c="            return bytes(raw)\n";d="            self.verified_signatures[path]=signature(first)\n            return bytes(raw)\n";e="        self.tick()\n    def reference(self,ref):";f="""        # No descriptor cleanup remains after this finite whole-reader rejoin.
        # These metadata samples are tied to the preceding exact byte rereads;
        # they do not imply atomicity, writer exclusion or absence of ABA.
        for path in self.cache:
            self.tick()
            require(path.resolve(strict=True)==path,'preclaim final origin differs')
            last=path.lstat()
            signature=(last.st_dev,last.st_ino,last.st_mode,last.st_nlink,last.st_size,last.st_mtime_ns,last.st_ctime_ns)
            require(stat.S_ISREG(last.st_mode) and signature==self.verified_signatures[path],'preclaim evidence changed before final whole-reader join')
        self.tick()
    def reference(self,ref):"""
assert old.count(a)==old.count(c)==old.count(e)==1;new=old.replace(a,b).replace(c,d).replace(e,f);inverse=new.replace(b,a).replace(d,c).replace(f,e);assert inverse==old
(D/'preclaim01.py').write_text(new);(D/'ORIGINAL_preclaim01.py').write_text(old);(D/'ORIGINAL_PC1_WITNESS01.json').write_bytes((V/'WITNESS01.json').read_bytes());(D/'ORIGINAL_PC1_MACHINE01.json').write_bytes((V/'MACHINE01.json').read_bytes())
# Exact three edited methods, every other AST member unchanged.
x=ast.parse(old);y=ast.parse(new);cx=next(n for n in x.body if isinstance(n,ast.ClassDef) and n.name=='Reader');cy=next(n for n in y.body if isinstance(n,ast.ClassDef) and n.name=='Reader');changes=[n.name for n in cx.body if isinstance(n,ast.FunctionDef) and ast.dump(n,include_attributes=False)!=ast.dump(next(k for k in cy.body if isinstance(k,ast.FunctionDef) and k.name==n.name),include_attributes=False)];assert changes==['__init__','_physical','finish'];
for i,n in enumerate(x.body):
 if isinstance(n,ast.ClassDef) and n.name=='Reader':continue
 assert ast.dump(n,include_attributes=False)==ast.dump(y.body[i],include_attributes=False)
(D/'SOURCE_INVERSE01.json').write_text(json.dumps({'schema_version':1,'original_sha256':hashlib.sha256(old.encode()).hexdigest(),'new_sha256':hashlib.sha256(new.encode()).hexdigest(),'complete_three_edit_literal_inverse':True,'changed_methods':changes,'all_other_ast_unchanged':True,'limits_unchanged':{'FILE':4194304,'TOTAL':8388608,'SECONDS':120},'Root_registration_or_native_release':None,'qualification':'Final sampled metadata rejoin after all real read descriptor cleanup, tied to exact reread samples. No continuous atomic writer exclusion or ABA assurance; no source/gate/admission or genuine missing recovery/COMPLETE body supplied.'},indent=2)+'\n');print(hashlib.sha256(new.encode()).hexdigest())
