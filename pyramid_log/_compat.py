# -*- coding: utf-8 -*-
#
# Copyright © 2021 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
""" Bits that used to be in pyramid.compat.
"""
import sys

PY2 = sys.version_info[0] == 2

if PY2:                                  # pragma: no cover
    from io import BytesIO as NativeIO   # noqa: F401
    binary_type = str
else:                                    # pragma: no cover
    from io import StringIO as NativeIO  # noqa: F401
    binary_type = bytes


def text_(s, encoding='latin-1', errors='strict'):
    """ If ``s`` is an instance of ``binary_type``, return
    ``s.decode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    return s


if PY2:                         # pragma: no cover
    def native_(s, encoding='latin-1', errors='strict'):
        """ If ``s`` is an instance of ``text_type``, return
        ``s.encode(encoding, errors)``, otherwise return ``str(s)``"""
        if isinstance(s, unicode):  # noqa: F821
            return s.encode(encoding, errors)
        return str(s)
else:
    def native_(s, encoding='latin-1', errors='strict'):
        """ If ``s`` is an instance of ``text_type``, return
        ``s``, otherwise return ``str(s, encoding, errors)``"""
        if isinstance(s, str):
            return s
        return str(s, encoding, errors)
