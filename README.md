TVault
======
version 0.5

Copyright (C) 2023 António Manuel Dias

contact: ammdias@gmail.com

website: [AMMDIAS GitHub](https://github.com/ammdias/tvault)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.


ABOUT THE PROGRAM
=================

TVault is a Linux command line script to store Time-based One-Time Password
(TOTP) secret keys and generate TOTP passwords for two-factor authentication
(2FA) on services that require it. It depends on `GnuPG` to encrypt the file
where the secret keys are stored and `oathtool` to generate the passwords. If
`xsel` is installed on the system, it will also copy the generated passwords
to the system clipboard (PRIMARY *and* CLIPBOARD) so that they may be pasted
on the service's login form.

TVault may also be used with a graphic interface for adding new services or
generating TOTP codes. For this, `zenity` must be installed on the system,
but this is the default on most distributions.


INSTALLATION AND BASIC USAGE
============================

## Installation

The following instructions describe the installation process for basic usage
in a Linux environment.

1. Download the zip file containing the program and uncompress it. Then, open a
   terminal in the directory where the program was uncompressed and run the
   installation script with Python 3:

         $ python3 INSTALL.py

     You will be prompted for the installation directory --- i.e. the directory
     under which the folder containing all the application files will be placed
     --- and for the start link directory --- i.e. the directory where the
     symbolic link for the program will be created.

     The default directories will install the program for the current user only
     and are suited for single-user systems.  If you want to keep these
     settings, just press ENTER when prompted.  The program will be installed in
     the directory `$HOME/.local/lib/TVault` and the symbolic link
     `$HOME/.local/bin/tvault` will be created.  On most Linux systems the
     `$HOME/.local/bin` directory will be inserted in the execution PATH, if it
     exists. If it doesn't, you will have to add it manually.

     If you want to install the program for all the users of the system, you
     should change the directories accordingly, e.g. `/usr/local/lib` for the
     installation directory and `/usr/local/bin` for the start link.  Of
     course, you will need to run the installation script with administration
     privileges:

         $ sudo python3 INSTALL.py

     If a previous installation exists on the selected directory, you will be
     asked if you want to overwrite it.  Answer "`yes`" (or just "`y`") if that
     is the case or "`no`"/"`n`" if not.

2. Test that the installation was successful with the command:

         $ tvault
         
     The program should print the license notice and usage on the terminal.


## Usage:
   
Before using the program, make sure `GnuPG` and `oathtool` are installed
on your system. The script will not work without them. Also, if you
want the script to copy the generated codes to the clipboard, which is
a nice feature to have so that you don't need to memorize them or
copy them yourself, you should install `xsel` if you are using X11 or
`wl-clipboard`, for `wl-copy`, if you are in Wayland instead.
    

### First use
     
If there is no vault file (the secret key storage) already created by a
previous installation, the program will create one the first time it is
run. The vault file is a simple text file encrypted by GnuPG, stored at
the user's home directory at `$HOME/.config/tvault` or `$HOME/.tvault`
if the directory `$HOME/.config` does not exist. You should backup this
file regularly, as it will store all service's secret keys used to
generate the TOTP codes to access the service's sites.

You may create the file by listing the stored keys:

    $ tvault -list

GnuPG will now ask for the key to encrypt the file. Enter the key in the
form and the file will be created. If everything goes well the program will
terminate stating that no services have been added yet.

You may also use the program's graphical user interface to do the same:

    $ tvault -gui

As with the option above, GnuPG will ask for the key to encrypt the file.
Then, it will show the service list dialog, with the option to add a new
a new service. You may press "Cancel" to close the dialog and then "OK"
to terminate the program.


### Adding a service (on the terminal)
     
When configuring Two-Factor Authentication (2FA) for a new service you
should choose "TOTP based authentication" in its site. The service will
then present you with your secret key, which should be a long alphanumeric
string.

To add that service to TVault's store use the command:

    $ tvault -add SERVICE SECRET

Replace `SERVICE` with the name of the service (it's just an identifier,
so it's your choice) and `SECRET` with the string given by the service.
If the secret key has spaces you may remove them or envelop the string
in quotes. For example, to add the secret key for a Mastodon instance:

    $ tvault -add mastodon "ABCD EFGH IJKL MNOP QRST UVWX YZ23 4567"

GnuPG will now ask for the key to open the vault file (the same you used
when creating the file) and then the key to encrypt the file again.
Every time you change the file it will be completely overwritten, using
the key you choose --- i.e. you may change the key or use the same, at
your option.

If the operation is successful, the service will be added to the vault
and the program will generate and print a new TOTP code for this service,
to finalize the setup on the site. If `xsel`, on X11, or `wl-clipboard`,
in Wayland are installed, this code will be copied to the clipboard and
may be pasted at the service's site form.


### Adding a service (on the graphical user interface)

To add a service using the graphical interface, start the script with
the `-gui` option, as described in 3.1 and insert the key to decrypt the
vault file, if the program asks for it.  Then select the option
`* Add a new service...`, insert the service name, the secret key
for the service (see the section above) and finally the key to encrypt
the vault file.  If all goes well, a dialog with the TOTP code to finalize
the setup on the service's site.  As before, this code will be copied to
the clipboard if `xsel` or `wl-clipboard` are installed.
     

### Generate a TOTP 
     
To generate a TOTP code for a service, use the command:

    $ tvault SERVICE

The program will print the generated password (6 digits) in the terminal
and, if `xsel` or `wl-clipboard` are installed, copy it to the system 
clipboard.  You may then insert it on the service input field. For example,
for the Mastodon service added earlier:

    $ tvault mastodon
    TOTP code for mastodon: 123456
    Code copied to clipboard.

Any time the service asks for a 2FA code, just open a terminal and use the
command above.

When using the graphical user interface, just select the service on the
dialog and press `OK`.
     

### Managing the vault file from the terminal
    
You may list all the stored services with the command:

    $ tvault -list

To delete a service no longer wanted:

    $ tvault -del SERVICE
 
To check the secret key of a service:

    $ tvault -secret SERVICE
 
To change the vault file's password:

    $ tvault -chpass

Note that each time the stored filed is read --- basically, every time you
use the program --- you will be prompted for its password, unless you have
used it recently and GnuPG agent has it cached.  Similarly, every time the
file is written you will be prompted for the password to encrypt it. You
may use the same password as before or change it.

The vault file may also be encrypted with a GnuPG public key, if the user
already has a public/private key pair on GnuPG's keyring.  This will ease
the use of the script, as it doesn't need to ask for the password to encrypt
the file, only the secret key passphrase to decrypt it.  To do this, use
the command:

    $ tvault -recipient KEY_ID

Replace KEY_ID with the identification of the public key to use (its email
address).  If the private key for that public key is not in GnuPG's keyring,
the command will fail, preventing the encryption of the file with a key that
the user cannot decrypt.

To revert the file to a symmetric key encryption, use the command:

    $ tvault -symmetric


### Uninstall the program
     
You may uninstall the program with the command:

    $ tvault -uninstall

or, from within the directory where the program ins installed:

    $ python3 UNINSTALL.py
