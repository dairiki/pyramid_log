# -*- coding: utf-8 -*-
""" A logging adapter for pyramid

This implements a logging adapter which adds little request-specific bits
to log records (so that they may be reference in log format strings.)

"""
from __future__ import absolute_import

import logging
from logging import LoggerAdapter
import sys
from weakref import WeakKeyDictionary

from pyramid.compat import text_type, PY3
from pyramid.decorator import reify
from pyramid.interfaces import IRequest
from pyramid.threadlocal import get_current_request

REQUEST_ATTRIBUTES = [
    'unauthenticated_userid',
    'authenticated_userid',
    'client_addr',
    'method',
    'url',
    'path',
    'path_info',
    'path_qs',
    'qs',
    ]

class deferred_value(object):
    def __init__(self, getter):
        self.getter = getter

    @reify
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
    return dict((attr, deferred_request_attribute(request, attr))
                for attr in REQUEST_ATTRIBUTES)

extra_data_cache = WeakKeyDictionary()

def get_extra_data(request):
    try:
        return extra_data_cache[request]
    except KeyError:
        extra = extra_data_cache[request] = extra_data(request)
        return extra

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

def getLogger(name=None, extra=None, request=get_current_request,
              adapter=PyramidLoggerAdapter):
    logger = logging.getLogger(name)
    return adapter(logger, extra, request)
