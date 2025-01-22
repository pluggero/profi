import urllib.parse
import base64
import sys
import re

def url_encode(data):
    return urllib.parse.quote(data)

def base64_encode(data):
    return base64.b64encode(data.encode()).decode()

def base64pwsh_encode(data):
    # blank command will store our fixed unicode variable
    blank_command = ""
    powershell_command = ""
    # Remove weird chars that could have been added by ISE
    n = re.compile(u'(\xef|\xbb|\xbf)')
    # loop through each character and insert null byte
    for char in (n.sub("", data)):
        # insert the nullbyte
        blank_command += char + "\x00"
    # assign powershell command as the new one
    powershell_command = blank_command
    # base64 encode the powershell command
    powershell_command = base64.b64encode(powershell_command.encode())
    return powershell_command.decode("utf-8")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: echo 'Hello World' | url_encode.py [--url | --base64 | --base64pwsh ]")
        sys.exit(1)

    option = sys.argv[1]

    # Read input from stdin (this works with piped input)
    input_string = sys.stdin.read().rstrip('\n')

    if option == '--url':
        encoded_string = url_encode(input_string)
    elif option == '--base64':
        encoded_string = base64_encode(input_string)
    elif option == '--base64pwsh':
        encoded_string = base64pwsh_encode(input_string)
    else:
        print("Invalid option. Use --url, --base64 or --base64pwsh.")
        sys.exit(1)

    print(encoded_string, end ='')

