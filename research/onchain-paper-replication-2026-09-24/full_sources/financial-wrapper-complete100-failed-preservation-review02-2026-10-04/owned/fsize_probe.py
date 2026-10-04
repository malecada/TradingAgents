import os
p=os.open("limit-negative",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
try:
 os.ftruncate(p,4194305)
except OSError as e:
 print("LIMIT",e.errno)
else:
 raise AssertionError("cap bypass")
finally:
 os.close(p)
