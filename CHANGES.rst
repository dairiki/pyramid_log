History
=======

Release 2.0 (unreleased)
------------------------

This release drops support for python 2.7.

API
^^^

- Raise ``ValueError`` if ``pyramid_log.Formatter`` is passed a value of
  other than ``'%'`` for ``style`` parameter.

- Issue a ``UserWarning`` if ``pyramid_log.Formatter`` is explicitly passed
  a ``validate=True``.

Release 1.0 (2021-12-05)
------------------------

This release adds support for python>=3.8 and pyramid>=2.

The 1.x releases will be the last to support running under python 2.7.

Compatibility
^^^^^^^^^^^^^

- Python >= 3.8: ``logger.Formatter`` requires the ``validate=False``
  argument, otherwise it forbids ``'.'`` in %-style format strings.
- Pyramid >= 2.0: provide our own replacement for ``pyramid.compat``
  which no longer exists

Testing
^^^^^^^

- Test under python 3.7–3.10 and pypy3.
- Stop testing under python 3.4 and 3.5.
- Test with Pyramid 1.*
- Convert CI tests from Travis to github workflow

Packaging
^^^^^^^^^

- The packaging has been PEP517-ized.

Release 0.2.1 (2017-12-17)
--------------------------

This release officially drops support for python 2.6, 3.2, 3.3 (and
therefore pypy3) and adds support for python 3.5 and 3.6.

Other than changes in test configuration, there are no substantive
changes from `0.2`.

Release 0.2 (2014-10-09)
------------------------

Features
^^^^^^^^

Better fallback values.
"""""""""""""""""""""""

- Now, by default, if an attribute is missing (which can happen, e.g.,
  for ``%(request.method)s`` is there is no current request) it is
  rendered as ``<?``\ *attribute-name*\ ``?>``
  (e.g. ``"<?request.method?>"``.)

- There is now a syntax for explicitly specifying fallback values.  E.g.
  ``"%(request.method|(no-request))"`` which will format to ``(no request)``,
  if there is no current request (or if the current request does not have
  a ``method`` attribute.)

Dict-like access to values
""""""""""""""""""""""""""

- When looking up a dotted name, if an attribute can not be found,
  ``dict``-style (``__getitem__``) lookup will be attempted.
  E.g. ``"%(request.matchdict.arg)"`` will get at
  ``request.matchdict['arg']``.

Release 0.1.1 (2014-10-02)
--------------------------

Bugs Fixed
^^^^^^^^^^

- If an exception is thrown by a request property, render it as ``None``.

- Disable logging during log formatting to prevent recursion if a request
  property generates a log message.

Release 0.1 (2014-10-02)
------------------------

- Initial release
