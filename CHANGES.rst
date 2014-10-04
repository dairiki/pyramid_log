*******
History
*******

Development Branch (new-style-format-string)
============================================

Change so that our ``Formatter`` uses a ``str.format`` style format
string, rather than a printf-style format string.  This greatly
simplifies the code.


Release 0.1.1 (2014-10-02)
==========================

Bugs Fixed
----------

- If an exception is thrown by a request property, render it as ``None``.

- Disable logging during log formatting to prevent recursion if a request
  property generates a log message.

Release 0.1 (2014-10-02)
========================

- Initial release
