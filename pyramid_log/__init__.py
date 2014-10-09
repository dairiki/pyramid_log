# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
""" A logging formatter which make pyramid request attributes available
for use in log messages.

"""
from __future__ import absolute_import

import logging
import sys
from pyramid.compat import PY3, native_, text_type
from pyramid.threadlocal import get_current_request

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

        This version is special in that it makes attributes of the
        pyramid request available for use in the log message.  For
        example, the request method may be interpolated into the log
        message by including ``'%(request.method)s'`` within the
        format string.

        See :meth:`logging.Formatter.format` for further details.

        """
        d = _MagicDict(record.__dict__)
        if not hasattr(record, 'request'):
            d['request'] = get_current_request()
        # Owing to a surfeit of multi-thread angst, instead of
        # directly replacing record.__dict__, we do this with a proxy
        # so as to avoid ever modifying the original log record.
        record = _ReplaceDict(record, d)

        # Disable logging during disable to prevent recursion (in case
        # a logged request property generates a log message)
        save_disable = logging.root.manager.disable
        logging.disable(record.levelno)
        try:
            return logging.Formatter.format(self, record)
        finally:
            logging.disable(save_disable)

class _ReplaceDict(object):
    """ A minimal object proxy which “replaces” the objects ``__dict__``.

    """
    __slots__ = ['dict', 'wrapped']

    def __init__(self, wrapped, dict_):
        object.__setattr__(self, 'wrapped', wrapped)
        object.__setattr__(self, 'dict', dict_)

    def __getattribute__(self, attr):
        dict_ = object.__getattribute__(self, 'dict')
        if attr == '__dict__':
            return dict_
        elif attr in dict_:
            return dict_[attr]
        else:
            wrapped = object.__getattribute__(self, 'wrapped')
            return getattr(wrapped, attr)

    def __setattr__(self, attr, value):
        dict_ = object.__getattribute__(self, 'dict')
        dict_[attr] = value

    def __delattr__(self, attr):
        raise NotImplementedError()


class Missing(object):
    def __init__(self, strval):
        self.strval = text_type(strval)

    def __repr__(self):
        strval = self.strval
        try:
            # Do this to avoid the anoying u in the Missing(u'foo')
            strval = native_(strval, 'ascii')
        except UnicodeEncodeError:
            pass
        return '%s(%r)' % (self.__class__.__name__, strval)

    def __str__(self):
        return self.strval

    if not PY3:                         # pragma: no branch
        __unicode__ = __str__

        def __str__(self):
            encoding = sys.getdefaultencoding()
            return self.__unicode__().encode(encoding, 'replace')

    def __int__(self):
        try:
            return int(self.strval)
        except ValueError:
            return 0

    def __float__(self):
        try:
            return float(self.strval)
        except ValueError:
            return float('NaN')

_marker = object()

class _MagicDict(dict):
    """ A dict which supports dotted-key chained lookup, with fallbacks
    if the lookup fails.

    Example::

        >>> d = _MagicDict({'a': {'b': 'foo'}})
        >>> d['a.b']                    # same as d['a']['b']
        'foo'

    Fallback values are appended after a pipe (``|``)::

        >>> d['a.b|fb']                 # same as d['a']['b']
        'foo'
        >>> d['a.z|fb']                 # there is non d['a']['z']
        'fb'

    """
    def __getitem__(self, key):
        key, pipe, fallback = key.partition('|')
        if not pipe:
            fallback = '?%s?' % key
        parts = key.split('.')
        try:
            v = dict.__getitem__(self, parts[0])
            for i, part in enumerate(parts[1:]):
                a = getattr(v, part, _marker)
                v = a if a is not _marker else v[part]
        except (LookupError, TypeError):
            return Missing(fallback)
        else:
            return v
