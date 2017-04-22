Welcome to Tachyonic Neutrino documentation!
============================================

Release v\ |version| (:ref:`Installation <install>`)

Tachyon is a flexible Python WSGI Web and RestApi application framework for rapid development. It's free and open source and before you ask: It's BSD Licensed! Contributions and contributors are welcome!

.. code:: python

    import logging

    import pyipcalc
    from tachyonic.neutrino import app
    from tachyonic.neutrino import jinja
    from tachyonic.common import constants as const

	@app.resources()
	class IPCalc():
		def __init__(self):
			app.router.add(const.HTTP_GET, '/ipcalc', self.ipcalc)
			app.router.add(const.HTTP_POST, '/ipcalc', self.ipcalc)

		def ipcalc(self, req, resp):
			net = None
			prefix = req.post.get('prefix', '192.168.0.0/24')
			net = pyipcalc.IPNetwork(prefix)
			t = jinja.get_template('ipcalc/ipcalc.html')

			resp.body = t.render(prefix=prefix, net=net)


Features
--------

- Routes based on URI templates.
- Jinja2 templating integration.
- Simple ORM. (serialized data json import and export)
- Mariadb/Mysql Pool manager and simple interface
- Policy/Rules Engine - Access control to resources.
- Loading of resource classes/functions and middlware classes via configuration file.
- Logging Facilities.

Useful Links
------------

- `Website <http://www.tachyonic.co.za/>`_
- `Pypi <https://pypi.python.org/pypi/tachyonic.neutrino>`_.
- `Github <https://github.com/TachyonProject/tachyonic_neutrino>`_.
- `Join mailing list <http://tachyonic.co.za/cgi-bin/mailman/listinfo/tachyon>`__.
- `Mail List Archives <http://tachyonic.co.za/pipermail/tachyon/>`__.
- `Pypi <https://pypi.python.org/pypi/tachyonic.neutrino>`_.

Documentation
-------------

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   user/index
   api/index
   community/index
