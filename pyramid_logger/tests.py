# -*- coding: utf-8 -*-
from __future__ import absolute_import

from pyramid.compat import text_type
from pyramid.request import Request
from pyramid import testing
import pytest

@pytest.fixture
def pyramid_config(request):
    config = testing.setUp()
    request.addfinalizer(testing.tearDown)
    return config

def test_deferred_value():
    from pyramid_logger import deferred_value

    class MockValue(object):
        def __int__(self):
            return 42

        def __float__(self):
            return 3.14159

        def __str__(self):
            return 'strval'
        __unicode__ = __str__

        def __repr__(self):
            return '<repr>'

    x = deferred_value(MockValue)

    assert "%d" % x == "42"
    assert "%.1f" % x == "3.1"
    assert "%r" % x == "<repr>"
    assert "%s" % x == "strval"
    # This tests deferred.__unicode__ under py2
    assert text_type("%s") % x == "strval"

def test_extra_data(pyramid_config):
    from pyramid_logger import extra_data
    pyramid_config.testing_securitypolicy('joe')
    request = Request.blank('http://example.org/p/?foo=bar')
    extra = dict(extra_data(request))
    assert str(extra['unauthenticated_userid']) == 'joe'
    assert str(extra['method']) == 'GET'
    assert str(extra['path_qs']) == '/p/?foo=bar'

def test_extra_data_with_no_request():
    from pyramid_logger import extra_data, REQUEST_ATTRIBUTES
    extra = set(extra_data(None))
    assert extra == set((attr, None) for attr in REQUEST_ATTRIBUTES)

class TestPyramidLoggerAdapter(object):

    def test_with_threadlocal_request(self, request, pyramid_config):
        from pyramid_logger import PyramidLoggerAdapter

        req = Request.blank('http://example.org/p/?foo=bar')
        pyramid_config.begin(request=req)
        request.addfinalizer(pyramid_config.end)
        logger = 'ignored'

        adapter = PyramidLoggerAdapter(logger)
        msg, kwargs = adapter.process('foo', {})
        assert msg == 'foo'
        assert "%(method)s" % kwargs['extra'] == 'GET'

    def test_with_explicit_request(self, pyramid_config):
        from pyramid_logger import PyramidLoggerAdapter
        req = Request.blank('http://example.org/p/?foo=bar')
        logger = 'ignored'

        adapter = PyramidLoggerAdapter(logger, request=req)
        msg, kwargs = adapter.process('foo', {})
        assert msg == 'foo'
        assert "%(method)s" % kwargs['extra'] == 'GET'

    def test_with_extras(self, pyramid_config):
        from pyramid_logger import PyramidLoggerAdapter
        req = Request.blank('http://example.org/p/?foo=bar')
        extra = {'bar': 'baz'}
        logger = 'ignored'

        adapter = PyramidLoggerAdapter(logger, request=req, extra=extra)
        msg, kwargs = adapter.process('foo', {})
        assert msg == 'foo'
        assert "%(bar)s" % kwargs['extra'] == 'baz'

    def test_with_explicit_extras(self, pyramid_config):
        from pyramid_logger import PyramidLoggerAdapter
        req = Request.blank('http://example.org/p/?foo=bar')
        extra = {'bar': 'baz'}
        logger = 'ignored'

        adapter = PyramidLoggerAdapter(logger, request=req)
        msg, kwargs = adapter.process('foo', {'extra': extra})
        assert msg == 'foo'
        assert "%(bar)s" % kwargs['extra'] == 'baz'

def test_getLogger():
    from pyramid_logger import getLogger
    adapter = getLogger('foo', adapter=MockLoggingAdapter)
    assert type(adapter) == MockLoggingAdapter
    assert adapter.args[0].name == 'foo'

class MockLoggingAdapter(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
