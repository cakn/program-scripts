import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cpp_parser

class TestLexer(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cpp_parser.build()

  def setUp(self):
    pass

  def runTest(self, data, expected_list):
    expected_list.append('EOF')

    lexer = cpp_parser.lexer
    lexer.input(data)
    length = 0
    token = lexer.token()
    while token:
      self.assertEqual(token.type, expected_list[length])
      length += 1
      token = lexer.token()
    # Need to add iterator for proxy lexer
    # for token, expected_token in zip(lexer, expected_list):
      # self.assertEqual(token.type, expected_token)
      # length += 1
    self.assertEqual(len(expected_list), length)

  def test_intType(self):
    data = 'int test_;'
    expected_list = ['ID', 'ID', ';']
    self.runTest(data, expected_list)

  def test_charType(self):
    data = 'char test_;'
    expected_list = ['ID', 'ID', ';']
    self.runTest(data, expected_list)

  def test_floatType(self):
    data = 'float test_;'
    expected_list = ['ID', 'ID', ';']
    self.runTest(data, expected_list)

  def test_namespaceType(self):
    data = 'std::string str_;'
    expected_list = ['ID', 'SCOPE', 'ID', 'ID', ';']
    self.runTest(data, expected_list)

  def test_templateType(self):
    data = 'vector<int> str_;'
    expected_list = ['ID', 'LANGLED', 'ID', 'RANGLED', 'ID', ';']
    self.runTest(data, expected_list)

if __name__ == '__main__':
  unittest.main()
