from pathlib import Path
import unittest
class Missing(unittest.TestCase):
 def test_actual_semantic_supplement_exists(self):self.assertTrue((Path(__file__).parent/'held_outcome01.py').exists())
if __name__=='__main__':unittest.main()
