import unittest
import os

if __name__ == "__main__":
  suite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
  unittest.TextTestRunner().run(suite)
