TVault
======
version 0.1

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
(2FA) on services that require it. It depdends on `GnuPG` to encrypt the file
where the secret keys are stored and `oathtool` to generate the passwords. If
`xclip` or `xsel` are installed on the system, it will also copy the generated
passwords to the system clipboard (primary and secondary) so that they may be
pasted on the service's login form.


INSTALLATION AND BASIC USAGE
============================

The following instructions describe the installation process for basic usage
in a Linux environment.

1. Open a terminal in the directory where the program was uncompressed and run
   the installation script with Python 3:

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
         
     The program should print the License notice and usage on the terminal.
     
3. Usage:
   
     Before using the program, make sure `GnuPG` and `oathtool` are installed
     on your system. The script will not work without them. Also, if you
     want the script to copy the generated codes to the clipboard, which is
     a nice feature to have, so that you don't need to memorize them or
     copy them yourself, you should install `xclip` or `xsel`.
    
     When configuring Two-Factor Authentication (2FA) for a new service you
     should choose "TOTP based authentication". The service will then present
     you with your secret key, which should be a long alphanumeric string.
    
     To add that service to TVault's store use the command:
    
          $ tvault -add SERVICE SECRET
    
     Replace `SERVICE` with the name of the service (it's just an identifier,
     so it's your choice) and `SECRET` with the string given by the service.
     If the secret key has spaces you may remove them or envelop the string
     in quotes. For example, to add the secret key for a Mastodon instance:
    
         $ tvault -add mastodon "ABCD 1234 EFGH 5678 IJKL 90MN OPQR STUV"
    
     The program should ask for a password to encrypt the vault file (actually
     it is GnuPG's agent that asks for the password). That is the password
     that will protect all your secret keys for the configured services, so
     choose a strong one and keep it safe --- without it you will be unable to
     access you services. The file will be saved in the user's home directory,
     `$HOME/.config/tvault` (default) or `$HOME/.tvault`, if the `$HOME/.config`
     diretory does not exist.
     
     Then, generate the temporary password to finish configuring the service
     with the command:
   
         $ tvault SERVICE
        
     The program will print the generated password (6 digits) in the terminal
     and, if `xclip` or `xsel` are installed, copy it to the system clipboard.
     You may then insert it on the service input field. For example, for the
     Mastodon service added earlier:
     
         $ tvault mastodon
         TOTP code for 'mastodon': 123456
         Code automatically copied to clipboard.
    
     Any time the service asks for a 2FA code, just open a terminal and use the
     command above.
    
     You may list all the stored services with the command.
     
         $ tvault -list
    
     To delete a service no longer wanted:
     
         $ tvault -del SERVICE
         
     And, to change the vault file's password:
     
         $ tvault -chpass
     
     Note that each time the stored filed is read --- basically, every time you
     use the program --- you will be prompted for its password, unless you have
     used it recently and GnuPG agent has it cached. Similarly, every time the
     file is written --- on the `add`, `del` and `chpass` actions --- you will
     be prompted for the password to encrypt it. You may use the same password
     as before or change it.
