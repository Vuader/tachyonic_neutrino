from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tachyonic.neutrino.web.dom import Dom


class Menu(object):
    def __init__(self):
        self.dom = Dom()

    def add_divider(self):
        li = self.dom.create_element('li')
        li.set_attribute('role','seperator')
        li.set_attribute('class','divider')

    def add_dropdown_heading(self, name):
        li = self.dom.create_element('li')
        li.set_attribute('class','dropdown-header')
        li.append(name)

    def add_submenu(self, name, menu):
        li = self.dom.create_element('li')
        li.set_attribute('class','dropdown-submenu')
        a = li.create_element('a')
        a.set_attribute('href','#')
        a.set_attribute('class','dropdown-toggle')
        a.set_attribute('data-toggle','dropdown')
        a.append(name)
        ul = li.create_element('ul')
        ul.set_attribute('class','dropdown-menu')
        ul.append(menu)

    def add_dropdown(self, name, menu):
        li = self.dom.create_element('li')
        a = li.create_element('a')
        a.set_attribute('href','#')
        a.set_attribute('class','dropdown-toggle')
        a.set_attribute('data-toggle','dropdown')
        a.append(name)
        s = a.create_element('span')
        s.set_attribute('class','caret')
        ul = li.create_element('ul')
        ul.set_attribute('class','dropdown-menu')
        ul.append(menu)

    def add_link(self, name, url, active=False, target=None,
                 modal_target=None,
                 onclick=None):
        li = self.dom.create_element('li')
        if active is True:
            li.set_attribute('class','nav-link active')
        else:
            li.set_attribute('class','nav-link')
        a = li.create_element('a')
        if target is not None:
            a.set_attribute('target', target)
        if onclick is not None:
            a.set_attribute('onclick', onclick)
        if modal_target is not None:
            a.set_attribute('data-show','true')
            a.set_attribute('data-toggle','modal')
            a.set_attribute('data-target',modal_target)
            a.set_attribute('data-remote',url)
        a.set_attribute('href',url)
        a.append(name)

    def __str__(self):
        toreturn = self.dom.get()
        if toreturn is not None:
            return toreturn
        else:
            return ''
