import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from text_object_type import *

import logging

class TestTextObjectType(unittest.TestCase):
  def setUp(self):
    pass

  def runTest(self, cursor, text, expected_span):
    result = main(cursor, Buffer(text))

    self.assertEqual(result, expected_span)
  def test_typeInt(self):
    self.runTest(Cursor(0, 2), "int test", TextSpan(Cursor(0, 0), Cursor(0, 3)))

  def test_typeStr(self):
    self.runTest(Cursor(0, 2), "std::string test", TextSpan(Cursor(0, 0), Cursor(0, 11)))

  def test_map(self):
    self.runTest(Cursor(0, 2), "std::map<int, int> test", TextSpan(Cursor(0, 0), Cursor(0, 18)))

  def test_mapInnerType(self):
    self.runTest(Cursor(0, 11), "std::map<int, int> test", TextSpan(Cursor(0, 9), Cursor(0, 12)))

  def test_nestedTemplates(self):
    self.runTest(Cursor(0, 2), "std::map<pair<a, b>, pair<a, pair<d, e>, c>> test", TextSpan(Cursor(0, 0), Cursor(0, 44)))

  def test_reference(self):
    self.runTest(Cursor(0, 2), "SomeType& test", TextSpan(Cursor(0, 0), Cursor(0, 8)))

  def test_const(self):
    self.runTest(Cursor(0, 9), "const SomeType& test", TextSpan(Cursor(0, 6), Cursor(0, 14)))

  def test_defaultNamespaceConst(self):
    self.runTest(Cursor(0, 9), "const ::SomeType& test", TextSpan(Cursor(0, 6), Cursor(0, 16)))

  def test_pointerInTemplate(self):
    self.runTest(Cursor(0, 3), "std::pair<A*, B*> test", TextSpan(Cursor(0, 0), Cursor(0, 17)))

    # singleColon
    # : Testing test

  def test_equals(self):
    self.runTest(Cursor(0, 11), "auto var = SomeType()", TextSpan(Cursor(0, 11), Cursor(0, 19)))

  def test_underscore(self):
    self.runTest(Cursor(0, 2), "some_type test", TextSpan(Cursor(0, 0), Cursor(0, 9)))

  def test_multiline(self):
    self.runTest(Cursor(0, 2), "std::string\ntest", TextSpan(Cursor(0, 0), Cursor(0, 11)))

if __name__ == '__main__':
  logging.getLogger("stream_parser.Parser").setLevel(logging.DEBUG)
  # logging.getLogger("stream_parser.Lexer").setLevel(logging.WARNING)
  unittest.main()
  # unittest.main(defaultTest="TestTextObjectType.test_pointerInTemplate")
