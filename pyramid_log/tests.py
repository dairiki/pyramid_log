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
    return logging.LogRecord('test', logging.INFO, __file__, 0, '', (), None)

class MockObject(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

class TestFormatter(object):
    def make_one(self, *args, **kwargs):
        from pyramid_log import Formatter
        return Formatter(*args, **kwargs)

    def test_with_explicit_request(self, log_record):
        log_record.request = Request.blank('/', POST={})
        formatter = self.make_one('%(request.method)s')
        assert formatter.format(log_record) == 'POST'

    def test_with_threadlocal_request(self, current_request, log_record):
        formatter = self.make_one('%(request.method)s')
        assert formatter.format(log_record) == 'GET'

    def test_format_called_with_log_disabled(self, log_record):
        manager = logging.root.manager
        class MockRequest(object):
            @property
            def disable(self):
                return manager.disable
        log_record.request = MockRequest()
        formatter = self.make_one('%(request.disable)s')
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

class TestChainingDict(object):
    def make_one(self, *args, **kwargs):
        from pyramid_log import _ChainingDict
        return _ChainingDict(*args, **kwargs)

    def test_chained_getitem(self):
        d = self.make_one({'a': {'b': 'x'}})
        assert d['a.b'] == 'x'

    def test_key_error(self):
        d = self.make_one()
        with pytest.raises(KeyError):
            d['missing']
        with pytest.raises(KeyError):
            d['missing.b']

class TestGetitemProxy(object):
    def make_one(self, wrapped):
        from pyramid_log import _GetitemProxy
        return _GetitemProxy(wrapped)

    def test_proxy(self):
        proxy = self.make_one(MockObject(x=1))
        assert proxy.x == 1
        assert isinstance(proxy, MockObject)

    def test_getitem(self):
        proxy = self.make_one(MockObject(x=42))
        assert proxy['x'] == 42
        assert proxy['missing'] is None

    def test_chained_attribute_access(self):
        proxy = self.make_one(MockObject(x=MockObject(y=42)))
        assert proxy['x.y'] == 42
        assert proxy['missing.y'] is None
        assert proxy['x.missing'] is None

    def test_proxy_none(self):
        proxy = self.make_one(None)
        assert proxy['foo'] is None
        assert isinstance(proxy, type(None))

    def test_getitem_returns_none_on_exception(self):
        class Obj(object):
            @property
            def err(self):
                raise RuntimeError()
        proxy = self.make_one(Obj())
        assert proxy['err'] is None
