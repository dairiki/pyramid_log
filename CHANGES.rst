History
=======

Next Release
------------

Features
^^^^^^^^

Better fallback values.
"""""""""""""""""""""""

- Now, by default, if an attribute is missing (which can happen, e.g.,
  for ``%(request.method)s`` is there is no current request) it is
  rendered as ``<?``*attribute-name*``?>``
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
