from stream_parser import *
from stream_lexer_cpp import CppStreamLexer, isSymbol, isId
import logging
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger(__name__)

def initParserStates(parser_state_class, lst):
  setattr(parser_state_class, "kAllStates", lst)
  for x in parser_state_class.kAllStates:
    setattr(parser_state_class, x, x)

def addParserRuleDefault(token_class, transition_map, state, transition, ignore=None):
  for token in token_class.kAllTokens:
    if ignore is None or token not in ignore:
      addParserRule(transition_map, state, token, transition)

def reverseToTokenBountry(cursor, text_buffer, same_cursor_start = False):
  # Check for line comments
  line = text_buffer.getLine(cursor.row)
  if line is None:
    return cursor
  slash_index = line.find("//")
  if slash_index != -1:
    return Cursor(cursor.row, slash_index)

  # Seek cursor to head of token so lexer could grab keywords or -> token
  cursor = cursor.clone()
  char = text_buffer.getChar(cursor)
  if char is not None:
    if isId(char):
      # We want cursor to be at the head of the id
      cursor_it = cursor.clone()
      while char is not None and isId(char):
        cursor.copy(cursor_it)
        cursor_it.moveBack(text_buffer)
        char = text_buffer.getChar(cursor_it)
    elif ">" == char:
      prev_cursor = cursor.clone()
      prev_cursor.moveBack(text_buffer)
      prev_char = text_buffer.getChar(prev_cursor)
      if prev_char == "-":
        cursor = prev_cursor
  return cursor

def runCppParser(parser_forward, parser_backward, cursor, text_buffer, allow_space_token = False,
    same_cursor_start = False):
  """
  Runs the parser both ways using the cpp stream lexer and returns the forward and backward spans
  """
  # Seek cursor to head of token so lexer could grab keywords or -> token
  cursor = reverseToTokenBountry(cursor, text_buffer)
  back_cursor = cursor.clone()
  if not same_cursor_start:
    back_cursor.moveBack(text_buffer)

  lexer_backward = CppStreamLexer(forward_direction = False, allow_space_token = allow_space_token)
  backward_span = parseText(lexer_backward, parser_backward, text_buffer, back_cursor, False)

  lexer_forward = CppStreamLexer(forward_direction = True, allow_space_token = allow_space_token)
  forward_span = parseText(lexer_forward, parser_forward, text_buffer, cursor, True)
  return forward_span, backward_span
