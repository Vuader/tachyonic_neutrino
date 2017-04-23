.. _tutorial:

Tutorial
========

If you haven't done so already, please refer to :ref:`install <install>` before continuing.


New Application
---------------

Create a folder named after your project and use neutrino.py to setup clean initial project structure.

.. code:: bash

    $ mkdir project
    $ tachyonic.py -c myproject project

This will create the neccesary stucture to run and start building your project.

**project/** - Location of Web Application Root.

**project/settings.cfg** - Default Configuration file.

**project/myproject/** - Your Web Application - Should be placed in package to be installed later.

**project/myproject/__init__.py** - Empty file.

**project/myproject/views/** - Views Modules.

**project/myproject/views/__init__.py** - Make sure to import your view modules here.

**project/myproject/middleware/** - Middleware Modules.

**project/myproject/views/__init__.py** - Empty file.

**project/myproject/models** - Modles Modules.

**project/myproject/miodles/__init__.py** - Empty file.

**project/myproject/templates** - Jinja2 Templates specific to Application

**project/myproject/static/myproject** - Static files for project. Images, stylesheets etc.

**project/templates/** Global templates. Simply creating a template in here for example templates/myproject/test.html will override the application template.

**project/static/** Your WSGI Webserver will serve these files. To populate or update them based on configured applications in settings.cfg run: neutrino.py -g .

**project/tmp/** Temporary Folder for session data etc. To clear session data files that expired run neutrino.py -e . (Its recommended to run a cron a job hourly)

**project/wsgi/** WSGI Scripts

**project/wsgi/__init__.py** WSGI Script for web server

**project/wsgi/app.py** WSGI Script for web server


During development it might be best to symblolic link static to your package static folder while coding. Also its best adviced to keep all static files in a folder named after the package in the static folder. If more applictions use the same static folder that work together this will resolve some conflicts. 


Install Application
-------------------
In production it would be a package for example from pypi. There are two parts of the installation. 

1. The package that contains your views, middleware, templates and static, configs to be installed by default. It could be installed by pip for example.
2. Run tachyonic -s package install_path to create necccesary root structure for webserver to run application. 


Development Server
------------------

Requires gunicorn - pip install gunicorn; This will start a webserver serving both dynamic and static content. 

.. code:: bash

    $ tachyonic.py -t project

project being the path of the application root where you could find the settings.cfg. 

Optional Paramaters are::

    --ip IP Addresses (default 127.0.0.1)
    --port HTTP Port (default port 8080)


Settings.cfg
------------
The settings.cfg file is located within your project directory. The purpose of this file to specify specific properties for the projects environment and import middleware and modules.

**Example:**

.. code::

    [application]
    # Project Name also used in logs.
    name = project

    # Modules to be imported with views
    modules = myproject.views, myproject2.views

    # Middleware
    middleware = myproject.middleware.authentication

    # Location of static images in http request
    static = /static

    # Session Timeout
    session_timeout = 7200

    # Incase of HA / Load Balancing Proxy
    use_x_forwarded_host = false
    use_x_forwarded_port = false

    # Database configuration
    # comment out if not needed.
    [mysql]
    database = blogdev
    host = 127.0.0.1
    username = blog
    password = t0ps3cret

    # Redis used to facilitate sesions over different web servers.
    # comment out if not needed.
    [redis]
    server = localhost
    port = 6379
    db = 0

    # Logging Facilities.
    [logging]
    # comment out to disable syslog.
    host = 127.0.0.1
    port = 514

    # Enable for more debug output and autorestart enabled.
    debug = true

    # Log file to file. Comment out to disable.
    file = /tmp/project.log

Views
-----
A view method, or *'view'* for short, is simply a Python class method that takes a web request and returns web response. The response can be the HTML content of a web page, json for restapi, image or anything else. The view contains the the logic neccessary to return that response. You can place your views anywhere, as long as its imported in the settings.cfg modules. The convention is to put the views in a directory called views, placed in the the application directory. Each category or specific views would go in there own module which will be imported by the __init__.py of the views subpackage.

When a page is requested, Neutrino creates a **Request Object** and **Response object**. If policy is applied to the route and passes then Neutrino loads the appropriate view, passing the Request as the first argument and Response as the second arguement to the view function/method.

*Multiple views could be group within a class or single view within in a function.*

A view could return content either via using return or resp.body. 

**Example of Class Grouped Views**:

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

**Example of Function Views**:

.. code:: python

    @app.resource(const.HTTP_GET, '/ipcalc')
    def ip_get(req, resp):
		net = pyipcalc.IPNetwork('192.168.0.0/24')
		t = jinja.get_template('ipcalc/ipcalc.html')
		resp.body = t.render(prefix=prefix, net=net)

    @app.resource(const.HTTP_POST, '/ipcalc')
    def ip_post(req, resp):
		prefix = req.post.get('prefix', '192.168.0.0/24')
		net = pyipcalc.IPNetwork(prefix)
		t = jinja.get_template('ipcalc/ipcalc.html')
		resp.body = t.render(prefix=prefix, net=net)


**Alternatively you could route views to a function without wrapping**:

.. code:: python
    
	def hello_world(req, resp):
		return "Hello World"

	app.router.add(const.HTTP_GET, '/', hello_world)


Templating Engine
-----------------
Neutrino uses Jinja2 for a conveniant way to generate HTML dynamically. Most common approaches relies on templates. Templates contain the static parts of HTML output as well as some special syntax for inserting dynamic content.

There is a standard API for loading and rendering templates. Templates are located within your applications template directory. All the applications are actually a python package with __init__.py.

**Template Usage**:

If your applications name is 'myproject' and your template you wish to render is 'home.html' it would go something like this:

.. code:: python

    t = app.jinja.get_template('myproject/home.html')


*If you create a directory 'myproject' in the web application root folders template directory and place 'home.html' in there it will override the tempate within the package.*

To render the loaded template with some variables, just call the render() method on the template


.. code:: python

    resp.body = t.render(the='variables', go='here')

**There is also a short cut to rendering template**:

.. code:: python

    resp.body = app.render_template('myproject/home.html', the='variables', go='here')


**Unicode Only**

Jinja2 is using Unicode internally which means that you have to pass Unicode objects to the render function or bytestrings that only consist of ASCII characters. Additionally newlines are normalized to one end of line sequence which is per default UNIX style (\n).

Python 2.x supports two ways of representing string objects. One is the str type and the other is the unicode type, both of which extend a type called basestring. Unfortunately the default is str which should not be used to store text based information unless only ASCII characters are used. With Python 2.6 it is possible to make unicode the default on a per module level and with Python 3 it will be the default.

To explicitly use a Unicode string you have to prefix the string literal with a u: u'Test'. That way Python will store the string as Unicode by decoding the string with the character encoding from the current Python module. If no encoding is specified this defaults to ‘ASCII’ which means that you can’t use any non ASCII identifier.

To set a better module encoding add the following comment to the first or second line of the Python module using the Unicode literal:

.. code:: python

    # -*- coding: utf-8 -*-

We recommend utf-8 as Encoding for Python modules and templates as it’s possible to represent every Unicode character in utf-8 and because it’s backwards compatible to ASCII. For Jinja2 the default encoding of templates is assumed to be utf-8.


Jinja2 Template Designer Documentation can be found here: http://jinja.pocoo.org/docs/dev/templates/

Middleware
----------
Middleware components provide a way to execute logic before the framework routes each request, after each request is routed but before the response. Middleware is registered by the settings.cfg file. 

There are two methods you can can define for middleware *'pre'* and *'post'*. *'pre'* being before the request is routed and *'post'* being after.

**Middleware Example Components**

.. code:: python

    class Login(object):
        def pre(self, req, resp):
            pass

    class Counter(object):
        def post(self, req, resp):
            pass

Each component’s pre and post methods are executed hierarchically, as a stack, following the ordering of the list within the settings.cfg. For example, if a list of middleware objects are passed as middle1, middle2, middle3, the order of execution is as follows::

    middle1.pre
        middle2.pre
            middle3.pre
                <route to view method>
            middle3.post
        middle2.post
    middle1.post

*Note that each component need not implement all methods*


Routing
-------

Request Object
--------------
The Request object contains metadata about the request. Request object behaves like a IO file/object. You can use **.read()** and **.readline()** to read the raw request body. However POST data is also included in the request body and can be access via **.post** dictionary like object.

.. autoclass:: tachyonic.neutrino.request.Request
   :members:


Response Object
---------------
The Response is contains the response headers, content, content_length and http_status for example. However keep in mind you can return data directly from your view without using the response object. Default stuats is set to 200 OK. esponse object behaves like a IO file/object. You can use **.write()** write to the response body. By setting a string value to the **.body** it will override anything from **.write()** method.

.. autoclass:: tachyonic.neutrino.response.Response
   :members:

Logging
-------

Error Handling
--------------

Policy Engine
-------------

MySQL/MariaDB
-------------

Model ORM
---------


Config/INI
----------




