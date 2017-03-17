Welcome to Tachyon Neutrino documentation!
==========================================

Release v\ |version| (:ref:`Installation <install>`)

Tachyon is a flexible Python Web and RestApi application framework for rapid development. It's free and open source and before you ask: It's BSD Licensed! Contributions and contributors are welcome!

.. code:: python

    class Books(nfw.Resource):
        def __init__(tachyon.Resource):
            app.router.add(tachyon.HTTP_GET, '/books/{id}', self.view_book)

        def view_book(self, req, resp, id):
            resp.headers['Content-Type'] = tachyon.TEXT_HTML
            title, book = book(id)
            t = tachyon.jinja.get_template('myproject/view_book.html')
            resp_bdy = t.render(title=title, book=book)

Features
--------

- Routes based on URI templates.
- Jinja2 templating integration.
- Simple ORM. (serialized data json import and export)
- Mariadb/Mysql Pool manager and simple interface
- Policy/Rules Engine - Access control to resources.
- Logging Facilities.
- Loading of resource classes via configuration file.

Useful Links
------------

- `Tachyon Home <http://www.tachyonic.co.za/>`_
- `Tachyon @ Pypi <#>`_
- `Tachyon @ Github <https://github.com/TachyonProject/tachyon_core>`_

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user/index
   api/index
   community/index
