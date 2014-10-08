# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
""" Compatibility bits for python 2.

This provides a logging formatter which supports ``str.format`` style
formatting.

"""
from __future__ import absolute_import

from inspect import getargspec
import logging
from pyramid.compat import text_type

class StrFormatFormatter(logging.Formatter):
    """ A logging.Formatter which supports str.format style formatting.

    The stock ``logging.Formatter`` in Python >= 3.2 already provides
    this functionality.  This is a replacement for use with Python < 3.2.

    It is broken in that it only supports ``style='{'`` (but that’s all
    we need for our purposes.)

    """
    def __init__(self, fmt=None, datefmt=None, style='{'):
        if fmt is None:
            fmt = '{message}'
        if style != '{':
            raise ValueError(
                "This formatter supports only style '{', not %r" % style)
        fmt = _FormatString(fmt)
        logging.Formatter.__init__(self, fmt, datefmt)

    def usesTime(self):
        return self._fmt.find('{asctime') >= 0

    def format(self, record):
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        return logging.Formatter.format(self, record)


class _FormatString(text_type):
    """ Use new-style format strings where printf-style strings are expected.

    This overrides the modulo operator (``%``) so that it invokes the
    :meth:`format` method of the string.  This allows (in some cases)
    passing a new style format string to a function expecting a printf-style
    string.

    """
    def __mod__(self, d):
        return self.format(**d)

if 'style' in getargspec(logging.Formatter.__init__).args:
    # Py3k
    Formatter = logging.Formatter       # pragma: NO COVER
else:
    # Python 2, Formatter does not support the ``style`` argument
    Formatter = StrFormatFormatter
