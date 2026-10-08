import contextlib
def same(): return 1
def outer():
 def same(): return 2
 return same
class Owner:
 def same(self): return 3
 @property
 def prop(self): return 4
@contextlib.contextmanager
def held():
 yield 5
@contextlib.contextmanager
def other():
 yield 6

# changed between calls
