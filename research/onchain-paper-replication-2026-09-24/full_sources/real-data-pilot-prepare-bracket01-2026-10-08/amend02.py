from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'compact_mcm.py';s=p.read_text();s=s.replace("        dictionary.check()\n        # Callback-free", "        kernel_pin = tuple((name,id(value),id(getattr(value,'__code__',None)))\n            for name,value in vars(kernel).items())\n        dictionary.check()\n        # Callback-free")
s=s.replace("        dictionary._pins()\n        require(dictionary.owner", "        dictionary._pins()\n        require(tuple((name,id(value),id(getattr(value,'__code__',None)))\n            for name,value in vars(kernel).items()) == kernel_pin,\n            'imported preparation kernel changed')\n        require(dictionary.owner")
p.write_text(s)
p=H/'test01.py';s=p.read_text().replace("'reservation','output')", "'reservation','output','kernel')").replace("     if case=='revoked':", "     if case=='kernel':self.kernel.validate_policy=lambda p,n:None\n     if case=='revoked':")
(H/'test02.py').write_text(s)
