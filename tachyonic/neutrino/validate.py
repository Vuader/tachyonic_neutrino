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
    """Is Unix socket

    Returns Bool wether file is unix socket.

    Args:
        socket (str): Socket path.
    """
    try:
        mode = os.stat(socket).st_mode
        is_socket = stat.S_ISSOCK(mode)
    except:
        is_socket = False
    return is_socket

def is_text(text):
    """Is Text?

    Returns Bool wether text.

    Args:
        text (str/bytes): Socket path.
    """
    if isinstance(text, str):
            return True
    elif isinstance(text, bytes):
        if is_binary(text):
            return False
        else:
            return True
    else:
        return False

def is_binary(data):
    """Is Binary?

    Returns Bool wether binary.

    Args:
        data (str/bytes): Possible binary or string.
    """
    if isinstance(data, str):
        return False
    elif isinstance(data, bytes):
        try:
            # if s contains any null, it's not text:
            if "\0".encode() in data:
                return True
            # an "empty" string is "text" (arbitrary but reasonable choice):
            # decode byte string from utf-8 to string.
            if not data or data.decode('utf-8') == '':
                return False
        except UnicodeDecodeError:
            # UnicodeDecodError means binary...
            return True
        return True
    else:
        return False

def is_byte_string(string):
    """Is Bytes String?

    Returns Bool wether Bytes String?

    Args:
        string (bytes): Possible binary or string.
    """
    if isinstance(string, bytes):
        if is_binary(string):
            return False
        else:
            return True
    else:
        return False
