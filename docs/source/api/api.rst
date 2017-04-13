.. _api:

The API Class
=============

Neutrino's API class is a WSGI "application" that you can host with any standard-compliant WSGI server.

.. code:: python

    from tachyonic.neutrino import app
    application = app(app_root)

.. autoclass:: tachyonic.neutrino.wsgi.Wsgi
   :members:
   :special-members: __call__

