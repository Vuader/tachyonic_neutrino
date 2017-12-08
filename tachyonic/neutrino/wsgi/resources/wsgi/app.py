import os

# Virtualenv location (default: None)
virtualenv = None

if virtualenv is not None:
    virtualenv = virtualenv.rstrip('/')
    # Add the site-packages of the chosen virtualenv to work with
    # site.addsitedir("%s/lib/python2.7/site-packages" % (virtualenv,))
    # Activate your virtualenv
    activate_env = "%s/bin/activate_this.py" % (virtualenv,)
    execfile(activate_env, dict(__file__=activate_env))

# App's root ../
app_root = (os.path.abspath(os.path.join(
                            os.path.dirname(__file__),
                            '..')))

# Initialize WSGI Object
from tachyonic.neutrino.wsgi import app
application = app(app_root)
