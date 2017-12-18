History
=======


Release 0.2.1 (2017-12-17)
--------------------------

This release officially drops support for python 2.6, 3.2, 3.3 (and theremore pypy3)
and adds support for python 3.5 and 3.6.

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
