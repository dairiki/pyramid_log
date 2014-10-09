# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
""" A logging formatter which make pyramid request attributes available
for use in log messages.

"""
from __future__ import absolute_import

import _ast
import ast
import logging

from chameleon import PageTextTemplate
from pyramid.compat import text_type
from pyramid.threadlocal import get_current_request

_marker = object()

class Formatter(logging.Formatter):
    ''' A logging formatter which makes attributes of the pyramid
    request available for use in its format string.

    Note that this uses a Chameleon_ text format string rather than
    the printf-style format string used by :cls:`logging.Formatter`.

    .. _Chameleon: http://chameleon.readthedocs.org/en/latest/

    Example usage::

        import logging
        import sys
        import pyramid_log

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(pyramid_log.Formatter(
            "${asctime} ${request.unauthenticated_userid|'-'} "
            "[${request.client_addr|'-'}]\\n"
            "  ${request.method|''} ${request.path_qs|''}\\n"
            "  ${levelname} ${message}"))
        root = logging.getLogger()
        root.addHandler(handler)
        root.warning("Say: %s", "howdy")

    which will produce a log message like::

        2014-10-01 17:55:02,001 user.principal [127.0.0.1]
          GET /page?arg=foo
          WARNING Say: howdy

    Passing an explicit request instance
    ====================================

    When generating a log message, the request instance may be passed
    in the ``extra`` dict, e.g.::

        log.warning("Foo: %s", "bar", extra={"request": request})

    If no request is explicitly set,
    :func:`pyramid.threadlocal.get_current_request` is called to
    determine the current request.

    '''
    default_format = '${message}'

    def __init__(self, fmt=None, datefmt=None, style=_marker):
        if style is not _marker:
            raise ValueError(
                "Unsupported style. Only chameleon format strings are "
                "supported by this formatter.")
        if not fmt:
            fmt = self.default_format
        # literal_false=True makes False expand to "False" (by
        # default, False exapands to the empty string.)
        template = PageTextTemplate(fmt, keep_source=True, literal_false=True)
        self.referenced_names = set(_referenced_names(template.source))
        del template.source
        logging.Formatter.__init__(self, _FormatString(fmt, template), datefmt)

    def format(self, record):
        """ Format the specific record as text.

        This version is special in that it makes attributes of the
        pyramid request available for use in the log message.  For
        example, the request method may be interpolated into the log
        message by including ``'${request.method}'`` within the
        format string.

        See :meth:`logging.Formatter.format` for further details.

        """
        referenced_names = self.referenced_names
        if 'request' in referenced_names:
            if not hasattr(record, 'request'):
                # Temporarily add request to record's dict.  Out of a
                # surfeit of multi-thread angst, we do this with a
                # proxy so as to avoid ever modifying the original log
                # record.
                request = get_current_request()
                d = dict(record.__dict__, request=request)
                record = _ReplaceDict(record, d)
        if 'asctime' in referenced_names:
            record.asctime = self.formatTime(record, self.datefmt)

        # disable logging during disable to prevent recursion
        # (in case a logged request property generates a log message)
        save_disable = logging.root.manager.disable
        logging.disable(record.levelno)
        try:
            return logging.Formatter.format(self, record)
        finally:
            logging.disable(save_disable)

class _FormatString(text_type):
    # Use a custom __mod__ to to fake out logging.Formatter into using
    # our template for formatting
    def __new__(typ, str, template):
        return text_type.__new__(typ, str)

    def __init__(self, str, template):
        self.template = template

    def __mod__(self, d):
        return self.template.render(**d)

def _referenced_names(template_source):
    """ Get referenced names from chameleon template source.

    """
    # Find calls to ``getitem('NAME')``
    tree = ast.parse(template_source)
    for node in ast.walk(tree):
        if isinstance(node, _ast.Call) \
               and isinstance(node.func, _ast.Name) \
               and node.func.id == 'getitem':
            assert list(map(type, node.args)) == [_ast.Str]
            yield node.args[0].s

class _ReplaceDict(object):
    """ A minimal object proxy which “replaces” the objects ``__dict__``.

    """
    __slots__ = ['__dict__', '_wrapped']

    def __init__(self, wrapped, d):
        self._wrapped = wrapped
        self.__dict__ = d

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)
