import argparse
from stream_parser import *
from stream_lexer_cpp import *
import stream_parser_util

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)

class ParserStates(object):
  pass

stream_parser_util.initParserStates(ParserStates, [
  "kStart",
  "kType",
  "kTemplate", # _ {
  "kBraceHead", # _ const {
  "kBraceHeadConst",
  "kTerminate",
  "kInBlock",
  "kFunctionName",
  "kFunctionType",
  "kFunctionParams",
  "kUnknown",
])

def getTokenPost(parser, token):
  parser.data["secondLastToken"] = parser.data.get("lastToken")
  parser.data["lastToken"] = token

def transitionTo(parser_state):
  def func(parser, token):
    parser.joinToken(token)
    return parser_state
  return func

def incrementLevel(parser, token):
  parser.joinToken(token)
  parser.level += 1

def checkLevel(next_state):
  def internalCheckLevel(parser, token):
    parser.joinToken(token)
    if parser.level == 0:
      return next_state
    else:
      parser.level -= 1
  return internalCheckLevel

def checkLevelEnterBraceHead(parser, token):
  parser.joinToken(token)
  if parser.level == 0:
    parser.data["braceSpan"] = parser.span
    logger.debug(("Setting braceSpan", parser.span))
    logger.debug(("Token", token))
    return ParserStates.kBraceHead
  else:
    parser.level -= 1

def stayAndJoin(parser, token):
  parser.joinToken(token)
  return None

def terminateGood(parser, token):
  parser.data['result'] = True
  return ParserStates.kTerminate

def checkParenBrace(parser, token):
  parser.joinToken(token)
  last_token = parser.data.get("lastToken")
  if last_token:
    if last_token.tokenType == TokenType.kRightParen:
      logger.debug("Confirmed function start")
      return ParserStates.kInBlock
    elif last_token.tokenType == TokenType.kConst:
      second_last_token = parser.data.get("secondLastToken")
      # Assume none case to be a RightParam (we started right on const keyword)
      if second_last_token is None or \
          second_last_token.tokenType == TokenType.kRightParen:
        # we met a const member function
        # ex() const {
        logger.debug("Confirmed function start")
        return ParserStates.kInBlock
  # Just a normal scope block
  parser.level += 1
  logger.debug(("Treat as normal start block Level:", parser.level))
  return ParserStates.kInBlock

def addParserRuleDefault(transition_map, state, transition):
  return stream_parser_util.addParserRuleDefault(TokenType,
      transition_map,
      state,
      transition,
      ignore=TokenType.kEnd)

parserTransitionForward = {}
parserTransitionBackward = {}

# Forwards
# Goal: Find end right brace of the block the cursor is on
# If inside the function block, proceed to find a non matching } brace
# If inside the function declaration, find a ){ match first
# If we encounter ; then we must be in function block
# If we encounter ){ as the first { encountered, we are likely in function declaration
#   (or ctor initialization list)
#   Also check for () const { const member functions
addParserRuleDefault(parserTransitionForward, ParserStates.kStart, transitionTo(ParserStates.kUnknown))
addParserRule(parserTransitionForward, ParserStates.kStart, TokenType.kRightBrace, transitionTo(ParserStates.kTerminate))
addParserRule(parserTransitionForward, ParserStates.kStart, TokenType.kSemiColon, transitionTo(ParserStates.kInBlock))

addParserRuleDefault(parserTransitionForward, ParserStates.kUnknown, stayAndJoin)
addParserRule(parserTransitionForward, ParserStates.kUnknown, TokenType.kLeftBrace, checkParenBrace)
addParserRule(parserTransitionForward, ParserStates.kUnknown, TokenType.kSemiColon, transitionTo(ParserStates.kInBlock))

addParserRuleDefault(parserTransitionForward, ParserStates.kInBlock, stayAndJoin)
addParserRule(parserTransitionForward, ParserStates.kInBlock, TokenType.kRightBrace, checkLevel(ParserStates.kTerminate))
addParserRule(parserTransitionForward, ParserStates.kInBlock, TokenType.kLeftBrace, incrementLevel)

# Backwards
# Find left brace first, then determine if the brace belongs to a function
# We should be starting from a right brace
addParserRule(parserTransitionBackward, ParserStates.kStart, TokenType.kRightBrace, transitionTo(ParserStates.kInBlock))
addParserRule(parserTransitionBackward, ParserStates.kStart, TokenType.kLeftBrace, transitionTo(ParserStates.kBraceHead))

addParserRuleDefault(parserTransitionBackward, ParserStates.kInBlock, stayAndJoin)
addParserRule(parserTransitionBackward, ParserStates.kInBlock, TokenType.kLeftBrace, checkLevelEnterBraceHead)
addParserRule(parserTransitionBackward, ParserStates.kInBlock, TokenType.kRightBrace, incrementLevel)

addParserRule(parserTransitionBackward, ParserStates.kBraceHead, TokenType.kRightParen, transitionTo(ParserStates.kFunctionParams))
addParserRule(parserTransitionBackward, ParserStates.kBraceHead, TokenType.kConst, transitionTo(ParserStates.kBraceHeadConst))

addParserRule(parserTransitionBackward, ParserStates.kBraceHeadConst, TokenType.kRightParen, transitionTo(ParserStates.kFunctionParams))

addParserRuleDefault(parserTransitionBackward, ParserStates.kFunctionParams, stayAndJoin)
addParserRule(parserTransitionBackward, ParserStates.kFunctionParams, TokenType.kLeftParen, checkLevel(ParserStates.kFunctionName))
addParserRule(parserTransitionBackward, ParserStates.kFunctionParams, TokenType.kRightParen, incrementLevel)

addParserRule(parserTransitionBackward, ParserStates.kFunctionName, TokenType.kId, transitionTo(ParserStates.kFunctionType))
addParserRule(parserTransitionBackward, ParserStates.kFunctionName, TokenType.kLeftParen, stayAndJoin)
addParserRule(parserTransitionBackward, ParserStates.kFunctionName, TokenType.kRightParen, stayAndJoin)
addParserRule(parserTransitionBackward, ParserStates.kFunctionName, TokenType.kLeftAngled, stayAndJoin)
addParserRule(parserTransitionBackward, ParserStates.kFunctionName, TokenType.kRightAngled, stayAndJoin)

addParserRuleDefault(parserTransitionBackward, ParserStates.kFunctionType, stayAndJoin)
addParserRule(parserTransitionBackward, ParserStates.kFunctionType, TokenType.kSemiColon, terminateGood)
addParserRule(parserTransitionBackward, ParserStates.kFunctionType, TokenType.kRightBrace, terminateGood)
addParserRule(parserTransitionBackward, ParserStates.kFunctionType, TokenType.kLeftBrace, terminateGood)
addParserRule(parserTransitionBackward, ParserStates.kFunctionType, TokenType.kString, terminateGood)
addParserRule(parserTransitionBackward, ParserStates.kFunctionType, TokenType.kEnd, terminateGood)

def parse(text_buffer, cursor, forward = True):
  logger.debug(("Start cursor", cursor))
  lexer = CppStreamLexer(forward_direction = forward)
  if forward:
    parser = Parser(parserTransitionForward, ParserStates.kStart)
  else:
    parser = Parser(parserTransitionBackward, ParserStates.kStart)

  # Hook events
  parser.getTokenPost = getTokenPost

  span = parseText(lexer, parser, text_buffer, cursor, forward)
  return span, lexer, parser

def isEof(cursor, text_buffer):
  char = text_buffer.getChar(cursor)
  return char is None

def main(cursor, text_buffer, inner = True, logger = None):
  """
  Attempts to find a cpp function text span at the cursor position by streaming input starting from the
  the cursor location.
  inner object includes the full return type without leading whitespace and the closing right brace

  For strings, since we cannot know if we are in a string or not without parsing the entire file, we'll
  make the assumption that the cursor is currently not inside a string
  """
  cursor = stream_parser_util.reverseToTokenBountry(cursor, text_buffer)

  processed_span = TextSpan(cursor, cursor)
  last_span = processed_span.clone()

  infinite_loop_guard = 0
  while infinite_loop_guard < 100:
    forward_span, _, _ = parse(text_buffer, processed_span.end, True)
    if forward_span is None:
      return None
    processed_span.join(forward_span)

    # start from ending brace parse backwards
    backward_cursor = processed_span.end.clone()
    if isEof(backward_cursor, text_buffer):
      backward_cursor.moveBack(text_buffer)
    backward_span, _, parser_backward = parse(text_buffer, backward_cursor, False)
    if parser_backward.data.get('result', False):
      # Function detected (good exit)
      processed_span.join(backward_span)
      return processed_span

    # No function join last brace detection
    brace_span = parser_backward.data.get("braceSpan")
    if brace_span is None:
      # Error getting starting brace
      return None
    processed_span.join(brace_span)
    if last_span == processed_span:
      break
    last_span = processed_span.clone()
    infinite_loop_guard += 1
