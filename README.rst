##################################
Request Attributes in Log Messages
##################################

|version| |py_versions| |py_implementation| |license| |build status| |trackgit|

What It Does
============

The `pyramid_log`_ distribution includes a Python `logging formatter`_
which makes Pyramid_ request attributes available for use in its
format string.  Specifically, ``pyramid_log.Formatter`` is special in
the following ways:

- It sets a ``.request`` attribute on the log record (if one doesn’t
  already exist.)

- It supports dotted attribute access in its format string. For
  example, ``"%(request.method)s"`` and even
  ``"%(request.matched_route.name)s"`` will work in the format string.

- There is a syntax for explicitly specifying fallback values.  For
  example, a format string of ``"%(request.method|<no request>)s"``
  will format to ``"<no request>"`` if there is no current request (or
  if the current request has no ``method`` attribute.)

The pyramid request has many attributes which can be useful when included
in the logs of a web app.  These include, but are not limited to:

- ``request.method``
- ``request.url`` (or ``request.path``, ``request.path_qs``, etc…)
- ``request.unauthenticated_userid``
- ``request.client_addr``
- ``request.GET`` (or ``request.POST`` or ``request.params``)
- ``request.matched_route.name``, ``request.view_name``

See the `Pyramid documentation <pyramid.request_>`_ for a more
complete list of available request attributes.

.. _pyramid_log: https://pypi.python.org/pypi/pyramid_log/
.. _logging formatter:
   https://docs.python.org/3/library/logging.html#formatter-objects
.. _pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
.. _pyramid.request:
   http://docs.pylonsproject.org/projects/pyramid/en/latest/api/request.html


Installation
============

The distribution may be downloaded from pypi_, but it may be easier to
install using pip_::

    pip install pyramid-log

It has been tested on python 3.7–3.11 and pypy.

Development happens at https://github.com/dairiki/pyramid_log/.

.. _pypi: `logging formatter`_
.. _pip: https://pip.pypa.io/en/latest/


Configuration
=============

Configuring Logging in a File
-----------------------------

If you configure logging in your application configuration (or some
other) file you can do something like::

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
    # NB: Here is the interesting part!
    class = pyramid_log.Formatter
    format = %(asctime)s %(request.method|no request)s %(request.path_qs|)s
             %(levelname)-5.5s [%(name)s] %(message)s

This will result in your log messages looking something like::

    2014-10-01 17:55:02,001 GET /path?arg=foo
    WARNI [myapp.views] This is some log message!

Refer to Pyramid’s `chapter on logging`_ and the documentation for the
Python logging_ module’s `configuration file format`_ for more details
on how this works.

.. _chapter on logging:
   http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/logging.html
.. _logging:
   https://docs.python.org/3/library/logging.html
.. _configuration file format:
   https://docs.python.org/3/library/logging.config.html#logging-config-fileformat


Imperative Configuration
------------------------

You can of course configure logging imperatively.  For example, with::

    import logging
    from pyramid_log import Formatter

    fmt = Formatter(
        '%(asctime)s %(request.client_addr|-)s'
        ' %(request.method|-)s %(request.path_qs|-)s: %(message)s')

    logging.basicConfig()
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(fmt)

Then, a view can log a message like so::

    log = logging.getLogger(__name__)

    @view_config(name='persimmon')
    def persimmon_view(request):
        log.warning("%s was called!", request.view_name)

Which will yield a log message like::

    2014-10-01 17:55:02,001 192.168.1.1 GET /persimmon: persimmon was called


Further Details
===============

Accessing Dict-like Values
--------------------------

The dot notation can be used to access not only instance attributes,
but also to access items in ``dict``-like values.  Attribute access is
tried first; if there is no attribute of the given name, then the
instances ``__getitem__`` method is tried.  For example,
``"%(request.matchdict.id)s"`` will get at
``request.matchdict['id']``.

Numeric Fallback
----------------

Explicit fallback values are always interpreted as strings, however,
if the fallback is used in a numeric context, an attempt will be made
at conversion to the requested type.  For example, if there is no
request, ``"%+(request.status_code|555)d"`` will format to ``"+555"``.

If the fallback string can not be converted to a numeric value, then
``0`` (zero) is used in integer contexts and NaN_ is used in ``float``
contexts.

.. _NaN: https://en.wikipedia.org/wiki/NaN

Default Fallback Values
-----------------------

If no fallback value is explicitly specified, then a default fallback
value will be used if the requested attribute does not exist.  The
missing attribute name is included in the default fallback value.  For
example ``"%(request.method)s"`` will produce ``"<?request.method?>"``
if there is no current request.


See Also
========

The `pyramid_logging`_ distribution provides similar functionality.

.. _pyramid_logging: https://pypi.python.org/pypi/pyramid_logging


Author
======

Jeff Dairiki <dairiki@dairiki.org>


.. ==== Badges ====

.. |build status| image::
    https://github.com/dairiki/pyramid_log/actions/workflows/tests.yml/badge.svg?branch=master
    :target: https://github.com/dairiki/pyramid_log/actions/workflows/tests.yml
.. |downloads| image::
    https://img.shields.io/pypi/dm/pyramid_log.svg
    :target: https://pypi.python.org/pypi/pyramid_log/
    :alt: Downloads
.. |version| image::
    https://img.shields.io/pypi/v/pyramid_log.svg
    :target: https://pypi.python.org/pypi/pyramid_log/
    :alt: Latest Version
.. |py_versions| image::
    https://img.shields.io/pypi/pyversions/pyramid_log.svg
    :target: https://pypi.python.org/pypi/pyramid_log/
    :alt: Supported Python versions
.. |py_implementation| image::
    https://img.shields.io/pypi/implementation/pyramid_log.svg
    :target: https://pypi.python.org/pypi/pyramid_log/
    :alt: Supported Python versions
.. |license| image::
    https://img.shields.io/pypi/l/pyramid_log.svg
    :target: https://github.com/dairiki/pyramid_log/blob/master/LICENSE
    :alt: License
.. |dev_status| image::
    https://img.shields.io/pypi/status/pyramid_log.svg
    :target: https://pypi.python.org/pypi/pyramid_log/
    :alt: Development Status
.. |trackgit| image::
    https://us-central1-trackgit-analytics.cloudfunctions.net/token/ping/lhat1p4ztjd57xd6xaml
    :target: https://trackgit.com
    :alt: Trackgit Views
