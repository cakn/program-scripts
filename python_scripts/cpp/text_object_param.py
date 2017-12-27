import argparse
from stream_parser import *
from stream_lexer_cpp import *
from stream_parser_util import *

import logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger(__name__)

class ParserStates(object):
  pass

initParserStates(ParserStates, [
  "kStart",
  "kDefault",
  "kInParen",
  "kInBrace",
  "kInAngled",
  "kInBracket",
  "kTerminate",
  "kInnerTerminate",
])

def transitionTo(parser_state):
  def func(parser, token):
    parser.joinToken(token)
    return parser_state
  return func

def transitionNoJoin(parser_state):
  def func(parser, token):
    return parser_state
  return func

def incrementLevel(parser, token):
  parser.joinToken(token)
  parser.level += 1

def incrementLevelAndTrans(transition):
  def incTrans(parser, token):
    parser.joinToken(token)
    parser.level += 1
    return transition
  return incTrans

def checkLevel(parser, token):
  parser.joinToken(token)
  if parser.level == 0:
    return ParserStates.kDefault
  else:
    parser.level -= 1

def stayAndJoin(parser, token):
  parser.joinToken(token)
  return None

def stayIgnore(parser, token):
  return None

def innerTerminate(parser, token):
  return ParserStates.kInnerTerminate

def terminateNoJoin(parser, token):
  return ParserStates.kTerminate

def defaultRuleIgnoreEnd(token_class, transition_map, state, transition):
  ignore = [TokenType.kEnd]
  addParserRuleDefault(token_class, transition_map, state, transition, ignore)

parserTransitionForward = {}
parserTransitionBackward = {}

braces = [
  [TokenType.kLeftParen, TokenType.kRightParen, ParserStates.kInParen],
  [TokenType.kLeftBrace, TokenType.kRightBrace, ParserStates.kInBrace],
  [TokenType.kLeftAngled, TokenType.kRightAngled, ParserStates.kInAngled],
  [TokenType.kLeftBracket, TokenType.kRightBracket, ParserStates.kInBracket],
]

# Forwards
defaultRuleIgnoreEnd(TokenType, parserTransitionForward, ParserStates.kDefault, stayAndJoin)
addParserRule(parserTransitionForward, ParserStates.kDefault, TokenType.kComma,
    innerTerminate)
addParserRule(parserTransitionForward, ParserStates.kDefault, TokenType.kSpace, stayIgnore)

for brace_data in braces:
  front_char = brace_data[0]
  back_char = brace_data[1]
  addParserRule(parserTransitionForward, ParserStates.kDefault, front_char,
      transitionTo(brace_data[2]))
  addParserRule(parserTransitionForward, ParserStates.kDefault, back_char,
      innerTerminate)

  defaultRuleIgnoreEnd(TokenType, parserTransitionForward, brace_data[2], stayAndJoin)
  addParserRule(parserTransitionForward, brace_data[2], front_char, incrementLevel)
  addParserRule(parserTransitionForward, brace_data[2], back_char, checkLevel)

  addParserRule(parserTransitionForward, brace_data[2], TokenType.kSpace, stayIgnore)

# Backwards
# Begin on kStart state to detect and ignore starting comma
defaultRuleIgnoreEnd(TokenType, parserTransitionBackward, ParserStates.kStart,
    transitionTo(ParserStates.kDefault))
addParserRule(parserTransitionBackward, ParserStates.kStart, TokenType.kComma,
    transitionNoJoin(ParserStates.kDefault))
addParserRule(parserTransitionBackward, ParserStates.kStart, TokenType.kSpace,
    transitionNoJoin(ParserStates.kDefault))

defaultRuleIgnoreEnd(TokenType, parserTransitionBackward, ParserStates.kDefault, stayAndJoin)
addParserRule(parserTransitionBackward, ParserStates.kDefault, TokenType.kComma,
    innerTerminate)
addParserRule(parserTransitionBackward, ParserStates.kDefault, TokenType.kSpace,
    stayIgnore)

for brace_data in braces:
  front_char = brace_data[1]
  back_char = brace_data[0]
  # Special rule for beginning on a brace, ignore and keep searching
  addParserRule(parserTransitionBackward, ParserStates.kStart, front_char,
      transitionTo(brace_data[2]))

  addParserRule(parserTransitionBackward, ParserStates.kDefault, front_char,
      transitionTo(brace_data[2]))
  addParserRule(parserTransitionBackward, ParserStates.kDefault, back_char,
      innerTerminate)

  defaultRuleIgnoreEnd(TokenType, parserTransitionBackward, brace_data[2], stayAndJoin)
  addParserRule(parserTransitionBackward, brace_data[2], front_char, incrementLevel)
  addParserRule(parserTransitionBackward, brace_data[2], back_char, checkLevel)

  addParserRule(parserTransitionBackward, brace_data[2], TokenType.kSpace, stayIgnore)

def searchUntil(text_buffer, cursor, pred, forward=True):
  it_cursor = cursor.clone()
  char = text_buffer.getChar(it_cursor)
  logger.info(("searching char", char))
  while char is not None and not pred(char):
    if forward:
      it_cursor.moveForward(text_buffer)
    else:
      it_cursor.moveBack(text_buffer)
    char = text_buffer.getChar(it_cursor)
    logger.info(("searching char", char))
  return it_cursor

def forwardSearch(text_buffer, cursor, pred):
  return searchUntil(text_buffer, cursor, pred, True)

def backwardSearch(text_buffer, cursor, pred):
  return searchUntil(text_buffer, cursor, pred, False)

def commaOrRightParen(s):
  return s in ",)"

def commaOrLeftParen(s):
  return s in ",("

def isNotWhitespace(s):
  return not s.isspace()

# Edge cases:
#  start on ,: take parameter on the left
#  start on (: treat as a paren inside a parameter and search outwards
#  start on ): treat as a paren inside a parameter and search outwards
def main(cursor, text_buffer, inner=True, logger = None):
  if logger is None:
    logger = logging.getLogger(__name__)

  parser_forward = Parser(parserTransitionForward, ParserStates.kDefault, end_state = ParserStates.kInnerTerminate)
  parser_backward = Parser(parserTransitionBackward, ParserStates.kStart, end_state = ParserStates.kInnerTerminate)
  forward_span, backward_span = runCppParser(
      parser_forward,
      parser_backward, 
      cursor, 
      text_buffer, 
      allow_space_token = True,
      same_cursor_start = True)

  logger.info(("forward_span", forward_span))
  logger.info(("backward_span", backward_span))

  inner_span = None
  if backward_span and forward_span:
    backward_span.join(forward_span)
    inner_span = backward_span
  elif backward_span:
    inner_span = backward_span
  else:
    inner_span = forward_span

  if inner:
    return inner_span

  if inner_span is None:
    #Error finding inner param, just return None
    return None

  logger.info(("Expanding from inner span", inner_span))
  # Search forward for comma or paren
  forward_cursor = forwardSearch(text_buffer, inner_span.end, commaOrRightParen)
  forward_char = text_buffer.getChar(forward_cursor)
  logger.info(("Forward cursor", forward_cursor, "With char", forward_char))
  backward_cursor = None
  if forward_char == ",":
    forward_cursor.moveForward(text_buffer)
    forward_cursor = forwardSearch(text_buffer, forward_cursor, isNotWhitespace)

    backward_cursor = inner_span.start
  elif forward_char == ")" or forward_char is None:
    # If None we're at end of file
    # Probably unclosed paren. We'll do our best expanding the backwards range anyways
    backward_cursor = backwardSearch(text_buffer, inner_span.start, commaOrLeftParen)
    backward_char = text_buffer.getChar(backward_cursor)
    logger.info(("back cursor", backward_cursor, "With char", backward_char))
    if backward_char is None or backward_char == "(":
      backward_cursor.moveForward(text_buffer)
      logger.info(("back cursor move forward", backward_cursor, "With char", backward_char))

  return TextSpan(backward_cursor, forward_cursor)
