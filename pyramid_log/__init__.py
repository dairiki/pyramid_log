# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
""" A logging formatter which make pyramid request attributes available
for use in log messages.

"""
from __future__ import absolute_import

import logging
from pyramid.threadlocal import get_current_request

from . import compat

class Formatter(compat.Formatter):
    ''' A logging formatter which makes attributes of the pyramid
    request available for use in its format string.

    Note that this uses a new-style format string (with replace fields
    delimited by curly braces ``{}`` rather than the printf-style format
    string used by :cls:`logging.Formatter`.

    Example usage::

        import logging
        import sys
        import pyramid_log

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(pyramid_log.Formatter(
            "{asctime} {request.unauthenticated_userid} "
            "[{request.client_addr}]\\n"
            "  {request.method} {request.path_qs}\\n"
            "  {levelname} {message}"))
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
    def __init__(self, fmt=None, datefmt=None, style='{'):
        compat.Formatter.__init__(self, fmt, datefmt, style)

    def format(self, record):
        """ Format the specific record as text.

        This version is special in that it makes attributes of the
        pyramid request available for use in the log message.  For
        example, the request method may be interpolated into the log
        message by including ``{request.method}`` within the format
        string.

        See :meth:`logging.Formatter.format` for further details.

        """
        if not hasattr(record, 'request'):
            # Temporarily add request to record's dict.  Out of of
            # surfeit of paranoia, we do this with a proxy so as to
            # avoid ever modifying the original log record.
            d = dict(record.__dict__, request=get_current_request())
            record = _ReplaceDict(record, d)

        save_disable = logging.root.manager.disable
        # disable logging during formatting to prevent recursion
        # (in case a logged request property generates a log message)
        logging.disable(record.levelno)
        try:
            return compat.Formatter.format(self, record)
        finally:
            logging.disable(save_disable)

class _ReplaceDict(object):
    """ A minimal object proxy which “replaces” the objects ``__dict__``.

    """
    __slots__ = ['__dict__', '_wrapped']

    def __init__(self, wrapped, d):
        self._wrapped = wrapped
        self.__dict__ = d

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)
