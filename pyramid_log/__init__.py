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
from zope.proxy import ProxyBase

class Formatter(logging.Formatter):
    ''' A logging formatter which makes attributes of the pyramid
    request available for use in its format string.

    Example usage::

        import logging
        import sys
        import pyramid_log

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(pyramid_log.Formatter(
            "%(asctime)s %(request.unauthenticated_userid)s "
            "[%(request.client_addr)s]\\n"
            "  %(request.method)s %(request.path_qs)\\n"
            "  %(levelname)s %(message)s"))
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
    def format(self, record):
        """ Format the specific record as text.

        This version special in that it makes attributes of the
        pyramid request available for use in the log message.  For
        example, the request method may be interpolated into the log
        message by including ``'%(request.method)s'`` within the format
        string.

        See :meth:`logging.Formatter.format` for further details.

        """
        if hasattr(record, 'request'):
            request = record.request
        else:
            request = get_current_request()

        d = _ChainingDict(record.__dict__)
        d['request'] = _GetitemProxy(request)

        # disable logging during disable to prevent recursion
        # (in case a logged request property generates a log message)
        save_disable = logging.root.manager.disable
        logging.disable(record.levelno)
        try:
            return logging.Formatter.format(self, _ReplaceDict(record, d))
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

class _ChainingDict(dict):
    """ A dict which supports dotted-key chained lookup.

    Example::

        >>> d = ChainingDict({'a': {'b': 'foo'}})
        >>> d['a.b']                    # same as d['a']['b']
        'foo'


    """
    def __missing__(self, key):
        left, dot, right = key.partition('.')
        if not dot:
            raise KeyError(key)
        try:
            return self[left][right]
        except KeyError:
            raise KeyError(key)

class _GetitemProxy(ProxyBase):
    """ A proxy which adds dict-like read-only access to an object’s
    attributes.

    Attribute chaining is supported using a dotted-key notation.

    Dictionary access to non-existant attributes returns None.

    Example usage::

        >>> d = GetitemProxy(request)

        >>> d['path']                   # gets request.path
        u '/foo'

        >>> d['matched_route.name']     # gets request.matched_route.name
        'foo_route'

        >>> d['unknown_attr']           # Missing attributes => None
        None

    """
    def __getitem__(self, key):
        val = self
        try:
            for attr in key.split('.'):
                val = getattr(val, attr)
        except:
            val = None
        return val
