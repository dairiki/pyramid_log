#
# Copyright © 2014–2021 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
""" A logging formatter which make pyramid request attributes available
for use in log messages.

"""

from contextlib import contextmanager
import logging
import warnings

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
            "%(asctime)s %(request.unauthenticated_userid|<anonymous>)s "
            "[%(request.client_addr|)s]\\n"
            "  %(request.method|-)s %(request.path_qs|-)\\n"
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
    try:
        logging.Formatter(validate=False)
        _validate_supported = True
    except TypeError:
        _validate_supported = False

    def __init__(self, fmt=None, datefmt=None, style='%', **kwargs):
        if style != '%':
            raise ValueError(
                f"Style {style!r} is not currently supported by "
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        # python >= 3.8 does not, by default, allow '.' in '%' format strings
        if self._validate_supported:
            if kwargs.get('validate'):
                warnings.warn(
                    "Forcing validate=False. "
                    "(%-style formatting strings with dotted attribute names "
                    "will not pass validation by logging.Formatter.)"
                )
            kwargs['validate'] = False
        super().__init__(fmt, datefmt, **kwargs)

    def format(self, record):
        """ Format the specific record as text.

        """
        # Temporarily set record.request to current Pyramid request object
        with _add_request_attr(record):
            # Disable logging to prevent recursion (in case, e.g., a logged
            # request property generates a log message)
            with logging_disabled(record.levelno):
                # magic_record.__dict__ supports dotted attribute lookup
                magic_record = _WrapDict(record, _DottedLookup)
                return super().format(magic_record)


@contextmanager
def _add_request_attr(record):
    """ Temporarily add Pyramid request attribute to log record.

    If ``record`` does not have a ``record`` attribute, ``record.request``
    is set to the current Pyramid request object for the duration
    of the context.
    If there is no active Pyramid request, the ``request`` attribute is
    is left unset.
    """
    added_attrs = []
    has_request = hasattr(record, 'request')
    if not has_request:
        request = get_current_request()
        if request is not None:
            record.request = request
            added_attrs.append('request')
    try:
        yield record
    finally:
        for attr in added_attrs:
            delattr(record, attr)


@contextmanager
def logging_disabled(level=logging.CRITICAL):
    """ Temporarily disable logging.
    """
    save_disable = logging.root.manager.disable
    logging.disable(level)
    try:
        yield
    finally:
        logging.disable(save_disable)


class _WrapDict:
    """ An object proxy which provides a “wrapped” version of the proxied
    object’s ``__dict__``.

    """
    __slots__ = ['_obj', '_dict_wrapper']

    def __init__(self, obj, dict_wrapper):
        self._obj = obj
        self._dict_wrapper = dict_wrapper

    @property
    def __dict__(self):
        return self._dict_wrapper(self._obj.__dict__)

    def __getattr__(self, attr):
        return getattr(self._obj, attr)

    def __setattr__(self, attr, value):
        if attr in self.__slots__:
            object.__setattr__(self, attr, value)
        else:
            setattr(self._obj, attr, value)

    def __delattr__(self, attr):
        return delattr(self._obj, attr)


class Missing:
    """ Returned for missing keys.

    This has decent values upon conversion to various types, making
    is usable by printf-style format strings without error.

    """
    def __init__(self, key, fallback=None):
        self.key = key
        self.fallback = fallback

    def __str__(self):
        fallback = self.fallback
        if fallback is None:
            return f'<?{self.key}?>'
        return fallback

    def __repr__(self):
        fallback = self.fallback
        if fallback is None:
            return f'<?{self.key}?>'
        return repr(fallback)

    _int_fallback = 0

    def __int__(self):
        fallback = self.fallback
        if fallback is None:
            return self._int_fallback
        try:
            return int(fallback)
        except ValueError:
            return self._int_fallback

    _float_fallback = float('NaN')

    def __float__(self):
        fallback = self.fallback
        if fallback is None:
            return self._float_fallback
        try:
            return float(fallback)
        except ValueError:
            return self._float_fallback


_marker = object()


class _DottedLookup:
    """ A dict which supports dotted-key chained lookup, with fallback
    if the lookup fails.

    Example::

        >>> d = _DottedLookup({'a': {'b': 'foo'}})
        >>> d['a.b']                    # same as d['a']['b']
        'foo'

    Fallback values are appended after a pipe (``|``)::

        >>> d['a.b|fb']                 # same as d['a']['b']
        'foo'
        >>> d['a.z|fb']                 # there is no d['a']['z']
        'fb'

    """
    def __init__(self, dict_):
        self.dict = dict_

    def __getitem__(self, key):
        key, pipe, fallback = key.partition('|')
        if not pipe:
            fallback = None
        parts = key.split('.')
        try:
            v = self.dict[parts[0]]
            for part in parts[1:]:
                a = getattr(v, part, _marker)
                v = a if a is not _marker else v[part]
        except (LookupError, TypeError):
            return Missing(key, fallback)
        else:
            return v
