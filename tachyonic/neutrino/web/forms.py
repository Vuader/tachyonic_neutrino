# -*- coding: utf-8 -*-
# Copyright (c) 2016-2017, Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
from collections import OrderedDict

import json

from tachyonic.common import exceptions
from tachyonic.neutrino.model import ModelDict
from tachyonic.neutrino import request
from tachyonic.neutrino.web.dom import Dom
log = logging.getLogger(__name__)


class Base(ModelDict):
    def __init__(self, data=None, validate=True, readonly=False, **kwargs):
        # 'Base.__init__' is too complex (35)
        # TODO: refactor for less complexity
        super(ModelDict, self).__init__(**kwargs)

        self.readonly = readonly

        if isinstance(data, request.Post):
            values = {}
            for v in data:
                #if v in self._declared_fields:
                values[v] = data[v]
        elif isinstance(data, request.Request):
            data = data.read()
            values = json.loads(data)
        elif isinstance(data, dict):
            values = data
        elif data is None:
            values = None
        else:
            raise exceptions.Error('forms only accept request or dict object')
        try:
            if values is not None:
                for v in self._declared_fields:
                    if hasattr(self, v):
                        field = getattr(self, v)
                        if isinstance(field, ModelDict.Bool):
                            if v not in values:
                                self._set({v: False}, validate)
                for v in values:
                    if hasattr(self, v):
                        t = v.replace('_confirm', '')
                        field = getattr(self, t)
                        if hasattr(field, 'label') and field.label is not None:
                            name = field.label
                        else:
                            name = v
                    if '_confirm' in v:
                        t = v.replace('_confirm', '')
                        field = getattr(self, t)
                        if field.label is not None:
                            name = field.label
                        else:
                            name = v
                        if values[t] is None or values[t] == '':
                            if values[v] is not None and values[v] != '':
                                raise exceptions.HTTPBadRequest(title="Field Invalid", description="%s mis-match" % (name,))
                    if hasattr(self, v):
                            if values[v] == '':
                                values[v] = None
                            if field.readonly is False or validate is False:
                                if isinstance(field, ModelDict.Bool):
                                    if isinstance(values[v], str):
                                        self._set({v: True}, validate)
                                    elif isinstance(values[v], int):
                                        self._set({v: values[v]}, validate)
                                    elif isinstance(values[v], unicode):
                                        self._set({v: True}, validate)
                                    elif isinstance(values[v], bool):
                                        self._set({v: values[v]}, validate)
                                elif isinstance(field, ModelDict.Password):
                                    if values[v] is not None:
                                        confirm = "%s_confirm" % (v)
                                        if confirm in values:
                                            if validate is True:
                                                c = values[confirm]
                                                if c == '':
                                                    c = None
                                                if c != values[v]:
                                                    raise exceptions.HTTPBadRequest(title="Field Invalid", description="%s mis-match" % (name,))
                                        self._set({v: values[v]}, validate)
                                elif isinstance(field, ModelDict.Integer):
                                    try:
                                        self._set({v: long(values[v])},
                                                  validate)
                                    except:
                                        self._set({v: values[v].value},
                                                  validate)
                                elif isinstance(field, ModelDict.Number):
                                    try:
                                        self._set({v: float(values[v])},
                                                  validate)
                                    except:
                                        self._set({v: values[v]}, validate)
                                elif isinstance(field, ModelDict.Text):
                                    if field.password is False:
                                        self._set({v: values[v]}, validate)
                                    else:
                                        if values[v] is not None and values[v] != '':
                                            self._set({v: values[v]}, validate)
                                else:
                                    self._set({v: values[v]}, validate)

        except exceptions.FieldError as e:
            raise exceptions.HTTPBadRequest(title="Field Invalid", description=e.user_error())

    def __str__(self):
        dom = Dom()
        for key in self._declared_fields:
            if key in self._data:
                value = self._data[key].value()
            else:
                value = ""

            f = self._declared_fields[key]
            if self.readonly is True:
                f.readonly = self.readonly

            if f.hidden is True:
                dom.append(self.hidden_input(key,
                                             value))
            elif isinstance(f, ModelDict.Dict):
                pass
            elif isinstance(f, ModelDict.List):
                pass
            elif isinstance(f, ModelDict.Bool):
                dom.append(self.checkbox(key,
                                         value,
                                         label=f.label,
                                         readonly=f.readonly,
                                         cls=f.cls,
                                         prefix=f.prefix,
                                         suffix=f.suffix))
            elif isinstance(f, ModelDict.Password):
                dom.append(self.input("%s" % (key,),
                                      value,
                                      label=f.label,
                                      readonly=f.readonly,
                                      required=f.required,
                                      size=f.length,
                                      max_length=f.max_length,
                                      placeholder=f.placeholder,
                                      cls=f.cls,
                                      prefix=f.prefix,
                                      suffix=f.suffix,
                                      password=True))
                if f.readonly is False:
                    dom.append(self.input("%s_confirm" % (key,),
                                          value,
                                          label="Confirm",
                                          readonly=f.readonly,
                                          required=f.required,
                                          size=f.length,
                                          max_length=f.max_length,
                                          placeholder=f.placeholder,
                                          cls=f.cls,
                                          prefix=f.prefix,
                                          suffix=f.suffix,
                                          password=True))
            else:
                if f.choices is not None:
                    choices = OrderedDict()
                    if isinstance(f.choices, list):
                        for c in f.choices:
                            choices[c] = c
                    else:
                        choices = f.choices

                    dom.append(self.select(key,
                                           value,
                                           label=f.label,
                                           options=choices,
                                           readonly=f.readonly,
                                           size=f.length,
                                           cls=f.cls,
                                           prefix=f.prefix,
                                           suffix=f.suffix))
                elif f.rows > 1:
                    dom.append(self.textarea(key,
                                             value,
                                             label=f.label,
                                             readonly=f.readonly,
                                             required=f.required,
                                             cols=f.cols,
                                             rows=f.rows,
                                             placeholder=f.placeholder,
                                             cls=f.cls,
                                             prefix=f.prefix,
                                             suffix=f.suffix))
                elif isinstance(f, ModelDict.Text):
                    dom.append(self.input(key,
                                          value,
                                          label=f.label,
                                          readonly=f.readonly,
                                          required=f.required,
                                          size=f.length,
                                          max_length=f.max_length,
                                          placeholder=f.placeholder,
                                          password=f.password,
                                          cls=f.cls,
                                          prefix=f.prefix,
                                          suffix=f.suffix))
                elif isinstance(f, ModelDict.Phone):
                    dom.append(self.input(key,
                                          value,
                                          label=f.label,
                                          readonly=f.readonly,
                                          required=f.required,
                                          size=16,
                                          max_length=17,
                                          placeholder=f.placeholder,
                                          cls=f.cls,
                                          prefix=f.prefix,
                                          suffix=f.suffix))
                else:
                    dom.append(self.input(key,
                                          value,
                                          label=f.label,
                                          readonly=f.readonly,
                                          required=f.required,
                                          size=f.length,
                                          max_length=f.max_length,
                                          placeholder=f.placeholder,
                                          cls=f.cls,
                                          prefix=f.prefix,
                                          suffix=f.suffix))
        return dom.get()


class Form(Base):
    def checkbox(self, name, value, label=None, readonly=False, prefix=None,
                 suffix=None, cls=None):
        dom = Dom()

        if label is not None:
            l = dom.create_element('label')
            l.set_attribute('for', name)
            l.append(label)

        if prefix is not None:
            dom.append(prefix)

        f = dom.create_element('input')
        f.set_attribute('type', 'checkbox')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        if readonly is True:
            f.set_attribute('disabled')

        if value is True:
            f.set_attribute('checked')

        if suffix is not None:
            dom.append(suffix)

        return dom

    def select(self, name, value, options, label=None, readonly=False,
               prefix=None, suffix=None, size=None, cls=None):
        dom = Dom()

        if label is not None:
            l = dom.create_element('label')
            l.set_attribute('for', name)
            l.append(label)

        if prefix is not None:
            dom.append(prefix)

        f = dom.create_element('select')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        for o in options:
            option = f.create_element('option')
            option.set_attribute('value', o)

            if o == value:
                option.set_attribute('selected')

            if readonly is True:
                f.set_attribute('disabled', 'disabled')

            option.append(options[o])

        if suffix is not None:
            dom.append(suffix)

        return dom

    def input(self, name, value, label=None, readonly=False, prefix=None,
              suffix=None, required=False, size=None, max_length=None,
              placeholder=None, password=False, cls=None):
        dom = Dom()

        if label is not None:
            l = dom.create_element('label')
            l.set_attribute('for', name)
            l.append(label)

        if prefix is not None:
            dom.append(prefix)

        f = dom.create_element('input')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        if password is True:
            f.set_attribute('type', 'password')
        else:
            f.set_attribute('type', 'text')
        f.set_attribute('value', value)

        if required is True:
            f.set_attribute('required')

        if readonly is True:
            f.set_attribute('readonly')

        if placeholder is not None:
            f.set_attribute('placeholder',placeholder)

        if max_length is not None:
            f.set_attribute('maxlength', max_length)

        if size is not None:
            f.set_attribute('size', size)

        if suffix is not None:
            dom.append(suffix)

        return dom

    def textarea(self, name, value, label=None, readonly=False, prefix=None,
                 suffix=None, required=False, rows=None, cols=None,
                 placeholder=None, cls=None):
        dom = Dom()

        if label is not None:
            l = dom.create_element('label')
            l.set_attribute('for', name)
            l.append(label)

        if prefix is not None:
            dom.append(prefix)

        f = dom.create_element('textarea')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
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
            dom.append(suffix)

        return dom

    def hidden_input(self, name, value):
        dom = Dom()

        f = dom.create_element('input')
        f.set_attribute('type', 'hidden')
        f.set_attribute('id', name)
        f.set_attribute('name', name)
        f.set_attribute('value', value)

        return dom
