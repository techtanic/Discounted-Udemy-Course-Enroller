# -*- coding: utf-8 -*-

import os
import os.path
import sys
import time
import glob
import http.cookiejar
import tempfile
import lz4.block
import datetime
import configparser
import base64
from Crypto.Cipher import AES

try:
    import json
except ImportError:
    import simplejson as json
try:
    # should use pysqlite2 to read the cookies.sqlite on Windows
    # otherwise will raise the "sqlite3.DatabaseError: file is encrypted or is not a database" exception
    from pysqlite2 import dbapi2 as sqlite3
except ImportError:
    import sqlite3

# external dependencies
import keyring
import pyaes
from pbkdf2 import PBKDF2

__doc__ = 'Load browser cookies into a cookiejar'


class BrowserCookieError(Exception):
    pass


def create_local_copy(cookie_file):
    """Make a local copy of the sqlite cookie database and return the new filename.
    This is necessary in case this database is still being written to while the user browses
    to avoid sqlite locking errors.
    """
    # check if cookie file exists
    if os.path.exists(cookie_file):
        # copy to random name in tmp folder
        tmp_cookie_file = tempfile.NamedTemporaryFile(suffix='.sqlite').name
        open(tmp_cookie_file, 'wb').write(open(cookie_file, 'rb').read())
        return tmp_cookie_file
    else:
        raise BrowserCookieError('Can not find cookie file at: ' + cookie_file)


def windows_group_policy_path():
    # we know that we're running under windows at this point so it's safe to do these imports
    from winreg import ConnectRegistry, HKEY_LOCAL_MACHINE, OpenKeyEx, QueryValueEx, REG_EXPAND_SZ, REG_SZ
    try:
        root = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        policy_key = OpenKeyEx(root, r"SOFTWARE\Policies\Google\Chrome")
        user_data_dir, type_ = QueryValueEx(policy_key, "UserDataDir")
        if type_ == REG_EXPAND_SZ:
            user_data_dir = os.path.expandvars(user_data_dir)
        elif type_ != REG_SZ:
            return None
    except OSError:
        return None
    return os.path.join(user_data_dir, "Default", "Cookies")


# Code adapted slightly from https://github.com/Arnie97/chrome-cookies
def crypt_unprotect_data(
        cipher_text=b'', entropy=b'', reserved=None, prompt_struct=None, is_key=False
):
    # we know that we're running under windows at this point so it's safe to try these imports
    import ctypes
    import ctypes.wintypes

    class DataBlob(ctypes.Structure):
        _fields_ = [
            ('cbData', ctypes.wintypes.DWORD),
            ('pbData', ctypes.POINTER(ctypes.c_char))
        ]

    blob_in, blob_entropy, blob_out = map(
        lambda x: DataBlob(len(x), ctypes.create_string_buffer(x)),
        [cipher_text, entropy, b'']
    )
    desc = ctypes.c_wchar_p()

    CRYPTPROTECT_UI_FORBIDDEN = 0x01

    if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), ctypes.byref(
                desc), ctypes.byref(blob_entropy),
            reserved, prompt_struct, CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(
                blob_out)
    ):
        raise RuntimeError('Failed to decrypt the cipher text with DPAPI')

    description = desc.value
    buffer_out = ctypes.create_string_buffer(int(blob_out.cbData))
    ctypes.memmove(buffer_out, blob_out.pbData, blob_out.cbData)
    map(ctypes.windll.kernel32.LocalFree, [desc, blob_out.pbData])
    if is_key:
        return description, buffer_out.raw
    else:
        return description, buffer_out.value


def get_linux_pass(browser="Chrome"):
    # Try to get pass from Gnome / libsecret if it seems available
    # https://github.com/n8henrie/pycookiecheat/issues/12
    my_pass = None
    try:
        import gi

        gi.require_version("Secret", "1")
        from gi.repository import Secret
    except (ImportError, AttributeError):
        pass
    else:
        flags = Secret.ServiceFlags.LOAD_COLLECTIONS
        service = Secret.Service.get_sync(flags)

        gnome_keyring = service.get_collections()
        unlocked_keyrings = service.unlock_sync(gnome_keyring).unlocked

        keyring_name = "{} Safe Storage".format(browser.capitalize())

        for unlocked_keyring in unlocked_keyrings:
            for item in unlocked_keyring.get_items():
                if item.get_label() == keyring_name:
                    item.load_secret_sync()
                    my_pass = item.get_secret().get_text()
                    break
            else:
                # Inner loop didn't `break`, keep looking
                continue

            # Inner loop did `break`, so `break` outer loop
            break

    # Try to get pass from keyring, which should support KDE / KWallet
    # if dbus-python is installed.
    if not my_pass:
        try:
            my_pass = keyring.get_password(
                "{} Keys".format(browser), "{} Safe Storage".format(browser)
            )
        except RuntimeError:
            pass

    if my_pass:
        return my_pass


class Chrome:
    def __init__(self, cookie_file=None, domain_name="", key_file=None):
        self.salt = b'saltysalt'
        self.iv = b' ' * 16
        self.length = 16
        # domain name to filter cookies by
        self.domain_name = domain_name
        if sys.platform == 'darwin':
            # running Chrome on OSX
            my_pass = keyring.get_password('Chrome Safe Storage', 'Chrome').encode(
                'utf8')  # get key from keyring
            iterations = 1003  # number of pbkdf2 iterations on mac
            self.key = PBKDF2(my_pass, self.salt,
                              iterations=iterations).read(self.length)
            cookie_file = cookie_file \
                or os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')

        elif sys.platform.startswith('linux'):
            # running Chrome on Linux
            for name in ('Chrome', 'Chromium'):
                my_pass = get_linux_pass(name)
                if my_pass is not None:
                    my_pass = my_pass.encode('utf8')
                    if name == 'Chromium':
                        paths = map(os.path.expanduser, [
                            '~/.config/chromium/Default/Cookies',
                        ])
                    else:
                        paths = map(os.path.expanduser, [
                            '~/.config/google-chrome/Default/Cookies',
                            '~/.config/google-chrome-beta/Default/Cookies'
                        ])
                    break
            else:
                # try default key 'peanuts' with all possible paths (probably won't work)
                my_pass = 'peanuts'
                paths = map(os.path.expanduser, [
                    '~/.config/google-chrome/Default/Cookies',
                    '~/.config/chromium/Default/Cookies',
                    '~/.config/google-chrome-beta/Default/Cookies'
                ])
            iterations = 1
            self.key = PBKDF2(my_pass, self.salt,
                              iterations=iterations).read(self.length)
            cookie_file = cookie_file or next(
                filter(os.path.exists, paths), None)

        elif sys.platform == "win32":

            # Read key from file
            key_file = key_file or glob.glob(os.path.join(os.getenv('APPDATA', ''), '..\Local\\Google\\Chrome\\User Data\\Local State')) \
                or glob.glob(os.path.join(os.getenv('LOCALAPPDATA', ''), 'Google\\Chrome\\User Data\\Local State')) \
                or glob.glob(os.path.join(os.getenv('APPDATA', ''), 'Google\\Chrome\\User Data\\Local State'))

            if isinstance(key_file, list):
                if key_file:
                    key_file = key_file[0]

            if key_file:
                f = open(key_file, 'rb')
                key_file_json = json.load(f)
                key64 = key_file_json['os_crypt']['encrypted_key'].encode(
                    'utf-8')

                # Decode Key, get rid of DPAPI prefix, unprotect data
                keydpapi = base64.standard_b64decode(key64)[5:]
                _, self.key = crypt_unprotect_data(keydpapi, is_key=True)

            # get cookie file from APPDATA
            # Note: in windows the \\ is required before a u to stop unicode errors
            cookie_file = cookie_file or windows_group_policy_path() \
                or glob.glob(os.path.join(os.getenv('APPDATA', ''), '..\Local\\Google\\Chrome\\User Data\\Default\\Cookies')) \
                or glob.glob(os.path.join(os.getenv('LOCALAPPDATA', ''), 'Google\\Chrome\\User Data\\Default\\Cookies')) \
                or glob.glob(os.path.join(os.getenv('APPDATA', ''), 'Google\\Chrome\\User Data\\Default\\Cookies'))
        else:
            raise BrowserCookieError(
                "OS not recognized. Works on Chrome for OSX, Windows, and Linux.")

        # if the cookie_file is None, could not find a Chrome cookie
        if cookie_file is None:
            raise BrowserCookieError('Failed to find Chrome cookie')
        
        # if the type of cookie_file is list, use the first element in the list
        if isinstance(cookie_file, list):
            if not cookie_file:
                raise BrowserCookieError('Failed to find Chrome cookie')
            cookie_file = cookie_file[0]

        self.tmp_cookie_file = create_local_copy(cookie_file)

    def __del__(self):
        # remove temporary backup of sqlite cookie database
        if hasattr(self, 'tmp_cookie_file'):  # if there was an error till here
            os.remove(self.tmp_cookie_file)

    def __str__(self):
        return 'chrome'

    def load(self):
        """Load sqlite cookies into a cookiejar
        """
        con = sqlite3.connect(self.tmp_cookie_file)
        cur = con.cursor()
        try:
            # chrome <=55
            cur.execute('SELECT host_key, path, secure, expires_utc, name, value, encrypted_value '
                        'FROM cookies WHERE host_key like "%{}%";'.format(self.domain_name))
        except sqlite3.OperationalError:
            # chrome >=56
            cur.execute('SELECT host_key, path, is_secure, expires_utc, name, value, encrypted_value '
                        'FROM cookies WHERE host_key like "%{}%";'.format(self.domain_name))

        cj = http.cookiejar.CookieJar()
        epoch_start = datetime.datetime(1601, 1, 1)
        for item in cur.fetchall():
            host, path, secure, expires, name = item[:5]
            if item[3] != 0:
                # ensure dates don't exceed the datetime limit of year 10000
                try:
                    offset = min(int(item[3]), 265000000000000000)
                    delta = datetime.timedelta(microseconds=offset)
                    expires = epoch_start + delta
                    expires = expires.timestamp()
                # Windows 7 has a further constraint
                except OSError:
                    offset = min(int(item[3]), 32536799999000000)
                    delta = datetime.timedelta(microseconds=offset)
                    expires = epoch_start + delta
                    expires = expires.timestamp()

            value = self._decrypt(item[5], item[6])
            c = create_cookie(host, path, secure, expires, name, value)
            cj.set_cookie(c)
        con.close()
        return cj

    @staticmethod
    def _decrypt_windows_chrome(value, encrypted_value):

        if len(value) != 0:
            return value

        if encrypted_value == "":
            return ""

        _, data = crypt_unprotect_data(encrypted_value)
        assert isinstance(data, bytes)
        return data.decode()

    def _decrypt(self, value, encrypted_value):
        """Decrypt encoded cookies
        """

        if sys.platform == 'win32':
            try:
                return self._decrypt_windows_chrome(value, encrypted_value)

            # Fix for change in Chrome 80
            except RuntimeError:  # Failed to decrypt the cipher text with DPAPI
                if not self.key:
                    raise RuntimeError(
                        'Failed to decrypt the cipher text with DPAPI and no AES key.')
                # Encrypted cookies should be prefixed with 'v10' according to the
                # Chromium code. Strip it off.
                encrypted_value = encrypted_value[3:]
                nonce, tag = encrypted_value[:12], encrypted_value[-16:]
                aes = AES.new(self.key, AES.MODE_GCM, nonce=nonce)

                data = aes.decrypt_and_verify(encrypted_value[12:-16], tag)
                return data.decode()

        if value or (encrypted_value[:3] not in [b'v11', b'v10']):
            return value

        # Encrypted cookies should be prefixed with 'v10' according to the
        # Chromium code. Strip it off.
        encrypted_value = encrypted_value[3:]
        encrypted_value_half_len = int(len(encrypted_value) / 2)

        cipher = pyaes.Decrypter(
            pyaes.AESModeOfOperationCBC(self.key, self.iv))
        decrypted = cipher.feed(encrypted_value[:encrypted_value_half_len])
        decrypted += cipher.feed(encrypted_value[encrypted_value_half_len:])
        decrypted += cipher.feed()
        return decrypted.decode("utf-8")


class Firefox:
    def __init__(self, cookie_file=None, domain_name=""):
        self.tmp_cookie_file = None
        cookie_file = cookie_file or self.find_cookie_file()
        self.tmp_cookie_file = create_local_copy(cookie_file)
        # current sessions are saved in sessionstore.js
        self.session_file = os.path.join(
            os.path.dirname(cookie_file), 'sessionstore.js')
        self.session_file_lz4 = os.path.join(os.path.dirname(
            cookie_file), 'sessionstore-backups', 'recovery.jsonlz4')
        # domain name to filter cookies by
        self.domain_name = domain_name

    def __del__(self):
        # remove temporary backup of sqlite cookie database
        if self.tmp_cookie_file:
            os.remove(self.tmp_cookie_file)

    def __str__(self):
        return 'firefox'

    @staticmethod
    def get_default_profile(user_data_path):
        config = configparser.ConfigParser()
        profiles_ini_path = glob.glob(os.path.join(
            user_data_path + '**', 'profiles.ini'))
        fallback_path = user_data_path + '**'

        if not profiles_ini_path:
            return fallback_path

        profiles_ini_path = profiles_ini_path[0]
        config.read(profiles_ini_path)

        profile_path = None
        for section in config.sections():
            if section.startswith('Install'):
                profile_path = config[section].get('Default')
                break
            # in ff 72.0.1, if both an Install section and one with Default=1 are present, the former takes precedence
            elif config[section].get('Default') == '1' and not profile_path:
                profile_path = config[section].get('Path')

        for section in config.sections():
            # the Install section has no relative/absolute info, so check the profiles
            if config[section].get('Path') == profile_path:
                absolute = config[section].get('IsRelative') == '0'
                return profile_path if absolute else os.path.join(os.path.dirname(profiles_ini_path), profile_path)

        return fallback_path

    @staticmethod
    def find_cookie_file():
        cookie_files = []

        if sys.platform == 'darwin':
            user_data_path = os.path.expanduser(
                '~/Library/Application Support/Firefox')
        elif sys.platform.startswith('linux'):
            user_data_path = os.path.expanduser('~/.mozilla/firefox')
        elif sys.platform == 'win32':
            user_data_path = os.path.join(
                os.environ.get('APPDATA'), 'Mozilla', 'Firefox')
            # legacy firefox <68 fallback
            cookie_files = glob.glob(os.path.join(os.environ.get('PROGRAMFILES'), 'Mozilla Firefox', 'profile', 'cookies.sqlite')) \
                or glob.glob(os.path.join(os.environ.get('PROGRAMFILES(X86)'), 'Mozilla Firefox', 'profile', 'cookies.sqlite'))
        else:
            raise BrowserCookieError(
                'Unsupported operating system: ' + sys.platform)

        cookie_files = glob.glob(os.path.join(Firefox.get_default_profile(user_data_path), 'cookies.sqlite')) \
            or cookie_files

        if cookie_files:
            return cookie_files[0]
        else:
            raise BrowserCookieError('Failed to find Firefox cookie')

    @staticmethod
    def __create_session_cookie(cookie_json):
        expires = str(int(time.time()) + 3600 * 24 * 7)
        return create_cookie(cookie_json.get('host', ''), cookie_json.get('path', ''), False, expires,
                             cookie_json.get('name', ''), cookie_json.get('value', ''))

    def __add_session_cookies(self, cj):
        if not os.path.exists(self.session_file):
            return
        try:
            json_data = json.loads(
                open(self.session_file, 'rb').read().decode())
        except ValueError as e:
            print('Error parsing firefox session JSON:', str(e))
        else:
            for window in json_data.get('windows', []):
                for cookie in window.get('cookies', []):
                    if self.domain_name == '' or self.domain_name in cookie.get('host', ''):
                        cj.set_cookie(Firefox.__create_session_cookie(cookie))

    def __add_session_cookies_lz4(self, cj):
        if not os.path.exists(self.session_file_lz4):
            return
        try:
            file_obj = open(self.session_file_lz4, 'rb')
            file_obj.read(8)
            json_data = json.loads(lz4.block.decompress(file_obj.read()))
        except ValueError as e:
            print('Error parsing firefox session JSON LZ4:', str(e))
        else:
            for cookie in json_data.get('cookies', []):
                if self.domain_name == '' or self.domain_name in cookie.get('host', ''):
                    cj.set_cookie(Firefox.__create_session_cookie(cookie))

    def load(self):
        con = sqlite3.connect(self.tmp_cookie_file)
        cur = con.cursor()
        cur.execute('select host, path, isSecure, expiry, name, value from moz_cookies '
                    'where host like "%{}%"'.format(self.domain_name))

        cj = http.cookiejar.CookieJar()
        for item in cur.fetchall():
            c = create_cookie(*item)
            cj.set_cookie(c)
        con.close()

        self.__add_session_cookies(cj)
        self.__add_session_cookies_lz4(cj)

        return cj


def create_cookie(host, path, secure, expires, name, value):
    """Shortcut function to create a cookie
    """
    return http.cookiejar.Cookie(0, name, value, None, False, host, host.startswith('.'), host.startswith('.'), path,
                                 True, secure, expires, False, None, None, {})


def chrome(cookie_file=None, domain_name="", key_file=None):
    """Returns a cookiejar of the cookies used by Chrome. Optionally pass in a
    domain name to only load cookies from the specified domain
    """
    return Chrome(cookie_file, domain_name, key_file).load()


def firefox(cookie_file=None, domain_name=""):
    """Returns a cookiejar of the cookies and sessions used by Firefox. Optionally
    pass in a domain name to only load cookies from the specified domain
    """
    return Firefox(cookie_file, domain_name).load()


def load(domain_name=""):
    """Try to load cookies from all supported browsers and return combined cookiejar
    Optionally pass in a domain name to only load cookies from the specified domain
    """
    cj = http.cookiejar.CookieJar()
    for cookie_fn in [chrome, firefox]:
        try:
            for cookie in cookie_fn(domain_name=domain_name):
                cj.set_cookie(cookie)
        except BrowserCookieError:
            pass
    return cj


if __name__ == '__main__':
    print(load())
