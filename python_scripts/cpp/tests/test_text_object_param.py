import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from text_object_param import *

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)

class TestTextObjectParamInner(unittest.TestCase):
  def setUp(self):
    pass

  def runTest(self, cursor, text, expected_span):
    result = main(cursor, Buffer(text), inner=True)

    self.assertEqual(result, expected_span)

  def runTestAll(self, text, expected_span):
    text_buffer = Buffer(text)
    for cursor in expected_span.iterate(text_buffer):
      logger.debug(("runTestAll cursor", cursor))
      result = main(cursor, text_buffer, inner=True)

      self.assertEqual(result, expected_span)

  def test_basic(self):
    self.runTestAll("func(hello)", TextSpan(Cursor(0, 5), Cursor(0, 10)))

  def test_multiParamStart(self):
    self.runTestAll("func(hello, world, testing)", TextSpan(Cursor(0, 5), Cursor(0, 10)))
    #                     ^^^^^

  def test_multiParamMid(self):
    self.runTestAll("func(hello, world, tests)", TextSpan(Cursor(0, 12), Cursor(0, 17)))
    #                            ^^^^^

  def test_multiParamEnd(self):
    self.runTestAll("func(hello, world, tests)", TextSpan(Cursor(0, 19), Cursor(0, 24)))
    #                                   ^^^^^

  def test_onComma(self):
    self.runTest(Cursor(0, 10), "func(hello, world, tests)", TextSpan(Cursor(0, 5), Cursor(0, 10)))
    #                                 ^^^^^
  def test_onLeftParen(self):
    # treat as inner paren and search outwards
    self.runTest(Cursor(0, 4), "func(hello, world, tests)", TextSpan(Cursor(0, 0), Cursor(0, 25)))

  def test_onRightParen(self):
    # treat as inner paren and search outwards
    self.runTest(Cursor(0, 24), "func(hello, world, tests)", TextSpan(Cursor(0, 0), Cursor(0, 25)))

  def test_onSpaceInParam(self):
    self.runTest(Cursor(0, 18), "func(hello, world, tests)", TextSpan(Cursor(0, 19), Cursor(0, 24)))
    #                                               ^^^^^
  def test_onEmpty(self):
    self.runTest(Cursor(0, 6), "func(,,)", None)

  def test_nestedParen(self):
    self.runTestAll("func(hello, world(), tests)", TextSpan(Cursor(0, 12), Cursor(0, 19)))

  def test_noMatchingParen(self):
    self.runTest(Cursor(0, 21), "func(hello, world, tests", TextSpan(Cursor(0, 19), Cursor(0, 24)))

  def test_arrow(self):
    self.runTestAll("func(hello, world->member, tests", TextSpan(Cursor(0, 12), Cursor(0, 25)))
    #                            ^^^^^^^^^^^^^

class TestTextObjectParamOutter(unittest.TestCase):
  def setUp(self):
    pass

  def runTest(self, cursor, text, expected_span):
    result = main(cursor, Buffer(text), inner=False)

    self.assertEqual(result, expected_span)

  def runTestAll(self, text, expected_span, test_span = None):
    if test_span is None:
      test_span = expected_span
    text_buffer = Buffer(text)
    for cursor in test_span.iterate(text_buffer):
      result = main(cursor, text_buffer, inner=False)

      self.assertEqual(result, expected_span)

  def test_basic(self):
    self.runTestAll("func(hello)", TextSpan(Cursor(0, 5), Cursor(0, 10)))

  def test_multiParamStart(self):
    self.runTestAll("func(hello, world, testing)", TextSpan(Cursor(0, 5), Cursor(0, 12)),
    #                     ^^^^^^^
        TextSpan(Cursor(0, 5), Cursor(0, 11)))

  def test_multiParamMid(self):
    self.runTestAll("func(hello, world, tests)", TextSpan(Cursor(0, 12), Cursor(0, 19)),
    #                            ^^^^^^^
        TextSpan(Cursor(0, 12), Cursor(0, 16)))

  def test_multiParamEnd(self):
    self.runTestAll("func(hello, world, tests)", TextSpan(Cursor(0, 17), Cursor(0, 24)),
    #                                 ^^^^^^^
        TextSpan(Cursor(0, 18), Cursor(0, 24)))

  def test_onComma(self):
    self.runTest(Cursor(0, 10), "func(hello, world, tests)", TextSpan(Cursor(0, 5), Cursor(0, 12)))
    #                                 ^^^^^^^
  def test_onLeftParen(self):
    # treat as inner paren and search outwards
    self.runTest(Cursor(0, 4), "func(hello, world, tests)", TextSpan(Cursor(0, 0), Cursor(0, 25)))

  def test_onRightParen(self):
    # treat as inner paren and search outwards
    self.runTest(Cursor(0, 24), "func(hello, world, tests)", TextSpan(Cursor(0, 0), Cursor(0, 25)))

  def test_onSpaceInParam(self):
    self.runTest(Cursor(0, 18), "func(hello, world, tests)", TextSpan(Cursor(0, 17), Cursor(0, 24)))
    #                                             ^^^^^^^
  def test_onEmpty(self):
    self.runTest(Cursor(0, 6), "func(,,)", None)

  def test_nestedParen(self):
    self.runTestAll("func(hello, world(), tests)", TextSpan(Cursor(0, 12), Cursor(0, 21)),
    #                            ^^^^^^^^^
        TextSpan(Cursor(0, 12), Cursor(0, 20)))

  def test_noMatchingParen(self):
    self.runTest(Cursor(0, 21), "func(hello, world, tests", TextSpan(Cursor(0, 17), Cursor(0, 24)))
    #                                             ^^^^^^^

  def test_arrow(self):
    self.runTestAll("func(hello, test->member, tests)", TextSpan(Cursor(0, 12), Cursor(0, 26)),
    #                            ^^^^^^^^^^^^^^
        TextSpan(Cursor(0, 12), Cursor(0, 25)))

if __name__ == '__main__':
  # logging.getLogger("text_object_function").setLevel(logging.DEBUG)
  logging.getLogger("stream_parser.Parser").setLevel(logging.DEBUG)
  # logging.getLogger("stream_parser.Parser").setLevel(logging.INFO)
  # logging.getLogger("text_object_param").setLevel(logging.INFO)
  # logging.getLogger("stream_parser.Lexer").setLevel(logging.DEBUG)
  # logger.setLevel(logging.DEBUG)
  unittest.main()
  # unittest.main(defaultTest="TestTextObjectParamOutter.test_arrow")
  # unittest.main(defaultTest="TestTextObjectParamInner.test_basic")
