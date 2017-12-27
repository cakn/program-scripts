from stream_parser import *
import copy

class LexerState(object):
  kAllStates = [
    "kDefault",
    "kInId",
    "kSpace",
    "kSubtract",
    "kRightAngled",
    "kForwardSlash",
    "kCommentLine",
    "kString",
    "kStringEscape",
    "kStringPotentialEscapedQuote",
    "kCommentMultiline",
    "kCommentMultilineStar",
    "kEnd"
  ]

class TokenType(object):
  kAllTokens = [
    "kId",
    "kSpace",
    "kString",
    "kColon",
    "kComma",
    "kStart",
    "kOther",
    "kStar",
    "kSemiColon",
    "kLeftAngled",
    "kRightAngled",
    "kLeftBrace",
    "kRightBrace",
    "kLeftBracket",
    "kRightBracket",
    "kLeftParen",
    "kRightParen",
    "kArrow",
    "kSubtract",
    "kSubtractOrArrow",
    "kForwardSlash",
    "kEnd",
  ]

  kKeyWords = [
   "const",
   "if",
   "else",
   "while",
   "switch",
  ]

keyWords = {}

for key_word in TokenType.kKeyWords:
  TokenType.kAllTokens.append("k" + key_word.title())

for token_name in TokenType.kAllTokens:
  setattr(TokenType, token_name, token_name)

for state_name in LexerState.kAllStates:
  setattr(LexerState, state_name, state_name)

for key_word in TokenType.kKeyWords:
  keyWords[key_word] = getattr(TokenType, "k" + key_word.title())

def isId(s):
  if s:
    return s.isalnum() or s == "_"
  return False

def isSpace(s):
  if s:
    return s.isspace()
  return False

def alwaysTrue(s):
  return True

def isNone(s):
  return s is None

def isSymbol(symbol):
  def isThisSymbol(s):
    if s:
      return s == symbol
    return False
  return isThisSymbol

def transition(state):
  def transitionFunc(start_pos, end_pos, prev_pos, text_buffer):
    return LexerReturn([], state, start_pos, True)
  return transitionFunc

def transitionIgnore(state):
  def transitionFunc(start_pos, end_pos, prev_pos, text_buffer):
    return LexerReturn([], state, None, True)
  return transitionFunc

def transitionIgnorePassChar(state):
  def transitionFunc(start_pos, end_pos, prev_pos, text_buffer):
    return LexerReturn([], state, None, False)
  return transitionFunc

def outputTokenTransDefault(token_type):
  def outputTokenFunc(start_pos, end_pos, prev_pos, text_buffer):
    return LexerReturn([Token(TextSpan(start_pos, end_pos, inclusive = True), token_type)], LexerState.kDefault, None, True)
  return outputTokenFunc

def outputTokenPassChar(token_type, new_state = LexerState.kDefault):
  def outputTokenPassCharFunc(start_pos, end_pos, prev_pos, text_buffer):
    token = Token(TextSpan(start_pos, prev_pos, inclusive = True), token_type)
    return LexerReturn([token], new_state, end_pos, False)
  return outputTokenPassCharFunc

def endIdState(start_pos, end_pos, prev_pos, text_buffer):
  token = Token(TextSpan(start_pos, prev_pos, inclusive = True), TokenType.kId)
  word = text_buffer.getSpan(token.span)
  if word in keyWords:
    new_type = keyWords[word]
    token.tokenType = new_type
  return LexerReturn([token], LexerState.kDefault, end_pos, False)

def doNothing(start_pos, end_pos, prev_pos, text_buffer):
  return LexerReturn([], None, start_pos, True)

def ignore(start_pos, end_pos, prev_pos, text_buffer):
  return LexerReturn([], None, None, True)

def outputEnd(start_pos, end_pos, prev_pos, text_buffer):
  token = Token(TextSpan(), TokenType.kEnd)
  return LexerReturn([token], None, None, True)

stateTransitionBase = {}
for key in LexerState.kAllStates:
  stateTransitionBase[key] = []

trans_list = stateTransitionBase[LexerState.kDefault]

trans_list.insert(0, [isNone, outputEnd])
trans_list.append([isId, transition(LexerState.kInId)])
trans_list.append([isSymbol(","), outputTokenTransDefault(TokenType.kComma)])
trans_list.append([isSymbol("<"), outputTokenTransDefault(TokenType.kLeftAngled)])
trans_list.append([isSymbol("{"), outputTokenTransDefault(TokenType.kLeftBrace)])
trans_list.append([isSymbol("}"), outputTokenTransDefault(TokenType.kRightBrace)])
trans_list.append([isSymbol("["), outputTokenTransDefault(TokenType.kLeftBracket)])
trans_list.append([isSymbol("]"), outputTokenTransDefault(TokenType.kRightBracket)])
trans_list.append([isSymbol("("), outputTokenTransDefault(TokenType.kLeftParen)])
trans_list.append([isSymbol(")"), outputTokenTransDefault(TokenType.kRightParen)])
trans_list.append([isSymbol(";"), outputTokenTransDefault(TokenType.kSemiColon)])
trans_list.append([isSymbol(":"), outputTokenTransDefault(TokenType.kColon)])
trans_list.append([isSymbol("*"), outputTokenTransDefault(TokenType.kStar)])
trans_list.append([isSymbol("\""), transition(LexerState.kString)])
trans_list.append([isSymbol("/"), transition(LexerState.kForwardSlash)])

stateTransitionBase[LexerState.kInId].append([isId, doNothing])
stateTransitionBase[LexerState.kInId].append([alwaysTrue, endIdState])

stateTransitionBase[LexerState.kString].append([isNone, outputTokenPassChar(TokenType.kString)])

stateTransitionBase[LexerState.kForwardSlash].append([isSymbol("*"), transitionIgnore(LexerState.kCommentMultiline)])

stateTransitionBase[LexerState.kCommentMultiline].append([isNone, transitionIgnorePassChar(LexerState.kDefault)])
stateTransitionBase[LexerState.kCommentMultiline].append([isSymbol("*"), transitionIgnore(LexerState.kCommentMultilineStar)])
stateTransitionBase[LexerState.kCommentMultiline].append([alwaysTrue, ignore])

stateTransitionBase[LexerState.kCommentMultilineStar].append(
    [isNone, transitionIgnorePassChar(LexerState.kDefault)])
stateTransitionBase[LexerState.kCommentMultilineStar].append(
    [isSymbol("/"), transitionIgnore(LexerState.kDefault)])
stateTransitionBase[LexerState.kCommentMultilineStar].append(
    [alwaysTrue, transitionIgnore(LexerState.kCommentMultiline)])

def stateTransitionSpaces(transitions, include):
  if include:
    transitions[LexerState.kDefault].append([isSpace, transition(LexerState.kSpace)])

    transitions[LexerState.kSpace].append([isSpace, doNothing])
    transitions[LexerState.kSpace].append([alwaysTrue, outputTokenPassChar(TokenType.kSpace)])
  else:
    transitions[LexerState.kDefault].append([isSpace, ignore])

def stateTransitionFinalize(transitions):
  transitions[LexerState.kDefault].append([alwaysTrue, outputTokenTransDefault(TokenType.kOther)])

  transitions[LexerState.kString].append([alwaysTrue, doNothing])

  transitions[LexerState.kForwardSlash].append([alwaysTrue, outputTokenPassChar(TokenType.kForwardSlash)])

def stateTransitionDirectional(transitions, forward = True):
  if forward:
    transitions[LexerState.kDefault].append([isSymbol(">"), outputTokenTransDefault(TokenType.kRightAngled)])
    transitions[LexerState.kDefault].append([isSymbol("-"), transition(LexerState.kSubtract)])

    transitions[LexerState.kString].append([isSymbol("\""), outputTokenTransDefault(TokenType.kString)])
    transitions[LexerState.kString].append([isSymbol("\\"), transition(LexerState.kStringEscape)])

    transitions[LexerState.kStringEscape].append([isNone, outputTokenPassChar(TokenType.kString)])
    transitions[LexerState.kStringEscape].append([alwaysTrue, transition(LexerState.kString)])

    transitions[LexerState.kForwardSlash].append([isSymbol("/"), transitionIgnore(LexerState.kCommentLine)])
    transitions[LexerState.kForwardSlash].append([alwaysTrue, outputTokenPassChar(TokenType.kForwardSlash)])

    transitions[LexerState.kCommentLine].append([isSymbol("\n"), transitionIgnore(LexerState.kDefault)])
    transitions[LexerState.kCommentLine].append([alwaysTrue, ignore])

    transitions[LexerState.kSubtract].append([isSymbol(">"), outputTokenTransDefault(TokenType.kArrow)])
    transitions[LexerState.kSubtract].append([alwaysTrue, outputTokenPassChar(TokenType.kSubtract)])
  else:
    transitions[LexerState.kDefault].append([isSymbol("-"), outputTokenTransDefault(TokenType.kSubtract)])
    transitions[LexerState.kDefault].append([isSymbol(">"), transition(LexerState.kRightAngled)])

    transitions[LexerState.kString].append([isSymbol("\""), transition(LexerState.kStringPotentialEscapedQuote)])

    transitions[LexerState.kStringPotentialEscapedQuote].append([isSymbol("\\"), transition(LexerState.kString)])
    transitions[LexerState.kStringPotentialEscapedQuote].append([alwaysTrue, outputTokenPassChar(LexerState.kString)])

    transitions[LexerState.kRightAngled].append([isSymbol("-"), outputTokenTransDefault(TokenType.kArrow)])
    transitions[LexerState.kRightAngled].append([alwaysTrue, outputTokenPassChar(TokenType.kRightAngled)])

def backwardNewLineEvent(cursor, text_buffer):
  # Seek to beginning of a line comment if there is one
  row = cursor.row
  line = text_buffer.getLine(row)
  if line is None:
    return cursor, None

  slash_index = line.find("//")
  if slash_index == -1:
    return cursor, None

  column = slash_index
  if column < 0:
    if row > 0:
      row -= 1
      column = len(text_buffer.getLine(row))
      return backwardNewLineEvent(Cursor(row, column), text_buffer)
  return Cursor(row, column), "\n"

# We assume we do not start inside of a string or a /* */ comment block
class CppStreamLexer(Lexer):
  def __init__(self, forward_direction = True, allow_space_token = False):
    transitions = copy.deepcopy(stateTransitionBase)
    stateTransitionSpaces(transitions, allow_space_token)
    stateTransitionDirectional(transitions, forward_direction)
    stateTransitionFinalize(transitions)
    Lexer.__init__(self, transitions, LexerState.kDefault)
    if forward_direction:
      pass
    else:
      self.newLineEvent = backwardNewLineEvent
