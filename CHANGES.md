TOTP Vault
==========

(C) 2023 António Manuel Dias

Changes List:

    * 0.5: Added support for Wayland clipboard (wl-clipboard).

    * 0.4: Added uninstall option.
           Simplified path discovery.
           Changed installation script.
           Updated README file.

    * 0.3: Added `-recipient` and `-symmetric` options.
           CLI error messages are now printed in stderr instead of stdout.
           Script exits with error if -gui option passed when a GUI is not
               available. Also, it will not try to add the code to the
               clipboard in the same situation.
           Service names must consist of letters and numbers.
           Updated README file.

    * 0.2: Added `-secret` option.
           Added `-gui` option.
           Service identifiers must start with letter or number.
           Removed `xclip` clipboard manager option, because of problems with
               `subprocess.run()` with option `capture_output=True`.
           Updated README file.

    * 0.1: Initial version.
