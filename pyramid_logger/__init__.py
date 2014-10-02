# -*- coding: utf-8 -*-
""" A logging adapter for pyramid

This implements a logging adapter which adds little request-specific bits
to log records (so that they may be reference in log format strings.)

"""
from __future__ import absolute_import

import logging
from logging import Logger, LoggerAdapter
import sys
from weakref import WeakKeyDictionary

from pyramid.compat import text_type, PY3
from pyramid.decorator import reify
from pyramid.interfaces import IRequest
from pyramid.threadlocal import get_current_request

REQUEST_ATTRIBUTES = [
    'unauthenticated_userid',
    'authenticated_userid',
    #'effective_principals',
    'client_addr',
    'remote_addr',
    'method',
    'url',
    #'application_url',
    'path',
    'script_name',
    'path_info',
    'path_url',
    'path_qs',
    'query_string',
    'scheme',
    #'server_name',
    #'server_port',
    'traversed',
    'subpath',
    'view_name',
    'matchdict',
    #'matched_route', FIXME: need route_name
    'locale_name',
    'GET',
    'POST',
    'params',
    'accept',
    'accept_charset',
    'accept_encoding',
    'accept_language',
    'authorization',
    'cache_control',
    'content_length',
    'content_type',
    'cookies',
    #'date',
    'domain',
    #'headers',
    'host',
    'host_port',
    'host_url',
    'http_version',
    #'if_match', # FIXME: et al
    'is_xhr',
    #localizer FIXME: ???
    #'max_forwards',
    #'pragma',
    #range
    'user_agent',
    #referer
    #referrer
    #remote_user
    #body
    #text
    ]

class deferred_value(object):
    def __init__(self, getter):
        self.getter = getter

    @property
    def value(self):
        return self.getter()

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return text_type(self.value)

    if not PY3:
        __unicode__ = __str__

        def __str__(self):
            return unicode(self).encode(sys.getdefaultencoding(), 'replace')

def deferred_request_attribute(request, attr):
    if request is None:
        return None
    else:
        return deferred_value(lambda : getattr(request, attr))


def extra_data(request):
    return [(attr, deferred_request_attribute(request, attr))
            for attr in REQUEST_ATTRIBUTES]

extra_data_cache = WeakKeyDictionary()

def get_extra_data(request):
    try:
        return extra_data_cache[request]
    except KeyError:
        extra = extra_data_cache[request] = extra_data(request)
        return extra

#FIXME: delete?
class PyramidContextFilter(object):
    """ A logging filter which adds attributes of the current pyramid request
    to the log record.

    """
    def __init__(self, request=get_current_request):
        self.request = request

    def filter(self, record):
        request = self.request
        if not IRequest.providedBy(request) and callable(request):
            request = request()
        # FIXME: check that attribute doesn't already exist?
        record.__dict__.update(get_extra_data(request))
        return True


# FIXME: rename to just Formatter?
class PyramidFormatter(logging.Formatter):
    ''' A logging formatter which makes some attributes of the current
    pyramid request available for use in its format string.

    Example usage::

        import logging
        import sys
        import pyramid_logger

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(pyramid_logger.PyramidFormatter(
            "%(asctime)s %(unauthenticated_userid)s [%(client_addr)s]"
            " %(method)s %(path_qs)\n"
            "    %(levelname)s %(message)s"))
        root = logging.getLogger()
        root.addHandler(handler)
        root.warning("Say: %s", "howdy")

    which will produce a log message like:

        2014-10-01 17:55:02,001 user.principal [127.0.0.1] GET /page?arg=foo
            WARNING Say: howdy

    '''
    def format(self, record):
        # FIXME: check that attribute doesn't already exist?
        record.__dict__.update(self._extra_data())
        return logging.Formatter.format(self, record)

    get_current_request = staticmethod(get_current_request)

    def _extra_data(self):
        request = self.get_current_request()
        return get_extra_data(request)

# FIXME: delete below here
class PyramidLoggerAdapter(LoggerAdapter):
    def __init__(self, logger, extra=None, request=get_current_request):
        LoggerAdapter.__init__(self, logger, extra=None)
        self.extra = extra
        self.request = request

    def process(self, msg, kwargs):
        explicit_extra = kwargs.get('extra')
        request = self.request
        if not IRequest.providedBy(request) and callable(request):
            request = request()
        if self.extra:
            extra = self.extra.copy()
        else:
            extra = {}
        extra.update(get_extra_data(request))
        if explicit_extra:
            extra.update(explicit_extra)
        kwargs['extra'] = extra
        return msg, kwargs

    def isEnabledFor(self, level):
        return self.logger.isEnabledFor(level)

def getLogger(name=None, extra=None, request=get_current_request,
              adapter=PyramidLoggerAdapter):
    logger = logging.getLogger(name)
    return adapter(logger, extra, request)
