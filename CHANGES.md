TOTP Vault
==========

(C) 2023 António Manuel Dias

Changes List:

    * 0.2: Added `-secret` option.
           Added `-gui` option.
           Service identifiers must start with letter or number.
           Removed `xclip` clipboard manager option, because of problems with
               `subprocess.run()` with option `capture_output=True`.
           Updated README file

    * 0.1: Initial version.
