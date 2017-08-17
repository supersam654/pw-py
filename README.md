# pw-py
###### A simple python password manager. Work-in-progress.

### Usage
`./pw.py --help` (or -help, -h, and --h)


### Features
- Use one master password to manage all other passwords
- Display passwords on demand
- Generates random passwords with upper/lower/numeral/special

### TODO
- Enable copying passwords to clipboard instead of displaying
- Add shared key re-encryption when new pubkeys are added
- Allow users to specify password generation rules
- Allow users to manually enter passwords
- Allow users to change passwords in a prettier way than having gpg prompt overwrite
- Shush the remaining happy-path gpg logging
- Add a custom sync service?

### Requirements
- `gpg` supporting RSA2048 and AES256
- `python 3`

### Disclaimer
This program is not guaranteed to be secure. The authors are not liable for any loss (data, personal, or other) that may result as a result of using this program.

### Security Model
This assumes that the physical machine has not been compromised. The integrity of python and gpg are assumed, as well as the absence of any keyloggers or other malware that could intercept the master password, dump sensitive information from the python memory segment, or otherwise snoop.
