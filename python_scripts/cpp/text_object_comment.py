from stream_parser import *
import logging

logging.basicConfig()
default_logger = logging.getLogger(__name__)
log = default_logger

def searchLines(text_buffer, line_list):
  for x in line_list:
    line = text_buffer.getLine(x)
    log.debug((x, line))
    if line is None or\
        not isCommentLine(line) and not isBlankLine(line):
      return x
  return None

def isCommentLine(line):
  return line.lstrip().startswith("//")

def isBlankLine(line):
  log.debug(("line len", len(line.strip()), line))
  return len(line.strip()) == 0

def main(cursor, text_buffer, inner=True, logger = None):
  """
  Comment text object for visual studio
  """
  if logger is None:
    logger = default_logger
  global log
  log = logger

  line_number = cursor.row
  span = TextSpan(Cursor(line_number, 0), Cursor(line_number, 0))
  if not isCommentLine(text_buffer.getLine(line_number)):
    return None

  back_index = searchLines(text_buffer, reversed(xrange(0, line_number)))
  if back_index is None:
    back_index = 0
  else:
    back_index += 1
  logger.debug(("back_index", back_index))

  forward_index = searchLines(text_buffer, xrange(line_number, text_buffer.maxLines()))
  if forward_index is None:
    forward_index = text_buffer.maxLines() - 1
  else:
    forward_index -= 1

  logger.debug(("forward_index", forward_index))

  logger.debug(("inner", inner))
  if inner:
    while isBlankLine(text_buffer.getLine(back_index)) and forward_index > back_index:
      back_index += 1
    while isBlankLine(text_buffer.getLine(forward_index)) and forward_index > back_index:
      forward_index -= 1

  logger.debug(("back_index", back_index))
  logger.debug(("forward_index", forward_index))
  # line = text_buffer.getLine(forward_index)
  # if line is None:
  #   forward_col = 0
  # else:
  #   forward_col = len(line)
  span = TextSpan(Cursor(back_index, 0), Cursor(forward_index + 1, 0))
  logger.debug(("span", span))
  return span
