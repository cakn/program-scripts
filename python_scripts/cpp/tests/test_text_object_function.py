import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from text_object_function import *

import logging

class TestTextObjectFunction(unittest.TestCase):
  def setUp(self):
    pass

  def runTest(self, cursor, text, expected_span):
    result = main(cursor, Buffer(text))

    self.assertEqual(result, expected_span)

  def runTestAll(self, text, expected_span):
    text_buffer = Buffer(text)
    for cursor in expected_span.iterate(text_buffer):
      result = main(cursor, text_buffer)

      self.assertEqual(result, expected_span)

  def test_basicInBlock(self):
    self.runTest(Cursor(0, 14), "int test() { all words; } void main();", TextSpan(Cursor(0, 0), Cursor(0, 25)))

  def test_basicOutOfBlock(self):
    self.runTest(Cursor(0, 2), "int test() { all words; } void main();", TextSpan(Cursor(0, 0), Cursor(0, 25)))

  def test_basicAll(self):
    self.runTestAll("int test() { all words; } void main();", TextSpan(Cursor(0, 0), Cursor(0, 25)))

  def test_nestedBracesBasic(self):
    self.runTest(Cursor(0, 14), "int test() { {all words;} } void main();", TextSpan(Cursor(0, 0), Cursor(0, 27)))
    self.runTestAll("int test() { {all words;} } void main();", TextSpan(Cursor(0, 0), Cursor(0, 27)))

  def test_nestedBracesMany(self):
    self.runTestAll("int test() { {{{all words;}}} } void main();", TextSpan(Cursor(0, 0), Cursor(0, 31)))

  def test_nestedBracesWithStatements(self):
    self.runTest(Cursor(0, 14), "int test() { m t; {all words;} } void main();", TextSpan(Cursor(0, 0), Cursor(0, 32)))
    self.runTestAll("int test() { m t; {all words;} } void main();", TextSpan(Cursor(0, 0), Cursor(0, 32)))

  def test_nestedIf(self):
    self.runTest(Cursor(0, 14), "int test() { if (test) {all words;} } void main();", TextSpan(Cursor(0, 0), Cursor(0, 37)))
    self.runTestAll("int test() { if (test) {all words;} } void main();", TextSpan(Cursor(0, 0), Cursor(0, 37)))

  def test_constReturn(self):
    self.runTest(Cursor(0, 25), "const int& test() { all words; } void main();", TextSpan(Cursor(0, 0), Cursor(0, 32)))
    self.runTestAll("const int& test() { all words; } void main();", TextSpan(Cursor(0, 0), Cursor(0, 32)))

  def test_prevFunctions(self):
    self.runTest(Cursor(0, 44), "void func2() { stuff } const int& test() { all words; } void main();", TextSpan(Cursor(0, 23), Cursor(0, 55)))
    self.runTestAll("void func2() { stuff } const int& test() { all words; } void main();", TextSpan(Cursor(0, 23), Cursor(0, 55)))

  def test_prevLBrace(self):
    self.runTest(Cursor(0, 20), "namespace asdf {  int test() { all words; } } void main();", TextSpan(Cursor(0, 18), Cursor(0, 43)))
    self.runTestAll("namespace asdf {  int test() { all words; } } void main();", TextSpan(Cursor(0, 18), Cursor(0, 43)))

  def test_constMember(self):
    self.runTest(Cursor(0, 2), "int test() const { all words; } void main()", TextSpan(Cursor(0, 0), Cursor(0, 31)))
    self.runTestAll("int test() const { all words; } void main()", TextSpan(Cursor(0, 0), Cursor(0, 31)))

  def test_constMemberNestedBraces(self):
    self.runTest(Cursor(0, 32), "int test() const { if (cond) {all words;} } void main()", TextSpan(Cursor(0, 0), Cursor(0, 43)))
    self.runTestAll("int test() const { if (cond) {all words;} } void main()", TextSpan(Cursor(0, 0), Cursor(0, 43)))

  def test_operatorParens(self):
    self.runTest(Cursor(0, 10), "stuff {} int operator()() { all words; } void main()", TextSpan(Cursor(0, 9), Cursor(0, 40)))
    self.runTestAll("stuff {} int operator()() { all words; } void main()", TextSpan(Cursor(0, 9), Cursor(0, 40)))

  def test_functionNameScoped(self):
    self.runTest(Cursor(0, 10), "stuff {} int Class::func() { all words; } void main()", TextSpan(Cursor(0, 9), Cursor(0, 41)))
    self.runTestAll("stuff {} int Class::func() { all words; } void main()", TextSpan(Cursor(0, 9), Cursor(0, 41)))

  def test_functionNameTemplate(self):
    self.runTest(Cursor(0, 10), "stuff {} int func<int>() { all words; } void main()", TextSpan(Cursor(0, 9), Cursor(0, 39)))
    self.runTestAll("stuff {} int func<int>() { all words; } void main()", TextSpan(Cursor(0, 9), Cursor(0, 39)))

  def test_quotesAfterFunc(self):
    self.runTestAll(""" #include "header" int func() { all words; } void main()""", TextSpan(Cursor(0, 19), Cursor(0, 44)))

  def test_switchStatement(self):
    self.runTestAll("""int func() { switch(value) { case: { stuff; break; } } } void main()""",
        TextSpan(Cursor(0, 0), Cursor(0, 56)))

  def test_newLineAfterParen(self):
    self.runTestAll("""int func() \n{ all words; } void main()""", TextSpan(Cursor(0, 0), Cursor(1, 14)))

  def test_comments(self):
    self.runTestAll("""int func() // comments here \n{ all words; } void main()""",
        TextSpan(Cursor(0, 0), Cursor(1, 14)))

# operator()()
# strings (best effort, assume cursor is outside of the string)
# comments

#possibly no type with ctor
#int test<types>() {}
#int test() { cout << hello >> in; }
#Ctor::Ctor() : words(text) {}
#Ctor::Ctor() : words(text), more(words) {}
# class : public stuff {}
if __name__ == '__main__':
  # logging.getLogger("text_object_function").setLevel(logging.DEBUG)
  # logging.getLogger("stream_parser.Parser").setLevel(logging.DEBUG)
  # logging.getLogger("stream_parser.Lexer").setLevel(logging.WARN)
  unittest.main()
  # unittest.main(defaultTest="TestTextObjectFunction.test_newLineAfterParen")
  # unittest.main(defaultTest="TestTextObjectFunction.test_comments")
