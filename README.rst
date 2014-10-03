###############################
Pyramid-log |build status icon|
###############################

This package includes a Python logging formatter which makes Pyramid_
request attributes available for use in its format string.

************
Installation
************

The package may be downloaded from pypi_, but it may be easier to
install using pip::

    pip install pyramid-log

***************
Getting Started
***************

To log the request method and path with all log messages::

    import logging
    from pyramid_log import Formatter

    fmt = Formatter(
        '%(asctime)s %(request.method)s %(request.path_qs)s: %(message)s')

    logging.basicConfig()
    for handler in logging.getLogger().handlers:
        handler.setFormatter(fmt)

Now, if, in one of your views, you do::

    log = logging.getLogger()
    log.warning("I say %s", "howdy!")

you’ll get a log message like::

    2014-10-01 17:55:02,001 GET /path?arg=foo: I say howdy!

All attributes of the current pyramid request are available for use in
the format string (using “dotted” keys starting with the prefix
``'request.'``.  (Admittedly, for logging purposes, some request
attributes are more useful than others.)  Adding extra dots to the key
will get you attributes of request attributes.  For example the
matched route name is available as ``%(request.matched_route.name)s``.

See the `pyramid.request`_ documentation for more details on what request
attributes might be available.

Configuring Logging in a File
=============================

If you configure logging in your app config (or some other) file you can
do something like::

    [loggers]
    key = root

    [handlers]
    keys = console

    [formatters]
    keys = pyramid

    [logger_root]
    level = INFO
    handlers = console

    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = NOTSET
    formatter = pyramid

    [formatter_pyramid]
    class = pyramid_log.Formatter
    format = %(asctime)s %(request.method)s %(request.path_qs)s
             %(levename)-5.5s [%(name)s][%(threadName)s] %(message)s

See the `pyramid chapter on logging`_ and the docs for the Python
logging_ module’s `configuration file format`_ for more details on how
this works.



***********
Development
***********

Development happens at https://github.com/dairiki/pyramid_log/.

********
See Also
********

The `pyramid_logging`_ package provides similar functionality.

.. _pyramid_logging: https://pypi.python.org/pypi/pyramid_logging

******
Author
******

Jeff Dairiki <dairiki@dairiki.org>

.. |build status icon| image::
    https://travis-ci.org/dairiki/pyramid_log.svg?branch=master
    :target: https://travis-ci.org/dairiki/pyramid_log

.. _pypi: https://pypi.python.org/pypi/pyramid_log/
.. _pip: https://pip.pypa.io/en/latest/
.. _pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
.. _pyramid.request:
   http://docs.pylonsproject.org/projects/pyramid/en/latest/api/request.html
.. _pyramid chapter on logging:
   http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/logging.html
.. _logging: https://docs.python.org/3/library/logging.html
.. _configuration file format:
   https://docs.python.org/3/library/logging.config.html#logging-config-fileformat
