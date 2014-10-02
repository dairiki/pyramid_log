# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

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

def test_formatter(request, pyramid_config):
    from pyramid_logger import PyramidFormatter
    req = Request.blank('http://example.org/p/?foo=bar')
    pyramid_config.begin(req)
    request.addfinalizer(pyramid_config.end)

    record = logging.LogRecord('test', logging.INFO, __file__, 0, '', (), None)
    formatter = PyramidFormatter('%(path_qs)s')
    assert formatter.format(record) == '/p/?foo=bar'
