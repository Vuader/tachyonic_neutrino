from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from tachyonic.neutrino import constants as const
import passlib.hash
import passlib.context

log = logging.getLogger(__name__)

def hash(password, algo=const.BLOWFISH, rounds=15):
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
        pass
    return hashed


def valid(password, hashed, plaintext=False):
    pwd_context = passlib.context.CryptContext(schemes=["md5_crypt", "bcrypt", "sha256_crypt", "sha512_crypt",
                                                        "ldap_md5", "ldap_salted_md5", "ldap_sha1", "ldap_salted_sha1",
                                                        "ldap_bcrypt", "ldap_sha256_crypt", "ldap_sha512_crypt"])

    if plaintext is True:
        if password == hashed:
            return True
        else:
            return False
    else:
        if pwd_context.verify(password, hashed):
            return True
        else:
            return False
