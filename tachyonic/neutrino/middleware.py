import logging

from tachyonic import app

from tachyonic.neutrino import Client
from tachyonic.neutrino import exceptions

log = logging.getLogger(__name__)


class Token(object):
    def __init__(self, interface='api'):
        self.interface = interface

    def pre(self, req, resp):
        resp.headers['content-type'] = 'application/json; charset=UTF-8'.encode('utf-8')
        req.context['token'] = None
        req.context['email'] = None
        req.context['username'] = None
        req.context['login'] = False
        req.context['domain_admin'] = False
        req.context['is_root'] = False
        req.context['domain_id'] = None
        req.context['domain'] = None
        req.context['domains'] = []
        req.context['tenants'] = []
        req.context['tenant_id'] = None
        req.context['external_id'] = None
        req.context['expire'] = None
        req.context['roles'] = []

        if 'token' in req.session:
            token = req.session.get('token')
        else:
            token = req.headers.get('X-Auth-Token')

        req.context['restapi'] = app.config.get("tachyon").get("restapi")
        if req.context['restapi'] is None:
            raise exceptions.ClientError('settings.cfg',
                                         'Missing [tachyon] restapi')
        if token is not None:
            api = Client(req.context['restapi'])
            # Get Domain
            if self.interface == 'ui' and req.post.get('X-Domain', None) is not None:
                domain = req.post.get('X-Domain', 'default')
            elif 'X-Domain' in req.headers:
                domain = req.headers.get('X-Domain', 'default')
            elif self.interface == 'ui' and 'domain' in req.session:
                domain = req.session.get('domain', 'default')
            else:
                domain = "default"

            if domain is None:
                domain = "default"

            # Get Tenant
            if self.interface == 'ui' and req.post.get('X-Tenant-Id', None) is not None:
                tenant_id = req.post.get('X-Tenant-Id', None)
            elif 'X-Tenant-Id' in req.headers:
                tenant_id = req.headers.get('X-Tenant-Id')
            elif self.interface == 'ui' and 'tenant_id' in req.session:
                tenant_id = req.session.get('tenant_id')
            else:
                tenant_id = None

            if tenant_id == "NULL":
                tenant_id = None

            # Validate against API and get details...
            auth = api.token(token, domain, tenant_id)
            if 'token' in auth:
                req.context['token'] = auth['token']
                req.context['email'] = auth['email']
                req.context['username'] = auth['username']
                req.context['login'] = True
                req.context['domains'] = []
                req.context['expire'] = auth['expire']
                req.context['roles'] = []
                req.context['extra'] = auth['extra']
                req.context['tenant_id'] = auth['tenant_id']
                req.context['external_id'] = auth['external_id']
                req.context['assignments'] = auth['roles']
                for r in auth['roles']:
                    domains = []
                    tenants = []
                    if r['domain_id'] not in domains:
                        req.context['domains'].append(( r['domain_id'], r['domain_name']))
                        domains.append(r['domain_id'])

                    if r['domain_name'] == domain or r['domain_id'] == domain:
                        if r['tenant_id'] is None:
                            req.context['domain_admin'] = True
                            req.context['roles'].append(r['role_name'])
                        elif r['tenant_id'] == tenant_id:
                            req.context['roles'].append(r['role_name'])
                        if r['tenant_id'] not in tenants:
                            req.context['tenants'].append((r['tenant_id'],
                                                           r['tenant_name']))
                            tenants.append(r['tenant_id'])

                        req.context['domain_id'] = r['domain_id']
                        req.context['domain'] = r['domain_name']
                        if ('is_root' in r and
                                r['is_root'] is True):
                            req.context['is_root'] = True

        if hasattr(self, 'init'):
            self.init(req, resp)

    def post(self, req, resp):
        Client.close_all()
