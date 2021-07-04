#!/usr/bin/python3
import sys
import string
import time
import datetime
import configparser

import requests
import spidev
import RPi.GPIO as GPIO
from unidecode import unidecode

# configuration
conf_file = 'settings.conf'
config = configparser.ConfigParser()
config.optionxform = lambda option: option # preserve case
try:
	with open(conf_file) as f:
		config.read_file(f)
except (FileNotFoundError, IOError):
	print('No settings file found. Run configurator.py script first')
	sys.exit(1)

server_url = config['Network']['server_url']
offset = config['Timings'].getfloat('offset')
press = config['Timings'].getfloat('press')
hold = config['Timings'].getfloat('hold')
wiper_dict = dict(config['Wipers'])

# functions
def request_playlist_info(server_url):
	urlendpoint = server_url + '/api/playlists'
	response = requests.get(urlendpoint)
	# return a tuple of playlist ID and number of tracks
	return response.json()['playlists'][0]['id'], response.json()['playlists'][0]['itemCount']

def request_playlist_content(server_url,playlist_info):
	tracklist = []
	total_time = 0
	playlist_ID = playlist_info[0]
	item_count = playlist_info[1]
	urlendpoint = server_url + '/api/query'
	payload = {'playlists':'true','playlistItems':'true','plref':playlist_ID,'plrange':'0:'+str(item_count),'plcolumns':'%artist% - %title%, %length_seconds%'}
	response = requests.get(urlendpoint, params=payload)

	for track in range(item_count):
		sanitized_track_name = unidecode(response.json()['playlistItems']['items'][track]['columns'][0])
		print(sanitized_track_name)
		tracklist.append(sanitized_track_name)
		total_time += int(response.json()['playlistItems']['items'][track]['columns'][1])
	print('Total playlist duration: ' + str(datetime.timedelta(seconds=total_time)))
	if total_time >= 4800:
		print('Warning: duration exceeds 80 minutes!')
	if item_count > 254:
		print('Warning: cannot record more than 254 tracks!')
	# return a list of tracks to label
	return tracklist

def request_track_remaining(server_url):
	urlendpoint = server_url + '/api/player'
	response = requests.get(urlendpoint)
	remaining = response.json()['player']['activeItem']['duration'] - response.json()['player']['activeItem']['position']
	# return remaining time in track (in seconds)
	return remaining

def set_mode_play(server_url,playlist_info):
	urlendpoint = server_url + '/api/player'
	requests.post(urlendpoint, params = {'isMuted':'false','playbackMode':'0'} ) # set default playback mode
	requests.post(urlendpoint + '/play/' + playlist_info[0]+'/0')

def set_stop(server_url):
	urlendpoint = server_url + '/api/player'
	requests.post(urlendpoint + '/stop')

def input_string(string_normalized,press,hold):
	# this function needs work
	track_letterlist = list(string_normalized)
	current_set = 'uppercase' # default
	common_set = [ "'", ',', '/', ':', ' ']
	common_set.reverse() # we move backwards on this list
	uppercase_set = list(string.ascii_uppercase)
	lowercase_set = list(string.ascii_lowercase)
	numbers_set = list(string.digits) + ['!', '"', '#', '$', '%', '&', '(', ')', '*', '.', ';', '<', '=', '>', '?', '@', '_', '`', '+', '-']
	#unsupported_set = ['[', '\', ']', '^', '{', '|', '}', '~']

	for letter in track_letterlist:
		if (letter in common_set):
			push_button('Pause',press,1)
			push_button('SearchLeft',press,common_set.index(letter)+1)
			push_button('Stop',press,1)
		elif (letter in uppercase_set):
			enter_correct_set('uppercase',current_set,press)
			push_button('SearchRight',press,uppercase_set.index(letter))
			push_button('Stop',press,1)
			current_set = 'uppercase'
		elif (letter in lowercase_set):
			enter_correct_set('lowercase',current_set,press)
			push_button('SearchRight',press,lowercase_set.index(letter))
			push_button('Stop',press,1)
			current_set = 'lowercase'
		elif (letter in numbers_set):
			enter_correct_set('numbers',current_set,press)
			push_button('SearchRight',press,numbers_set.index(letter))
			push_button('Stop',press,1)
			current_set = 'numbers'
		else:
			enter_correct_set('numbers',current_set,press)
			push_button('SearchRight',press,24) # catch-all replace with '?'
			push_button('Stop',press,1)
			current_set = 'numbers'

	push_button('Stop',hold,1)


def enter_correct_set(wanted_set,current_set,press):
	# look up how many times to press 'Pause' to get to the wanted charset
	set_moves = { 	'uppercase': {'uppercase':1, 'lowercase':2, 'numbers':3 },
        		'lowercase': {'uppercase':3, 'lowercase':1, 'numbers':2 },
		        'numbers':   {'uppercase':2, 'lowercase':3, 'numbers':1 }}

	times = set_moves[current_set][wanted_set]
	push_button('Pause',press,times)

def hw_push(type,wiper):
	#SPI MAGIC
	command0 = 0b00000000 # CH0: 00h address + 00 write cmd + 00 data
	command1 = 0b00010000 # CH1: 01h address + 00 write cmd + 00 data
	spi.xfer([command0, wiper])
	spi.xfer([command1, wiper])
	GPIO.output(23,1) # disable SHDN pin
	time.sleep(type)
	GPIO.output(23,0) # enable SHDN pin
	time.sleep(type)

def push_button(button,type,times):
	for i in range (times):
		# wiper values for each button from the config file
		hw_push(type,int(wiper_dict[button]))

def cleanup_exit():
	push_button('Stop',press,1)
	set_stop(server_url)
	GPIO.cleanup()
	print('Bye!')
	sys.exit(0)


# hardware setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 976000

# actual program starts here

print('> Connect your Sony Recorder and insert a blank MD')
input('Press Enter when ready.')
push_button('Record',press,1) # REC Standby
time.sleep(0.5)
print('REC Standby...')

print('> Open up Foobar2000 with the playlist you want to record')
input('Press Enter when ready.')
print('The following tracks will be burned & labelled:')
playlist_info = request_playlist_info(server_url)
tracklist = request_playlist_content(server_url,playlist_info)
input('Press Enter to begin.')

push_button('Pause',press,1) # start recording
set_mode_play(server_url,playlist_info)

for track_number, track in enumerate(tracklist):
	try:
		print('Recording: ' + tracklist[track_number])
		time.sleep(0.5)
		push_button('Display',hold,1)
		push_button('Stop',press,2) # enter labelling mode
		input_string(tracklist[track_number],press,hold)
		track_remaining = request_track_remaining(server_url)
		print(f'Track labelled. Time to TMark: {track_remaining:0.0f}s')
		time.sleep(track_remaining - offset)
		if track_number+1 != len(tracklist):
			push_button('TMark',press,1)
		else:
			push_button('Stop',press,1)

	except KeyboardInterrupt:
		answer = input('\nFinish recording current track? [Y/N] ')
		if answer == 'Y':
			track_remaining = request_track_remaining(server_url)
			print('Finishing track: ' + track + f' left: {track_remaining:0.0f}s')
			time.sleep(track_remaining - offset)
			cleanup_exit()
		else:
			cleanup_exit()

print('Waiting for TOC to save...')
time.sleep(10)
cleanup_exit()
