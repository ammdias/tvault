#!/usr/bin/env python3
"""Installation script for TOTP Vault program.
"""

FILES = ('tvault.py', 'LICENSE.md', 'README.md',
         '__version__', 'CHANGES.md')
APP_NAME = 'TVault' # will be the name of installation directory
START_SCRIPT = 'tvault.py'
LINK_NAME = 'tvault'
CONFIG_FILES = ()  # must be a tuple or list

__version__ = '0.1'
__date__ = '2023-10-27'
__author__ = 'António Manuel Dias <ammdias@gmail.com>'
__license__ = '''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import os.path
import shutil
from itertools import zip_longest

PKG_DIR = sys.path[0]
INSTALL_DIR = os.path.join('~', '.local', 'lib')
BIN_DIR = os.path.join('~', '.local', 'bin')
CONFIG_DIR = os.path.join('~', '.config')


def _quit(msg):
    '''Print error message and quit.
    '''
    print(f'Error: {msg}\n', file=sys.stderr)
    sys.exit(1)


def yesno(question):
    """Get a yes or no answer to a question.
    """
    answer = ''
    while answer not in ('y', 'yes', 'n', 'no'):
        answer = input(question + ' (y/n): ').strip().lower()

    return answer in ('y', 'yes')


try:
    # print greeting
    print(__doc__)
    print('Version:', __version__)
    print('Copyright (C) 2023', __author__)
    print(__license__)


    # get installation directories
    d = input(f'Installation directory [{INSTALL_DIR}]: ').strip()
    INSTALL_DIR = os.path.expanduser(os.path.join(d or INSTALL_DIR, APP_NAME))
    START_SCRIPT_PATH = os.path.join(INSTALL_DIR, START_SCRIPT)

    d = input(f'Start link directory [{BIN_DIR}]: ').strip()
    BIN_DIR = os.path.expanduser(d or BIN_DIR)
    LINK_PATH = os.path.join(BIN_DIR, LINK_NAME)

    if CONFIG_FILES:
        d = input(f'Configuration files directory [{CONFIG_DIR}]: ').strip()
        CONFIG_DIR = os.path.expanduser(d or CONFIG_DIR)
        if len(CONFIG_FILES) > 1:
            CONFIG_DIR = os.path.join(CONFIG_DIR, APP_NAME)

    print()


    # check if install path exists and clean it if it does
    if PKG_DIR == INSTALL_DIR or PKG_DIR == BIN_DIR:
        _quit("Installation directory cannot be the same as package directory.")
    try:
        if os.path.exists(INSTALL_DIR):
            try:
                with open(os.path.join(INSTALL_DIR, '__version__'), 'r') as f:
                    oldversion = f.read().strip()
            except:
                pass  # corrupted previous installation? just remove it.
            else:
                print(f'Version {__version__} will be installed '
                      f'over existing version {oldversion}.')
                if not yesno('Proceed anyway?'):
                    _quit("Installation interrupted by user.")
                print()
            print('Removing old version...')
            shutil.rmtree(INSTALL_DIR)
        if os.path.lexists(LINK_PATH):
            print('Removing old symbolic link to startup script...')
            os.remove(LINK_PATH)
    except Exception as e:
        _quit(f"Could not remove old installation. Reason:\n{e}")


    # copy files to install directory
    try:
        print('Creating installation directory...')
        os.makedirs(INSTALL_DIR)
        print('Copying files:')
        for i in FILES:
            print(f'... {i}')
            shutil.copy2(os.path.join(PKG_DIR, i), INSTALL_DIR) 
    except Exception as e:
        _quit(f"Could not copy files to installation directory. Reason:\n{e}")


    # make symbolic link to application start script
    try:
        print('Creating symbolic link to startup script...')
        os.chmod(START_SCRIPT_PATH, 0o755)
        os.makedirs(BIN_DIR, exist_ok=True)
        os.symlink(START_SCRIPT_PATH, LINK_PATH)
    except Exception as e:
        _quit(f"Could not create symbolic link to application script. Reason:\n{e}")

    # copy default configuration files, if they don't already exist
    if CONFIG_FILES:
        try:
            print('Creating configuration files directory...')
            os.makedirs(CONFIG_DIR, exist_ok=True)
            print('Copying necessary configuration files:')
            for i in CONFIG_FILES:
                if not os.path.exists(os.path.join(CONFIG_DIR, i)):
                    print(f'... {i}')
                    shutil.copy2(os.path.join(PKG_DIR, i), CONFIG_DIR) 
        except Exception as e:
            _quit(f"Could not copy configuration files. Reason:\n{e}")

    print('\nApplication successfully installed.\n')

except:
    print("\nInstallation interrupted by user or unknown error.\n")
