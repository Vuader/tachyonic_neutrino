from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tachyonic.neutrino.web import forms
from tachyonic.neutrino.web.dom import Dom


class Form(forms.Base):
    def __init__(self, data=None, validate=True, readonly=False, cols=1,
                 **kwargs):
        forms.Base.__init__(self, data, validate,
                                  readonly, **kwargs)
        self._form_group_style = ""
        if cols > 1:
            width = int(100 / cols)
            self._form_group_style = "float: left;" \
                                     + "margin-left:0px;" \
                    + "min-height:60px;padding-left:2px;min-width:%s%s;max-width:%s%s;overflow:none;" % (width,
                                                                        '%',
                                                                        width,
                                                                       '%')

    def checkbox(self, name, value, label, readonly=False, prefix=None,
                 suffix=None, cls=None):
        dom = Dom()
        form_group = dom.create_element('div')
        if cls is not None:
            form_group.set_attribute('class', "form-group %s" % (cls,))
        else:
            form_group.set_attribute('class', 'form-group')
        form_group.set_attribute('style', self._form_group_style)
        form_group.set_attribute('id', "form_group_%s" % (name,))
        col_sm = form_group.create_element('div')
        checkbox = col_sm.create_element('div')
        checkbox.set_attribute('class', 'checkbox')

        l = checkbox.create_element('label')
        l.set_attribute('for', name)

        f = l.create_element('input')
        f.set_attribute('type', 'checkbox')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        if readonly is True:
            f.set_attribute('disabled')

        if value is True:
            f.set_attribute('checked')

        l.append(label)

        return dom

    def select(self, name, value, options, label=None, readonly=False,
               prefix=None, suffix=None, size=None, cls=None):
        dom = Dom()
        form_group = dom.create_element('div')
        form_group.set_attribute('style', self._form_group_style)
        if cls is not None:
            form_group.set_attribute('class', "form-group %s" % (cls,))
        else:
            form_group.set_attribute('class', 'form-group')
        form_group.set_attribute('id', "form_group_%s" % (name,))

        l = form_group.create_element('label')
        l.set_attribute('for', name)
        l.append(label)

        field = form_group.create_element('div')
        field.set_attribute('class', 'input-group')
        field.set_attribute('style', 'width:100%;')

        if prefix is not None:
            p = field.create_element('span')
            p.set_attribute('class', 'input-group-addon')
            p.append(prefix)
            if size is not None:
                size += len(prefix)

        f = field.create_element('select')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        f.set_attribute('class', 'form-control')
        for o in options:
            option = f.create_element('option')
            option.set_attribute('value', o)

            if o == value:
                option.set_attribute('selected')

            if readonly is True:
                f.set_attribute('disabled', 'disabled')

            option.append(options[o])

        if suffix is not None:
            s = field.create_element('span')
            s.set_attribute('class', 'input-group-addon')
            s.append(suffix)
            if size is not None:
                size += len(suffix)

        if size is not None:
            field.set_attribute('style', "width:%sem;max-width:100%s" %
                                (size,'%'))

        return dom

    def input(self, name, value, label=None, readonly=False, prefix=None,
              suffix=None, required=False, size=None, max_length=None,
              placeholder=None, password=False, cls=None):
        dom = Dom()
        form_group = dom.create_element('div')
        form_group.set_attribute('style', self._form_group_style)
        if cls is not None:
            form_group.set_attribute('class', "form-group %s" % (cls,))
        else:
            form_group.set_attribute('class', 'form-group')
        form_group.set_attribute('id', "form_group_%s" % (name,))

        l = form_group.create_element('label')
        l.set_attribute('for', name)
        if required is True:
            label = "%s (*)" % (label,)
        l.append(label)

        field = form_group.create_element('div')
        field.set_attribute('class', 'input-group')
        field.set_attribute('style', 'width:100%;')

        if size is not None:
            size = int(size)

        if prefix is not None:
            p = field.create_element('span')
            p.set_attribute('class', 'input-group-addon')
            p.append(prefix)
            if size is not None:
                size += len(prefix)

        f = field.create_element('input')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        if password is True:
            f.set_attribute('type', 'password')
        else:
            f.set_attribute('type', 'text')
        f.set_attribute('value', value)
        f.set_attribute('class', 'form-control')

        if required is True:
            f.set_attribute('required')

        if readonly is True:
            f.set_attribute('readonly')

        if placeholder is not None:
            f.set_attribute('placeholder', placeholder)

        if max_length is not None:
            f.set_attribute('maxlength', max_length)

        if suffix is not None:
            s = field.create_element('span')
            s.set_attribute('class', 'input-group-addon')
            s.append(suffix)
            if size is not None:
                size += len(suffix)

        if size is not None:
            field.set_attribute('style', "width:%sem;max-width:100%s" %
                                (size,'%'))

        return dom

    def textarea(self, name, value, label=None, readonly=False, prefix=None,
                 suffix=None, required=False, rows=None, cols=None,
                 placeholder=None, cls=None):
        dom = Dom()

        form_group = dom.create_element('div')
        form_group.set_attribute('style', self._form_group_style)
        if cls is not None:
            form_group.set_attribute('class', "form-group %s" % (cls,))
        else:
            form_group.set_attribute('class', 'form-group')
        form_group.set_attribute('id', "form_group_%s" % (name,))

        l = form_group.create_element('label')
        l.set_attribute('for', name)
        l.append(label)

        field = form_group.create_element('div')
        field.set_attribute('class', 'input-group')
        field.set_attribute('style', 'width:100%;')

        if prefix is not None:
            p = field.create_element('span')
            p.set_attribute('class', 'input-group-addon')
            p.append(prefix)

        f = field.create_element('textarea')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        f.set_attribute('class', 'form-control')
        f.set_attribute('style', 'width:100%')
        f.append(value)

        if required is True:
            f.set_attribute('required')

        if readonly is True:
            f.set_attribute('readonly')

        if placeholder is not None:
            f.set_attribute('placeholder',placeholder)

        if cols is not None:
            f.set_attribute('cols', cols)

        if rows is not None:
            f.set_attribute('rows', rows)

        if suffix is not None:
            s = field.create_element('span')
            s.set_attribute('class', 'input-group-addon')
            s.append(suffix)

        return dom
