#############################################
More bits to stick in your log format strings
#############################################

This package includes a logger adapter which sticks a bunch of Pyramid
request attributes onto logged LogRecords.  These attributes are then
available for use in log format strings.

***************
Getting Started
***************

Where normally you would do something like::

    import logging
    log = logging.getLogger('myapp')
    log.warning("I say: %s", "howdy!")

instead, use the ``getLogger`` provided by ``pyramid_logger``::

    import pyramid_logging
    log = pyramid_logging.getLogger('myapp')
    log.warning("I say: %s", "howdy!")

What this does is make a bunch of extra log record attributes available.
These extra attributes may be used in ``logger.Formatter`` format strings.
For example, you can now do::

    logging.basicConfig(format=(
        "%(asctime)s %(unauthenticated_userid)s [%(client_addr)s]"
        " %(method)s %(path_qs)\n"
        "    %(levelname)s %(message)s"
        ))

to get log messages which look like::

    2014-10-01 17:55:02,001 user.principal [127.0.0.1] GET /page?arg=foo
        WARNING I say: howdy!


********************
Supported Attributes
********************

The following pyramid request attributes are made available by the logging
adapter:

- ``unauthenticated_userid``
- ``authenticated_userid``
- ``client_addr``
- ``method``
- ``url``
- ``path``
- ``path_info``
- ``path_qs``
- ``qs``

***********
Development
***********

Development happens at https://github.com/dairiki/pyramid_logger/.

********
See Also
********

The `pyramid_logging`_ package provides similar functionality.

.. _pyramid_logging: https://pypi.python.org/pypi/pyramid_logging

******
Author
******

Jeff Dairiki <dairiki@dairiki.org>
