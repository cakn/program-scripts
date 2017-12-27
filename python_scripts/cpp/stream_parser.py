import functools
import logging
import sys

logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger(__name__)
parserLogger = logging.getLogger(__name__ + ".Parser")
lexLogger = logging.getLogger(__name__ + ".Lexer")

def inRange(x, lst):
  return x >= 0 and x < len(lst)

class StateExitAction(object):
  kAllActions = [
    "kPushToken",
    "kPass",
    "kCheckKeyWords"
  ]
for x in StateExitAction.kAllActions:
  setattr(StateExitAction, x, x)

class Buffer(object):
  def __init__(self, text):
    self.text = text.split('\n')

  def getChar(self, cursor):
    if inRange(cursor.row, self.text):
      if inRange(cursor.column, self.text[cursor.row]):
        return self.text[cursor.row][cursor.column]
      elif cursor.column == len(self.text[cursor.row]) and \
          not cursor.row + 1 == len(self.text):
        return '\n'
    return None

  def getLine(self, line):
    if inRange(line, self.text):
      return self.text[line]
    else:
      return None

  def maxLines(self):
    return len(self.text)

  def getLastCursorPos(self):
    return Cursor(self.maxLines() - 1, len(self.text[-1]) - 1)

  def getSpan(self, text_span):
    chars = []
    cursor_it = text_span.start.clone()
    c = self.getChar(cursor_it)
    while c is not None and cursor_it != text_span.end:
      chars.append(c)
      cursor_it.moveForward(self)
      c = self.getChar(cursor_it)
    return ''.join(chars)

@functools.total_ordering
class Cursor(object):
  """
  row == -1 and column == -1 is the non-positional head of the file used when the cursor moves
  backwards from (0, 0) position and will become (0, 0) again when moved forward
  """
  def __init__(self):
    self.row = 0
    self.column = 0

  def __init__(self, row = 0, column = 0):
    self.row = row
    self.column = column

  def __eq__(self, other):
    if type(self) != type(other):
      return False
    return self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not self.__eq__(other)

  def __le__(self, other):
    if self.row == other.row:
      return self.column <= other.column
    else:
      return self.row < other.row

  def __str__(self):
    return "Cursor(row: {}, column: {})".format(self.row, self.column)

  def __repr__(self):
    return str(self)

  def clone(self):
    ret = Cursor()
    ret.copy(self)
    return ret

  def copy(self, other):
    self.row = other.row
    self.column = other.column

  def moveBack(self, text_buffer):
    if self.row >= 0:
      self.column -= 1
      if self.column < 0:
        self.row -= 1
        if self.row < 0:
          self.column = -1
        else:
          self.column = len(text_buffer.text[self.row])

  def moveForward(self, text_buffer = None):
    if text_buffer:
      if inRange(self.row , text_buffer.text):
        self.column += 1
        if len(text_buffer.text[self.row]) < self.column:
          self.column = 0
          self.row += 1
      elif self.row == -1 and self.column == -1:
        self.row = 0
        self.column = 0
    else:
      self.column += 1

class TextSpan(object):
  def __init__(self, start_cursor = None, end_cursor = None, inclusive = False):
    if not start_cursor:
      start_cursor = Cursor(0, 0)
    if not end_cursor:
      end_cursor = Cursor(0, 0)

    self.start = start_cursor.clone()
    self.end = end_cursor.clone()
    if self.start > self.end:
      self.start, self.end = self.end, self.start

    if inclusive:
      self.end.moveForward()

  def __eq__(self, other):
    if type(self) != type(other):
      return False
    return self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not self.__eq__(other)

  def __str__(self):
    return "TextSpan(({}, {}), ({}, {}))".format(
        self.start.row, self.start.column,
        self.end.row, self.end.column)

  def __repr__(self):
    return "TextSpan(({}, {}), ({}, {}))".format(
        self.start.row, self.start.column,
        self.end.row, self.end.column)

  def iterate(self, text_buffer):
    cursor = self.start.clone()
    while cursor != self.end:
      yield cursor
      cursor.moveForward(text_buffer)

  def clone(self):
    ret = TextSpan(self.start, self.end)
    return ret

  def join(self, span):
    self.start = min(self.start, span.start)
    self.end = max(self.end, span.end)

class Token(object):
  def __init__(self, span, token_type):
    self.span = span.clone()
    self.tokenType = token_type
  def __str__(self):
      return "Token({}, {})".format(self.span, self.tokenType)
  def __repr__(self):
    return str(self)
  def __eq__(self, other):
    if type(self) != type(other):
      return False
    return self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not self.__eq__(other)

class Parser(object):
  def __init__(self, transitions, start_state, end_state = None):
    self.transitions = transitions
    self.state = start_state
    self.endState = end_state
    self.span = None
    self.level = 0
    self.data = {}

    self.getTokenPost = None

  def joinToken(self, token):
    if self.span is None:
      self.span = token.span
    else:
      self.span.join(token.span)
    parserLogger.debug(("Added in span", token.span, "Result", self.span))

  def parseToken(self, token):
    parserLogger.info(("Parsing token", token, "current span", self.span))
    if self.state in self.transitions and \
        token.tokenType in self.transitions[self.state]:
      transition_func = self.transitions[self.state][token.tokenType]
      parserLogger.debug(("Calling transition_func state:", self.state, " token: ", token.tokenType))
      new_state = transition_func(self, token)
      if new_state:
        parserLogger.info(("transition ", self.state, " => ", new_state, " with ", token.tokenType))
        self.state = new_state
      if self.getTokenPost:
        self.getTokenPost(self, token)
    else:
      # Terminate
      parserLogger.info(("Terminate from state ", self.state, " with token ", token.tokenType))
      return True

    if self.state == self.endState:
      parserLogger.info(("Terminate from end_state ", self.state))
      return True

class LexerReturn(object):
  def __init__(self, tokens, new_state, new_start_pos, transition):
    self.tokens = tokens
    self.newState = new_state
    # Set to None to take next char as new start
    self.newStartPos = new_start_pos
    # bool to keep checking states or not
    self.transition = transition


class Lexer(object):
  def __init__(self, transitions, start_state):
    self.transitions = transitions
    self.state = start_state
    self.start_cursor = None
    self.prev_cursor = None
    self.lastLine = None
    self.newLineEvent = None

  def lex(self, cursor, text_buffer):
    if self.start_cursor is None:
      lexLogger.debug(("Set start_cursor from none", cursor))
      self.start_cursor = cursor.clone()
    if self.prev_cursor is None:
      self.prev_cursor = cursor.clone()

    next_char_override = None
    if self.lastLine != cursor.row:
      if self.newLineEvent:
        cursor, next_char_override = self.newLineEvent(cursor, text_buffer)
        lexLogger.debug(("New line adjust cursor", cursor))

    self.lastLine = cursor.row
    next_char = text_buffer.getChar(cursor)
    if next_char_override:
      next_char = next_char_override

    tokens = []
    running = True
    while running:
      def transition():
        transitions = self.transitions[self.state]
        for transition_data in transitions:
          if transition_data[0](next_char):
            lexLogger.debug(("Transition success", transition_data))
            lex_return = transition_data[1](
                self.start_cursor.clone(),
                cursor.clone(),
                self.prev_cursor.clone(), text_buffer)
            return lex_return
      lex_return = transition()
      if lex_return:
        if len(lex_return.tokens) > 0:
          lexLogger.info(("Created token", lex_return.tokens))
          tokens.extend(lex_return.tokens)
        if self.start_cursor != lex_return.newStartPos:
          lexLogger.debug(("New start cursor", self.start_cursor, " => ", lex_return.newStartPos))
          self.start_cursor = lex_return.newStartPos
        if lex_return.newState:
          if lex_return.newState != self.state:
            lexLogger.info(("Changing state", self.state, " => ", lex_return.newState, "Cursor", self.start_cursor))
            self.state = lex_return.newState
        if lex_return.transition:
          running = False
        else:
          lexLogger.debug("Continuing state transitions")
      else:
        running = False

    self.prev_cursor.copy(cursor)
    return tokens, cursor

def addParserRule(transition_map, current_state, next_token_state, func):
  if current_state not in transition_map:
    transition_map[current_state] = {}
  transition_map[current_state][next_token_state] = func

def parseText(lexer, parser, text_buffer, cursor, forward=True):
  parserLogger.info(("parseText BEGIN", cursor, "Forward:", forward))
  iterator_cursor = cursor.clone()
  terminate = False
  first_run = True
  while not terminate:
    if first_run:
      first_run = False
    else:
      if forward:
        iterator_cursor.moveForward(text_buffer)
      else:
        iterator_cursor.moveBack(text_buffer)
    new_tokens, iterator_cursor = lexer.lex(iterator_cursor, text_buffer)
    for token in new_tokens:
      terminate = parser.parseToken(token)
      if terminate:
        break
  parserLogger.info(("parseText END Result", parser.span))
  return parser.span

