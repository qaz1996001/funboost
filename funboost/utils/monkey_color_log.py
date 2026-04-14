# -*- coding: utf-8 -*-
# @Author  : ydf
# @Time    : 2022/8/1 0001 17:54
"""
If an existing project does not use LogManager, this monkey patch can be applied to automatically make any logs in the project colorful and clickable.

"""

import sys
import os
import logging


class ColorHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """
    os_name = os.name
    terminator = '\n'
    bule = 96 if os_name == 'nt' else 36
    yellow = 93 if os_name == 'nt' else 33

    def __init__(self, stream=None, ):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - %(levelname)s - %(message)s',
            "%Y-%m-%d %H:%M:%S")
        if stream is None:
            stream = sys.stdout  # stderr has no color.
        self.stream = stream
        self._display_method = 7 if self.os_name == 'posix' else 0

    def setFormatter(self, fmt):
        pass  # Prevent custom log format. Always use the clickable format.

    def flush(self):
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        finally:
            self.release()

    def emit0(self, record):
        """
        Non-split color mode (entire message in one color).
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            stream = self.stream
            if record.levelno == 10:
                # msg_color = ('\033[0;32m%s\033[0m' % msg)  # green
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, 32, msg))  # green
            elif record.levelno == 20:
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # cyan/blue 36    96
            elif record.levelno == 30:
                msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
            elif record.levelno == 40:
                msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # magenta
            elif record.levelno == 50:
                msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # red
            else:
                msg_color = msg
            # print(msg_color,'***************')
            stream.write(msg_color)
            stream.write(self.terminator)
            self.flush()
        except BaseException :
            self.handleError(record)

    def emit(self, record):
        """
        Split color mode (prefix and message in different color styles).
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            stream = self.stream
            msg1, msg2 = self.__spilt_msg(record.levelno, msg)
            if record.levelno == 10:
                # msg_color = ('\033[0;32m%s\033[0m' % msg)  # green
                msg_color = f'\033[0;32m{msg1}\033[0m \033[7;32m{msg2}\033[0m'  # green
            elif record.levelno == 20:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # cyan/blue 36    96
                msg_color = f'\033[0;{self.bule}m{msg1}\033[0m \033[7;{self.bule}m{msg2}\033[0m'
            elif record.levelno == 30:
                # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
                msg_color = f'\033[0;{self.yellow}m{msg1}\033[0m \033[7;{self.yellow}m{msg2}\033[0m'
            elif record.levelno == 40:
                # msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # magenta
                msg_color = f'\033[0;35m{msg1}\033[0m \033[7;35m{msg2}\033[0m'
            elif record.levelno == 50:
                # msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # red
                msg_color = f'\033[0;31m{msg1}\033[0m \033[7;31m{msg2}\033[0m'
            else:
                msg_color = msg
            # print(msg_color,'***************')
            stream.write(msg_color)
            stream.write(self.terminator)
            self.flush()
        except BaseException :
            self.handleError(record)

    @staticmethod
    def __spilt_msg(log_level, msg: str):
        split_text = '- LEVEL -'
        if log_level == 10:
            split_text = '- DEBUG -'
        elif log_level == 20:
            split_text = '- INFO -'
        elif log_level == 30:
            split_text = '- WARNING -'
        elif log_level == 40:
            split_text = '- ERROR -'
        elif log_level == 50:
            split_text = '- CRITICAL -'
        msg_split = msg.split(split_text, maxsplit=1)
        return msg_split[0] + split_text, msg_split[-1]

    def __repr__(self):
        level = logging.getLevelName(self.level)
        name = getattr(self.stream, 'name', '')
        if name:
            name += ' '
        return '<%s %s(%s)>' % (self.__class__.__name__, name, level)


logging.StreamHandler = ColorHandler  # REMIND This line is the monkey patch. Try commenting it out to compare.
"""
This is the monkey patch. It should be applied at the very beginning of the script, as early as possible.
Otherwise, scripts using `from logging import StreamHandler` won't get the colorful handler.
Only `import logging; logging.StreamHandler` usage will get the color. So the monkey patch should be applied early.
"""


def my_func():
    """
    Simulates regular console StreamHandler logging usage. Automatically becomes colorful.
    :return:
    """
    from logging import StreamHandler
    logger = logging.getLogger('abc')
    print(logger.handlers)
    print(StreamHandler().formatter)
    logger.addHandler(StreamHandler())
    logger.setLevel(10)
    print(logger.handlers)
    for _ in range(100):
        logger.debug('a debug level log' * 5)
        logger.info('an info level log' * 5)
        logger.warning('a warning level log' * 5)
        logger.error('an error level log' * 5)
        logger.critical('a critical level log' * 5)


if __name__ == '__main__':
    my_func()
