#!/usr/bin/python3
#pylint: disable=missing-docstring
#pylint: disable-msg=C0103
import ipaddress
import string
import sys
import yaml

def set_default(user_input, default):
    if user_input == '':
        user_input = default
        return user_input
    return user_input

host = input('IP address of the computer with the music player: ')
try:
    ip = ipaddress.ip_address(host)
except ValueError as err:
    print(err)
    sys.exit(1)
port = input('Port used by the beefweb plugin (default: 8880) ')
port = set_default(port, 8880)
server_url = 'http://' + host + ':' + str(port)

shdn_gpio = input('GPIO used for Shutdown pin (default: 23) ')
shdn_gpio = set_default(shdn_gpio, 23)

offset = input('TMark negative offset in seconds: (default: 0.1) ')
offset = set_default(offset, 0.1)

press = input('Duration of a short button press in seconds: (default: 0.03) ')
press = set_default(press, 0.03)

hold = input('Duration of a long button press in seconds: (default: 2.1) ')
hold = set_default(hold, 2.1)

button_dict = {
    'Play' : 255,
    'Left' : 251,
    'Right': 237,
    'Pause' : 228,
    'Stop' : 217,
    'TMark' : 190,
    'Display' : 161,
    'Record' : 142
}

#character set navigation for MZ-R90
set_moves = {'uppercase': {'uppercase':1, 'lowercase':2, 'numbers':3},
             'lowercase': {'uppercase':3, 'lowercase':1, 'numbers':2},
             'numbers':   {'uppercase':2, 'lowercase':3, 'numbers':1}}

#character set for MZ-R90
common_set = ["'", ',', '/', ':', ' ']
uppercase_set = list(string.ascii_uppercase)
lowercase_set = list(string.ascii_lowercase)
numbers_set = (list(string.digits)
               + ['!', '"', '#', '$', '%', '&', '(', ')', '*', '.', ';',
                  '<', '=', '>', '?', '@', '_', '`', '+', '-'])
complete_set = common_set + uppercase_set + common_set + lowercase_set + common_set + numbers_set

entrypoints = {'uppercase':complete_set.index('A'),
               'lowercase':complete_set.index('a'),
               'numbers':complete_set.index('0')}

for button in button_dict:
    wiper_value = input(f"Wiper value for {button}: (default: {str(button_dict[button])})")
    button_dict[button] = set_default(wiper_value, button_dict[button])

with open('settings.conf', 'w') as config_file:
    yaml.dump({'server_url':server_url,
               't_offset':offset,
               't_press':press,
               't_hold':hold,
               'wipers':button_dict,
               'shdn':shdn_gpio,
               'c_set_moves':set_moves,
               'c_complete':complete_set,
               'c_entrypoints':entrypoints,
               'c_common_set':common_set,
               'c_uppercase_set':uppercase_set,
               'c_lowercase_set':lowercase_set,
               'c_numbers_set':numbers_set},
              config_file)
