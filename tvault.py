#!/usr/bin/env python3

"""TVault
Command line script to store Time-based One-Time Password (TOTP) secret keys
and generate TOTP passwords for two-factor authentication (2FA) on services that
require it.  Depends on GnuPG for encrypting TOTP secrets and oathtool to generate
the passwords.
"""

__version__ = '0.4'
__date__ = '2023-12-09'
__author__ = 'António Manuel Dias <ammdias@gmail.com>'
__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import sys
import shutil
import os
import subprocess


usage = """Usage:
  Add SERVICE to available services:
  $ tvault -add SERVICE SECRET

  Generate TOTP for SERVICE:
  $ tvault SERVICE

  Launch a Graphical User Interface to generate a TOTP or add a new service:
  $ tvault -gui

  List all available services:
  $ tvault -list

  Remove SERVICE from available services:
  $ tvault -del SERVICE

  Show secret key for SERVICE:
  $ tvault -secret SERVICE

  Change vault password:
  $ tvault -chpass

  Encrypt vault file with a GnuPG public key
  $ tvault -recipient KEY_ID

  Encrypt vault file with symmetric key
  $ tvault -symmetric

  Uninstall the program
  $ tvault -uninstall
"""


#------------------------------------------------------------------------------
# Main function

def run(args):
    """Run the script.
    """
    # get tool paths
    tools = gettoolpaths('gpg', 'oathtool')
    if tools['gpg'] is None or tools['oathtool'] is None:
        raise TVaultException("TOTP Vault needs GnuPG and oathtool to run.\n"
                              "Please make sure these are installed and in the PATH.")
    if 'DISPLAY' in os.environ:
        tools |= gettoolpaths('xsel')
        if tools['xsel'] is None:
            print("xsel is not installed.\n"
                  "Generated codes will not be automatically copied to the clipboard.\n"
                  "If you want this feature, please install xsel.")

    # get vault file path
    vaultpath = getvaultpath()

    # execute action
    match args[0], len(args):
        case '-gui', 1:
            if 'DISPLAY' in os.environ:
                showgui(tools, vaultpath)
            else:
                raise TVaultException('GUI not available on this terminal.')
        case '-list', 1:
            listservices(tools, vaultpath)
        case '-add', 3:
            addservice(tools, vaultpath, *args[1:])
        case '-del', 2:
            delservice(tools, vaultpath, args[1])
        case '-secret', 2:
            showservicekey(tools, vaultpath, args[1])
        case '-chpass', 1:
            changepassword(tools, vaultpath)
        case '-recipient', 2:
            addrecipient(tools, vaultpath, args[1])
        case '-symmetric', 1:
            delrecipient(tools, vaultpath)
        case '-uninstall', 1:
            from UNINSTALL import uninstall
            uninstall()
        case service, 1:
            generatetotp(tools, vaultpath, service)
        case _:
            raise TVaultException(usage)


#------------------------------------------------------------------------------
# CLI functions

def listservices(tools, vaultpath):
    """List services available on vault file.
    """
    services = decrypt(tools, vaultpath)
    services = '\n'.join([f'* {name}' for name in services if name.isalnum()])
    if services:
        print(f"Available services:\n{services}")
    else:
        print('No service has been added yet.')


def addservice(tools, vaultpath, service, secret):
    """Add service to vault file.
    """
    service, secret = sanitycheck(service, secret)
    services = decrypt(tools, vaultpath)
    services[service] = secret
    encrypt(tools, vaultpath, services)
    generatetotp(tools, vaultpath, service)


def delservice(tools, vaultpath, service):
    """Delete service from vault file.
    """
    services = decrypt(tools, vaultpath)
    if service not in services:
        raise TVaultException(f'Service {service} not found.')

    del services[service]
    encrypt(tools, vaultpath, services)


def showservicekey(tools, vaultpath, service):
    """Show secret key of service on vault file.
    """
    services = decrypt(tools, vaultpath)
    if service not in services:
        raise TVaultException(f'Service {service} not found.')

    print(f'Secret key for {service}: {services[service]}')


def changepassword(tools, vaultpath):
    """Change vault file password.
    """
    services = decrypt(tools, vaultpath)
    encrypt(tools, vaultpath, services)


def addrecipient(tools, vaultpath, recipient):
    """Encrypt vault file with a GnuPG public key.
    """
    services = decrypt(tools, vaultpath)
    services['-recipient'] = recipient
    encrypt(tools, vaultpath, services)


def delrecipient(tools, vaultpath):
    """Encrypt vault file with symmetric key.
    """
    services = decrypt(tools, vaultpath)
    if '-recipient' in services:
        del services['-recipient']
    encrypt(tools, vaultpath, services)


def generatetotp(tools, vaultpath, service):
    """Generate TOTP for service on vault file.
    """
    services = decrypt(tools, vaultpath)
    if service not in services:
        raise TVaultException(f'Service {service} not found.')

    code = totp(tools, services[service])
    print(f'TOTP code for {service}: {code}')

    # if possible, copy code to clipboard
    clipboardinsert(tools, code)


#------------------------------------------------------------------------------
# GUI functions

def showgui(tools, vaultpath):
    """Run graphical user interface.
    """
    tools |= gettoolpaths('zenity')
    if tools['zenity'] is None:
        raise TVaultException('Zenity not found.')

    try:
        services = decrypt(tools, vaultpath)
        service_names = [name for name in services if name.isalnum()]
        service_names.append('* Add a service...')
        service = gservice(tools, service_names)
        match service:
            case '* Add a service...':
                gaddservice(tools, vaultpath, services)
            case _:
                code = totp(tools, services[service])
                gshowcode(tools, service, code)
    except SubrunException as e:
        gerror(tools, f"Error while executing {e.command}.\n"
                      f"{e.errortext}")
    except Exception as e:
        gerror(tools, str(e))


def gservice(tools, items):
    """Choose service.
    """
    return zenity(tools, '--list', '--text=Choose service:', '--column=Service',
                         '--hide-header', *items)


def gshowcode(tools, service, code):
    """Show service code.
    """
    clipboardinsert(tools, code)
    zenity(tools, '--info', f'--text=Code for {service}: {code}')


def gaddservice(tools, vaultpath, services):
    """Add a service.
    """
    service = ggettext(tools, 'New service name:')
    secret = ggettext(tools, f'Secret key for service {service}:')
    service, secret = sanitycheck(service, secret)

    services[service] = secret
    encrypt(tools, vaultpath, services)
    code = totp(tools, secret)
    gshowcode(tools, service, code)


def ggettext(tools, text):
    """Get text from user.
    """
    return zenity(tools, '--entry', f'--text={text}')


def gerror(tools, error):
    """Show error message and exit.
    """
    zenity(tools, '--error', f'--text={error}')
    sys.exit(1)


#------------------------------------------------------------------------------
# tools

def gettoolpaths(*tools):
    """Check system for tool paths.
       Returns dictionary with paths for tools.
    """
    return { t: shutil.which(t) for t in tools }


def getvaultpath():
    """Get vault file path.
    """
    home = os.path.expanduser('~')
    config_dir = os.path.join(home, '.config')
    if os.path.isdir(config_dir):
        return os.path.join(config_dir, 'tvault')
    else:
        return os.path.join(home, '.tvault')


def encrypt(tools, vaultpath, services):
    """Encode and encrypt service/secret pairs into vault file.
    """
    # build vault from services' name / secret pairs
    # one service perline, separator is ':'
    vault = '\n'.join(f'{name}:{services[name]}' for name in services)
    if '-recipient' in services:
        if not isrecipient(tools, services['-recipient']):
            raise TVaultException(f"Secret key for {services['-recipient']} not found.")
        subrun(tools['gpg'], '--encrypt', '--quiet', '--armour', '--yes',
                             '--recipient', services['-recipient'],
                             '--output', vaultpath, inpt=vault)
    else:
        subrun(tools['gpg'], '--quiet', '--symmetric', '--armour',
                             '--yes', '--output', vaultpath, inpt=vault)


def decrypt(tools, vaultpath):
    """Decrypt vault file,
       return dictionary with service/secret pairs.
    """
    services = {}
    if not os.path.exists(vaultpath):
       encrypt(tools, vaultpath, services)

    res = subrun(tools['gpg'], '--quiet', '--decrypt', vaultpath)

    # read vault service names / secret codes
    # one service per line
    # empty lines or lines started with ';' are ignored
    for line in res.splitlines():
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        name, sep, secret = line.partition(':')
        if not sep or not secret:
            raise TVaultException(f"Corrupted line in vault file at '{vaultpath}'.")
        services[name] = secret

    return services


def isrecipient(tools, keyid):
    """Check if secret key is in GnuPG keyring.
    """
    keyid = f'<{keyid}>'
    uids = [i for i in subrun(tools['gpg'], '--list-secret-keys').splitlines()
              if i.startswith('uid') and '[ultimate]' in i and keyid in i]

    return len(uids) > 0


def totp(tools, secret):
    """Generate TOTP code for service.
    """
    return subrun(tools['oathtool'], '--base32', '--totp', secret)


def sanitycheck(service, secret):
    """Sanity check service name and secret.
    """
    service, secret = service.strip(), secret.strip()
    if not service or not secret:
        raise TVaultException('Service name and secret must not be empty.')
    if not service.isalnum():
        raise TVaultException('Service name must consist of letters and numbers.')
    for c in secret.upper():
        if c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ 234567':
            raise TVaultException('Secret key is not a valid base32 string.') 
    
    return service, secret


def clipboardinsert(tools, text):
    """Insert text on primary and secondary clipboard.
    """
    if 'xsel' in tools:
        subrun(tools['xsel'], '--input', '--primary', inpt=text)
        subrun(tools['xsel'], '--input', '--clipboard', inpt=text)
        print('Code copied to clipboard.')


def subrun(command, *options, inpt=None):
    """Execute system command.
    """
    if inpt:
        inpt = inpt.encode(sys.stdin.encoding) 

    res = subprocess.run([command, *options], capture_output=True, input=inpt)
    if res.returncode != 0:
        etext = res.stderr.decode(sys.stdout.encoding).strip() if res.stderr else ''
        raise SubrunException(command, res.returncode, etext)
                              
    return res.stdout.decode(sys.stdout.encoding).strip() if res.stdout else ''


def zenity(tools, dialog, *options):
    """Show zenity dialog.
    """
    try:
        return subrun(tools['zenity'], dialog, '--title=TVault', *options)
    except SubrunException as e:
        if e.errorcode == 1:
            gerror(tools, 'Action cancelled by user.')
        else:
            raise e


#------------------------------------------------------------------------------
# Exceptions

class TVaultException(Exception):
    pass


class SubrunException(TVaultException):
    def __init__(self, command, errorcode, errortext):
        super().__init__(f'Failed to execute {command}.')
        self.command = command
        self.errorcode = errorcode
        self.errortext = errortext


#------------------------------------------------------------------------------
# Script entry point

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        try:
            run(sys.argv[1:])
        except SubrunException as e:
            print(f'Error while executing {e.command}.', file=sys.stderr)
            print(e.errortext, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            sys.exit(1)
    else:
        print(f"""
{__doc__}
version {__version__}
Copyright (C) 2023 {__author__}
{__license__}
{usage}
""")
