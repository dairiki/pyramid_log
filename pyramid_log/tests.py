# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
from __future__ import absolute_import

import logging
import math

from pyramid.request import Request
from pyramid import testing
import pytest

from ._compat import NativeIO, text_


@pytest.fixture
def current_request(request):
    r = Request.blank('/')
    testing.setUp(request=r)
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
        logger.warning("testing")
        assert logstream.getvalue() == "<DATE> GET /path?foo=bar : testing\n"

    def test_without_request(self, logstream):
        logger = logging.getLogger()
        logger.warning("is this thing on?")
        assert logstream.getvalue() == "<DATE> - - : is this thing on?\n"


@pytest.fixture
def log_record():
    return logging.LogRecord('test', logging.INFO, __file__, 0, '', (), None)


class TestFormatter(object):
    def make_one(self, *args, **kwargs):
        from pyramid_log import Formatter
        return Formatter(*args, **kwargs)

    def test_with_explicit_request(self, log_record):
        log_record.request = Request.blank('/', POST={})
        formatter = self.make_one('%(request.method)s')
        assert formatter.format(log_record) == 'POST'
        assert hasattr(log_record, 'request')

    def test_with_threadlocal_request(self, current_request, log_record):
        formatter = self.make_one('%(request.method)s')
        assert formatter.format(log_record) == 'GET'
        assert not hasattr(log_record, 'request')

    def test_with_no_request(self, log_record):
        formatter = self.make_one('%(request|no request)s')
        assert formatter.format(log_record) == 'no request'
        assert not hasattr(log_record, 'request')

    def test_format_asctime(self, log_record):
        formatter = self.make_one('asctime=%(asctime)s', datefmt="DATEFMT")
        assert formatter.format(log_record) == 'asctime=DATEFMT'

    def test_format_parentheses_in_fallback(self, log_record):
        formatter = self.make_one('%(request.method|(no request))s')
        assert formatter.format(log_record) == '(no request)'

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


class MockObject(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


class MockWrapper(object):
    def __init__(self, d):
        self.wrapped = d


class TestWrapDict(object):
    def make_one(self, obj, dictwrapper):
        from pyramid_log import _WrapDict
        return _WrapDict(obj, dictwrapper)

    def test_dict(self):
        obj = MockObject()
        proxy = self.make_one(obj, MockWrapper)
        assert type(proxy.__dict__) is MockWrapper
        assert proxy.__dict__.wrapped is obj.__dict__

    def test_getattr(self):
        class Obj(object):
            def m(self):
                return 'foo'
            x = 'bar'
        proxy = self.make_one(Obj(), MockWrapper)
        assert proxy.m() == 'foo'
        assert proxy.x == 'bar'
        with pytest.raises(AttributeError):
            proxy.y

    def test_setattr(self):
        obj = MockObject(x='orig')
        proxy = self.make_one(obj, MockWrapper)
        proxy.x = 'changed'
        assert proxy.x == 'changed'
        assert obj.x == 'changed'
        proxy.y = 'changed'
        assert proxy.y == 'changed'
        assert obj.y == 'changed'

    def test_delattr(self):
        obj = MockObject(x='orig')
        proxy = self.make_one(obj, MockWrapper)
        del proxy.x
        assert obj.__dict__ == {}


EURO_SIGN = text_('\N{EURO SIGN}', 'unicode-escape')


class TestMissing(object):
    def make_one(self, key, fallback=None):
        from pyramid_log import Missing
        return Missing(key, fallback)

    @pytest.mark.parametrize('fallback, expected', [
        (None, "<?attr.name?>"),
        ('foo', "'foo'"),
        (EURO_SIGN, repr(EURO_SIGN)),
        ])
    def test_repr(self, fallback, expected):
        missing = self.make_one("attr.name", fallback)
        assert repr(missing) == expected

    def test_repr_unicode_key(self):
        # carefully constructed to work in python 3.2
        missing = self.make_one(EURO_SIGN)
        assert repr(missing) in (
            r"<?\u20ac?>",              # py2
            "<?%s?>" % EURO_SIGN,       # py3k
            )

    def test_str(self):
        missing = self.make_one('key', "foo")
        assert str(missing) == "foo"

    @pytest.mark.parametrize('fallback, expected', [
        (None, 0),
        ('123', 123),
        ('foo', 0),
        ])
    def test_int(self, fallback, expected):
        missing = self.make_one('somekey', fallback)
        assert int(missing) == expected

    @pytest.mark.parametrize('fallback, expected', [
        ('123', 123.0),
        ('3.14', 3.14),
        ])
    def test_float(self, fallback, expected):
        missing = self.make_one('somekey', fallback)
        assert float(missing) == expected

    def test_float_default_fallback(self):
        missing = self.make_one('somekey', None)
        assert math.isnan(float(missing))

    def test_float_not_a_number(self):
        missing = self.make_one('somekey', 'notanumber')
        assert math.isnan(float(missing))

    @pytest.mark.parametrize('fallback, asint, asfloat', [
        ('foo', '0', 'nan'),
        ('12', '12', '12.00'),
        ])
    def test_format(self, fallback, asint, asfloat):
        missing = self.make_one('key', fallback)
        assert '%s' % missing == fallback
        assert '%r' % missing == repr(fallback)
        assert '%d' % missing == asint
        assert '%.2f' % missing == asfloat

    def test_format_unicode(self):
        missing = self.make_one('key', EURO_SIGN)
        # missing.__str__()
        assert '%s' % missing in (
            r'\u20ac',                  # py2
            EURO_SIGN,                  # py3k
            )
        # This tests missing.__unicode__() under python 2
        assert text_('%s') % missing == EURO_SIGN


class TestDottedLookup(object):
    def make_one(self, dict_):
        from pyramid_log import _DottedLookup
        return _DottedLookup(dict_)

    def test_dotted_attribute_lookup(self):
        d = self.make_one({'a': MockObject(b=MockObject(c='d'))})
        assert d['a.b.c'] == 'd'

    def test_getitem_lookup(self):
        d = self.make_one({'a': {'b': 'c'}})
        assert d['a.b'] == 'c'

    def test_fallback(self):
        d = self.make_one({'a': MockObject(b='x')})
        assert str(d['c|rats']) == 'rats'
        assert str(d['a.c|rats']) == 'rats'
        assert str(d['a.b.c|rats']) == 'rats'

    def test_default_fallback(self):
        d = self.make_one({'a': MockObject(b='x')})
        assert str(d['missing-key']) == '<?missing-key?>'
        assert str(d['a.missing-key']) == '<?a.missing-key?>'
