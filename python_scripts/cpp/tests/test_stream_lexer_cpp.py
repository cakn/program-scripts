import unittest

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from stream_lexer_cpp import *

import logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger(__name__)

class TestStreamLexerCpp(unittest.TestCase):
  def setUp(self):
    pass

  @staticmethod
  def getTokenList(text, **kargs):
    logger.debug("Start forward test")
    lexer = CppStreamLexer(**kargs)
    text_buffer = Buffer(text)
    tokens = []
    cursor = Cursor(0,0)
    next_char = text_buffer.getChar(cursor)
    while next_char:
      new_token, cursor = lexer.lex(cursor, text_buffer)
      if new_token:
        tokens.extend(new_token)
      cursor.moveForward(text_buffer)
      next_char = text_buffer.getChar(cursor)
    new_token, cursor = lexer.lex(cursor, text_buffer)
    if new_token:
      tokens.extend(new_token)
    if len(tokens) > 0 and tokens[-1].tokenType == TokenType.kEnd:
      tokens.pop()
    return tokens

  @staticmethod
  def getTokenListReverse(text, **kargs):
    logger.debug("Start reverse test")
    lexer = CppStreamLexer(forward_direction = False, **kargs)
    text_buffer = Buffer(text)
    tokens = []
    cursor = text_buffer.getLastCursorPos()
    next_char = text_buffer.getChar(cursor)
    while next_char:
      new_tokens, cursor = lexer.lex(cursor, text_buffer)
      tokens.extend(new_tokens)
      cursor.moveBack(text_buffer)
      next_char = text_buffer.getChar(cursor)
    new_tokens, cursor = lexer.lex(cursor, text_buffer)
    if new_tokens:
      tokens.extend(new_tokens)
    # expect end token
    if len(tokens) > 0 and tokens[-1].tokenType == TokenType.kEnd:
      tokens.pop()
    tokens.reverse()
    return tokens

  def runTestTokenType(self, text, expected_tokens, **kargs):
    tokens = TestStreamLexerCpp.getTokenList(text, **kargs)
    tokens = [x.tokenType for x in tokens]
    self.assertListEqual(tokens, expected_tokens)

    tokens = TestStreamLexerCpp.getTokenListReverse(text, **kargs)
    tokens = [x.tokenType for x in tokens]
    self.assertListEqual(tokens, expected_tokens)

  def runTest(self, text, expected_tokens):
    tokens = TestStreamLexerCpp.getTokenList(text)
    self.assertListEqual(tokens, expected_tokens)

    tokens = TestStreamLexerCpp.getTokenListReverse(text)
    self.assertListEqual(tokens, expected_tokens)

  def test_basic(self):
    self.runTestTokenType("words and words", [TokenType.kId, TokenType.kId, TokenType.kId])

  def test_span(self):
    self.runTest("words and words", [
      Token(TextSpan(Cursor(0, 0), Cursor(0, 5)), TokenType.kId),
      Token(TextSpan(Cursor(0, 6), Cursor(0, 9)), TokenType.kId),
      Token(TextSpan(Cursor(0, 10), Cursor(0, 15)), TokenType.kId),
    ])

  def test_multiSpaces(self):
    self.runTest("words   and  words", [
      Token(TextSpan(Cursor(0, 0), Cursor(0, 5)), TokenType.kId),
      Token(TextSpan(Cursor(0, 8), Cursor(0, 11)), TokenType.kId),
      Token(TextSpan(Cursor(0, 13), Cursor(0, 18)), TokenType.kId),
    ])

  def test_singleSpan(self):
    self.runTest("words(and)words", [
      Token(TextSpan(Cursor(0, 0), Cursor(0, 5)), TokenType.kId),
      Token(TextSpan(Cursor(0, 5), Cursor(0, 6)), TokenType.kLeftParen),
      Token(TextSpan(Cursor(0, 6), Cursor(0, 9)), TokenType.kId),
      Token(TextSpan(Cursor(0, 9), Cursor(0, 10)), TokenType.kRightParen),
      Token(TextSpan(Cursor(0, 10), Cursor(0, 15)), TokenType.kId),
    ])

  def test_symbols(self):
    self.runTestTokenType("""{ } < > [ ] ( ): , * ; """,
        [TokenType.kLeftBrace,
        TokenType.kRightBrace,
        TokenType.kLeftAngled,
        TokenType.kRightAngled,
        TokenType.kLeftBracket,
        TokenType.kRightBracket,
        TokenType.kLeftParen,
        TokenType.kRightParen,
        TokenType.kColon,
        TokenType.kComma,
        TokenType.kStar,
        TokenType.kSemiColon,
    ])
  def test_arrow(self):
    self.runTest("test->word", [
      Token(TextSpan(Cursor(0, 0), Cursor(0, 4)), TokenType.kId),
      Token(TextSpan(Cursor(0, 4), Cursor(0, 6)), TokenType.kArrow),
      Token(TextSpan(Cursor(0, 6), Cursor(0, 10)), TokenType.kId),
    ])

  def test_keywords(self):
    self.runTestTokenType("const if else while switch",
        [TokenType.kConst,
        TokenType.kIf,
        TokenType.kElse,
        TokenType.kWhile,
        TokenType.kSwitch,
    ])

  def test_allowSpaces(self):
    self.runTestTokenType("words and words", [
      TokenType.kId,
      TokenType.kSpace,
      TokenType.kId,
      TokenType.kSpace,
      TokenType.kId], allow_space_token = True)

  def test_lineComments(self):
    self.runTest("words and//and words\n//skip this line\nmore words", [
        Token(TextSpan(Cursor(0, 0), Cursor(0, 5)), TokenType.kId),
        Token(TextSpan(Cursor(0, 6), Cursor(0, 9)), TokenType.kId),
        Token(TextSpan(Cursor(2, 0), Cursor(2, 4)), TokenType.kId),
        Token(TextSpan(Cursor(2, 5), Cursor(2, 10)), TokenType.kId),
    ])

  def test_strings(self):
    self.runTest("""words "and more" words""", [
        Token(TextSpan(Cursor(0, 0), Cursor(0, 5)), TokenType.kId),
        Token(TextSpan(Cursor(0, 6), Cursor(0, 16)), TokenType.kString),
        Token(TextSpan(Cursor(0, 17), Cursor(0, 22)), TokenType.kId),
    ])

  def test_stringsEscapedQuote(self):
    self.runTest("""words "and \\"more" words""", [
        Token(TextSpan(Cursor(0, 0), Cursor(0, 5)), TokenType.kId),
        Token(TextSpan(Cursor(0, 6), Cursor(0, 18)), TokenType.kString),
        Token(TextSpan(Cursor(0, 19), Cursor(0, 24)), TokenType.kId),
    ])

  def test_multilineComment(self):
    self.runTest("words /*and\nmore\nstuff*/ words", [
        Token(TextSpan(Cursor(0, 0), Cursor(0, 5)), TokenType.kId),
        Token(TextSpan(Cursor(2, 8), Cursor(2, 13)), TokenType.kId),
    ])

if __name__ == '__main__':
  logger.setLevel(logging.DEBUG)
  logging.getLogger("stream_parser").setLevel(logging.DEBUG)
  unittest.main()
  # unittest.main(defaultTest="TestStreamLexerCpp.test_arrow")
  # unittest.main(defaultTest="TestStreamLexerCpp.test_lineComments")
