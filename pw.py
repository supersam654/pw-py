#!/usr/bin/env python3
import sys, os
import subprocess as sp
import getpass
import string

from os.path import expanduser # works on all platforms, except when Windows AD maps to network drive
home_path = expanduser("~")
pubk_directory = '{}/.pw-py/keys/'.format(home_path)
pw_directory = '{}/.pw-py/pws/'.format(home_path)
shared_key_file = pubk_directory + 'shared.key'

os.makedirs(pubk_directory, exist_ok=True)
os.makedirs(pw_directory, exist_ok=True)

USAGE = "\nNAME\n\tpw-py - password manager written in python\n\nSYNOPSIS\n\t./pw-py [OPTION] [SITENAME]\n\nDESCRIPTION\n\t-i, --initialize\n\t\tSet up local / shared key\n\t-g, --generate [SITENAME]\n\t\tgenerate password for site\n\n\t-s, --show [SITENAME]\n\t\tshow password for site\n\t-c --clipboard [SITENAME]\n\t\tcopy password for site to clipboard\n"

def gen_password(length):
    import string
    printable = string.ascii_letters + string.digits + string.punctuation
    try:
        import secrets
        sec = secrets.SystemRandom()
    except ImportError:
        import random
        sec = random.SystemRandom()
    pw = [None] * length
    for i in range(length):
        pw[i] = sec.choice(printable)
    return pw

def encrypt_arr_to_file(byte_arr, file_name):
    args = ['gpg', '--armor', '-e', '-r', 'pw-py', '-o', file_name]
    p = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE, bufsize=1, universal_newlines=True)
    for i in range(len(byte_arr)):
        p.stdin.write(byte_arr[i])
        byte_arr[i] = None
    p.stdin.write("\n")
    res = p.communicate()[0]

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(USAGE)
    elif sys.argv[1] == '-i' or sys.argv[1] == '--init':
        master_pw = getpass.getpass("Enter a master password - DO NOT lose this or you will lose access to the passwords stored on this computer:\n")
        master_pw2 = getpass.getpass("Re-enter the master password:\n")
        if master_pw != master_pw2:
            print("Passwords did not match! Re-run the script and enter matching passwords")
            sys.exit(0)
        print("**** GENERATING GPG KEY\n")
        with open('key-params.txt', 'r') as fd:
            key_params = fd.read()
        args = ['gpg', '--gen-key', '--batch']
        p = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE, bufsize=1, universal_newlines=True)
        p.stdin.write(key_params.format(master_pw))
        public_key = p.communicate()[0]
        print(public_key)

        import platform
        pubk_filename = pubk_directory + platform.node() + ".gpg"
        args = ['gpg', '--armor', '--export', 'pw-py']
        p = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE, bufsize=1, universal_newlines=True)
        text = p.communicate()[0]
        with open(pubk_filename, 'w') as public_key_file:
            public_key_file.write(public_key)
        print("**** EXPORTED GPG KEY TO {}".format(pubk_filename))

        if os.path.isfile(shared_key_file):
            # re-encrypt file
            print("**** Re-encrypting shared key")
            print("**** Done pretending to re-encrypt " + shared_key_file)
        else:
            print("**** Generating new shared key")
            shared_key = gen_password(128)
            encrypt_arr_to_file(shared_key, shared_key_file)
            print("**** Exported encrypted shared key to " + shared_key_file)

    elif sys.argv[1] == '-g' or sys.argv[1] == '--generate':
        print ("**** GENERATING AND SAVING PASSWORD")
        if len(sys.argv) < 3:
            print ("**** Specify website or storage phrase to generate a password")
            # TODO: specify options for length, etc

        # TODO: allow actual character limitations
        reqUpper = True
        reqLower = True
        reqDigit = True
        reqSpecial = True
        reqs = [
            lambda x: not reqUpper or (any(c.isupper() for c in x)),
            lambda x: not reqLower or (any(c.islower() for c in x)),
            lambda x: not reqDigit or (any(c.isdigit() for c in x)),
            lambda x: not reqSpecial or (any(c in string.punctuation for c in x))
        ]
        while True:
            pw = gen_password(20)
            reqs_met = True
            for i in reqs:
                if not i(pw):
                    reqs_met = False
            if reqs_met:
                break

        pw = "".join(str(c) for c in pw)
        pw_filename = pw_directory + sys.argv[2]

        master_pw = getpass.getpass("Master password: ")
        args1 = ['gpg', '-d', '--batch', '--passphrase', master_pw, shared_key_file]
        p1 = sp.Popen(args1, stdin=sp.PIPE, stdout=sp.PIPE)
        shared_key = p1.communicate()[0]
        shared_key = str(shared_key, 'utf-8').strip()

        args2 = ['gpg', '--armor', '--symmetric', '--cipher-algo', 'AES256', '--passphrase', shared_key, '-o', pw_filename]
        p2 = sp.Popen(args2, stdin=sp.PIPE, stdout=sp.PIPE, bufsize=1, universal_newlines=True)
        p2.stdin.write(pw)
        output = p2.communicate()[0]
        print ("**** Saved password to {0}".format(sys.argv[2]))

    elif (sys.argv[1] == "--show" or sys.argv[1] == "-s" or sys.argv[1] == "--clipboard" or sys.argv[1] == "-c") and len(sys.argv) >= 3:
        pattern = sys.argv[2]
        import glob
        matching_files = glob.glob(pw_directory + "*" + pattern + "*")
        if len(matching_files) == 0:
            print ("Unable to find match for: {}".format(pattern))
        elif len(matching_files) > 1:
            print ("Found multiple matches, please try again specifying which one")
            print (matching_files)
        else:
            master_pw = getpass.getpass("Master password: ")
            args1 = ['gpg', '-d', '--batch', '-q', '--passphrase', master_pw, shared_key_file]
            p1 = sp.Popen(args1, stdin=sp.PIPE, stdout=sp.PIPE)
            shared_key = p1.communicate()[0]
            shared_key = str(shared_key, 'utf-8').strip()

            args2 = ['gpg', '-q', '--passphrase', shared_key, '-d', matching_files[0]]
            p2 = sp.Popen(args2, stdin=sp.PIPE, stdout=sp.PIPE)
            output = p2.communicate()[0]
            output = str(output, 'UTF-8').strip()

            if sys.argv[1] == "--show" or sys.argv[1] == "-s":
                print (output)
            else:
                print ("PRETENDING TO COPY TO CLIPBOARD")
    else:
        print ("****Unrecognized option")
        print (USAGE)
