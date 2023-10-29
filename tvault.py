#!/usr/bin/env python3

"""TVault
Command line script to store Time-based One-Time Password (TOTP)  secret keys
and generate TOTP passwords for two-factor authentication (2FA) on services that
require it.  Depends on GnuPG for encrypting TOTP secrets and oathtool to generate
the passwords.
"""

__version__ = '0.1'
__date__ = '2023-10-29'
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
  List all available services:
  $ tvault -list

  Add SERVICE to available services:
  $ tvault -add SERVICE SECRET

  Remove SERVICE from available services:
  $ tvault -del SERVICE

  Change vault password:
  $ tvault -chpass

  Generate TOTP for SERVICE:
  $ tvault SERVICE
"""


def run(args):
    """Main function."""

    # get tool paths
    tools = gettoolpaths('gpg', 'oathtool', 'xclip', 'xsel')
    if 'gpg' not in tools or 'oathtool' not in tools:
        error("TOTP Vault needs GnuPG and oathtool to run.\n"
              "Please make sure these are installed and in the PATH.")
    if 'xclip' not in tools and 'xsel' not in tools:
        print("Neither xclip or xsel are installed.\n"
              "Generated codes will not be automatically copied to clipboard.\n"
              "If you want this feature, please install one of those tools.")

    # get vault file path
    vaultpath = getvaultpath()

    # execute action: list, add, delete or generate TOTP
    match args[0], len(args):
        case '-list', 1:
            listservices(tools, vaultpath)
        case '-add', 3:
            addservice(tools, vaultpath, *args[1:])
        case '-del', 2:
            deleteservice(tools, vaultpath, args[1])
        case '-chpass', 1:
            changepassword(tools, vaultpath)
        case service, 1:
            generatetotp(tools, vaultpath, service)
        case _:
            print(usage)


def listservices(tools, vaultpath):
    """List services available on vault file."""
    services = decrypt(tools, vaultpath)
    print('Available services:')
    if services:
        for name in services:
            print(f"* {name}")
    else:
        print("No service has been added yet.")


def addservice(tools, vaultpath, service, secret):
    """Add service to vault file."""
    service, secret = sanitycheck(service, secret)
    services = decrypt(tools, vaultpath)
    services[service] = secret
    encrypt(tools, vaultpath, services)


def deleteservice(tools, vaultpath, service):
    """Delete service from vault file."""
    services = decrypt(tools, vaultpath)
    if service not in services:
        error(f"Service '{service}' not found.")

    del services[service]
    encrypt(tools, vaultpath, services)


def changepassword(tools, vaultpath):
    """Change vault file password."""
    services = decrypt(tools, vaultpath)
    encrypt(tools, vaultpath, services)


def generatetotp(tools, vaultpath, service):
    """Generate TOTP for service on vault file."""
    services = decrypt(tools, vaultpath)
    if service not in services:
        error(f"Service '{service}' not found.")

    res = subprocess.run([tools['oathtool'], '--base32', '--totp',
                         services[service]], capture_output=True)
    if res.returncode != 0:
        error("Error running oathtool.")

    totp = res.stdout.decode(sys.stdout.encoding).strip()
    print(f"TOTP code for '{service}': {totp}")

    # if possible, copy code to clipboard
    clipboardinsert(tools, totp)


def gettoolpaths(*tools):
    """Check system for tool paths.
       Returns dictionary with paths for tools."""
    res = {}
    for t in tools:
        path = shutil.which(t)
        if path:
            res[t] = path

    return res


def getvaultpath():
    """Get vault file path."""
    home = os.path.expanduser('~')
    config_dir = os.path.join(home, '.config')
    if os.path.isdir(config_dir):
        return os.path.join(config_dir, 'tvault')
    else:
        return os.path.join(home, '.tvault')


def encrypt(tools, vaultpath, services):
    """Encode and encrypt service/secret pairs into vault file."""
    # build vault from services' name / secret pairs
    # one service perline, separator is ':'
    vault = '\n'.join(f"{name}:{services[name]}" for name in services)
    res = subprocess.run([tools['gpg'], '--quiet', '--symmetric', '--armour',
                         '--yes', '--output', vaultpath],
                         input=vault.encode(sys.stdin.encoding))
    if res.returncode != 0:
        error(f"Unable to write vault file at '{vaultpath}'.")


def decrypt(tools, vaultpath):
    """Decrypt vault file,
       return dictionary with service/secret pairs."""
    services = {}
    if not os.path.exists(vaultpath):
       encrypt(tools, vaultpath, services)

    res = subprocess.run([tools['gpg'], '--quiet', '--decrypt', vaultpath],
                         capture_output = True)
    if res.returncode != 0:
       error(f"Wrong password or corrupted vault file at '{vaultpath}'.")

    # read vault service names / secret codes
    # one service per line
    # empty lines or lines started with ';' are ignored
    for line in res.stdout.decode(sys.stdout.encoding).splitlines():
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        name, sep, secret = line.partition(':')
        if not sep or not secret:
            error(f"Corruted line in vault at '{vaultpath}'.")
        services[name] = secret

    return services


def sanitycheck(service, secret):
    """Sanity check service name and secret."""
    service, secret = service.strip(), secret.strip()
    if not service or not secret:
        error("Service name and secret must not be empty.")
    if ':' in service:
        error("Service name must not contain a colon.")
    if service.startswith(';') or service.startswith('-'):
        error("Service name must not start with semicolon or dash.")
    
    return service, secret


def clipboardinsert(tools, text):
    """Insert text on primary and secondary clipboard."""
    text = text.encode(sys.stdin.encoding)

    if tools['xclip']:
        subprocess.run([tools['xclip'], '-in', '-selection', 'primary'], input=text)
        subprocess.run([tools['xclip'], '-in', '-selection', 'clipboard'], input=text)
        
    elif tools['xsel']:
        subprocess.run([tools['xsel'], '--input', '--primary'], input=text)
        subprocess.run([tools['xsel'], '--input', '--clipboard'], input=text)

    else:
        return

    print("Code automatically copied to clipboard.")


def error(text):
    """Show error message and exit."""
    print(f"Error: {text}")
    sys.exit(1)


#------------------------------------------------------------------------------

if __name__ == "__main__":
    if 2 > len(sys.argv) or len(sys.argv) > 4:
        print(f"""
{__doc__}
version {__version__}
Copyright (C) 2023 {__author__}
{__license__}
{usage}
""")
    else:
        run(sys.argv[1:])
