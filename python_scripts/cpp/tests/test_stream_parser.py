import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from stream_parser import *

class TestStreamParserTextSpan(unittest.TestCase):
  def setUp(self):
    pass

  def test_basicInit(self):
    x = TextSpan(Cursor(0, 0), Cursor(0, 1))
    self.assertEqual(x.start, Cursor(0, 0))
    self.assertEqual(x.end, Cursor(0, 1))

  def test_reverseCursors(self):
    x = TextSpan(Cursor(0, 20), Cursor(0, 5))
    self.assertEqual(x.start, Cursor(0, 5))
    self.assertEqual(x.end, Cursor(0, 20))

  def test_inclusive(self):
    x = TextSpan(Cursor(0, 1), Cursor(0, 5), inclusive = True)
    self.assertEqual(x.start, Cursor(0, 1))
    self.assertEqual(x.end, Cursor(0, 6))

  def test_inclusiveReverseCursors(self):
    x = TextSpan(Cursor(0, 5), Cursor(0, 1), inclusive = True)
    self.assertEqual(x.start, Cursor(0, 1))
    self.assertEqual(x.end, Cursor(0, 6))

  def test_forIteration(self):
    text = "1" * 20
    text_buffer = Buffer(text)
    x = TextSpan(Cursor(0, 1), Cursor(0, 10))
    index = 1
    for c in x.iterate(text_buffer):
      self.assertEqual(Cursor(0, index), c)
      index += 1
    self.assertEqual(index, 10)

  def test_forIterationMultiline(self):
    text = "12345\n1234567890\n123"
    text_buffer = Buffer(text)
    x = TextSpan(Cursor(0, 0), Cursor(2, 3))
    index = 0
    row = 0
    line_len = [6, 11, 4]
    for c in x.iterate(text_buffer):
      self.assertEqual(Cursor(row, index), c)
      index += 1
      if line_len[row] == index:
        row += 1
        index = 0
    self.assertEqual(index, 3)
    self.assertEqual(row, 2)

  def test_newCursorCopy(self):
    a = Cursor(0, 1)
    b = Cursor(0, 5)
    x = TextSpan(a, b, inclusive = True)
    self.assertEqual(x.start, Cursor(0, 1))
    self.assertEqual(x.end, Cursor(0, 6))
    self.assertEqual(a, Cursor(0, 1))
    self.assertEqual(b, Cursor(0, 5))
    a.column = 3
    b.column = 10
    self.assertEqual(x.start, Cursor(0, 1))
    self.assertEqual(x.end, Cursor(0, 6))
    self.assertEqual(a, Cursor(0, 3))
    self.assertEqual(b, Cursor(0, 10))

if __name__ == '__main__':
  unittest.main()
  # unittest.main(defaultTest="StreamParserTextSpan.")
