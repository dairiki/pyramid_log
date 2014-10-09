# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
from __future__ import absolute_import

import logging

from pyramid.request import Request
from pyramid import testing
import pytest

@pytest.fixture
def current_request(request):
    r = Request.blank('/')
    config = testing.setUp(request=r)
    request.addfinalizer(testing.tearDown)
    return r

@pytest.fixture
def log_record():
    return logging.LogRecord('test', logging.INFO, __file__, 0, 'msg', (), None)

class MockObject(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

class TestFormatter(object):
    def make_one(self, *args, **kwargs):
        from pyramid_log import Formatter
        return Formatter(*args, **kwargs)

    def test_init_raises_value_error(self):
        with pytest.raises(ValueError):
            self.make_one(style='$')

    def test_default_format(self, log_record):
        log_record.msg = 'the message'
        formatter = self.make_one()
        assert formatter.format(log_record) == 'the message'

    def test_with_explicit_request(self, log_record):
        log_record.request = Request.blank('/', POST={})
        formatter = self.make_one('${request.method}')
        assert formatter.format(log_record) == 'POST'

    def test_with_threadlocal_request(self, current_request, log_record):
        formatter = self.make_one('${request.method}')
        assert formatter.format(log_record) == 'GET'

    def test_format_time(self, log_record):
        formatter = self.make_one(fmt="${'='.join(['asctime', asctime])}",
                                  datefmt='DATEFMT')
        assert formatter.format(log_record) == 'asctime=DATEFMT'

    @pytest.mark.parametrize('expr,expected', [
        ('False', 'False'),
        ('True', 'True'),
        ('None', ''),
        ('[1,1+1]', '[1, 2]'),
        ])
    def test_format_expr(self, log_record, expr, expected):
        formatter = self.make_one('${%s}' % expr)
        assert formatter.format(log_record) == expected

    def test_format_called_with_log_disabled(self, log_record):
        manager = logging.root.manager
        class MockRequest(object):
            @property
            def disable(self):
                return manager.disable
        log_record.request = MockRequest()
        formatter = self.make_one('${request.disable}')
        assert formatter.format(log_record) == '%d' % log_record.levelno
        # Check that manager.disable is restored
        assert not manager.disable

class TestReplaceDict(object):
    def make_one(self, obj, d):
        from pyramid_log import _ReplaceDict
        return _ReplaceDict(obj, d)

    def test_getattr(self):
        class Obj(object):
            def m(self):
                return 'foo'
        obj = Obj()
        proxy = self.make_one(obj, {'x': 'bar'})
        assert proxy.m() == 'foo'
        assert proxy.x == 'bar'

    def test_setattr_modifies_proxy(self):
        obj = MockObject(x='orig')
        d = {}
        proxy = self.make_one(obj, d)
        proxy.x = 'changed'
        assert d['x'] == 'changed'
        assert obj.x == 'orig'

    def test_init_with_explicit_dict(self):
        obj = object()
        d = {}
        proxy = self.make_one(obj, d)
        assert proxy.__dict__ is d
