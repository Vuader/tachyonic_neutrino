# -*- coding: utf-8 -*-
# Copyright (c) 2016-2017, Christiaan Frans Rademan, Allan Swanepoel.
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

import logging
import passlib.hash
import passlib.context

from tachyonic.neutrino import constants as const
from tachyonic.neutrino.exceptions import Error

log = logging.getLogger(__name__)


def hash(password, algo=const.BLOWFISH, rounds=15):
    """Hash Password.

    Provide a simple interface for hashing passwords using specified algorithm
    and rounds.

    Args:
        password (str): Clear Text Password
        algo (str): algorithm (defined in tachyonic.neutrino.constants)
            * CLEARTEXT
            * BLOWFISH
            * SHA256
            * SHA512
            * LDAP_MD5
            * LDAP_SMD5
            * LDAP_SHA1
            * LDAP_SSHA1
            * LDAP_CLEARTEXT
            * LDAP_BLOWFISH
            * LDAP_SHA256
            * LDAP_SHA512
        rounds (int): Hashing rounds...

    Returns hashed value of password.
    """

    if (rounds < 1000 and
            (algo == const.SHA256 or
             algo == const.SHA512 or
             algo == const.LDAP_SHA256 or
             algo == const.LDAP_SHA512)):
        rounds = 1000

    if algo == const.BLOWFISH:
        hashed = passlib.hash.bcrypt.encrypt(password, rounds=rounds)
    elif algo == const.CLEARTEXT:
        hashed = passlib.hash.md5_crypt.encrypt(password)
    elif algo == const.SHA256:
        hashed = passlib.hash.sha256_crypt.encrypt(password, rounds=rounds)
    elif algo == const.SHA512:
        hashed = passlib.hash.sha512_crypt.encrypt(password, rounds=rounds)
    elif algo == const.LDAP_MD5:
        hashed = passlib.hash.ldap_md5.encrypt(password)
    elif algo == const.LDAP_SMD5:
        hashed = passlib.hash.ldap_salted_md5.encrypt(password)
    elif algo == const.LDAP_SHA1:
        hashed = passlib.hash.ldap_sha1.encrypt(password)
    elif algo == const.LDAP_SSHA1:
        hashed = passlib.hash.ldap_salted_sha1.encrypt(password)
    elif algo == const.LDAP_CLEARTEXT:
        hashed = passlib.hash.ldap_plaintext.encrypt(password)
    elif algo == const.LDAP_BLOWFISH:
        hashed = passlib.hash.ldap_bcrypt.encrypt(password, rounds=rounds)
    elif algo == const.LDAP_SHA256:
        hashed = passlib.hash.ldap_sha256_crypt.encrypt(password, rounds=rounds)
    elif algo == const.LDAP_SHA512:
        hashed = passlib.hash.ldap_sha512_crypt.encrypt(password, rounds=rounds)
    else:
        raise Error('Invalid hash specified %s' % algo)
    return hashed


def valid(password, hashed):
    """ Validate password against hash.

    Args:
        password (str): Clear Text Password
        hashed (str): Hashed value of Password
        plaintext (bool): Wether plaintext or not.

    Return bool wether password matches.
    """

    # Initilize pwd_content globally per process.
    # Purpose is faster loading initially.
    global pwd_context

    try:
        pwd_context
    except:
        schemes=["md5_crypt", "bcrypt", "sha256_crypt", "sha512_crypt",
                 "ldap_md5", "ldap_salted_md5", "ldap_sha1", "ldap_salted_sha1",
                 "ldap_bcrypt", "ldap_sha256_crypt", "ldap_sha512_crypt"]
        pwd_context = passlib.context.CryptContext(schemes=schemes)

    # If Password is Clear-Text
    if password == hashed:
        return True
    else:
        # Validate Password using pwd_context
        if pwd_context.verify(password, hashed):
            return True
        else:
            return False
