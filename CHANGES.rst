*******
History
*******

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
