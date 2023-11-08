#!/usr/bin/env python3

"""TVault
Command line script to store Time-based One-Time Password (TOTP) secret keys
and generate TOTP passwords for two-factor authentication (2FA) on services that
require it.  Depends on GnuPG for encrypting TOTP secrets and oathtool to generate
the passwords.
"""

__version__ = '0.2'
__date__ = '2023-11-05'
__author__ = 'António Manuel Dias <ammdias@gmail.com>'
__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import sys
import shutil
import os.path
import subprocess


usage = """Usage:
  Add SERVICE to available services:
  $ tvault -add SERVICE SECRET

  Generate TOTP for SERVICE:
  $ tvault SERVICE

  Show secret key for SERVICE:
  $ tvault -secret SERVICE

  Remove SERVICE from available services:
  $ tvault -del SERVICE

  List all available services:
  $ tvault -list

  Change vault password:
  $ tvault -chpass

  Launch a Graphical User Interface to generate a TOTP or add a new service:
  $ tvault -gui
"""


#------------------------------------------------------------------------------
# Main function

def run(args):
    """Run the script.
    """
    # get tool paths
    tools = gettoolpaths('gpg', 'oathtool', 'xsel')
    if 'gpg' not in tools or 'oathtool' not in tools:
        raise TVaultException("TOTP Vault needs GnuPG and oathtool to run.\n"
                              "Please make sure these are installed and in the PATH.")
    if 'xsel' not in tools:
        print("xsel is not installed.\n"
              "Generated codes will not be automatically copied to the clipboard.\n"
              "If you want this feature, please install xsel.")

    # get vault file path
    vaultpath = getvaultpath()

    # execute action
    match args[0], len(args):
        case '-gui', 1:
            showgui(tools, vaultpath)
        case '-list', 1:
            listservices(tools, vaultpath)
        case '-add', 3:
            addservice(tools, vaultpath, *args[1:])
        case '-del', 2:
            deleteservice(tools, vaultpath, args[1])
        case '-secret', 2:
            showservicekey(tools, vaultpath, args[1])
        case '-chpass', 1:
            changepassword(tools, vaultpath)
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
    print('Available services:')
    if services:
        for name in services:
            print(f'* {name}')
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


def deleteservice(tools, vaultpath, service):
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
    zenity = gettoolpaths('zenity')
    if not zenity:
        raise TVaultException('Zenity not found.')
    tools |= zenity

    try:
        services = decrypt(tools, vaultpath)
        service_names = [*services, '* Add a service...']
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
    secret = ggettext(tools, f'Secret key for service {service}:').strip()
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
    res = {}
    for t in tools:
        path = shutil.which(t)
        if path:
            res[t] = path

    return res


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
            raise TVaultException(f"Corruted line in vault file at '{vaultpath}'.")
        services[name] = secret

    return services


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
    if ':' in service:
        raise TVaultException('Service name can not contain a colon.')
    if not service[0].isalnum():
        raise TVaultException('Service name must start with a letter or a number.')
    
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
    if 2 <= len(sys.argv) <= 4:
        try:
            run(sys.argv[1:])
        except SubrunException as e:
            print(f'Error while executing {e.command}.')
            print(e.errortext)
            sys.exit(1)
        except Exception as e:
            print(f'Error: {e}')
            sys.exit(1)
    else:
        print(f"""
{__doc__}
version {__version__}
Copyright (C) 2023 {__author__}
{__license__}
{usage}
""")
