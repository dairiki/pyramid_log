# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
from __future__ import absolute_import

import logging
import math

from pyramid.compat import NativeIO, text_
from pyramid.request import Request
from pyramid import testing
import pytest

@pytest.fixture
def current_request(request):
    r = Request.blank('/')
    config = testing.setUp(request=r)
    request.addfinalizer(testing.tearDown)
    return r

class TestIntegration(object):
    """ Integration tests.

    """
    @pytest.fixture
    def logstream(self, monkeypatch):
        """ Patch the root logger to log to an in-memory stream.
        """
        import pyramid_log
        logstream = NativeIO()
        root = logging.getLogger()
        monkeypatch.setattr(root, 'handlers', [])
        handler = logging.StreamHandler(logstream)
        fmt = ("%(asctime)s "
               "%(request.method|-)s %(request.path_qs|-)s : "
               "%(message)s")
        formatter = pyramid_log.Formatter(fmt, datefmt="<DATE>")
        handler.setFormatter(formatter)
        root.addHandler(handler)
        return logstream

    def test_with_request(self, logstream, current_request):
        current_request.GET['foo'] = 'bar'
        current_request.path_info = '/path'
        logger = logging.getLogger()
        logger.warn("testing")
        assert logstream.getvalue() == "<DATE> GET /path?foo=bar : testing\n"

    def test_without_request(self, logstream):
        logger = logging.getLogger()
        logger.warn("is this thing on?")
        assert logstream.getvalue() == "<DATE> - - : is this thing on?\n"

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

    def test_format_asctime(self, current_request, log_record):
        formatter = self.make_one('asctime=%(asctime)s', datefmt="DATEFMT")
        assert formatter.format(log_record) == 'asctime=DATEFMT'

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
        d = {'x': 'bar'}
        proxy = self.make_one(obj, d)
        assert proxy.m() == 'foo'
        assert proxy.x == 'bar'
        assert proxy.__dict__ is d

    def test_setattr_modifies_proxy(self):
        obj = MockObject(x='orig')
        d = {}
        proxy = self.make_one(obj, d)
        proxy.x = 'changed'
        assert d['x'] == 'changed'
        assert obj.x == 'orig'

    def test_delattr_not_supported(self):
        proxy = self.make_one(object(), {'x': 1})
        with pytest.raises(NotImplementedError):
            del proxy.x

class TestMissing(object):
    def make_one(self, strval):
        from pyramid_log import Missing
        return Missing(strval)

    def test_repr(self):
        missing = self.make_one("foo")
        assert repr(missing) == "Missing('foo')"

    def test_repr_unicode_strval(self):
        # carefully constructed to work in python 3.2
        euro_sign = text_('\N{EURO SIGN}', 'unicode-escape')
        missing = self.make_one(euro_sign)
        assert repr(missing) in (
            r"Missing(u'\u20ac')",       # py2
            "Missing('%s')" % euro_sign, # py3k
            )

    def test_str(self):
        missing = self.make_one("foo")
        assert str(missing) == "foo"

    @pytest.mark.parametrize('strval, expected', [
        ('123', 123),
        ('foo', 0),
        ])
    def test_int(self, strval, expected):
        missing = self.make_one(strval)
        assert int(missing) == expected

    @pytest.mark.parametrize('strval, expected', [
        ('123', 123.0),
        ('3.14', 3.14),
        ])
    def test_float(self, strval, expected):
        missing = self.make_one(strval)
        assert float(missing) == expected

    def test_float_nan(self):
        missing = self.make_one('foo')
        assert math.isnan(float(missing))

class TestMagicDict(object):
    def make_one(self, *args, **kwargs):
        from pyramid_log import _MagicDict
        return _MagicDict(*args, **kwargs)

    def test_chained_getitem(self):
        d = self.make_one({'a': MockObject(b='x')})
        assert d['a.b'] == 'x'

    def test_fallback(self):
        d = self.make_one({'a': MockObject(b='x')})
        assert str(d['c|rats']) == 'rats'
        assert str(d['a.c|rats']) == 'rats'
        assert str(d['a.b.c|rats']) == 'rats'

    def test_default_fallback(self):
        d = self.make_one({'a': MockObject(b='x')})
        assert str(d['missing-key']) == '?missing-key?'
        assert str(d['a.missing-key']) == '?a.missing-key?'
