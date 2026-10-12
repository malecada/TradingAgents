"""Exact AST frontier on a temporary FIFO, with a hard250ms alarm."""
from check01 import Fixture,unittest,os
import signal,time
class FIFO(unittest.TestCase):
 def test_fifo_rejected_before_block(self):
  f=Fixture();path=f.root/'research_runs/old000/claim.json';path.unlink();os.mkfifo(path)
  def expired(signum,frame):raise TimeoutError('FIFO blocked before regular-file check')
  old=signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,.25);start=time.monotonic()
  try:
   with self.assertRaisesRegex(ValueError,'regular history body required'):f.env['_history_frontier'](f.root)
   self.assertLess(time.monotonic()-start,.25)
  finally:
   signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old);f.close()
if __name__=='__main__':unittest.main(verbosity=2)
