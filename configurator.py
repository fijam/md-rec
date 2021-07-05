#!/usr/bin/python3
import yaml
import ipaddress

def set_default(input,default):
	if input == '':
		input = default
		return input
	else:
		return input

host = input('IP address of the computer with the music player: ')
try:
	ip = ipaddress.ip_address(host)
except ValueError:
	raise
port = input('Port used by the beefweb plugin (default: 8880) ')
port = set_default(port, 8880)
server_url = 'http://' + host + ':' + str(port)

offset = input('TMark negative offset in seconds: (default: 0.1) ')
offset = set_default(offset, 0.1)

press = input('Duration of a short button press in seconds: (default: 0.03) ')
press = set_default(press, 0.03)

hold = input('Duration of a long button press in seconds: (default: 2.2) ')
hold = set_default(hold, 2.2)

#defaults are currently wrong
button_dict = {
	'SearchLeft' : 12,
	'SearchRight': 24,
	'Pause' : 48,
	'Stop' : 64,
	'TMark' : 128,
	'Display' : 192,
	'Record' : 224
}

#character set navigation for MZ-R90
set_moves = {'uppercase': {'uppercase':1, 'lowercase':2, 'numbers':3 },
       		'lowercase': {'uppercase':3, 'lowercase':1, 'numbers':2 },
	        'numbers':   {'uppercase':2, 'lowercase':3, 'numbers':1 }}

for button in button_dict:
	wiper_value = input('Wiper value for ' + button +': (default: ' + str(button_dict[button]) + ') ' )
	button_dict[button] = set_default(wiper_value, button_dict[button])

with open('settings.conf', 'w') as config_file:
	yaml.dump({'server_url':server_url,
		'offset':offset,
		'press':press,
		'hold':hold,
		'wipers':button_dict,
		'set_moves':set_moves},
		config_file,
		default_flow_style=False)
