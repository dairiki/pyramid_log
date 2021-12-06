#
# Copyright © 2014–2021 Geoffrey T. Dairiki <dairiki@dairiki.org>
#

import io
import logging
import math
import sys

from pyramid.request import Request
from pyramid import testing
import pytest

from pyramid_log import (
    _add_request_attr,
    logging_disabled,
    _DottedLookup,
    Formatter,
    Missing,
    _WrapDict,
)


@pytest.fixture
def current_request(request):
    r = Request.blank('/')
    testing.setUp(request=r)
    request.addfinalizer(testing.tearDown)
    return r


class TestIntegration:
    """ Integration tests.

    """
    @pytest.fixture
    def logstream(self, monkeypatch):
        """ Patch the root logger to log to an in-memory stream.
        """
        logstream = io.StringIO()
        root = logging.getLogger()
        monkeypatch.setattr(root, 'handlers', [])
        handler = logging.StreamHandler(logstream)
        fmt = ("%(asctime)s "
               "%(request.method|-)s %(request.path_qs|-)s : "
               "%(message)s")
        handler.setFormatter(Formatter(fmt, datefmt="<DATE>"))
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


requires_validate = pytest.mark.skipif(sys.version_info < (3, 8),
                                       reason="validate requires python>=3.8")


class TestFormatter:
    def test_init_with_unsupported_style(self):
        with pytest.raises(ValueError):
            Formatter('formatstr', style='$')

    @requires_validate
    def test_init_warns_if_validation_requested(self):
        with pytest.warns(UserWarning, match='validate'):
            Formatter('%(request.method)s', validate=True)

    @requires_validate
    @pytest.mark.filterwarnings("error")
    def test_init_accepts_validate_for_strformat(self):
        Formatter('{request.method}', style='{', validate=True)

    def test_with_explicit_request(self, log_record):
        log_record.request = Request.blank('/', POST={})
        formatter = Formatter('%(request.method)s')
        assert formatter.format(log_record) == 'POST'

    def test_with_threadlocal_request(self, current_request, log_record):
        formatter = Formatter('%(request.method)s')
        assert formatter.format(log_record) == 'GET'

    def test_strformat_style(self, current_request, log_record):
        formatter = Formatter('{request.method}', style='{')
        assert formatter.format(log_record) == 'GET'

    @pytest.mark.xfail(strict=True)
    def test_strformat_style_missing(self, current_request, log_record):
        formatter = Formatter('{request.foo}', style='{')
        assert formatter.format(log_record) == 'GET'

    def test_with_no_request(self, log_record):
        formatter = Formatter('%(request|no request)s')
        assert formatter.format(log_record) == 'no request'

    def test_format_asctime(self, log_record):
        formatter = Formatter('asctime=%(asctime)s', datefmt="DATEFMT")
        assert formatter.format(log_record) == 'asctime=DATEFMT'

    def test_format_parentheses_in_fallback(self, log_record):
        formatter = Formatter('%(request.method|(no request))s')
        assert formatter.format(log_record) == '(no request)'


class MockObject:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class MockWrapper:
    def __init__(self, d):
        self.wrapped = d


class Test_add_request_attr:
    @pytest.fixture
    def record(self):
        return MockObject()

    def test_adds_threadlocal_request(self, record, current_request):
        with _add_request_attr(record):
            assert record.request is current_request
        assert not hasattr(record, 'request')

    def test_explicit_request(self, record, current_request):
        explicit_request = object()
        record.request = explicit_request
        with _add_request_attr(record):
            assert record.request is explicit_request
        assert record.request is explicit_request

    def test_no_request(self, record):
        with _add_request_attr(record):
            assert not hasattr(record, 'request')

    def test_target_is_record(self, record, current_request):
        with _add_request_attr(record) as record_with_request:
            assert record is record_with_request


class Test_logging_disabled:
    def test(self):
        assert logging.root.manager.disable == 0
        with logging_disabled(logging.WARNING):
            assert logging.root.manager.disable == logging.WARNING
        assert logging.root.manager.disable == 0

    def test_disables_logging(self, caplog):
        with logging_disabled(logging.WARNING):
            logging.warning("a warning")
            assert len(caplog.records) == 0
            logging.error("an error")
            assert len(caplog.records) == 1
        logging.warning("another warning")
        assert len(caplog.records) == 2


class TestWrapDict:
    def test_dict(self):
        obj = MockObject()
        proxy = _WrapDict(obj, MockWrapper)
        assert type(proxy.__dict__) is MockWrapper
        assert proxy.__dict__.wrapped is obj.__dict__

    def test_getattr(self):
        class Obj:
            def m(self):
                return 'foo'
            x = 'bar'
        proxy = _WrapDict(Obj(), MockWrapper)
        assert proxy.m() == 'foo'
        assert proxy.x == 'bar'
        with pytest.raises(AttributeError):
            proxy.y

    def test_setattr(self):
        obj = MockObject(x='orig')
        proxy = _WrapDict(obj, MockWrapper)
        proxy.x = 'changed'
        assert proxy.x == 'changed'
        assert obj.x == 'changed'
        proxy.y = 'changed'
        assert proxy.y == 'changed'
        assert obj.y == 'changed'

    def test_delattr(self):
        obj = MockObject(x='orig')
        proxy = _WrapDict(obj, MockWrapper)
        del proxy.x
        assert obj.__dict__ == {}


EURO_SIGN = '\N{EURO SIGN}'


class TestMissing:
    @pytest.mark.parametrize('fallback, expected', [
        (None, "<?attr.name?>"),
        ('foo', "'foo'"),
        (EURO_SIGN, repr(EURO_SIGN)),
        ])
    def test_repr(self, fallback, expected):
        missing = Missing("attr.name", fallback)
        assert repr(missing) == expected

    def test_repr_unicode_key(self):
        # carefully constructed to work in python 3.2
        missing = Missing(EURO_SIGN)
        assert repr(missing) == f"<?{EURO_SIGN}?>"

    def test_str(self):
        missing = Missing('key', "foo")
        assert str(missing) == "foo"

    @pytest.mark.parametrize('fallback, expected', [
        (None, 0),
        ('123', 123),
        ('foo', 0),
        ])
    def test_int(self, fallback, expected):
        missing = Missing('somekey', fallback)
        assert int(missing) == expected

    @pytest.mark.parametrize('fallback, expected', [
        ('123', 123.0),
        ('3.14', 3.14),
        ])
    def test_float(self, fallback, expected):
        missing = Missing('somekey', fallback)
        assert float(missing) == expected

    def test_float_default_fallback(self):
        missing = Missing('somekey', None)
        assert math.isnan(float(missing))

    def test_float_not_a_number(self):
        missing = Missing('somekey', 'notanumber')
        assert math.isnan(float(missing))

    @pytest.mark.parametrize('fallback, asint, asfloat', [
        ('foo', '0', 'nan'),
        ('12', '12', '12.00'),
        ])
    def test_format(self, fallback, asint, asfloat):
        missing = Missing('key', fallback)
        assert '%s' % missing == fallback
        assert '%r' % missing == repr(fallback)
        assert '%d' % missing == asint
        assert '%.2f' % missing == asfloat

    def test_format_unicode(self):
        missing = Missing('key', EURO_SIGN)
        assert '%s' % missing == EURO_SIGN


class TestDottedLookup:
    def test_dotted_attribute_lookup(self):
        d = _DottedLookup({'a': MockObject(b=MockObject(c='d'))})
        assert d['a.b.c'] == 'd'

    def test_getitem_lookup(self):
        d = _DottedLookup({'a': {'b': 'c'}})
        assert d['a.b'] == 'c'

    def test_fallback(self):
        d = _DottedLookup({'a': MockObject(b='x')})
        assert str(d['c|rats']) == 'rats'
        assert str(d['a.c|rats']) == 'rats'
        assert str(d['a.b.c|rats']) == 'rats'

    def test_default_fallback(self):
        d = _DottedLookup({'a': MockObject(b='x')})
        assert str(d['missing-key']) == '<?missing-key?>'
        assert str(d['a.missing-key']) == '<?a.missing-key?>'
