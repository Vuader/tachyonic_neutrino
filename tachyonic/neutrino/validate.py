# -*- coding: utf-8 -*-
# Copyright (c) 2017, Christiaan Frans Rademan.
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

import os
import sys
import stat
import logging

log = logging.getLogger(__name__)

def is_socket(socket):
    try:
        mode = os.stat(socket).st_mode
        is_socket = stat.S_ISSOCK(mode)
    except:
        is_socket = False
    return is_socket


def is_text(s):
    if isinstance(s, str):
        if is_binary(s):
            return False
        else:
            return True
    else:
        return False


def is_binary(s):
    if isinstance(s, str) or isinstance(s, bytes):
        try:
            if s == '':
                return False
            # if s contains any null, it's not text:
            if "\0" in s:
                return True
            # an "empty" string is "text" (arbitrary but reasonable choice):
            if not s:
                return False
        except UnicodeDecodeError:
            return True
    else:
        return False

def is_byte_string(string):
    if sys.version_info[0] == 2:
        if isinstance(string, str):
            return True
        else:
            return False
    else:
        if isinstance(string, bytes):
            return True
        else:
            return False
