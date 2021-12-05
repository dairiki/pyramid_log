# -*- coding: utf-8 -*-
#
# Copyright © 2021 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
from __future__ import absolute_import

import pytest

from ._compat import native_, text_


SAMPLE_TEXT = "text"


@pytest.mark.parametrize('input, text', [
    ("text", u"text"),
    (b"binary", u"binary"),
    (u"unicode", u"unicode"),
])
def test_text(input, text):
    output = text_(input)
    assert output == text
    assert type(output) is type(text)


@pytest.mark.parametrize('input, text', [
    ("text", "text"),
    (b"binary", "binary"),
    (u"unicode", "unicode"),
])
def test_native(input, text):
    output = native_(input)
    assert output == text
    assert type(output) is type(text)
