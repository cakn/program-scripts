import argparse
from stream_parser import *
from stream_lexer_cpp import *
import stream_parser_util

class ParserStates(object):
  pass

stream_parser_util.initParserStates(ParserStates, [
  "kStart",
  "kType",
  "kTemplate",
  "kTypeColon1",
  "kTypeColon2",
  "kTerminate",
])

def transitionTo(parser_state):
  def func(parser, token):
    parser.joinToken(token)
    return parser_state
  return func

def incrementLevel(parser, token):
  parser.joinToken(token)
  parser.level += 1

def checkLevel(parser, token):
  parser.joinToken(token)
  if parser.level == 0:
    return ParserStates.kTerminate
  else:
    parser.level -= 1

def stayAndJoin(parser, token):
  parser.joinToken(token)
  return None

parserTransitionForward = {}
parserTransitionBackward = {}

# Forwards
addParserRule(parserTransitionForward, ParserStates.kStart, TokenType.kId, transitionTo(ParserStates.kType))
addParserRule(parserTransitionForward, ParserStates.kStart, TokenType.kColon, transitionTo(ParserStates.kTypeColon1))

addParserRule(parserTransitionForward, ParserStates.kType, TokenType.kLeftAngled, transitionTo(ParserStates.kTemplate))
addParserRule(parserTransitionForward, ParserStates.kType, TokenType.kColon, transitionTo(ParserStates.kTypeColon1))

addParserRule(parserTransitionForward, ParserStates.kTypeColon1, TokenType.kColon, transitionTo(ParserStates.kTypeColon2))
addParserRule(parserTransitionForward, ParserStates.kTypeColon2, TokenType.kId, transitionTo(ParserStates.kType))

addParserRule(parserTransitionForward, ParserStates.kTemplate, TokenType.kLeftAngled, incrementLevel)
addParserRule(parserTransitionForward, ParserStates.kTemplate, TokenType.kRightAngled, checkLevel)
addParserRule(parserTransitionForward, ParserStates.kTemplate, TokenType.kId, stayAndJoin)
addParserRule(parserTransitionForward, ParserStates.kTemplate, TokenType.kComma, stayAndJoin)
addParserRule(parserTransitionForward, ParserStates.kTemplate, TokenType.kColon, stayAndJoin)
addParserRule(parserTransitionForward, ParserStates.kTemplate, TokenType.kStar, stayAndJoin)

# Backwards
addParserRule(parserTransitionBackward, ParserStates.kStart, TokenType.kId, transitionTo(ParserStates.kType))
addParserRule(parserTransitionBackward, ParserStates.kStart, TokenType.kColon, transitionTo(ParserStates.kTypeColon1))

addParserRule(parserTransitionBackward, ParserStates.kType, TokenType.kColon, transitionTo(ParserStates.kTypeColon1))
addParserRule(parserTransitionBackward, ParserStates.kTypeColon1, TokenType.kColon, transitionTo(ParserStates.kTypeColon2))
addParserRule(parserTransitionBackward, ParserStates.kTypeColon2, TokenType.kId, transitionTo(ParserStates.kType))


def main(cursor, text_buffer, inner=True, logger = None):
  parser_forward = Parser(parserTransitionForward, ParserStates.kStart)
  parser_backward = Parser(parserTransitionBackward, ParserStates.kStart)
  forward_span, backward_span = stream_parser_util.runCppParser(
      parser_forward,
      parser_backward,
      cursor,
      text_buffer)
  # lexer_backward = CppStreamLexer()
  # parser_backward = Parser(parserTransitionBackward, ParserStates.kStart)
  # backward_span = parseText(lexer_backward, parser_backward, TokenType.kEnd, text_buffer, cursor, False)

  # lexer_forward = CppStreamLexer()
  # parser_forward = Parser(parserTransitionForward, ParserStates.kStart)
  # forward_span = parseText(lexer_forward, parser_forward, TokenType.kEnd, text_buffer, cursor, True)
  if backward_span and forward_span:
    backward_span.join(forward_span)
    return backward_span
  elif backward_span:
    return backward_span
  else:
    return forward_span
